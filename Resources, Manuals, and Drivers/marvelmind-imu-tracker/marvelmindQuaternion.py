import numpy as np
import math

def normalize(v):
    v = np.array(v)
    norm=np.linalg.norm(v)
    if norm==0:
        norm=np.finfo(v.dtype).eps
    return v/norm

def calculateCSRotationQuaternion(lst1,lst2,matchlist=None):
    if not matchlist:
        matchlist=range(len(lst1))
    M=np.matrix([[0,0,0],[0,0,0],[0,0,0]])

    for i,coord1 in enumerate(lst1):
        x=np.matrix(np.outer(coord1,lst2[matchlist[i]]))
        M=M+x

    N11=float(M[0][:,0]+M[1][:,1]+M[2][:,2])
    N22=float(M[0][:,0]-M[1][:,1]-M[2][:,2])
    N33=float(-M[0][:,0]+M[1][:,1]-M[2][:,2])
    N44=float(-M[0][:,0]-M[1][:,1]+M[2][:,2])
    N12=float(M[1][:,2]-M[2][:,1])
    N13=float(M[2][:,0]-M[0][:,2])
    N14=float(M[0][:,1]-M[1][:,0])
    N21=float(N12)
    N23=float(M[0][:,1]+M[1][:,0])
    N24=float(M[2][:,0]+M[0][:,2])
    N31=float(N13)
    N32=float(N23)
    N34=float(M[1][:,2]+M[2][:,1])
    N41=float(N14)
    N42=float(N24)
    N43=float(N34)

    N=np.matrix([[N11,N12,N13,N14],\
                 [N21,N22,N23,N24],\
                 [N31,N32,N33,N34],\
                 [N41,N42,N43,N44]])

    values,vectors=np.linalg.eig(N)
    w=list(values)
    mw=max(w)
    quat= vectors[:,w.index(mw)]
    quat=np.array(quat).reshape(-1,).tolist()
    quat = normalize(quat)
    return quat

def calculateVectorRotationQuaternion(v1,v2):
    q = np.append(np.array([0]),np.cross(v1, v2))
    q[0] = np.sqrt((np.linalg.norm(v1)*np.linalg.norm(v1)) * (np.linalg.norm(v2)*np.linalg.norm(v2))) + np.dot(v1, v2)
    q = normalize(q)
    return q

def qMult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return [w, x, y, z]

def qConjugate(q):
    w, x, y, z = q
    return (w, -x, -y, -z)

def quaternionRotate(q1, v1):
    q2 = np.append([0], v1)
    return qMult(qMult(q1, q2), qConjugate(q1))[1:]

def quaternionToEulerianAngle(q):
    w, x, y, z = q
    ysqr = y*y
    
    t0 = +2.0 * (w * x + y*z)
    t1 = +1.0 - 2.0 * (x*x + ysqr)
    X = math.degrees(math.atan2(t0, t1))
    
    t2 = +2.0 * (w*y - z*x)
    t2 =  1 if t2 > 1 else t2
    t2 = -1 if t2 < -1 else t2
    Y = math.degrees(math.asin(t2))
    
    t3 = +2.0 * (w * z + x*y)
    t4 = +1.0 - 2.0 * (ysqr + z*z)
    Z = math.degrees(math.atan2(t3, t4))
    
    return X, Y, Z 

def eulerToQuaternion( pitch,  roll,  yaw):
    q = [0,0,0,0]
    t0 = math.cos(yaw * 0.5)
    t1 = math.sin(yaw * 0.5)
    t2 = math.cos(roll * 0.5)
    t3 = math.sin(roll * 0.5)
    t4 = math.cos(pitch * 0.5)
    t5 = math.sin(pitch * 0.5)

    q[0] = t0 * t2 * t4 + t1 * t3 * t5
    q[1] = t0 * t3 * t4 - t1 * t2 * t5
    q[2] = t0 * t2 * t5 + t1 * t3 * t4
    q[3] = t1 * t2 * t4 - t0 * t3 * t5

    normalize(q)
    return q

def degreesDistance(alpha, beta):
    phi = abs(beta - alpha) % 360.0;
    if (phi > 180.0):
        distance = 360.0 - phi
    else:
        distance=phi

    sign = 0
    if ((alpha - beta >= 0 and alpha - beta <= 180) or (alpha - beta <=-180 and alpha - beta>= -360)):
        sign=1
    else:
        sign=-1
    return sign*distance



def slerp(v0, v1, t):
    v0 = normalize(v0)
    v1 = normalize(v1)

    dot = v0[0]*v1[0] + v0[1]*v1[1] + v0[2]*v1[2] + v0[3]*v1[3]

    DOT_THRESHOLD = 0.9995
    if (abs(dot) > DOT_THRESHOLD):
        result=[v0[0] + t * (v1[0] - v0[0]), v0[1] + t * (v1[1] - v0[1]),
                v0[2] + t * (v1[2] - v0[2]), v0[3] + t * (v1[3] - v0[3])]
        normalize(result)
        return result

    if (dot < 0.0):
        v1[0] = -v1[0]
        v1[1] = -v1[1]
        v1[2] = -v1[2]
        v1[3] = -v1[3]
        dot = -dot;

    if (dot<-1): dot=-1
    if (dot>1): dot=1
    theta_0 = math.acos(dot)
    theta = theta_0 * t

    v2=[v1[0] - v0[0]*dot, v1[1] - v0[1]*dot, v1[2] - v0[2]*dot, v1[3] - v0[3]*dot]
    normalize(v2)

    result=[v0[0] * math.cos(theta) + v2[0] * math.sin(theta),v0[1] * math.cos(theta) + v2[1] * math.sin(theta),v0[2] * math.cos(theta) + v2[2] * math.sin(theta),v0[3] * math.cos(theta) + v2[3] * math.sin(theta)]
    return result