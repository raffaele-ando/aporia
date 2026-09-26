import numpy as np
from PIL import Image
import potrace

def trace_mask(mask, turdsize=2, alphamax=1.0, opttolerance=0.2, opticurve=True):
    bmp = potrace.Bitmap(~(mask.astype(bool)))
    return bmp.trace(turdsize=turdsize, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                     alphamax=alphamax, opticurve=opticurve, opttolerance=opttolerance)

def path_to_d(path, sx=1.0, sy=1.0, ox=0.0, oy=0.0, prec=3):
    """Convert potrace path to SVG 'd' with transform x->(x-ox)*sx, y->(y-oy)*sy"""
    def P(p):
        return f"{round((p[0]-ox)*sx, prec)},{round((p[1]-oy)*sy, prec)}"
    out = []
    for curve in path:
        start = curve.start_point
        out.append(f"M{P((start.x, start.y))}")
        for seg in curve:
            if seg.is_corner:
                out.append(f"L{P((seg.c.x, seg.c.y))}L{P((seg.end_point.x, seg.end_point.y))}")
            else:
                out.append(f"C{P((seg.c1.x, seg.c1.y))} {P((seg.c2.x, seg.c2.y))} {P((seg.end_point.x, seg.end_point.y))}")
        out.append("Z")
    return "".join(out)
