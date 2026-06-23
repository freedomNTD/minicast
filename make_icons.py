"""Generate MiniCast's tray/app icons programmatically with Pillow.

Reproducible, dependency-free (apart from Pillow) art for the cast-themed
brand. Run::

    python make_icons.py

It overwrites the files under ``minicast/assets/``:

* ``icon.png``               1024×1024 colour app icon (rounded square +
                             blue→violet gradient + white Cast glyph)
* ``icon.ico``               multi-size Windows icon (16..256)
* ``menu_light{,_large}.png``   single-colour *dark* Cast glyph on transparent
                             (renders crisply on a light menu/task bar)
* ``menu_dark{,_large}.png``    single-colour *light* Cast glyph on transparent
                             (for dark menu/task bars)

The glyph is a "Cast" symbol: concentric Wi-Fi-style arcs fanning out from a
bottom-corner receiver dot — the universal "cast to a screen" cue that DLNA /
Chromecast users instantly recognise.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter


ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'minicast', 'assets')

# Brand palette: blue → violet, reminiscent of modern cast/streaming apps.
GRADIENT_TOP = (62, 132, 255)     # #3E84FF
GRADIENT_BOTTOM = (138, 92, 246)  # #8A5CF6
GLYPH_COLOR = (255, 255, 255, 255)

SUPERSAMPLE = 4  # render 4× larger then downscale for smooth anti-aliasing


def _rounded_gradient(size, radius_ratio=0.22):
    """Square image with a vertical blue→violet gradient and rounded corners."""
    s = size * SUPERSAMPLE
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    grad = Image.new('RGBA', (1, s))
    for y in range(s):
        t = y / max(s - 1, 1)
        r = int(GRADIENT_TOP[0] + (GRADIENT_BOTTOM[0] - GRADIENT_TOP[0]) * t)
        g = int(GRADIENT_TOP[1] + (GRADIENT_BOTTOM[1] - GRADIENT_TOP[1]) * t)
        b = int(GRADIENT_TOP[2] + (GRADIENT_BOTTOM[2] - GRADIENT_TOP[2]) * t)
        grad.putpixel((0, y), (r, g, b, 255))
    grad = grad.resize((s, s))
    mask = Image.new('L', (s, s), 0)
    d = ImageDraw.Draw(mask)
    radius = int(s * radius_ratio)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img.resize((size, size), Image.LANCZOS)


def _cast_glyph(size, color):
    """Draw the Cast glyph centred on a transparent square.

    The arcs emanate from a receiver dot anchored at the bottom-centre and
    open upward like Wi-Fi waves, ending at a corner rectangle representing
    the destination screen.
    """
    s = size * SUPERSAMPLE
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx = s * 0.5        # receiver dot centre x
    cy = s * 0.66       # receiver dot centre y (lower-third)
    dot_r = s * 0.055   # receiver dot radius
    line_w = max(s * 0.052, 2)

    # Three concentric arcs opening upward, fanning out from the receiver.
    for i, radius in enumerate((s * 0.15, s * 0.26, s * 0.37)):
        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        d.arc(bbox, start=140, end=220, fill=color, width=int(line_w))

    # Filled receiver dot.
    d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=color)

    return img.resize((size, size), Image.LANCZOS)


def make_app_icon(size=1024):
    bg = _rounded_gradient(size)
    glyph = _cast_glyph(int(size * 0.62), GLYPH_COLOR)
    bg.alpha_composite(glyph, (
        (size - glyph.width) // 2,
        (size - glyph.height) // 2,
    ))
    return bg


def make_template_icon(size, glyph_rgba):
    """Transparent-background single-colour glyph for menu/task bars."""
    glyph = _cast_glyph(size, glyph_rgba)
    # Match the legacy assets: a tightly-cropped square with the glyph.
    return glyph


def _generate_icns(app_icon):
    """Build a macOS .icns from the 1024px app icon via iconutil.

    Only runs on macOS where iconutil exists; otherwise this is a no-op (the
    repo already ships a committed icon.icns as a fallback).
    """
    import shutil
    import subprocess
    import tempfile

    if shutil.which('iconutil') is None:
        print("iconutil not found — skipping .icns generation")
        return

    # iconutil requires the directory to end with the .iconset extension.
    iconset = tempfile.mkdtemp(prefix='iconset_', suffix='.iconset')
    try:
        # iconutil requires a specific filename layout inside the iconset.
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for s in sizes:
            app_icon.resize((s, s)).save(
                os.path.join(iconset, 'icon_{}x{}.png'.format(s, s)))
        for s in [16, 32, 128, 256, 512]:
            app_icon.resize((s * 2, s * 2)).save(
                os.path.join(iconset, 'icon_{}x{}@2x.png'.format(s, s)))
        out = os.path.join(ASSETS, 'icon.icns')
        subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', out], check=True)
        print("generated", out)
    finally:
        shutil.rmtree(iconset, ignore_errors=True)


def main():
    os.makedirs(ASSETS, exist_ok=True)

    # Colour app icon.
    app_icon = make_app_icon(1024)
    app_icon.save(os.path.join(ASSETS, 'icon.png'))
    # Windows multi-size .ico (skipped on non-Windows where Pillow can't write it).
    if sys.platform == 'win32':
        ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                     (128, 128), (256, 256)]
        app_icon.save(os.path.join(ASSETS, 'icon.ico'), sizes=ico_sizes)
    else:
        # macOS/Linux: regenerate the .icns bundle icon via iconutil.
        _generate_icns(app_icon)

    # Menu/task-bar template glyphs.
    DARK = (16, 16, 20, 255)    # near-black for light bars
    LIGHT = (245, 247, 255, 255)  # near-white for dark bars
    make_template_icon(1000, DARK).save(os.path.join(ASSETS, 'menu_light.png'))
    make_template_icon(1000, LIGHT).save(os.path.join(ASSETS, 'menu_dark.png'))
    make_template_icon(800, DARK).save(
        os.path.join(ASSETS, 'menu_light_large.png'))
    make_template_icon(800, LIGHT).save(
        os.path.join(ASSETS, 'menu_dark_large.png'))

    print("generated icons in", ASSETS)


if __name__ == '__main__':
    main()
