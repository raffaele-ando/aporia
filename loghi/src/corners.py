import numpy as np

def turning(xy, k):
    p0 = np.roll(xy, k, axis=0); p2 = np.roll(xy, -k, axis=0)
    v1 = xy - p0; v2 = p2 - xy
    a1 = np.arctan2(v1[:,1], v1[:,0]); a2 = np.arctan2(v2[:,1], v2[:,0])
    return (a2 - a1 + np.pi) % (2*np.pi) - np.pi

def find_corners(xy, k=14, thr_deg=22, min_gap=10):
    t = turning(xy, k)
    mag = np.abs(t)
    idx = np.where(mag > np.radians(thr_deg))[0]
    if len(idx) == 0: return []
    groups, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > min_gap:
            groups.append((start, prev)); start = i
        prev = i
    groups.append((start, prev))
    # handle wraparound merge
    corners = []
    for a,b in groups:
        seg = np.arange(a, b+1)
        corners.append(int(seg[np.argmax(mag[seg])]))
    # merge first/last if wrapping close
    n = len(xy)
    if len(corners) > 1 and (corners[0] + n - corners[-1]) <= min_gap:
        keep = corners[0] if mag[corners[0]] >= mag[corners[-1]] else corners[-1]
        corners = [keep] + corners[1:-1]
    return sorted(corners), t
