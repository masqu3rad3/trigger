import pymel.core as pm

# import extraProcedures as extra
# reload(extra)

def circle(name, scale, location=None, normal=(0, 1, 0)):
    """
    Createa a circle controller. Nothing Fancy...
    Args:
        name: name of the controller. Must be a String
        scale: scale value as vector, example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 
        normal: Optional Normal as vector. Default is (0, 1, 0) Y Up
    Returns:
        Controller node

    """

    cont_circle=pm.circle(name=name, nr=normal, ch=0)
    pm.setAttr(cont_circle[0].scale, scale)
    if location:
        pm.move(cont_circle[0], location)
    pm.makeIdentity(cont_circle, a=True)
    return cont_circle[0]


def cube(name, scale, location=None):
    """
    Createa a cube controller as a single shape
    Args:
        name: name of the controller. Must be a String
        scale: Scale value as vector. example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 

    Returns:
        Controller node
    """
    cont_cube = pm.curve(name=name, d=1, p=[(-1, 1, 1), (-1, 1, -1), (1, 1, -1), \
                                             (1, 1, 1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, 1),
                                             (-1, -1, 1), (1, -1, 1), \
                                             (1, 1, 1), (1, 1, -1), (1, -1, -1), (1, -1, 1), (1, -1, -1), (-1, -1, -1)],
                          k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    pm.setAttr(cont_cube.scale, scale)
    if location:
        pm.move(cont_cube, location)
    pm.makeIdentity(cont_cube, a=True)
    return cont_cube

def thigh(name, scale, location=None):
    """
    Createa a cube controller as a single shape
    Args:
        name: name of the controller. Must be a String
        scale: Scale value as vector. example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 
        
    Returns:
        Controller node
    """
    cont_thigh=pm.curve(name=name, d=1, p=[(-1, 1, 1), (-1, 1, -1), (1, 1, -1), \
                                           (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), \
                                           (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)], k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    pm.setAttr(cont_thigh.scale, scale)
    if location:
        pm.move(cont_thigh, location)
    pm.makeIdentity(cont_thigh, a=True)
    return cont_thigh
    
def star(name, scale, location=None):
    """
    Createa a star-ish shaped controller
    Args:
        name: name of the controller. Must be a String
        scale: Scale value as vector. example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 

    Returns:
        Controller node
    """
    cont_star=pm.circle(name=name, nr=(0, 1, 0), ch=0, radius=1.5)
    pm.rebuildCurve(cont_star, s=12, ch=0)
    pm.select(cont_star[0].cv[0], cont_star[0].cv[2], cont_star[0].cv[4], cont_star[0].cv[6], cont_star[0].cv[8], cont_star[0].cv[10])
    pm.scale(0.5, 0.5, 0.5)
    pm.select(d=True)
    pm.setAttr(cont_star[0].scale, scale)
    if location:
        pm.move(cont_star, location)
    pm.makeIdentity(cont_star, a=True)
    return cont_star[0]
    
def fkikSwitch(name, scale, location=None):
    """
    Createa a FK-IK controller. 
    Args:
        name: name of the controller. Must be a String
        scale: Scale value as vector. example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 

    Returns:
        A list Containing Controller Node (index 0) and Reverse node (1) to be used
        in conjunction with fk_ik attribute.
        [Controller Node, Reverse Node for connections]
    """
    letter_fk_f=pm.curve (d= 1, p= [( -8.145734, -5.011799, 0 ), ( -8.145734, 4.99286, 0 ), ( -1.059101, 4.99286, 0 ), ( -1.059101, 2.908556, 0 ), ( -5.227709, 2.908556,0 ), ( -5.227709, 1.241113, 0 ), ( -1.892823, 1.241113, 0 ), ( -1.892823, -0.843191, 0 ), ( -5.227709, -0.843191, 0 ), ( -5.227709, -5.011799, 0 ), ( -8.145734, -5.011799, 0)], k=[ 0 ,  1 ,  2 ,  3 ,  4 ,  5 ,  6 ,  7 ,  8 ,  9 ,  10 ], name="letterFK_F")
    letter_f_k_k=pm.curve (d= 1, p= [(  1.025203, -5.011799, 0 ), (  1.025203, 4.99286, 0 ), (  3.943228, 4.99286, 0 ), (  3.943228, 1.215065, 0 ), (  7.193445, 4.99286, 0 ), (  11.029861, 4.99286, 0 ), (  7.382331, 1.084794, 0 ), (  11.029861, -5.011799, 0 ), (  7.857814, -5.011799, 0 ), (  5.669293, -0.752001, 0 ), (  3.943228, -2.608331, 0 ), (  3.943228, -5.011799, 0 ), (  1.025203, -5.011799, 0)], k= [0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12], name="letterFK_K")
    pm.parent(letter_f_k_k+"Shape", letter_fk_f, r=True, s=True)
    pm.delete(letter_f_k_k)
    letter_fk=pm.rename(letter_fk_f, "letterFK")
    letter_ik=pm.duplicate(letter_fk, name="letterIK")

    pm.move(-4.168608, 0, 0, "letterIKShape.cv[2]", r=True, os=True, wd=True)
    pm.move(-4.168608, 0, 0, "letterIKShape.cv[3]", r=True, os=True, wd=True)
    pm.move(-3.334886, 0, 0, "letterIKShape.cv[6]", r=True, os=True, wd=True)
    pm.move(-3.334886, 0, 0, "letterIKShape.cv[7]", r=True, os=True, wd=True)
    pm.move(2.897946, 0, 0, "letterIKShape.cv[0:10]", r=True, os=True, wd=True)
    pm.move(-1.505933, 0, 0, "letterIK_KShape.cv[0:12]", r=True, os=True, wd=True)

    blShape_FKtoIK=pm.blendShape(letter_ik, letter_fk)

    cont_FK_IK=pm.rename(letter_fk, name)
    pm.select(cont_FK_IK)
    pm.addAttr( shortName="fk_ik", longName="FK_IK", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
    

    fk_ik_rvs=pm.createNode("reverse", name="fk_ik_rvs"+name)
    cont_FK_IK.fk_ik >> blShape_FKtoIK[0].weight[0]
    cont_FK_IK.fk_ik >> fk_ik_rvs.inputX

    pm.setAttr(cont_FK_IK.scale, (0.1,0.1,0.1))
    pm.delete(letter_ik)
    pm.select(cont_FK_IK)
    pm.makeIdentity(a=True)

    pm.setAttr(cont_FK_IK.scale, scale)
    if location:
        pm.move(cont_FK_IK, location)
    pm.makeIdentity(a=True)
    return [cont_FK_IK, fk_ik_rvs]
    
def shoulder(name, scale, location=None):
    """
    Createa a bended Eliptical controller for shoulders.
    Args:
        name: name of the controller. Must be a String
        scale: Scale value as vector. example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 

    Returns:
        Controller node
    """
    cont_shoulder=pm.curve (d=3, p=((-3, 0, 1),(-1, 2, 1), (1, 2, 1), (3, 0, 1), (3, 0, 0),(3, 0, -1),(1, 2, -1),(-1, 2, -1),(-3, 0, -1),(-3, 0, 0)),k=(0,0,0,1,2,3,4,5,6,7,7,7),name=name)
    pm.setAttr(cont_shoulder.scale, (0.5, 0.5, 0.5))
    pm.makeIdentity(cont_shoulder, a=True)
    pm.setAttr(cont_shoulder.scale, scale)
    pm.rotate(cont_shoulder, (0,90,0))
    if location:
        pm.move(cont_shoulder, location)
    pm.makeIdentity(cont_shoulder, a=True)
    return cont_shoulder

def plus(name, scale, location=None):
    """
    Createa a plus controller. Usually for pole vector
    Args:
        name: name of the controller. Must be a String
        scale: scale value as vector, example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """
    cont_Pole=pm.curve(name=name, d=1,p=[(-1, 0, -3), (-1, 0, -1),(-3, 0, -1), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (1, 0, 3), (1, 0, 1), (3, 0, 1), (3, 0, -1), (1, 0, -1), (1, 0, -3), (-1, 0, -3)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
    pm.setAttr(cont_Pole + ".scale", (0.4, 0.4, 0.4))
    pm.makeIdentity(cont_Pole, a=True, s=True)
    pm.setAttr(cont_Pole.scale, scale)
    if location:
        pm.move(cont_Pole, location)
    pm.makeIdentity(cont_Pole, a=True)
    return cont_Pole
    
def waist(name, scale, location=None):
    """
    Createa a plus controller. Usually for pole vector
    Args:
        name: name of the controller. Must be a String
        scale: scale value as vector, example (1,1.5,1)
        location: Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """
    cont_waist=pm.curve(d=1, p=[(-6.086269,0,2.259307), (-7.671805,0,-2.12977e-007),(-6.086269,0,-2.259308),(-6.08099,0,-1.545085),(-4.755284, 0, -1.545085), (-4.045086, 0, -2.938927), (-2.938927, 0, -4.045086), (-1.545086, 0, -4.755285), (-1.545086, 0, -6.080991), (-2.259309, 0, -6.08627), (-1.05973e-006, 0, -7.671805), (2.259307, 0, -6.086271), (1.545086, 0, -6.122436), (1.545086, 0, -4.755285), (2.938928, 0, -4.045087), (4.045088, 0, -2.938928), (4.755286, 0, -1.545086), (6.080994, 0, -1.545086), (6.086271, 0, -2.259301), (7.671804, 0, 3.02757e-006), (6.086267, 0, 2.259305), (6.080992, 0, 1.545085), (4.755283, 0, 1.545085), (4.045085, 0, 2.938926), (2.938926, 0, 4.045085), (1.545085, 0, 4.755283), (1.545085, 0, 6.080991), (2.259307, 0, 6.086268), (6.06841e-007, 0, 7.671803), (-2.259307, 0, 6.086269), (-1.545085, 0, 6.080991), (-1.545085, 0, 4.755283), (-2.938927, 0, 4.045085), (-4.045086, 0, 2.938927), (-4.755284, 0, 1.545085), (-6.08099, 0, 1.545085), (-6.086269, 0, 2.259307)], k=[ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36 ])
    pm.setAttr(cont_waist + ".scale", (0.2, 0.2, 0.2))
    pm.makeIdentity(cont_waist, a=True, s=True)
    pm.setAttr(cont_waist.scale, scale)
    if location:
        pm.move(cont_waist, location)
    pm.makeIdentity(cont_waist, a=True)
    return cont_waist

def square(name, scale, location=None):

    cont_square=pm.curve(d=1, p= [(1, 0, 1), (-1, 0, 1), (-1, 0, -1), (1, 0, -1), (1, 0, 1)], k=[0, 1, 2, 3, 4])
    pm.setAttr(cont_square.scale, scale)
    if location:
        pm.move(cont_square, location)
    pm.makeIdentity(cont_square, a=True)
    return cont_square