"""This module is to communicate with other python applications sharing the same interpreter session."""

class ApiHandler():
    main_ui = None

    @classmethod
    def set_trigger_handler(cls, trigger_handler):
        """Define the trigger handler."""
        cls.main_ui = trigger_handler

    def validate_trigger_handler(self):
        """Validate the trigger handler."""
        if not self.main_ui:
            raise RuntimeError("Trigger handler is not defined.")

    def save_session(self):
        """Save the current session."""
        self.validate_trigger_handler()
        self.main_ui.save_trigger()

    def save_session_as(self, file_path):
        """Save the current session."""
        self.validate_trigger_handler()
        self.main_ui.vcs_save_session(file_path)
        return file_path

    def export_session(self, file_path):
        """Export the current session to the given file path."""
        self.validate_trigger_handler()
        self.main_ui.actions_handler.export_session(file_path)

    def open_session(self, file_path):
        """Open the given file path."""
        self.validate_trigger_handler()
        self.main_ui.open_trigger(file_path)

    def build_session(self):
        """Build the session."""
        self.validate_trigger_handler()
        self.main_ui.actions_handler.run_all_actions()

    def is_modified(self):
        """Returns True if the scene has unsaved changes."""
        self.validate_trigger_handler()
        return self.main_ui.actions_handler.is_modified()

    def get_session_file(self):
        """Get the current trigger session."""
        self.validate_trigger_handler()
        return self.main_ui.actions_handler.session_path

    def get_trigger_version(self):
        """Return the version of the trigger."""
        self.validate_trigger_handler()
        return self.main_ui.get_version()

    def update_info(self, *args, **kwargs):
        work_obj, version = self.tik.project.get_current_work()

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

