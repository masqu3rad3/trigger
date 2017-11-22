import pymel.core as pm

def circle(name="cont_circle", scale=(1,1,1), location=None, normal=(0, 1, 0)):
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

    cont_circle=pm.circle(name=name, nr=normal, ch=0)
    pm.setAttr(cont_circle[0].scale, scale)
    if location:
        pm.move(cont_circle[0], location)
    pm.makeIdentity(cont_circle, a=True)
    return cont_circle[0]


def cube(name="cont_cube", scale=(1,1,1), location=None):
    """
    Creates a cube controller as a single shape
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) Scale value as vector. example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 

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

def thigh(name="cont_thigh", scale=(1,1,1), location=None):
    """
    Creates a cube controller as a single shape
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) Scale value as vector. example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
        
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
    
def star(name="cont_star", scale=(1,1,1), location=None, normal=(0, 1, 0)):
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
    cont_star=pm.circle(name=name, nr=normal, ch=0, s=12, radius=1.5)[0]
    # pm.rebuildCurve(cont_star, s=12, ch=0)
    # pm.select(cont_star[0].cv[0], cont_star[0].cv[2], cont_star[0].cv[4], cont_star[0].cv[6], cont_star[0].cv[8], cont_star[0].cv[10])
    pm.scale(cont_star.cv[0,2,4,6,8,10], (0.5, 0.5, 0.5))
    # pm.scale(0.5, 0.5, 0.5)
    pm.select(d=True)
    pm.setAttr(cont_star.scale, scale)
    if location:
        pm.move(cont_star, location)
    pm.makeIdentity(cont_star, a=True)
    return cont_star
    
def fkikSwitch(name="cont_fkik", scale=(1,1,1), location=None):
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
    # return [cont_FK_IK, fk_ik_rvs]
    return cont_FK_IK, fk_ik_rvs

def shoulder(name="cont_shoulder", scale=(1,1,1), location=None, normal=(0,1,0)):
    """
    Creates a bended Eliptical controller for shoulders.
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) Scale value as vector. example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 

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
    if not normal == (0, 1, 0):
        pm.rotate(-normal[0]*90, normal[1]*180, normal[1]*90 )
        pm.makeIdentity(cont_shoulder, a=True, t=False, r=True, s=False)

    pm.makeIdentity(cont_shoulder, a=True)


    pm.closeCurve(cont_shoulder, ch=0, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)
    pm.delete(cont_shoulder, ch=True)

    return cont_shoulder

def plus(name="cont_plus", scale=(1,1,1), location=None, normal=(1,0,0)):
    """
    Creates a plus controller. Usually for pole vector
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) scale value as vector, example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
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
    if not normal == (1, 0, 0):
        pm.rotate(cont_Pole, normal[0]*90, normal[1]*90, normal[2]*90)
        # pm.rotate(cont_Pole, (0,0,90))
        pm.makeIdentity(cont_Pole, a=True)
    return cont_Pole


    
def waist(name="cont_waist", scale=(1,1,1), location=None):
    """
    Creates a plus controller. Usually for pole vector
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) scale value as vector, example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """
    cont_waist=pm.curve(name=name, d=1, p=[(-6.086269,0,2.259307), (-7.671805,0,-2.12977e-007),(-6.086269,0,-2.259308),(-6.08099,0,-1.545085),(-4.755284, 0, -1.545085), (-4.045086, 0, -2.938927), (-2.938927, 0, -4.045086), (-1.545086, 0, -4.755285), (-1.545086, 0, -6.080991), (-2.259309, 0, -6.08627), (-1.05973e-006, 0, -7.671805), (2.259307, 0, -6.086271), (1.545086, 0, -6.122436), (1.545086, 0, -4.755285), (2.938928, 0, -4.045087), (4.045088, 0, -2.938928), (4.755286, 0, -1.545086), (6.080994, 0, -1.545086), (6.086271, 0, -2.259301), (7.671804, 0, 3.02757e-006), (6.086267, 0, 2.259305), (6.080992, 0, 1.545085), (4.755283, 0, 1.545085), (4.045085, 0, 2.938926), (2.938926, 0, 4.045085), (1.545085, 0, 4.755283), (1.545085, 0, 6.080991), (2.259307, 0, 6.086268), (6.06841e-007, 0, 7.671803), (-2.259307, 0, 6.086269), (-1.545085, 0, 6.080991), (-1.545085, 0, 4.755283), (-2.938927, 0, 4.045085), (-4.045086, 0, 2.938927), (-4.755284, 0, 1.545085), (-6.08099, 0, 1.545085), (-6.086269, 0, 2.259307)], k=[ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36 ])
    pm.setAttr(cont_waist + ".scale", (0.2, 0.2, 0.2))
    pm.makeIdentity(cont_waist, a=True, s=True)
    pm.setAttr(cont_waist.scale, scale)
    if location:
        pm.move(cont_waist, location)
    pm.makeIdentity(cont_waist, a=True)
    return cont_waist

def square(name="cont_square", scale=(1,1,1), location=None):
    """
    Creates a square controller. 
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) scale value as vector, example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """
    cont_square=pm.curve(name=name, d=1, p= [(1, 0, 1), (-1, 0, 1), (-1, 0, -1), (1, 0, -1), (1, 0, 1)], k=[0, 1, 2, 3, 4])
    pm.setAttr(cont_square.scale, scale)
    if location:
        pm.move(cont_square, location)
    pm.makeIdentity(cont_square, a=True)
    return cont_square

def ngon(name="cont_ngon", scale=(1,1,1), location=None):
    """
    Creates a ngon controller. 
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) scale value as vector, example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """

    cont_ngon=pm.curve(name=name, d=1, p=[ (-2, 0, -4), (2, 0, -4), (4, 0, -2), (4, 0, 2), (2, 0, 4), (-2, 0, 4), (-4, 0, 2), (-4, 0, -2), (-2, 0, -4)], k=[0, 1, 2, 3, 4, 5, 6, 7, 8])
    pm.setAttr(cont_ngon + ".scale", (0.25, 0.25, 0.25))
    pm.makeIdentity(cont_ngon, a=True, s=True)
    pm.setAttr(cont_ngon.scale, scale)
    if location:
        pm.move(cont_ngon, location)
    pm.makeIdentity(cont_ngon, a=True)
    return cont_ngon

def triCircle(name="cont_triCircle", scale=(1,1,1), location=None):
    """
    Creates a circle controller with triangles on each direction. 
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) scale value as vector, example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 
    Returns:
        Controller node

    """
    cont_triCircle=pm.circle(name=name, nr=(0,1,0), ch=0)
    masterTri=pm.curve(bezier=True, d=3, p=[(0, 0, 0.240), (0, 0, 0.240), (-0.150, 0, 0), (-0.150, 0, 0), (-0.150, 0, 0), (0, 0, -0.240), (0, 0, -0.240), (0, 0, -0.240), (-0.03, 0, -0.03), (-0.03, 0, 0), (0, 0, 0.240)])


    # pm.setAttr(masterTri.scale, (0.03,0.03,0.03))
    # pm.closeCurve(masterTri, ch=0, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)

    pm.move(masterTri,(-1.036, 0, 0))
    pm.xform(masterTri, piv=(0,0,0), ws=True)
    pm.makeIdentity(masterTri, a=True)
    for i in range (0,4):
        newTri=pm.duplicate(masterTri)
        pm.makeIdentity(newTri, a=True)
        newTriShape=newTri[0].getShape()
        pm.rotate(masterTri, (0,90,0), r=True)
        pm.parent(newTriShape, cont_triCircle[0], r=True, s=True)
        pm.delete(newTri)
    pm.delete(masterTri)
    pm.setAttr(cont_triCircle[0].scale, scale)
    if location:
        pm.move(cont_triCircle[0], location)
    pm.makeIdentity(cont_triCircle, a=True)
    return cont_triCircle[0]


def curvedCircle(name="cont_curvedCircle", scale=(1, 1, 1), location=None):
    """
    Creates a slightly curved circle controller
    Args:
        name: (String) name of the controller. Must be a String
        scale: (Vector) Scale value as vector. example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 

    Returns:
        Controller node
    """
    cont_curvedCircle = pm.circle(name=name, nr=(0,1,0), ch=0, s=12, radius=1)[0]
    pm.move(cont_curvedCircle.cv[3,4,5,9,10,11], (0, 0.25, 0), r=True)
    pm.setAttr(cont_curvedCircle.scale, scale)
    if location:
        pm.move(cont_curvedCircle, location)
    pm.makeIdentity(cont_curvedCircle, a=True)
    return cont_curvedCircle

def halfDome(name="cont_halfDome", scale=(1,1,1), location=None, normal=(0,1,0)):
    """
    Creates a Half-Dome curve
    Args:
        name: (String) name of the controller
        scale: (Vector) Scale value as vector. example (1,1.5,1)
        location: (Vector) Optional Location as vector. example (12,0,2) 

    Returns:
        Controller node
    """

    halfCurve=pm.curve(name=name, bezier=True, d=3, p=[(-2, 0, 0), (-2, 0, 0), (-2, 0, -2), (0, 0, -2), (2, 0, -2), (2, 0, 0), (2, 0, 0)],
             k=[0, 0, 0, 1, 1, 1, 2, 2, 2])
    halfCurveD1=pm.duplicate(halfCurve)
    pm.rotate(halfCurveD1, (90,0,0))
    pm.makeIdentity(halfCurveD1, a=True)

    halfCurveD2 = pm.duplicate(halfCurve)
    pm.rotate(halfCurveD2, (180, 0, 0))
    pm.makeIdentity(halfCurveD2, a=True)

    halfCurveD3 = pm.duplicate(halfCurveD1)
    pm.rotate(halfCurveD3, (0,90,0))
    pm.makeIdentity(halfCurveD3, a=True)

    halfCurveD1Shape = halfCurveD1[0].getShape()
    halfCurveD2Shape = halfCurveD2[0].getShape()
    halfCurveD3Shape = halfCurveD3[0].getShape()

    pm.parent(halfCurveD1Shape, halfCurve, r=True, s=True)
    pm.delete(halfCurveD1)
    pm.parent(halfCurveD2Shape, halfCurve, r=True, s=True)
    pm.delete(halfCurveD2)
    pm.parent(halfCurveD3Shape, halfCurve, r=True, s=True)
    pm.delete(halfCurveD3)

    pm.setAttr(halfCurve.scale, scale)
    if location:
        pm.move(halfCurve, location)
    pm.makeIdentity(halfCurve, a=True)
    pm.select(d=True)
    if not normal == (0, 1, 0):
        pm.rotate(halfCurve, normal[0]*90, normal[1]*90, normal[2]*90)
        # pm.rotate(cont_Pole, (0,0,90))
        pm.makeIdentity(halfCurve, a=True)
    return halfCurve

def looper(name="cont_looper", scale=(1,1,1), location=None, normal=(0,1,0)):

    cont_Looper=pm.curve(name=name, d=1, p=[(0,0,-1),(1,0,-1),(1,0,1),(-1,0,1),(-1,0,-2),(2,0,-2),(2,0,2),(-2,0,2),(-2,0,-3),(3,0,-3),(3,0,3),(-3,0,3),(-3,0,-3)],
             k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
    pm.setAttr(cont_Looper + ".scale", (0.333, 0.333, 0.333))
    pm.makeIdentity(cont_Looper, a=True, s=True)
    pm.setAttr(cont_Looper.scale, scale)
    if location:
        pm.move(cont_Looper, location)
    pm.makeIdentity(cont_Looper, a=True)
    if not normal == (1, 0, 0):
        pm.rotate(cont_Looper, normal[0]*90, normal[1]*90, normal[2]*90)
        # pm.rotate(cont_Pole, (0,0,90))
        pm.makeIdentity(cont_Looper, a=True)
    return cont_Looper

def triangle(name="cont_triangle", scale=(1,1,1), location=None, normal=(0,1,0)):
    cont_Triangle=pm.curve(name=name, d=1, p=[(0,0,-3),(-3,0,2),(3,0,2),(0,0,-3)],k=[0,1,2,3])
    pm.setAttr(cont_Triangle + ".scale", (0.333, 0.333, 0.333))
    pm.makeIdentity(cont_Triangle, a=True, s=True)
    pm.setAttr(cont_Triangle.scale, scale)
    if location:
        pm.move(cont_Triangle, location)
    pm.makeIdentity(cont_Triangle, a=True)
    if not normal == (1, 0, 0):
        pm.rotate(cont_Triangle, normal[0]*90, normal[1]*90, normal[2]*90)
        # pm.rotate(cont_Pole, (0,0,90))
        pm.makeIdentity(cont_Triangle, a=True)
    return cont_Triangle
