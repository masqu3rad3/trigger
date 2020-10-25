from trigger.ui.Qt import QtWidgets
from trigger.core import logger

LOG = logger.Logger()

class Feedback():
    def __init__(self, *args, **kwargs):
        # super(Feedback, self).__init__()
        self.parent=None

    def pop_info(self, title="Info", text="", details="", critical=False):
        msg = QtWidgets.QMessageBox(parent=self.parent)
        if critical:
            msg.setIcon(QtWidgets.QMessageBox.Critical)
        else:
            msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setInformativeText(details)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
        msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
        return msg.exec_()

    def pop_question(self, title="Question", text="", details="", buttons=["save", "no", "cancel"]):
        button_dict = {
            "yes": "QtWidgets.QMessageBox.Yes",
            "save": "QtWidgets.QMessageBox.Save",
            "ok": "QtWidgets.QMessageBox.Ok",
            "no": "QtWidgets.QMessageBox.No",
            "cancel": "QtWidgets.QMessageBox.Cancel"
        }
        widgets = []
        for button in buttons:
            widget = button_dict.get(button)
            if not widget:
                LOG.throw_error("Non-valid button defined. Valid buttons are: %s" %button_dict.keys())
            widgets.append(widget)

        q = QtWidgets.QMessageBox(parent=self.parent)
        q.setIcon(QtWidgets.QMessageBox.Question)
        q.setWindowTitle(title)
        q.setText(text)
        q.setInformativeText(details)
        eval('q.setStandardButtons(%s)' %(" | ".join(widgets)))
        ret = q.exec_()
        for key, value in button_dict.items():
            if ret == eval(value):
                return key


    # def infoPop(self, textTitle="info", textHeader="", textInfo="", type="I"):
    #     msg = QtWidgets.QMessageBox(parent=self.parent)
    #     if type == "I":
    #         msg.setIcon(QtWidgets.QMessageBox.Information)
    #     if type == "C":
    #         msg.setIcon(QtWidgets.QMessageBox.Critical)
    #
    #     msg.setText(textHeader)
    #     msg.setInformativeText(textInfo)
    #     msg.setWindowTitle(textTitle)
    #     msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    #     msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
    #     msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
    #     msg.show()

    # def queryPop(self, type, textTitle="Question", textHeader="", textInfo=""):
    #     """
    #     Pops a query window
    #
    #     Args:
    #         type: (String) Valid types are: 'yesNoCancel', 'okCancel', 'yesNo'
    #         textTitle: (String) Title of the text
    #         textHeader: (String) Message header
    #         textInfo: (String) Message details
    #
    #     Returns: (String) 'yes', 'no', 'ok' or 'cancel' depending on the type
    #
    #     """
    #
    #     if type == "yesNoCancel":
    #
    #         q = QtWidgets.QMessageBox(parent=self.parent)
    #         q.setIcon(QtWidgets.QMessageBox.Question)
    #         q.setText(textHeader)
    #         q.setInformativeText(textInfo)
    #         q.setWindowTitle(textTitle)
    #         q.setStandardButtons(
    #             QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
    #
    #         q.button(QtWidgets.QMessageBox.Save).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.Save).setFixedWidth(100)
    #         q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
    #         q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
    #         ret = q.exec_()
    #         if ret == QtWidgets.QMessageBox.Save:
    #             return "yes"
    #         elif ret == QtWidgets.QMessageBox.No:
    #             return "no"
    #         elif ret == QtWidgets.QMessageBox.Cancel:
    #             return "cancel"
    #
    #     if type == "okCancel":
    #         q = QtWidgets.QMessageBox(parent=self)
    #         q.setIcon(QtWidgets.QMessageBox.Question)
    #         q.setText(textHeader)
    #         q.setInformativeText(textInfo)
    #         q.setWindowTitle(textTitle)
    #         q.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
    #         q.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
    #         q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
    #         ret = q.exec_()
    #         if ret == QtWidgets.QMessageBox.Ok:
    #             return "ok"
    #         elif ret == QtWidgets.QMessageBox.Cancel:
    #             return "cancel"
    #
    #     if type == "yesNo":
    #         q = QtWidgets.QMessageBox(parent=self)
    #         q.setIcon(QtWidgets.QMessageBox.Question)
    #         q.setText(textHeader)
    #         q.setInformativeText(textInfo)
    #         q.setWindowTitle(textTitle)
    #         q.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    #         q.button(QtWidgets.QMessageBox.Yes).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.Yes).setFixedWidth(100)
    #         q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
    #         q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
    #         ret = q.exec_()
    #         if ret == QtWidgets.QMessageBox.Yes:
    #             return "yes"
    #         elif ret == QtWidgets.QMessageBox.No:
    #             return "no"
