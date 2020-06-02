from maya import cmds
import trigger.library.functions as extra

class Icon(object):
    def __init__(self):
        super(Icon, self).__init__()

        self.iconDictionary={"Circle": self.circle,
                             "Cube": self.cube,
                             "Thigh": self.thigh,
                             "Star": self.star,
                             "FkikSwitch": self.fkikSwitch,
                             "Shoulder": self.shoulder,
                             "Plus": self.plus,
                             "Waist": self.waist,
                             "Square": self.square,
                             "Ngon": self.ngon,
                             "TriCircle": self.triCircle,
                             "CurvedCircle": self.curvedCircle,
                             "HalfDome": self.halfDome,
                             "Looper": self.looper,
                             "Triangle": self.triangle,
                             "Pyramid": self.pyramid,
                             "Diamond": self.diamond,
                             "Arrow": self.arrow,
                             "Preferences": self.preferences,
                             }


    def createIcon(self, iconType, iconName=None, scale=(1,1,1), location=None, normal=(0,1,0)):
        if iconType not in (self.getIconsList()):
            cmds.warning("This icon is not available. Valid Icons are:\n  %s" %(self.iconDictionary.keys()))
            return

        if not iconName:
            iconName = "%s_cont" %iconType


        rvsCon = None
        if iconType == "FkikSwitch":
            cont, rvsCon = self.iconDictionary[iconType](name=iconName)
        else:
            cont = self.iconDictionary[iconType](name=iconName)

        for shape in extra.getShapes(cont):
            if shape != "%sShape" % cont:
                cmds.rename(shape, extra.uniqueName("%sShape" % cont))

        cmds.setAttr("%s.scale" % cont, scale[0], scale[1], scale[2])
        extra.alignNormal(cont, normal)
        cmds.makeIdentity(cont, a=True)

        if location:
            cmds.move(location[0], location[1], location[2], cont)

        return cont, rvsCon

    def getIconsList(self):
        return self.iconDictionary.keys()

    def circle(self, name="circle_cont"):
        """
        Creates a circle controller. Nothing Fancy...
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
            normal: (Vector) Optional Normal as vector. Default is (0, 1, 0) Y Up
        Returns:
            Controller node

        """

        cont_circle = cmds.circle(name=name, nr=(0, 1, 0), ch=0)
        return cont_circle[0]

    def cube(self, name="cube_cont"):
        """
        Creates a cube controller as a single shape
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            Controller node
        """
        cont_cube = cmds.curve(name=name, d=1, p=[(-1, 1, 1), (-1, 1, -1), (1, 1, -1), \
                                                (1, 1, 1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1), (-1, 1, -1),
                                                (-1, 1, 1),
                                                (-1, -1, 1), (1, -1, 1), \
                                                (1, 1, 1), (1, 1, -1), (1, -1, -1), (1, -1, 1), (1, -1, -1),
                                                (-1, -1, -1)],
                             k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
        return cont_cube

    def thigh(self, name="thigh_cont"):
        """
        Creates a cube controller as a single shape
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            Controller node
        """
        cont_thigh = cmds.curve(name=name, d=1, p=[(-1, 1, 1), (-1, 1, -1), (1, 1, -1), \
                                                 (1, 1, 1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1), (-1, 1, -1),
                                                 (-1, 1, 1), (-1, -1, 1), (1, -1, 1), \
                                                 (1, 1, 1), (1, 1, -1), (1, -1, -1), (1, -1, 1), (1, -1, -1),
                                                 (-1, -1, -1)],
                              k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
        return cont_thigh

    def star(self, name="star_cont"):
        """
        Creates a star-ish shaped controller
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
            normal: (Vector) Optional normal override

        Returns:
            Controller node
        """
        cont_star = cmds.circle(name=name, nr=(0,1,0), ch=0, s=12, radius=1.5)[0]
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[0]" %cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[2]" %cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[4]" %cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[6]" %cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[8]" %cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[10]" %cont_star)

        cmds.select(d=True)
        return cont_star

    def fkikSwitch(self, name="fkik_cont"):
        """
        Creates a FK-IK controller.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            A list Containing Controller Node (index 0) and Reverse node (1) to be used
            in conjunction with fk_ik attribute.
            [Controller Node, Reverse Node for connections]
        """
        letter_fk_f = cmds.curve(d=1, p=[(-8.145734, -5.011799, 0), (-8.145734, 4.99286, 0), (-1.059101, 4.99286, 0),
                                       (-1.059101, 2.908556, 0), (-5.227709, 2.908556, 0), (-5.227709, 1.241113, 0),
                                       (-1.892823, 1.241113, 0), (-1.892823, -0.843191, 0), (-5.227709, -0.843191, 0),
                                       (-5.227709, -5.011799, 0), (-8.145734, -5.011799, 0)],
                               k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], name="letterFK_F")
        letter_f_k_k = cmds.curve(d=1, p=[(1.025203, -5.011799, 0), (1.025203, 4.99286, 0), (3.943228, 4.99286, 0),
                                        (3.943228, 1.215065, 0), (7.193445, 4.99286, 0), (11.029861, 4.99286, 0),
                                        (7.382331, 1.084794, 0), (11.029861, -5.011799, 0), (7.857814, -5.011799, 0),
                                        (5.669293, -0.752001, 0), (3.943228, -2.608331, 0), (3.943228, -5.011799, 0),
                                        (1.025203, -5.011799, 0)], k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                name="letterFK_K")

        letter_f_k_k_shape = extra.getShapes(letter_f_k_k)[0]
        cmds.parent(letter_f_k_k_shape, letter_fk_f, r=True, s=True)
        cmds.delete(letter_f_k_k)
        letter_fk = cmds.rename(letter_fk_f, "letterFK")
        letter_ik = cmds.duplicate(letter_fk, name="letterIK", renameChildren=True)[0]
        letter_ik_shapes = extra.getShapes(letter_ik)

        cmds.move(-4.168608, 0, 0, "{0}.cv[2]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-4.168608, 0, 0, "{0}.cv[3]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-3.334886, 0, 0, "{0}.cv[6]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-3.334886, 0, 0, "{0}.cv[7]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(2.897946, 0, 0, "{0}.cv[0:10]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-1.505933, 0, 0, "{0}.cv[0:12]".format(letter_ik_shapes[1]), r=True, os=True, wd=True)

        blShape_FKtoIK = cmds.blendShape(letter_ik, letter_fk)

        cont_FK_IK = cmds.rename(letter_fk, name)
        cmds.addAttr(cont_FK_IK, shortName="fk_ik", longName="FK_IK", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
                   k=True)

        fk_ik_rvs = cmds.createNode("reverse", name="fk_ik_rvs%s" % name)
        cmds.connectAttr("%s.fk_ik" %cont_FK_IK, "%s.weight[0]" %blShape_FKtoIK[0])
        cmds.connectAttr("%s.fk_ik" %cont_FK_IK, "%s.inputX" %fk_ik_rvs)

        cmds.setAttr("%s.scale" %cont_FK_IK, 0.1, 0.1, 0.1)
        cmds.delete(letter_ik)
        cmds.select(cont_FK_IK)
        cmds.makeIdentity(a=True)
        return cont_FK_IK, fk_ik_rvs

    def shoulder(self, name="shoulder_cont"):
        """
        Creates a bended Eliptical controller for shoulders.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            Controller node
        """

        cont_shoulder = cmds.curve(d=3,
                 p=[(0, 0, 5), (1, 0, 5), (2, 0, 5), (2, 1, 4), (2, 2, 3), (2, 3, 2), (2, 3, 1), (2, 3, 0), (2, 3, -1),
                    (2, 3, -2), (2, 2, -3), (2, 1, -4), (2, 0, -5), (1, 0, -5), (0, 0, -5), (-1, 0, -5), (-2, 0, -5),
                    (-2, 1, -4), (-2, 2, -3), (-2, 3, -2), (-2, 3, -1), (-2, 3, 0), (-2, 3, 1), (-2, 3, 2), (-2, 2, 3),
                    (-2, 1, 4), (-2, 0, 5), (-1, 0, 5), (0, 0, 5)],
                 k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                    26, 26, 26], name=name)

        cmds.setAttr("%s.scale" % cont_shoulder, 0.5, 0.5, 0.5)
        cmds.makeIdentity(cont_shoulder, a=True)
        cmds.makeIdentity(cont_shoulder, a=True)

        return cont_shoulder

    def plus(self, name="plus_cont"):
        """
        Creates a plus controller. Usually for pole vector
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """
        cont_Pole = cmds.curve(name=name, d=1,
                             p=[(-1, 0, -3), (-1, 0, -1), (-3, 0, -1), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (1, 0, 3),
                                (1, 0, 1), (3, 0, 1), (3, 0, -1), (1, 0, -1), (1, 0, -3), (-1, 0, -3)],
                             k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        cmds.setAttr("%s.scale" % cont_Pole, 0.4, 0.4, 0.4)
        cmds.makeIdentity(cont_Pole, a=True, s=True)
        return cont_Pole

    def waist(self, name="waist_cont"):
        """
        Creates a plus controller. Usually for pole vector
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """
        cont_waist = cmds.curve(name=name, d=1,
                              p=[(-6.086269, 0, 2.259307), (-7.671805, 0, -2.12977e-007), (-6.086269, 0, -2.259308),
                                 (-6.08099, 0, -1.545085), (-4.755284, 0, -1.545085), (-4.045086, 0, -2.938927),
                                 (-2.938927, 0, -4.045086), (-1.545086, 0, -4.755285), (-1.545086, 0, -6.080991),
                                 (-2.259309, 0, -6.08627), (-1.05973e-006, 0, -7.671805), (2.259307, 0, -6.086271),
                                 (1.545086, 0, -6.122436), (1.545086, 0, -4.755285), (2.938928, 0, -4.045087),
                                 (4.045088, 0, -2.938928), (4.755286, 0, -1.545086), (6.080994, 0, -1.545086),
                                 (6.086271, 0, -2.259301), (7.671804, 0, 3.02757e-006), (6.086267, 0, 2.259305),
                                 (6.080992, 0, 1.545085), (4.755283, 0, 1.545085), (4.045085, 0, 2.938926),
                                 (2.938926, 0, 4.045085), (1.545085, 0, 4.755283), (1.545085, 0, 6.080991),
                                 (2.259307, 0, 6.086268), (6.06841e-007, 0, 7.671803), (-2.259307, 0, 6.086269),
                                 (-1.545085, 0, 6.080991), (-1.545085, 0, 4.755283), (-2.938927, 0, 4.045085),
                                 (-4.045086, 0, 2.938927), (-4.755284, 0, 1.545085), (-6.08099, 0, 1.545085),
                                 (-6.086269, 0, 2.259307)],
                              k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                                 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36])
        cmds.setAttr("%s.scale" % cont_waist, 0.2, 0.2, 0.2)
        cmds.makeIdentity(cont_waist, a=True, s=True)
        return cont_waist

    def square(self, name="square_cont"):
        """
        Creates a square controller.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """
        cont_square = cmds.curve(name=name, d=1, p=[(1, 0, 1), (-1, 0, 1), (-1, 0, -1), (1, 0, -1), (1, 0, 1)],
                               k=[0, 1, 2, 3, 4])
        return cont_square

    def ngon(self, name="ngon_cont"):
        """
        Creates a ngon controller.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """

        cont_ngon = cmds.curve(name=name, d=1,
                             p=[(-2, 0, -4), (2, 0, -4), (4, 0, -2), (4, 0, 2), (2, 0, 4), (-2, 0, 4), (-4, 0, 2),
                                (-4, 0, -2), (-2, 0, -4)], k=[0, 1, 2, 3, 4, 5, 6, 7, 8])
        cmds.setAttr("%s.scale" % cont_ngon, 0.25, 0.25, 0.25)
        cmds.makeIdentity(cont_ngon, a=True, s=True)
        return cont_ngon

    def triCircle(self, name="triCircle_cont"):
        """
        Creates a circle controller with triangles on each direction.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """
        cont_triCircle = cmds.circle(name=name, nr=(0, 1, 0), ch=0)[0]
        masterTri = cmds.curve(bezier=True, d=3,
                             p=[(0, 0, 0.240), (0, 0, 0.240), (-0.150, 0, 0), (-0.150, 0, 0), (-0.150, 0, 0),
                                (0, 0, -0.240), (0, 0, -0.240), (0, 0, -0.240), (-0.03, 0, -0.03), (-0.03, 0, 0),
                                (0, 0, 0.240)])
        cmds.move(-1.036, 0, 0, masterTri)
        cmds.xform(masterTri, piv=(0, 0, 0), ws=True)
        cmds.makeIdentity(masterTri, a=True)
        for i in range(0, 4):
            newTri = cmds.duplicate(masterTri, name="arrow_%i" %i)[0]
            cmds.makeIdentity(newTri, a=True)
            newTriShape = extra.getShapes(newTri)[0]
            # previously created tricircle shapes clashes with this
            newTriShape = cmds.rename(newTriShape, extra.uniqueName(newTriShape))
            cmds.rotate(0, 90, 0, masterTri, r=True)
            cmds.parent(newTriShape, cont_triCircle, r=True, s=True)
            cmds.delete(newTri)
        cmds.delete(masterTri)
        return cont_triCircle

    def curvedCircle(self, name="curvedCircle_cont"):
        """
        Creates a slightly curved circle controller
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            Controller node
        """
        cont_curvedCircle = cmds.circle(name=name, nr=(0, 1, 0), ch=0, s=12, radius=1)[0]
        for cv_num in [3, 4, 5, 9, 10, 11]:
            cmds.move(0, 0.25, 0, "%s.cv[%i]" % (cont_curvedCircle, cv_num), r=True)
        return cont_curvedCircle

    def halfDome(self, name="halfDome_cont"):

        cont_halfCurve = cmds.curve(name=name, d=1,
                                  p=[(-2.98023e-008, 0, 1), (-0.309017, 0, 0.951057), (-0.587785, 0, 0.809017),
                                     (-0.809017, 0, 0.587785), (-0.951057, 0, 0.309017), (-1, 0, 0),
                                     (-0.987689, 0.156434, 0),
                                     (-0.951057, 0.309017, 0), (-0.891007, 0.453991, 0), (-0.809017, 0.587785, 0),
                                     (-0.707107, 0.707107, 0), (-0.587785, 0.809017, 0), (-0.453991, 0.891007, 0),
                                     (-0.309017, 0.951057, 0), (-0.156435, 0.987688, 0), (0, 1, 0),
                                     (-4.66211e-009, 0.987688, 0.156434), (-9.20942e-009, 0.951057, 0.309017),
                                     (-1.353e-008, 0.891007, 0.453991), (-1.75174e-008, 0.809017, 0.587785),
                                     (-2.10734e-008, 0.707107, 0.707107), (-2.41106e-008, 0.587785, 0.809017),
                                     (-2.65541e-008, 0.453991, 0.891007), (-2.83437e-008, 0.309017, 0.951057),
                                     (-2.94354e-008, 0.156434, 0.987688), (-2.98023e-008, 0, 1),
                                     (0.309017, 0, 0.951057),
                                     (0.587785, 0, 0.809017), (0.809017, 0, 0.587785), (0.951057, 0, 0.309017),
                                     (1, 0, 0),
                                     (0.987688, 0.156434, 0), (0.951057, 0.309017, 0), (0.891007, 0.453991, 0),
                                     (0.809017, 0.587785, 0), (0.707107, 0.707107, 0), (0.587785, 0.809017, 0),
                                     (0.453991, 0.891007, 0), (0.309017, 0.951057, 0), (0.156434, 0.987688, 0),
                                     (0, 1, 0),
                                     (0, 0.987688, -0.156435), (0, 0.951057, -0.309017), (0, 0.891007, -0.453991),
                                     (0, 0.809017, -0.587786), (0, 0.707107, -0.707107), (0, 0.587785, -0.809017),
                                     (0, 0.453991, -0.891007), (0, 0.309017, -0.951057), (0, 0.156434, -0.987689),
                                     (0, 0, -1), (-0.309017, 0, -0.951057), (-0.587785, 0, -0.809017),
                                     (-0.809017, 0, -0.587785),
                                     (-0.951057, 0, -0.309017), (-1, 0, 0), (-0.951057, 0, -0.309017),
                                     (-0.809017, 0, -0.587785),
                                     (-0.587785, 0, -0.809017), (-0.309017, 0, -0.951057), (0, 0, -1),
                                     (0.309017, 0, -0.951057),
                                     (0.587786, 0, -0.809017), (0.809018, 0, -0.587786), (0.951057, 0, -0.309017),
                                     (1, 0, 0)],
                                  k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                                     23, 24, 25, 26, 27, 28, 29, 30,
                                     31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
                                     52, 53, 54, 55, 56, 57, 58,
                                     59, 60, 61, 62, 63, 64, 65])
        cmds.makeIdentity(cont_halfCurve, a=True, s=True)
        return cont_halfCurve

    def looper(self, name="looper_cont"):

        cont_Looper = cmds.curve(name=name, d=1,
                               p=[(0, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -2), (2, 0, -2), (2, 0, 2),
                                  (-2, 0, 2), (-2, 0, -3), (3, 0, -3), (3, 0, 3), (-3, 0, 3), (-3, 0, -3)],
                               k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        cmds.setAttr("%s.scale" % cont_Looper, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_Looper, a=True, s=True)
        return cont_Looper

    def triangle(self, name="triangle_cont"):
        cont_Triangle = cmds.curve(name=name, d=1, p=[(0, 0, -3), (-3, 0, 2), (3, 0, 2), (0, 0, -3)], k=[0, 1, 2, 3])
        # pm.setAttr(cont_Triangle + ".scale", (0.333, 0.333, 0.333))
        cmds.setAttr("%s.scale" % cont_Triangle, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_Triangle, a=True, s=True)
        return cont_Triangle

    def pyramid(self, name="pyramid_cont"):
        cont_Pyramid = cmds.curve(name=name, d=1,
                                p=[(-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1), (-1, 0, 1), (0, 2, 0), (1, 0, -1),
                                   (-1, 0, -1), (0, 2, 0), (1, 0, 1)], k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        cmds.setAttr("%s.scale" %cont_Pyramid, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_Pyramid, a=True, s=True)
        return cont_Pyramid

    def diamond(self, name="diamond_cont"):
        cont_diamond = cmds.curve(name=name, d=1,
                                p=[(0.341725, 0, 1.051722), (1.105846, 0, 0), (0, 0.962601, 0), (0.341725, 0, 1.051722),
                                   (0, -0.962601, 0), (1.105846, 0, 0), (0.341725, 0, -1.051722), (0, 0.962601, 0),
                                   (-0.894648, 0, -0.65),
                                   (0, -0.962601, 0), (0.341725, 0, -1.051722), (-0.894648, 0, -0.65),
                                   (-0.894648, 0, 0.65), (0.341725, 0, 1.051722), (0, -0.962601, 0),
                                   (-0.894648, 0, 0.65), (0, 0.962601, 0)],
                                k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
        cmds.makeIdentity(cont_diamond, a=True, s=True)
        return cont_diamond

    def arrow(self, name="arrow_cont"):
        cont_arrow = cmds.curve(name=name, d=1, p=[(0.0335873, 0, 1.055001), (-4.955996, 0, 0.971701), (-4.983113, 0, 2.081272),
                         (-7.934906, 0, -0.0118149), (-4.93066, 0, -2.06217), (-4.973678, 0, -0.968172),
                         (0.0696592, 0, -1.018287), (0.0192114, 0, 1.054761)], k=[0, 1, 2, 3, 4, 5, 6, 7])
        cmds.makeIdentity(cont_arrow, a=True, s=True)
        return cont_arrow

    def preferences(self, name="pref_cont"):
        cont_pref = cmds.curve(name=name, d=1, p=[(-2.005908, -0.00143437, 2.011916), (-2.005908, -0.00143437, -2.997386),
                         (0.138344, -0.00143437, -2.997386), (0.364393, -0.00143437, -2.990991),
                         (0.577802, -0.00143437, -2.971805), (0.778569, -0.00143437, -2.939829),
                         (0.966696, -0.00143437, -2.895063), (1.142182, -0.00143437, -2.837506),
                         (1.305028, -0.00143437, -2.767159), (1.455232, -0.00143437, -2.684021),
                         (1.592796, -0.00143437, -2.588093), (1.715837, -0.00143437, -2.479426),
                         (1.822472, -0.00143437, -2.358071), (1.912702, -0.00143437, -2.224027),
                         (1.986526, -0.00143437, -2.077296), (2.043945, -0.00143437, -1.917877),
                         (2.084959, -0.00143437, -1.745769), (2.109567, -0.00143437, -1.560974),
                         (2.11777, -0.00143437, -1.363491), (2.109539, -0.00143437, -1.165979),
                         (2.084849, -0.00143437, -0.981102), (2.043697, -0.00143437, -0.808856),
                         (1.986085, -0.00143437, -0.649244), (1.912013, -0.00143437, -0.502265),
                         (1.82148, -0.00143437, -0.367918), (1.714486, -0.00143437, -0.246204),
                         (1.591032, -0.00143437, -0.137124), (1.45311, -0.00143437, -0.0407822),
                         (1.302712, -0.00143437, 0.0427137), (1.139839, -0.00143437, 0.113364),
                         (0.964491, -0.00143437, 0.171169), (0.776667, -0.00143437, 0.216129),
                         (0.576368, -0.00143437, 0.248242), (0.363594, -0.00143437, 0.267511),
                         (0.138344, -0.00143437, 0.273934), (-0.479363, -0.00143437, 0.273934),
                         (-0.479363, -0.00143437, -0.662097), (0.000736963, -0.00143437, -0.662097),
                         (0.176589, -0.00143437, -0.673313), (0.331649, -0.00143437, -0.706958),
                         (0.465917, -0.00143437, -0.763035), (0.579392, -0.00143437, -0.841541),
                         (0.669587, -0.00143437, -0.941439), (0.734012, -0.00143437, -1.061687),
                         (0.772666, -0.00143437, -1.202287), (0.785551, -0.00143437, -1.363238),
                         (0.772666, -0.00143437, -1.524095), (0.734012, -0.00143437, -1.664412),
                         (0.669587, -0.00143437, -1.784188), (0.579392, -0.00143437, -1.883424),
                         (0.465917, -0.00143437, -1.961269), (0.331649, -0.00143437, -2.016872),
                         (0.176589, -0.00143437, -2.050235), (0.000736963, -0.00143437, -2.061355),
                         (-0.714014, -0.00143437, -2.061355), (-0.714014, -0.00143437, 2.011916),
                         (-2.005908, -0.00143437, 2.011916)],
                 k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
                    52, 53, 54, 55, 56])
        cmds.setAttr("%s.scale" %cont_pref, 0.333, 0.333, 0.333)
        cmds.setAttr("%s.rotate" % cont_pref, 90, 0, 0)
        cmds.makeIdentity(cont_pref, a=True)
        return cont_pref
