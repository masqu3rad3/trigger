import os
import glob
import json
import logging

from maya import cmds, mel

from trigger.core.decorators import tracktime

LOG = logging.getLogger(__name__)


class FaceMocap:
    """Mocap handler for importing motion capture data from json and csv files."""

    def __init__(self):
        """Initialize the mocap handler.

        Args:
            json_file (str): Path to the json file.
            csv_file (str): Path to the csv file.
            keep_files (bool): Keep the json and csv files after import.

        """
        self._mapping = None
        self._start_frame = 1
        self._controller = None
        self.mappings_dictionary = {}

        self._get_mappings()  # get the available mappings

        # set the first mapping as the default (if available)
        if self.mappings_dictionary:
            self.set_mapping(list(self.mappings_dictionary.keys())[0])

        self._enable_neutralize = True
        self._neutralize_frame = 0

    @property
    def enable_neutralize(self):
        """Get the enable neutralize flag."""
        return self._enable_neutralize

    def set_enable_neutralize(self, value):
        """Set the enable neutralize flag."""
        if not isinstance(value, bool):
            raise ValueError("Enable neutralize must be a boolean.")
        self._enable_neutralize = value

    @property
    def mapping(self):
        """Get the mapping."""
        return self._mapping

    def set_mapping(self, mapping_name):
        """Set the mapping from the list of available mappings.

        Args:
            mapping_name (str): Name of the mapping.

        """
        mapping_path = self.mappings_dictionary[mapping_name]
        self._mapping = self._load_json(mapping_path)

    @property
    def neutralize_frame(self):
        """Get the neutralize frame."""
        return self._neutralize_frame

    def set_neutralize_frame(self, neutralize_frame):
        """Set the neutralize frame."""
        if not isinstance(neutralize_frame, int):
            raise ValueError("Neutralize frame must be an integer.")
        self._neutralize_frame = neutralize_frame
    @property
    def controller(self):
        """Get the controller."""
        return self._controller

    def set_controller(self, controller):
        """Set the controller."""
        self._controller = controller

    @property
    def start_frame(self):
        """Get the start frame."""
        return self._start_frame

    def set_start_frame(self, start_frame):
        """Set the start frame."""
        self._start_frame = start_frame

    def list_mappings(self):
        """List the available mappings."""
        mapping_names = list(self.mappings_dictionary.keys())
        LOG.info("Available Mappings: %s", mapping_names)
        return mapping_names

    def _get_mappings(self):
        """Get the available mappings."""
        self.mappings_dictionary = {}
        # look at the mappings directory and list the available .json mappings
        dir_path = os.path.dirname(os.path.realpath(__file__))
        mappings_dir = os.path.join(dir_path, "mappings")
        # glob all json files from the mappings directory
        mappings_list = glob.glob(os.path.join(mappings_dir, "*.json"))
        for mapping_path in mappings_list:
            mapping_name = os.path.basename(mapping_path).split(".")[0]
            self.mappings_dictionary[mapping_name] = mapping_path
            LOG.info(mapping_name)

    @tracktime
    def import_audio2face_data(self, json_file):
        """Import the audio2face data.

        Args:
            json_file (str): Path to the json file.
        """
        if not self._controller or not cmds.objExists(self._controller):
            raise ValueError("Controller not defined or doesn't exist.")

        audio_2_face_data = self._load_json(json_file)
        fps = audio_2_face_data["exportFps"]
        self.set_scene_fps(fps)

        frame_range = [
            self.start_frame,
            self.start_frame + audio_2_face_data["numFrames"],
        ]

        self.set_ranges(
            [frame_range[0], frame_range[0], frame_range[1], frame_range[1]]
        )

        audio_file = audio_2_face_data["trackPath"]
        # set the audio file in Maya
        cmds.sound(file=audio_file, name="audio2face_sound", offset=frame_range[0])
        playback_slider = mel.eval("$tmpVar=$gPlayBackSlider")
        cmds.timeControl(
            playback_slider, edit=True, sound="audio2face_sound", displaySound=True
        )
        cmds.playbackOptions(playbackSpeed=1)  # set playback speed to real-time

        cmds.currentTime(frame_range[0])

        # create the animlayers for the lower and upper face
        lower_face_layer = cmds.animLayer("a2f_lowerFace")
        upper_face_layer = cmds.animLayer("a2f_upperFace")

        for static_key, value in self._mapping["statics"].items():
            cmds.animLayer(lower_face_layer, edit=True, attribute="{}.{}".format(self._controller, static_key))
            cmds.animLayer(upper_face_layer, edit=True, attribute="{}.{}".format(self._controller, static_key))
            cmds.setKeyframe(self._controller, value=value, attribute=static_key, animLayer=lower_face_layer)
            cmds.setKeyframe(self._controller, value=value, attribute=static_key, animLayer=upper_face_layer)

        self.__apply_a2f_data(self._mapping["upper_face_mappings"], audio_2_face_data, upper_face_layer, frame_range[0])
        self.__apply_a2f_data(self._mapping["lower_face_mappings"], audio_2_face_data, lower_face_layer, frame_range[0])

        # create a neutralize layer if the neutralize frame is set
        if self._enable_neutralize:
            neutralize_layer = cmds.animLayer("a2f_neutralize")
            self.__neutralize(self._neutralize_frame, self._mapping["upper_face_mappings"].values(), neutralize_layer)
            self.__neutralize(self._neutralize_frame, self._mapping["lower_face_mappings"].values(), neutralize_layer)

    def __apply_a2f_data(self, trigger_mappings, audio_2_face_data, animlayer, start_frame):
        """Apply the audio2face data to the controller."""
        for key, data in trigger_mappings.items():
            id = audio_2_face_data["facsNames"].index(key)
            for dest_attr_pack in data:
                mult = dest_attr_pack[3]
                attr = dest_attr_pack[0]
                cmds.animLayer(animlayer, edit=True, attribute="{}.{}".format(self._controller, attr))
                for frame, value_list in enumerate(audio_2_face_data["weightMat"]):
                    mapped_value = dest_attr_pack[1] + (dest_attr_pack[2] - dest_attr_pack[1]) * value_list[id] * mult
                    cmds.setKeyframe(self._controller, value=mapped_value, attribute=attr, time=frame + start_frame,
                                     animLayer=animlayer)

    def __neutralize(self, neutralize_frame, mapping_datas, neutralize_layer):
        """Neutralize the animation data."""
        for data in mapping_datas:
            for dest_attr_pack in data:
                attr = dest_attr_pack[0]
                min_value = dest_attr_pack[1]
                cmds.animLayer(neutralize_layer, edit=True, attribute="{}.{}".format(self._controller, attr))
                cmds.setKeyframe(self._controller, value=min_value, attribute=attr, time=neutralize_frame, animLayer=neutralize_layer)


    @staticmethod
    def _load_json(file_path):
        """Load the given json file."""
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r") as f_p:
                    data = json.load(f_p)
                    return data
            except ValueError:
                LOG.error("Corrupted file => %s", file_path)
                raise
        else:
            LOG.error("File cannot be found => %s", file_path)
            raise FileNotFoundError

    @staticmethod
    def set_scene_fps(fps_value):
        """
        Set the FPS value in DCC if supported.
        Args:
            fps_value: (integer) fps value

        Returns: None

        """
        # maya is a bit weird with fps.
        # there are number of predefined fps values. Some float, some int.
        # Int ones don't accept float values and vice versa.
        if int(fps_value) == fps_value:
            fps_value = int(fps_value)
        try:
            mel.eval(f"currentUnit -time {fps_value}fps;")
        except RuntimeError as exc:
            raise RuntimeError("Invalid FPS value") from exc

    @staticmethod
    def set_ranges(range_list):
        """Set the timeline ranges.
        Args:
            range_list: list of ranges as [<animation start>, <user min>, <user max>,
                                            <animation end>]

        Returns: None
        """
        cmds.playbackOptions(
            animationStartTime=range_list[0],
            minTime=range_list[1],
            maxTime=range_list[2],
            animationEndTime=range_list[3],
        )
