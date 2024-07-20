"""Simple api handler for Audio2Face."""

from pathlib import Path
import os
import subprocess
import http.client
import time
import logging
import json

# default_arkit.usd file is in the same folder with this file
USD_FILE = Path(__file__).parent / "default_arkit.usd"

LOG = logging.getLogger(__name__)

def process_wav_file(wav_file_path, export_path=None, overwrite=False):
    """Convenience function to process the wav file through A2F.

    Args:
        wav_file_path (str): Path to the wav file.
        export_path (str): Path to export the json file. If not specified, the json file will be exported to the same directory with the wav file.
    """

    export_path = export_path or Path(wav_file_path).with_suffix(".json").as_posix()
    if Path(export_path).exists():
        if not overwrite:
            LOG.warning(
                "Output file already exists. Set overwrite to True to overwrite the file. Skipping A2F processing.")
            return export_path
        else:
            Path(export_path).unlink()

    a2f = A2F()
    a2f.launch_a2f()

    connection = a2f.connect()

    a2f.load_file(USD_FILE.as_posix(), conn=connection)

    wav_dir = Path(wav_file_path).parent
    wav_name_with_suffix = Path(wav_file_path).name
    a2f.set_root_path(wav_dir.as_posix(), conn=connection)
    a2f.set_track(wav_name_with_suffix, conn=connection)
    a2f.export_json(export_path, conn=connection)

    # a2f automatically adds _bsweight before the extension. Remove it.
    goal_path = Path(export_path)
    auto_path = goal_path.with_stem(f"{goal_path.stem}_bsweight")
    auto_path.rename(goal_path)

    a2f.stop_a2f()
    return export_path


class A2F:
    def __init__(self):
        self.a2f_executable = "C:/Users/kutlu/AppData/Local/ov/pkg/audio2face-2023.2.0/kit/kit.exe"
        self.kit = "C:/Users/kutlu/AppData/Local/ov/pkg/audio2face-2023.2.0/apps/audio2face_headless.kit"
        # self.kit = "C:/Users/kutlu/AppData/Local/ov/pkg/audio2face-2023.2.0/apps/audio2face.kit"

        self.host = "localhost"
        self.port = 8011
        self.process = None

    def launch_a2f(self):
        """Launch Audio2Face."""
        LOG.info("Launching Audio2Face...")
        self.process = subprocess.Popen([self.a2f_executable, self.kit], env=os.environ.copy())

        # Wait until the service is ready
        self.wait_until_ready()

        LOG.info("Audio2Face launched.")

        self.conn = http.client.HTTPConnection(self.host, self.port, timeout=5)

        LOG.info("Audio2Face connection established.")

    def wait_until_ready(self):
        """Wait until the Audio2Face service is ready."""
        max_attempts = 60  # Maximum number of attempts
        attempt = 0
        while attempt < max_attempts:
            if self.check_service_status():
                print("Service is ready.")
                return
            attempt += 1
            time.sleep(1)  # Wait for 1 second before the next attempt

        raise TimeoutError(
            "Service did not become ready within the expected time.")

    def connect(self):
        """Establish the connection to the Audio2Face service."""
        return http.client.HTTPConnection(self.host, self.port, timeout=5000)

    def check_service_status(self):
        """Check if the service is up and running by making a simple HTTP request."""
        conn = self.connect()
        try:
            conn.request("GET", "/status")
            response = conn.getresponse()
            return response.status == 200
        except Exception as e:
            LOG.debug(f"Exception while checking service status: {e}")
            return False
        finally:
            conn.close()

    def stop_a2f(self):
        """Stop the Audio2Face service."""
        # self.conn.close()
        if self.process is not None:
            LOG.info("Stopping Audio2Face...")
            try:
                self.process.terminate()  # Try to terminate gracefully
                self.process.wait(timeout=10)  # Wait up to 10 seconds for the process to terminate
            except subprocess.TimeoutExpired:
                LOG.warning("Process did not terminate gracefully. Forcing termination...")
                self.process.kill()  # Force kill if not terminated gracefully
            finally:
                self.process = None
                LOG.info("Audio2Face stopped.")

    def load_file(self, file_path, conn=None):
        # check the connection
        # if not self.conn:
        #     raise ConnectionError("Connection is not established.")

        conn = conn or self.connect()

        # check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        data = json.dumps({"file_name": file_path})

        # send the request
        conn.request(
            method="POST",
            url="/A2F/USD/Load",
            body=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode()

        LOG.info(f"Status: {response.status}")
        LOG.info(f"Response: {response_data}")

        conn.close()

    def get_a2f_player_instances(self, conn=None):
        # check the connection
        # if not self.conn:
        #     raise ConnectionError("Connection is not established.")

        # create a new connection
        conn = conn or self.connect()

        # send the request
        conn.request(
            method="GET",
            url="/A2F/Player/GetInstances",
            headers={
                "Accept": "application/json"
            }
        )

        # Get the response
        response = conn.getresponse()
        # response_data = response.read().decode()

        # convert it into a python dictionary
        response_data = json.loads(response.read())

        if not response_data.get("status") == 'OK':
            raise Exception(f"Failed to get player instances: {response_data}")

        conn.close()

        return response_data["result"]["regular"]

    def set_root_path(self, root_path, a2f_player=None, conn=None):
        """Set the root path to the a2f player.

        Args:
            root_path (str): Root path to player.
            a2f_player (str): Name of the a2f player. If not specified, the first player will be used.
            conn (http.client.HTTPConnection): Connection to the Audio2Face service. If not specified, a new connection will be established.
        """

        conn = conn or self.connect()

        if not a2f_player:
            a2f_player = self.get_a2f_player_instances(conn=conn)[0]

        data = json.dumps({"a2f_player": a2f_player, "dir_path": root_path})

        conn.request(
            method="POST",
            url="/A2F/Player/SetRootPath",
            body=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode()

        LOG.info(f"Status: {response.status}")
        LOG.info(f"Response: {response_data}")

        conn.close()

    def get_tracks(self, conn=None, a2f_player=None):
        """Get the tracks from the currently set root."""

        conn = conn or self.connect()

        if not a2f_player:
            a2f_player = self.get_a2f_player_instances(conn=conn)[0]

        data = json.dumps({"a2f_player": a2f_player})
        conn.request(
            method="POST",
            url="/A2F/Player/GetTracks",
            body=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        # Get the response
        response = conn.getresponse()
        # response_data = response.read().decode()

        # convert it into a python dictionary
        response_data = json.loads(response.read())

        if not response_data.get("status") == 'OK':
            conn.close()
            raise Exception(f"Failed to get player instances: {response_data}")

        conn.close()

        return response_data["result"]

    def set_track(self, track_name, conn=None, a2f_player=None):
        """Set the track to the player."""

        conn = conn or self.connect()

        if not a2f_player:
            a2f_player = self.get_a2f_player_instances(conn=conn)[0]

        data = json.dumps({"a2f_player": a2f_player, "file_name": track_name, "time_range": [0,-1]})
        conn.request(
            method="POST",
            url="/A2F/Player/SetTrack",
            body=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

        )

        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode()

        LOG.info(f"Status: {response.status}")
        LOG.info(f"Response: {response_data}")

        conn.close()

    def get_blendshape_solvers(self, conn=None):
        """Get the blendshape solvers from the a2f scene."""

        conn = conn or self.connect()

        conn.request(
            method="GET",
            url="/A2F/Exporter/GetBlendShapeSolvers",
            headers={
                "Accept": "application/json",
            }
        )

        # Get the response
        response = conn.getresponse()
        # response_data = response.read().decode()

        # convert it into a python dictionary
        response_data = json.loads(response.read())

        if not response_data.get("status") == 'OK':
            conn.close()
            raise Exception(f"Failed to get player instances: {response_data}")

        conn.close()

        return response_data["result"]

    def export_json(self,
                    file_path,
                    blendshape_solver=None,
                    conn=None
                    ):
        """Export the blendshape solvers to a json file."""

        export_directory = Path(file_path).parent.as_posix()
        file_name = str(Path(file_path).stem)

        conn = conn or self.connect()

        blendshape_solver = blendshape_solver or self.get_blendshape_solvers(conn=conn)[0]

        data = json.dumps({
            "solver_node": blendshape_solver,
            "export_directory": export_directory,
            "file_name": file_name,
            "format": "json",
            "batch": False,
            "fps": 0
                           })
        conn.request(
            method="POST",
            url="/A2F/Exporter/ExportBlendshapes",
            body=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode()

        LOG.info(f"Status: {response.status}")
        LOG.info(f"Response: {response_data}")

        conn.close()


# curl -X GET "http://localhost:8011/status" -H "accept: application/json"