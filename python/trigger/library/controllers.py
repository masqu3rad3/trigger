from maya import cmds
from trigger.library import functions
from trigger.library import naming


class Icon(object):
    def __init__(self):
        self.iconDictionary = {"Circle": self.circle,
                               "Cube": self.cube,
                               "Thigh": self.thigh,
                               "Star": self.star,
                               "FkikSwitch": self.fk_ik_switch,
                               "Shoulder": self.shoulder,
                               "Plus": self.plus,
                               "Waist": self.waist,
                               "Square": self.square,
                               "Sphere": self.sphere,
                               "Ngon": self.ngon,
                               "TriCircle": self.tricircle,
                               "CurvedCircle": self.curved_circle,
                               "HalfDome": self.half_dome,
                               "Looper": self.looper,
                               "Triangle": self.triangle,
                               "Pyramid": self.pyramid,
                               "Diamond": self.diamond,
                               "Arrow": self.arrow,
                               "Preferences": self.preferences,
                               "DropCircleX": self.drop_circle_x,
                               "Rotator": self.rotator,
                               "CurvedArrow": self.curved_arrow,
                               "DualCurvedArrow": self.dual_curved_arrow,
                               "Lollipop": self.lollipop,
                               "Drop": self.drop
                               }

    def create_icon(self,
                    icon_type,
                    icon_name=None,
                    scale=(1, 1, 1),
                    location=None,
                    normal=(0, 1, 0)):
        if icon_type not in (self.get_icons_list()):
            cmds.warning("This icon is not available. Valid Icons are:\n  %s" % (self.iconDictionary.keys()))
            return

        icon_name = icon_name or "%s_cont" % icon_type

        rvsCon = None
        if icon_type == "FkikSwitch":
            cont, rvsCon = self.iconDictionary[icon_type](name=icon_name)
        else:
            cont = self.iconDictionary[icon_type](name=icon_name)

        for shape in functions.getShapes(cont):
            if shape != "%sShape" % cont:
                cmds.rename(shape, naming.uniqueName("%sShape" % cont))

        cmds.setAttr("%s.scale" % cont, *scale)
        functions.alignNormal(cont, normal)
        cmds.makeIdentity(cont, a=True)

        if location:
            cmds.move(location[0], location[1], location[2], cont)

        return cont, rvsCon

    def get_icons_list(self):
        return self.iconDictionary.keys()

    @staticmethod
    def circle(name="circle_cont"):
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

    @staticmethod
    def cube(name="cube_cont"):
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

    @staticmethod
    def thigh(name="thigh_cont"):
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

    @staticmethod
    def star(name="star_cont"):
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
        cont_star = cmds.circle(name=name, nr=(0, 1, 0), ch=0, s=12, radius=1.5)[0]
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[0]" % cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[2]" % cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[4]" % cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[6]" % cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[8]" % cont_star)
        cmds.scale(0.5, 0.5, 0.5, "%s.cv[10]" % cont_star)

        cmds.select(d=True)
        return cont_star

    @staticmethod
    def drop(name="drop_cont"):
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
        _cont = cmds.curve(d=3, p=[(3, 0.999999, 0), (3.195091, 0.980784, 0), (3.382684, 0.923878, 0),
                                    (3.55557, 0.831468, 0), (3.707106, 0.707106, 0), (3.831469, 0.555569, 0),
                                    (3.923879, 0.382683, 0), (3.980784, 0.19509, 0), (4, 0, 0), (3.980785, -0.19509, 0),
                                    (3.923879, -0.382683, 0), (3.83147, -0.55557, 0), (3.707107, -0.707107, 0),
                                    (3.55557, -0.83147, 0), (3.382683, -0.923879, 0), (3.19509, -0.980785, 0),
                                    (3, -1, 0), (2.801629, -0.980785, 0), (2.539676, -0.923879, 0),
                                    (2.255514, -0.831469, 0), (1.9439, -0.707106, 0), (1.59123, -0.55557, 0),
                                    (1.136886, -0.382683, 0), (0.611128, -0.19509, 0), (2.38419e-07, 3.27826e-07, 0),
                                    (0.611129, 0.195091, 0), (1.136886, 0.382683, 0), (1.59123, 0.55557, 0),
                                    (1.9439, 0.707106, 0), (2.255515, 0.831469, 0), (2.539676, 0.923879, 0),
                                    (2.80163, 0.980784, 0), (3, 0.999999, 0)],
                            k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                               23, 24, 25, 26, 27, 28, 29, 30, 30, 30], name=name)

        cmds.select(d=True)
        return _cont

    @staticmethod
    def fk_ik_switch(name="fkik_cont"):
        """
        Creates a FK-IK controller.
        Args:
            name: (String) name of the controller. Must be a String

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

        letter_f_k_k_shape = functions.getShapes(letter_f_k_k)[0]
        cmds.parent(letter_f_k_k_shape, letter_fk_f, r=True, s=True)
        cmds.delete(letter_f_k_k)
        letter_fk = cmds.rename(letter_fk_f, "letterFK")
        letter_ik = cmds.duplicate(letter_fk, name="letterIK", renameChildren=True)[0]
        letter_ik_shapes = functions.getShapes(letter_ik)

        cmds.move(-4.168608, 0, 0, "{0}.cv[2]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-4.168608, 0, 0, "{0}.cv[3]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-3.334886, 0, 0, "{0}.cv[6]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-3.334886, 0, 0, "{0}.cv[7]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(2.897946, 0, 0, "{0}.cv[0:10]".format(letter_ik_shapes[0]), r=True, os=True, wd=True)
        cmds.move(-1.505933, 0, 0, "{0}.cv[0:12]".format(letter_ik_shapes[1]), r=True, os=True, wd=True)

        bl_shape_f_kto_ik = cmds.blendShape(letter_ik, letter_fk)

        cont_fk_ik = cmds.rename(letter_fk, name)
        cmds.addAttr(cont_fk_ik, shortName="fk_ik", longName="FK_IK", defaultValue=1.0, minValue=0.0, maxValue=1.0,
                     at="float",
                     k=True)
        cmds.addAttr(cont_fk_ik, shortName="fk_ik_reverse", longName="FK_IK_Reverse", defaultValue=1.0, minValue=0.0,
                     maxValue=1.0, at="float")

        fk_ik_rvs = cmds.createNode("reverse", name="fk_ik_rvs%s" % name)
        cmds.connectAttr("%s.fk_ik" % cont_fk_ik, "%s.weight[0]" % bl_shape_f_kto_ik[0])
        cmds.connectAttr("%s.fk_ik" % cont_fk_ik, "%s.inputX" % fk_ik_rvs)

        cmds.connectAttr("%s.outputX" % fk_ik_rvs, "%s.fk_ik_reverse" % cont_fk_ik)

        cmds.setAttr("%s.scale" % cont_fk_ik, 0.1, 0.1, 0.1)
        cmds.delete(letter_ik)
        cmds.select(cont_fk_ik)
        cmds.makeIdentity(a=True)
        return cont_fk_ik, fk_ik_rvs

    @staticmethod
    def drop_circle_x(name="dropCircle_cont"):
        cont_drop_circle_x = cmds.curve(d=3,
                                        p=[(4.47035e-07, 0.999999, 0), (0.195091, 0.980784, 0), (0.382683, 0.923878, 0),
                                           (0.55557, 0.831468, 0), (0.707106, 0.707106, 0), (0.831469, 0.555569, 0),
                                           (0.923879, 0.382683, 0), (0.980784, 0.19509, 0), (1, 0, 0),
                                           (0.980785, -0.19509, 0), (0.923879, -0.382683, 0), (0.831469, -0.55557, 0),
                                           (0.707107, -0.707107, 0), (0.55557, -0.83147, 0), (0.382683, -0.923879, 0),
                                           (0.19509, -0.980785, 0), (-1.63913e-07, -1, 0), (-0.19509, -0.980785, 0),
                                           (-0.382683, -0.923879, 0), (-0.55557, -0.831469, 0),
                                           (-0.707107, -0.707106, 0), (-0.831469, -0.55557, 0),
                                           (-0.923879, -0.382683, 0), (-0.980785, -0.19509, 0),
                                           (-0.999999, 3.27826e-07, 0), (-0.980785, 0.195091, 0),
                                           (-0.923879, 0.382683, 0), (-0.831469, 0.55557, 0), (-0.707106, 0.707106, 0),
                                           (-0.555569, 0.831469, 0), (-0.382683, 0.923879, 0), (-0.19509, 0.980784, 0),
                                           (4.47035e-07, 0.999999, 0)],
                                        k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                           20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 30, 30])
        x_plus = cmds.curve(d=3, p=[(3, 0.999999, 0), (3.195091, 0.980784, 0), (3.382684, 0.923878, 0),
                                    (3.55557, 0.831468, 0), (3.707106, 0.707106, 0), (3.831469, 0.555569, 0),
                                    (3.923879, 0.382683, 0), (3.980784, 0.19509, 0), (4, 0, 0), (3.980785, -0.19509, 0),
                                    (3.923879, -0.382683, 0), (3.83147, -0.55557, 0), (3.707107, -0.707107, 0),
                                    (3.55557, -0.83147, 0), (3.382683, -0.923879, 0), (3.19509, -0.980785, 0),
                                    (3, -1, 0), (2.801629, -0.980785, 0), (2.539676, -0.923879, 0),
                                    (2.255514, -0.831469, 0), (1.9439, -0.707106, 0), (1.59123, -0.55557, 0),
                                    (1.136886, -0.382683, 0), (0.611128, -0.19509, 0), (2.38419e-07, 3.27826e-07, 0),
                                    (0.611129, 0.195091, 0), (1.136886, 0.382683, 0), (1.59123, 0.55557, 0),
                                    (1.9439, 0.707106, 0), (2.255515, 0.831469, 0), (2.539676, 0.923879, 0),
                                    (2.80163, 0.980784, 0), (3, 0.999999, 0)],
                            k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                               23, 24, 25, 26, 27, 28, 29, 30, 30, 30], name="%s_plus" % name)
        x_minus = cmds.curve(d=3, p=[(-3, 0.999999, 0), (-2.801629, 0.980784, 0), (-2.539676, 0.923878, 0),
                                     (-2.255514, 0.831468, 0), (-1.943899, 0.707106, 0), (-1.59123, 0.555569, 0),
                                     (-1.136886, 0.382683, 0), (-0.611132, 0.19509, 0), (0, 0, 0),
                                     (-0.611131, -0.19509, 0), (-1.136885, -0.382683, 0), (-1.59123, -0.55557, 0),
                                     (-1.943899, -0.707107, 0), (-2.255514, -0.83147, 0), (-2.539676, -0.923879, 0),
                                     (-2.80163, -0.980785, 0), (-3, -1, 0), (-3.195091, -0.980785, 0),
                                     (-3.382684, -0.923879, 0), (-3.55557, -0.831469, 0), (-3.707107, -0.707106, 0),
                                     (-3.831469, -0.55557, 0), (-3.923879, -0.382683, 0), (-3.980785, -0.19509, 0),
                                     (-3.999999, 3.27826e-07, 0), (-3.980784, 0.195091, 0), (-3.923879, 0.382683, 0),
                                     (-3.831469, 0.55557, 0), (-3.707106, 0.707106, 0), (-3.555569, 0.831469, 0),
                                     (-3.382683, 0.923879, 0), (-3.19509, 0.980784, 0), (-3, 0.999999, 0)],
                             k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                                23, 24, 25, 26, 27, 28, 29, 30, 30, 30], name="%s_minus" % name)

        _bl_node = cmds.blendShape([x_plus, x_minus], cont_drop_circle_x)

        # TODO : promote xMinus and xPlus

        cmds.delete(x_plus)
        cmds.delete(x_minus)
        return cont_drop_circle_x



    @staticmethod
    def shoulder(name="shoulder_cont"):
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
                                   p=[(0, 0, 5), (1, 0, 5), (2, 0, 5), (2, 1, 4), (2, 2, 3), (2, 3, 2), (2, 3, 1),
                                      (2, 3, 0), (2, 3, -1),
                                      (2, 3, -2), (2, 2, -3), (2, 1, -4), (2, 0, -5), (1, 0, -5), (0, 0, -5),
                                      (-1, 0, -5), (-2, 0, -5),
                                      (-2, 1, -4), (-2, 2, -3), (-2, 3, -2), (-2, 3, -1), (-2, 3, 0), (-2, 3, 1),
                                      (-2, 3, 2), (-2, 2, 3),
                                      (-2, 1, 4), (-2, 0, 5), (-1, 0, 5), (0, 0, 5)],
                                   k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                      21, 22, 23, 24, 25,
                                      26, 26, 26], name=name)

        cmds.setAttr("%s.scale" % cont_shoulder, 0.5, 0.5, 0.5)
        cmds.makeIdentity(cont_shoulder, a=True)
        cmds.makeIdentity(cont_shoulder, a=True)

        return cont_shoulder

    @staticmethod
    def plus(name="plus_cont"):
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

    @staticmethod
    def waist(name="waist_cont"):
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

    @staticmethod
    def square(name="square_cont"):
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

    @staticmethod
    def sphere(name="sphere_cont"):
        cont_sphere = cmds.curve(name=name, d=1, p=[(-2.98023e-08, 0, 1), (-2.94354e-08, 0.156434, 0.987688),
                                                    (-2.83437e-08, 0.309017, 0.951057),
                                                    (-2.65541e-08, 0.453991, 0.891007),
                                                    (-2.41106e-08, 0.587785, 0.809017),
                                                    (-2.10734e-08, 0.707107, 0.707107),
                                                    (-1.75174e-08, 0.809017, 0.587785),
                                                    (-1.353e-08, 0.891007, 0.453991),
                                                    (-9.20942e-09, 0.951057, 0.309017),
                                                    (-4.66211e-09, 0.987688, 0.156434), (0, 1, 0),
                                                    (0, 0.987688, -0.156435),
                                                    (0, 0.951057, -0.309017), (0, 0.891007, -0.453991),
                                                    (0, 0.809017, -0.587786),
                                                    (0, 0.707107, -0.707107), (0, 0.587785, -0.809017),
                                                    (0, 0.453991, -0.891007),
                                                    (0, 0.309017, -0.951057), (0, 0.156434, -0.987689), (0, 0, -1),
                                                    (0, -0.156434, -0.987689),
                                                    (0, -0.309017, -0.951057), (0, -0.453991, -0.891007),
                                                    (0, -0.587785, -0.809017),
                                                    (0, -0.707107, -0.707107), (0, -0.809017, -0.587786),
                                                    (0, -0.891007, -0.453991),
                                                    (0, -0.951057, -0.309017), (0, -0.987688, -0.156435), (0, -1, 0),
                                                    (-4.66211e-09, -0.987688, 0.156434),
                                                    (-9.20942e-09, -0.951057, 0.309017),
                                                    (-1.353e-08, -0.891007, 0.453991),
                                                    (-1.75174e-08, -0.809017, 0.587785),
                                                    (-2.10734e-08, -0.707107, 0.707107),
                                                    (-2.41106e-08, -0.587785, 0.809017),
                                                    (-2.65541e-08, -0.453991, 0.891007),
                                                    (-2.83437e-08, -0.309017, 0.951057),
                                                    (-2.94354e-08, -0.156434, 0.987688), (-2.98023e-08, 0, 1),
                                                    (0.309017, 0, 0.951057),
                                                    (0.587785, 0, 0.809017), (0.809017, 0, 0.587785),
                                                    (0.951057, 0, 0.309017), (1, 0, 0),
                                                    (0.951057, 0, -0.309017), (0.809018, 0, -0.587786),
                                                    (0.587786, 0, -0.809017),
                                                    (0.309017, 0, -0.951057), (0, 0, -1), (-0.309017, 0, -0.951057),
                                                    (-0.587785, 0, -0.809017),
                                                    (-0.809017, 0, -0.587785), (-0.951057, 0, -0.309017), (-1, 0, 0),
                                                    (-0.951057, 0, 0.309017),
                                                    (-0.809017, 0, 0.587785), (-0.587785, 0, 0.809017),
                                                    (-0.309017, 0, 0.951057),
                                                    (-2.98023e-08, 0, 1), (-2.94354e-08, 0.156434, 0.987688),
                                                    (-2.83437e-08, 0.309017, 0.951057),
                                                    (-2.65541e-08, 0.453991, 0.891007),
                                                    (-2.41106e-08, 0.587785, 0.809017),
                                                    (-2.10734e-08, 0.707107, 0.707107),
                                                    (-1.75174e-08, 0.809017, 0.587785),
                                                    (-1.353e-08, 0.891007, 0.453991),
                                                    (-9.20942e-09, 0.951057, 0.309017),
                                                    (-4.66211e-09, 0.987688, 0.156434), (0, 1, 0),
                                                    (-0.156435, 0.987688, 0),
                                                    (-0.309017, 0.951057, 0), (-0.453991, 0.891007, 0),
                                                    (-0.587785, 0.809017, 0),
                                                    (-0.707107, 0.707107, 0), (-0.809017, 0.587785, 0),
                                                    (-0.891007, 0.453991, 0),
                                                    (-0.951057, 0.309017, 0), (-0.987689, 0.156434, 0), (-1, 0, 0),
                                                    (-0.987689, -0.156434, 0),
                                                    (-0.951057, -0.309017, 0), (-0.891007, -0.453991, 0),
                                                    (-0.809017, -0.587785, 0),
                                                    (-0.707107, -0.707107, 0), (-0.587785, -0.809017, 0),
                                                    (-0.453991, -0.891007, 0),
                                                    (-0.309017, -0.951057, 0), (-0.156435, -0.987688, 0), (0, -1, 0),
                                                    (0.156434, -0.987688, 0),
                                                    (0.309017, -0.951057, 0), (0.453991, -0.891007, 0),
                                                    (0.587785, -0.809017, 0),
                                                    (0.707107, -0.707107, 0), (0.809017, -0.587785, 0),
                                                    (0.891007, -0.453991, 0),
                                                    (0.951057, -0.309017, 0), (0.987688, -0.156434, 0), (1, 0, 0),
                                                    (0.987688, 0.156434, 0),
                                                    (0.951057, 0.309017, 0), (0.891007, 0.453991, 0),
                                                    (0.809017, 0.587785, 0),
                                                    (0.707107, 0.707107, 0), (0.587785, 0.809017, 0),
                                                    (0.453991, 0.891007, 0),
                                                    (0.309017, 0.951057, 0), (0.156434, 0.987688, 0), (0, 1, 0)],
                                 k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                                    23, 24, 25, 26,
                                    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
                                    48, 49, 50, 51,
                                    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72,
                                    73, 74, 75, 76,
                                    77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97,
                                    98, 99, 100,
                                    101, 102, 103, 104, 105, 106, 107, 108, 109, 110])

        return cont_sphere

    @staticmethod
    def ngon(name="ngon_cont"):
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

    @staticmethod
    def tricircle(name="triCircle_cont"):
        """
        Creates a circle controller with triangles on each direction.
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) scale value as vector, example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)
        Returns:
            Controller node

        """
        cont_tri_circle = cmds.circle(name=name, nr=(0, 1, 0), ch=0)[0]
        master_tri = cmds.curve(bezier=True, d=3,
                               p=[(0, 0, 0.240), (0, 0, 0.240), (-0.150, 0, 0), (-0.150, 0, 0), (-0.150, 0, 0),
                                  (0, 0, -0.240), (0, 0, -0.240), (0, 0, -0.240), (-0.03, 0, -0.03), (-0.03, 0, 0),
                                  (0, 0, 0.240)])
        cmds.move(-1.036, 0, 0, master_tri)
        cmds.xform(master_tri, piv=(0, 0, 0), ws=True)
        cmds.makeIdentity(master_tri, a=True)
        for i in range(0, 4):
            newTri = cmds.duplicate(master_tri, name="arrow_%i" % i)[0]
            cmds.makeIdentity(newTri, a=True)
            newTriShape = functions.getShapes(newTri)[0]
            # previously created tricircle shapes clashes with this
            newTriShape = cmds.rename(newTriShape, naming.uniqueName(newTriShape))
            cmds.rotate(0, 90, 0, master_tri, r=True)
            cmds.parent(newTriShape, cont_tri_circle, r=True, s=True)
            cmds.delete(newTri)
        cmds.delete(master_tri)
        return cont_tri_circle

    @staticmethod
    def curved_circle(name="curvedCircle_cont"):
        """
        Creates a slightly curved circle controller
        Args:
            name: (String) name of the controller. Must be a String
            scale: (Vector) Scale value as vector. example (1,1.5,1)
            location: (Vector) Optional Location as vector. example (12,0,2)

        Returns:
            Controller node
        """
        cont_curved_circle = cmds.circle(name=name, nr=(0, 1, 0), ch=0, s=12, radius=1)[0]
        for cv_num in [3, 4, 5, 9, 10, 11]:
            cmds.move(0, 0.25, 0, "%s.cv[%i]" % (cont_curved_circle, cv_num), r=True)
        return cont_curved_circle

    @staticmethod
    def half_dome(name="halfDome_cont"):

        cont_half_curve = cmds.curve(name=name, d=1,
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
                                       31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
                                       51,
                                       52, 53, 54, 55, 56, 57, 58,
                                       59, 60, 61, 62, 63, 64, 65])
        cmds.makeIdentity(cont_half_curve, a=True, s=True)
        return cont_half_curve

    @staticmethod
    def looper(name="looper_cont"):

        cont_looper = cmds.curve(name=name, d=1,
                                 p=[(0, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -2), (2, 0, -2), (2, 0, 2),
                                    (-2, 0, 2), (-2, 0, -3), (3, 0, -3), (3, 0, 3), (-3, 0, 3), (-3, 0, -3)],
                                 k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        cmds.setAttr("%s.scale" % cont_looper, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_looper, a=True, s=True)
        return cont_looper

    @staticmethod
    def triangle(name="triangle_cont"):
        cont_triangle = cmds.curve(name=name, d=1, p=[(0, 0, -3), (-3, 0, 2), (3, 0, 2), (0, 0, -3)], k=[0, 1, 2, 3])
        cmds.setAttr("%s.scale" % cont_triangle, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_triangle, a=True, s=True)
        return cont_triangle

    @staticmethod
    def pyramid(name="pyramid_cont"):
        cont_pyramid = cmds.curve(name=name, d=1,
                                  p=[(-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1), (-1, 0, 1), (0, 2, 0), (1, 0, -1),
                                     (-1, 0, -1), (0, 2, 0), (1, 0, 1)], k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        cmds.setAttr("%s.scale" % cont_pyramid, 0.333, 0.333, 0.333)
        cmds.makeIdentity(cont_pyramid, a=True, s=True)
        return cont_pyramid

    @staticmethod
    def diamond(name="diamond_cont"):
        cont_diamond = cmds.curve(name=name, d=1,
                                  p=[(0.341725, 0, 1.051722), (1.105846, 0, 0), (0, 0.962601, 0),
                                     (0.341725, 0, 1.051722),
                                     (0, -0.962601, 0), (1.105846, 0, 0), (0.341725, 0, -1.051722), (0, 0.962601, 0),
                                     (-0.894648, 0, -0.65),
                                     (0, -0.962601, 0), (0.341725, 0, -1.051722), (-0.894648, 0, -0.65),
                                     (-0.894648, 0, 0.65), (0.341725, 0, 1.051722), (0, -0.962601, 0),
                                     (-0.894648, 0, 0.65), (0, 0.962601, 0)],
                                  k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
        cmds.makeIdentity(cont_diamond, a=True, s=True)
        return cont_diamond

    @staticmethod
    def arrow(name="arrow_cont"):
        cont_arrow = cmds.curve(name=name, d=1,
                                p=[(0.0335873, 0, 1.055001), (-4.955996, 0, 0.971701), (-4.983113, 0, 2.081272),
                                   (-7.934906, 0, -0.0118149), (-4.93066, 0, -2.06217), (-4.973678, 0, -0.968172),
                                   (0.0696592, 0, -1.018287), (0.0192114, 0, 1.054761)], k=[0, 1, 2, 3, 4, 5, 6, 7])
        cmds.makeIdentity(cont_arrow, a=True, s=True)
        return cont_arrow

    @staticmethod
    def preferences(name="pref_cont"):
        cont_pref = cmds.curve(name=name, d=1,
                               p=[(-2.005908, -0.00143437, 2.011916), (-2.005908, -0.00143437, -2.997386),
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
                               k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                                  24, 25, 26,
                                  27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
                                  48, 49, 50, 51,
                                  52, 53, 54, 55, 56])
        cmds.setAttr("%s.scale" % cont_pref, 0.333, 0.333, 0.333)
        cmds.setAttr("%s.rotate" % cont_pref, 90, 0, 0)
        cmds.makeIdentity(cont_pref, a=True)
        return cont_pref

    @staticmethod
    def rotator(name="rotator_cont"):
        _cont = cmds.curve(name=name, d=3,
                           p=[(-1.49012e-08, 0, 1), (-1.49012e-08, 0, 1.043301), (-1.49012e-08, 0, 1.086603),
                              (-1.49012e-08, 0, 1.129904), (-2.98023e-08, 0, 1.173205), (0.0375, 0, 1.151554),
                              (0.075, 0, 1.129904), (0.1125, 0, 1.108253), (0.15, 0, 1.086603), (0.1875, 0, 1.064952),
                              (0.225, 0, 1.043301), (0.2625, 0, 1.021651), (0.3, 0, 1), (0.2625, 0, 0.978349),
                              (0.225, 0, 0.956699), (0.1875, 0, 0.935048), (0.15, 0, 0.913397), (0.1125, 0, 0.891747),
                              (0.075, 0, 0.870096), (0.0375, 0, 0.848446), (0, 0, 0.826795), (0, 0, 0.870096),
                              (-7.45058e-09, 0, 0.913397), (-1.49012e-08, 0, 0.956699), (-1.49012e-08, 0, 1),
                              (-0.0782174, 0, 0.993844), (-0.155953, 0, 0.984649), (-0.232726, 0, 0.969373),
                              (-0.308066, 0, 0.94813), (-0.381504, 0, 0.921032), (-0.452593, 0, 0.888264),
                              (-0.520888, 0, 0.850012), (-0.585976, 0, 0.806527), (-0.647446, 0, 0.758062),
                              (-0.704931, 0, 0.70493), (-0.758062, 0, 0.647446), (-0.806527, 0, 0.585976),
                              (-0.850012, 0, 0.520888), (-0.888264, 0, 0.452593), (-0.921032, 0, 0.381504),
                              (-0.94813, 0, 0.308066), (-0.969373, 0, 0.232726), (-0.984649, 0, 0.155953),
                              (-0.993845, 0, 0.0782171), (-0.996922, 0, -1.65775e-07), (-0.993845, 0, -0.0782174),
                              (-0.984649, 0, -0.155953), (-0.969373, 0, -0.232726), (-0.94813, 0, -0.308066),
                              (-0.921032, 0, -0.381504), (-0.888264, 0, -0.452594), (-0.850012, 0, -0.520888),
                              (-0.806527, 0, -0.585977), (-0.758062, 0, -0.647447), (-0.70493, 0, -0.704931),
                              (-0.647446, 0, -0.758062), (-0.585976, 0, -0.806527), (-0.520888, 0, -0.850012),
                              (-0.452593, 0, -0.888265), (-0.381504, 0, -0.921032), (-0.308066, 0, -0.94813),
                              (-0.232726, 0, -0.969373), (-0.155953, 0, -0.984649), (-0.0782171, 0, -0.993845),
                              (2.23517e-07, 0, -1.000001), (2.08616e-07, 0, -0.956699), (2.08616e-07, 0, -0.913398),
                              (2.08616e-07, 0, -0.870097), (1.93715e-07, 0, -0.826796), (0.0375002, 0, -0.848446),
                              (0.0750002, 0, -0.870097), (0.1125, 0, -0.891747), (0.15, 0, -0.913398),
                              (0.1875, 0, -0.935049), (0.225, 0, -0.956699), (0.2625, 0, -0.97835), (0.3, 0, -1.000001),
                              (0.2625, 0, -1.021651), (0.225, 0, -1.043302), (0.1875, 0, -1.064952),
                              (0.15, 0, -1.086603), (0.1125, 0, -1.108254), (0.0750002, 0, -1.129904),
                              (0.0375002, 0, -1.151555), (2.23517e-07, 0, -1.173206), (2.23517e-07, 0, -1.129904),
                              (2.16067e-07, 0, -1.086603), (2.08616e-07, 0, -1.043302), (2.23517e-07, 0, -1.000001)],
                           k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                              23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
                              45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
                              67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 86, 86])
        cmds.makeIdentity(_cont, a=True)
        return _cont

    @staticmethod
    def curved_arrow(name="curvedArrow_cont"):
        _cont = cmds.curve(name=name, d=1, p=[(0, -0.954929, 1.653986), (0.0416667, -0.919075, 1.632761),
                                              (0.0833333, -0.883692, 1.610758), (0.166667, -0.814409, 1.564465),
                                              (0.333333, -0.682225, 1.463037), (0.388889, -0.640193, 1.426713),
                                              (0.444444, -0.599235, 1.389181), (0.5, -0.559385, 1.350474),
                                              (0.417852, -0.567843, 1.35888), (0.335703, -0.576354, 1.367233),
                                              (0.253555, -0.584916, 1.375532), (0.253555, -0.557868, 1.348956),
                                              (0.253555, -0.531353, 1.321848), (0.253555, -0.505381, 1.294219),
                                              (0.253555, -0.430827, 1.208315), (0.253555, -0.361519, 1.118125),
                                              (0.253555, -0.187432, 0.82511), (0.253555, -0.0681992, 0.505817),
                                              (0.253555, -0.0413541, 0.395286), (0.253555, -0.0211365, 0.283353),
                                              (0.253555, -0.0113765, 0.208148), (0.253555, -0.00761816, 0.170415),
                                              (0.253555, -0.000846997, 0.0568723), (0.253555, -0.000846955, -0.0568719),
                                              (0.253555, -0.00761813, -0.170414), (0.253555, -0.0113764, -0.208147),
                                              (0.253555, -0.0211365, -0.283352), (0.253555, -0.041354, -0.395285),
                                              (0.253555, -0.0681991, -0.505816), (0.253555, -0.187432, -0.825109),
                                              (0.253555, -0.361519, -1.118125), (0.253555, -0.430827, -1.208315),
                                              (0.253555, -0.505381, -1.294219), (0.253555, -0.531353, -1.321848),
                                              (0.253555, -0.557868, -1.348956), (0.253555, -0.584916, -1.375532),
                                              (0.335703, -0.576354, -1.367232), (0.417852, -0.567843, -1.35888),
                                              (0.5, -0.559385, -1.350474), (0.444444, -0.599235, -1.389181),
                                              (0.388889, -0.640193, -1.426713), (0.333333, -0.682225, -1.463037),
                                              (0.166667, -0.814409, -1.564465), (0.0833333, -0.883692, -1.610758),
                                              (0.0416667, -0.919075, -1.632761), (0, -0.954929, -1.653986),
                                              (-0.0416667, -0.919075, -1.632761), (-0.0833333, -0.883692, -1.610758),
                                              (-0.166667, -0.814409, -1.564465), (-0.333333, -0.682225, -1.463037),
                                              (-0.388889, -0.640193, -1.426713), (-0.444444, -0.599235, -1.389181),
                                              (-0.5, -0.559385, -1.350474), (-0.417852, -0.567843, -1.35888),
                                              (-0.335703, -0.576354, -1.367232), (-0.253555, -0.584916, -1.375532),
                                              (-0.253555, -0.557868, -1.348956), (-0.253555, -0.531353, -1.321848),
                                              (-0.253555, -0.505381, -1.294219), (-0.253555, -0.430827, -1.208315),
                                              (-0.253555, -0.361519, -1.118125), (-0.253555, -0.187432, -0.825109),
                                              (-0.253555, -0.0681991, -0.505816), (-0.253555, -0.041354, -0.395285),
                                              (-0.253555, -0.0211365, -0.283352), (-0.253555, -0.0113764, -0.208147),
                                              (-0.253555, -0.00761813, -0.170414),
                                              (-0.253555, -0.000846955, -0.0568719),
                                              (-0.253555, -0.000846997, 0.0568723), (-0.253555, -0.00761816, 0.170415),
                                              (-0.253555, -0.0113765, 0.208148), (-0.253555, -0.0211365, 0.283353),
                                              (-0.253555, -0.0413541, 0.395286), (-0.253555, -0.0681992, 0.505817),
                                              (-0.253555, -0.187432, 0.82511), (-0.253555, -0.361519, 1.118125),
                                              (-0.253555, -0.430827, 1.208315), (-0.253555, -0.505381, 1.294219),
                                              (-0.253555, -0.531353, 1.321848), (-0.253555, -0.557868, 1.348956),
                                              (-0.253555, -0.584916, 1.375532), (-0.335703, -0.576354, 1.367233),
                                              (-0.417852, -0.567843, 1.35888), (-0.5, -0.559385, 1.350474),
                                              (-0.444444, -0.599235, 1.389181), (-0.388889, -0.640193, 1.426713),
                                              (-0.333333, -0.682225, 1.463037), (-0.166667, -0.814409, 1.564465),
                                              (-0.0833333, -0.883692, 1.610758), (-0.0416667, -0.919075, 1.632761),
                                              (0, -0.954929, 1.653986)],
                           k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                              25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
                              47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
                              69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90])
        cmds.makeIdentity(_cont, a=True, s=True)
        return _cont

    @staticmethod
    def dual_curved_arrow(name="dualCurvedArrow_cont"):
        _cont = cmds.curve(name=name, d=1, p=[(0, -0.954929, -1.653986), (-0.0416667, -0.919075, -1.632761),
                                              (-0.0833333, -0.883692, -1.610758), (-0.166667, -0.814409, -1.564465),
                                              (-0.333333, -0.682225, -1.463037), (-0.388889, -0.640193, -1.426713),
                                              (-0.444444, -0.599235, -1.389181), (-0.5, -0.559385, -1.350474),
                                              (-0.417852, -0.567843, -1.35888), (-0.335703, -0.576354, -1.367232),
                                              (-0.253555, -0.584916, -1.375532), (-0.253555, -0.557868, -1.348956),
                                              (-0.253555, -0.531353, -1.321848), (-0.253555, -0.505381, -1.294219),
                                              (-0.253555, -0.430827, -1.208315), (-0.253555, -0.361519, -1.118125),
                                              (-0.253555, -0.187432, -0.825109), (-0.253555, -0.0681991, -0.505816),
                                              (-0.253555, -0.041354, -0.395285), (-0.253555, -0.0211365, -0.283352),
                                              (-0.283352, -0.0211365, -0.253555), (-0.395285, -0.041354, -0.253555),
                                              (-0.505816, -0.0681991, -0.253555), (-0.825109, -0.187432, -0.253555),
                                              (-1.118125, -0.361519, -0.253555), (-1.208315, -0.430827, -0.253555),
                                              (-1.294219, -0.505381, -0.253555), (-1.321848, -0.531353, -0.253555),
                                              (-1.348956, -0.557868, -0.253555), (-1.375532, -0.584916, -0.253555),
                                              (-1.367232, -0.576354, -0.335703), (-1.35888, -0.567843, -0.417852),
                                              (-1.350474, -0.559385, -0.5), (-1.389181, -0.599235, -0.444444),
                                              (-1.426713, -0.640193, -0.388889), (-1.463037, -0.682225, -0.333333),
                                              (-1.564465, -0.814409, -0.166667), (-1.610758, -0.883692, -0.0833333),
                                              (-1.632761, -0.919075, -0.0416667), (-1.653986, -0.954929, 0),
                                              (-1.632761, -0.919075, 0.0416667), (-1.610758, -0.883692, 0.0833333),
                                              (-1.564465, -0.814409, 0.166667), (-1.463037, -0.682225, 0.333333),
                                              (-1.426713, -0.640193, 0.388889), (-1.389181, -0.599235, 0.444444),
                                              (-1.350474, -0.559385, 0.5), (-1.35888, -0.567843, 0.417852),
                                              (-1.367232, -0.576354, 0.335703), (-1.375532, -0.584916, 0.253555),
                                              (-1.348956, -0.557868, 0.253555), (-1.321848, -0.531353, 0.253555),
                                              (-1.294219, -0.505381, 0.253555), (-1.208315, -0.430827, 0.253555),
                                              (-1.118125, -0.361519, 0.253555), (-0.825109, -0.187432, 0.253555),
                                              (-0.505816, -0.0681991, 0.253555), (-0.395285, -0.041354, 0.253555),
                                              (-0.283352, -0.0211365, 0.253555), (-0.253555, -0.0211365, 0.283353),
                                              (-0.253555, -0.0413541, 0.395286), (-0.253555, -0.0681992, 0.505817),
                                              (-0.253555, -0.187432, 0.82511), (-0.253555, -0.361519, 1.118125),
                                              (-0.253555, -0.430827, 1.208315), (-0.253555, -0.505381, 1.294219),
                                              (-0.253555, -0.531353, 1.321848), (-0.253555, -0.557868, 1.348956),
                                              (-0.253555, -0.584916, 1.375532), (-0.335703, -0.576354, 1.367233),
                                              (-0.417852, -0.567843, 1.35888), (-0.5, -0.559385, 1.350474),
                                              (-0.444444, -0.599235, 1.389181), (-0.388889, -0.640193, 1.426713),
                                              (-0.333333, -0.682225, 1.463037), (-0.166667, -0.814409, 1.564465),
                                              (-0.0833333, -0.883692, 1.610758), (-0.0416667, -0.919075, 1.632761),
                                              (0, -0.954929, 1.653986), (0.0416667, -0.919075, 1.632761),
                                              (0.0833333, -0.883692, 1.610758), (0.166667, -0.814409, 1.564465),
                                              (0.333333, -0.682225, 1.463037), (0.388889, -0.640193, 1.426713),
                                              (0.444444, -0.599235, 1.389181), (0.5, -0.559385, 1.350474),
                                              (0.417852, -0.567843, 1.35888), (0.335703, -0.576354, 1.367233),
                                              (0.253555, -0.584916, 1.375532), (0.253555, -0.557868, 1.348956),
                                              (0.253555, -0.531353, 1.321848), (0.253555, -0.505381, 1.294219),
                                              (0.253555, -0.430827, 1.208315), (0.253555, -0.361519, 1.118125),
                                              (0.253555, -0.187432, 0.82511), (0.253555, -0.0681992, 0.505817),
                                              (0.253555, -0.0413541, 0.395286), (0.253555, -0.0211365, 0.283353),
                                              (0.283353, -0.0211365, 0.253555), (0.395286, -0.0413541, 0.253555),
                                              (0.505817, -0.0681992, 0.253555), (0.82511, -0.187432, 0.253555),
                                              (1.118125, -0.361519, 0.253555), (1.208315, -0.430827, 0.253555),
                                              (1.294219, -0.505381, 0.253555), (1.321848, -0.531353, 0.253555),
                                              (1.348956, -0.557868, 0.253555), (1.375532, -0.584916, 0.253555),
                                              (1.367233, -0.576354, 0.335703), (1.35888, -0.567843, 0.417852),
                                              (1.350474, -0.559385, 0.5), (1.389181, -0.599235, 0.444444),
                                              (1.426713, -0.640193, 0.388889), (1.463037, -0.682225, 0.333333),
                                              (1.564465, -0.814409, 0.166667), (1.610758, -0.883692, 0.0833333),
                                              (1.632761, -0.919075, 0.0416667), (1.653986, -0.954929, 0),
                                              (1.632761, -0.919075, -0.0416667), (1.610758, -0.883692, -0.0833333),
                                              (1.564465, -0.814409, -0.166667), (1.463037, -0.682225, -0.333333),
                                              (1.426713, -0.640193, -0.388889), (1.389181, -0.599235, -0.444444),
                                              (1.350474, -0.559385, -0.5), (1.35888, -0.567843, -0.417852),
                                              (1.367233, -0.576354, -0.335703), (1.375532, -0.584916, -0.253555),
                                              (1.348956, -0.557868, -0.253555), (1.321848, -0.531353, -0.253555),
                                              (1.294219, -0.505381, -0.253555), (1.208315, -0.430827, -0.253555),
                                              (1.118125, -0.361519, -0.253555), (0.82511, -0.187432, -0.253555),
                                              (0.505817, -0.0681992, -0.253555), (0.395286, -0.0413541, -0.253555),
                                              (0.283353, -0.0211365, -0.253555), (0.253555, -0.0211365, -0.283352),
                                              (0.253555, -0.041354, -0.395285), (0.253555, -0.0681991, -0.505816),
                                              (0.253555, -0.187432, -0.825109), (0.253555, -0.361519, -1.118125),
                                              (0.253555, -0.430827, -1.208315), (0.253555, -0.505381, -1.294219),
                                              (0.253555, -0.531353, -1.321848), (0.253555, -0.557868, -1.348956),
                                              (0.253555, -0.584916, -1.375532), (0.335703, -0.576354, -1.367232),
                                              (0.417852, -0.567843, -1.35888), (0.5, -0.559385, -1.350474),
                                              (0.444444, -0.599235, -1.389181), (0.388889, -0.640193, -1.426713),
                                              (0.333333, -0.682225, -1.463037), (0.166667, -0.814409, -1.564465),
                                              (0.0833333, -0.883692, -1.610758), (0.0416667, -0.919075, -1.632761),
                                              (0, -0.954929, -1.653986)],
                           k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                              25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
                              47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
                              69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90,
                              91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                              111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128,
                              129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146,
                              147, 148, 149, 150, 151, 152, 153, 154, 155, 156])
        cmds.makeIdentity(_cont, a=True, s=True)
        return _cont

    @staticmethod
    def lollipop(name="lollipop_cont"):
        _cont = cmds.curve(name=name, d=1,
                           p=[(0, 0, 0), (0, 0, -1), (0, 0, -2), (0, 0, -3), (0, 0, -4), (-0.309017, 0, -4.048944),
                              (-0.587785, 0, -4.190983), (-0.809017, 0, -4.412215), (-0.951057, 0, -4.690983),
                              (-1, 0, -5), (-0.951057, 0, -5.309017), (-0.809017, 0, -5.587785),
                              (-0.587785, 0, -5.809017), (-0.309017, 0, -5.951057), (0, 0, -6),
                              (0.309017, 0, -5.951057), (0.587786, 0, -5.809018), (0.809018, 0, -5.587786),
                              (0.951057, 0, -5.309017), (1, 0, -5), (0.951057, 0, -4.690983), (0.809017, 0, -4.412215),
                              (0.587785, 0, -4.190983), (0.309017, 0, -4.048944), (-2.98023e-08, 0, -4)],
                           k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
        cmds.makeIdentity(_cont, a=True, s=True)
        return _cont
