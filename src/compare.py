import numpy as np, io
from PIL import Image
import cairosvg

def render_path(d, W, H, scale=1.0):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' \
          f'<rect width="{W}" height="{H}" fill="#fff"/><path d="{d}" fill="#000" fill-rule="evenodd"/></svg>'
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H)
    return np.array(Image.open(io.BytesIO(png)).convert('L'))

def metrics(mask_ref, gray_render, thr=128):
    m2 = gray_render < thr
    inter = (mask_ref & m2).sum(); union = (mask_ref | m2).sum()
    diff = np.logical_xor(mask_ref, m2)
    return dict(iou=inter/union, xor_px=int(diff.sum()), ref_px=int(mask_ref.sum()),
                pct=100*diff.sum()/mask_ref.sum())

def gray_metrics(ref_gray, ren_gray):
    """anti-aliasing-aware: mean abs difference on 0..1"""
    a = ref_gray.astype(np.float64)/255; b = ren_gray.astype(np.float64)/255
    return dict(mae=float(np.abs(a-b).mean()), rmse=float(np.sqrt(((a-b)**2).mean())),
                maxerr=float(np.abs(a-b).max()))
