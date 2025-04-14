"""Tik Manager version control integration."""

import dataclasses
import tik_manager4
from tik_manager4.ui.mcv import project_mcv
from tik_manager4.ui.Qt import QtWidgets
from tik_manager4.ui.widgets.common import ResolvedText, TikIconButton
import tik_manager4._version as version


from tik_manager4.ui import main

from trigger.version_control.api import ApiHandler


@dataclasses.dataclass
class DisplayWidgets:
    """Display widgets."""

    resolved_text: ResolvedText


class VCS(object):
    """Tik Manager4 version control integrator."""

    def __init__(self, trigger_main_window):
        """Initialize."""
        # self._trigger_main_window = trigger_main_window
        self.trigger_main_window = trigger_main_window
        # self.tik = tik_manager4.initialize("trigger")

        self.display_widgets = DisplayWidgets(
            resolved_text=ResolvedText(
                "Current Session is not a Tik Manager Work", color="yellow"
            ),
        )

        self.api_handler = ApiHandler()
        self.api_handler.set_trigger_handler(trigger_main_window)

    def build_session_header(self, layout):
        """Build the session header."""
        # add all display widgets to the layout
        tik = tik_manager4.initialize("trigger")
        project_setter = project_mcv.TikProjectLayout(tik)
        layout.addLayout(project_setter)
        buttons_lay = QtWidgets.QHBoxLayout()
        buttons_lay.setSpacing(5)
        tik_main_btn = TikIconButton(
            icon_name="tik4_main_ui.png", size=32, icon_size=22, circle=False
        )
        tik_main_btn.setToolTip("Open Tik Manager4 main UI")
        tik_new_version_btn = TikIconButton(
            icon_name="tik4_new_version.png", size=32, icon_size=22, circle=False
        )
        tik_new_version_btn.setToolTip("Create new version")
        tik_publish_btn = TikIconButton(
            icon_name="tik4_publish.png", size=32, icon_size=22, circle=False
        )
        tik_publish_btn.setToolTip("Publish the current version")
        buttons_lay.addWidget(tik_main_btn)
        buttons_lay.addWidget(tik_new_version_btn)
        buttons_lay.addWidget(tik_publish_btn)

        # insert the tik button into the the beginning of project_setter layout
        project_setter.insertLayout(0, buttons_lay)

        layout.addWidget(self.display_widgets.resolved_text)
        self.update_info()

        tik_main_btn.clicked.connect(self.launch_main_ui)
        tik_new_version_btn.clicked.connect(self.save_new_version)

        tik_publish_btn.clicked.connect(self.publish)

    def update_info(self):
        """Update the info on UI."""
        tik = tik_manager4.initialize("trigger")
        work_obj, version = tik.project.get_current_work()
        # current_scene_path = self.tik_trigger_handler.get_scene_file()

        if work_obj:
            self.display_widgets.resolved_text.set_text(
                f"{work_obj.path}/{work_obj.name} - Version:{version}"
            )
            self.display_widgets.resolved_text.set_color("cyan")
        else:
            self.display_widgets.resolved_text.set_text(
                "Current Session is not a Tik Manager Work"
            )
            self.display_widgets.resolved_text.set_color("yellow")

    def launch_main_ui(self):
        """Launch the main UI."""
        window_name = f"Tik Manager {version.__version__} - trigger"
        all_widgets = QtWidgets.QApplication.allWidgets()
        for entry in all_widgets:
            try:
                if entry.objectName() == window_name:
                    entry.close()
                    entry.deleteLater()
            except (AttributeError, TypeError):
                pass
        tik = tik_manager4.initialize("trigger")
        ui = main.MainUI(
            tik, parent=self.trigger_main_window, window_name=window_name
        )
        ui.show()
        self.update_info()
        # ui.exec_()

    def save_new_version(self):
        """Save new version."""
        # we need to reinitialize the tik object because it may get overridden by maya tik object
        tik = tik_manager4.initialize("trigger")
        ui = main.MainUI(tik, parent=self.trigger_main_window)
        ui.on_new_version()
        self.update_info()

    def publish(self):
        """Publish the current version."""
        tik = tik_manager4.initialize("trigger")
        ui = main.MainUI(tik, parent=self.trigger_main_window)
        ui.on_publish_scene()
        self.update_info()
