"""Base node object class for inheriting purposes"""
from maya import cmds


class BaseNode(object):
    def __init__(self):
        super(BaseNode, self).__init__()
        self.dag_path = None
        self._name = None

    @property
    def name(self):
        if not self.dag_path:
            return None
        self._name = self.dag_path.split("|")[-1]
        return self._name

    @name.setter
    def name(self, val):
        self._name = val
        # if not self.dag_path:
        #     return None
        cmds.rename(self.dag_path, val)
        self.refresh_dag_path()

    def refresh_dag_path(self, force=False):
        """
        resets the dag path. This method assumes that the object has a unique name.
        Args:
            force: If True, pick up the first encountered in the list. If false throws an error for
            non unique objects

        Returns: None

        """
        encounters = cmds.ls(self._name, l=True)
        if len(encounters) > 1 and not force:
            raise Exception("Object %s is not unique" % self._name)
        self.dag_path = encounters[0]
