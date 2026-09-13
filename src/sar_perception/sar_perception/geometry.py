"""Pinhole camera geometry for a vertical cylinder with known radius."""
import math


def cylinder_point(left, right, center_v, fx, fy, cx, cy, radius):
    if not all(math.isfinite(v) for v in [left,right,center_v,fx,fy,cx,cy,radius]) or fx<=0 or fy<=0 or radius<=0 or right<=left:
        raise ValueError('Invalid camera intrinsics or silhouette')
    a=math.atan((left-cx)/fx); b=math.atan((right-cx)/fx)
    bearing=(a+b)/2
    distance=radius/math.sin((b-a)/2)
    z=distance*math.cos(bearing)
    return distance*math.sin(bearing), (center_v-cy)*z/fy, z
