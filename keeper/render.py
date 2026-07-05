"""Render an image into the terminal in three styles.

  color : truecolor half-block (2 px per cell) — looks like a photo.
  ascii : brightness-ramp characters, each tinted with its pixel color —
          recognizable but unmistakably terminal art. (default)
  mono  : green phosphor brightness ramp — max retro, works on ANY terminal
          (no truecolor needed).

Every renderer returns (lines, error_message_or_None).
"""
from .art import RESET

RAMP = " .:-=+*#%@"  # dark -> dense


def _load(path, width, cell_ratio, crop=False):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None, None, "Pillow not installed (pip install Pillow)"
    try:
        img = Image.open(path).convert("RGB")
    except Exception as e:
        return None, None, f"couldn't open {path}: {e}"
    if crop:  # center-crop to the subject: middle 60% wide, 92% tall
        w, h = img.size
        img = img.crop((int(0.20 * w), int(0.04 * h),
                        int(0.80 * w), int(0.96 * h)))
        img = ImageOps.autocontrast(img, cutoff=1)  # boost busy photos only
    w, h = img.size
    new_h = max(1, int(width * h / w * cell_ratio))
    img = img.resize((width, new_h))
    return img.load(), new_h, None


def render_color(path, width=64, crop=False):
    """Truecolor half-block. Two vertical pixels per character cell."""
    # half-blocks pack 2 rows per cell, so double the vertical resolution
    px, new_h, err = _load(path, width, 1.0, crop)
    if err:
        return None, err
    if new_h % 2:  # need an even number of rows
        new_h -= 1
    lines = []
    for y in range(0, new_h, 2):
        row = []
        for x in range(width):
            tr, tg, tb = px[x, y]
            br, bg, bb = px[x, y + 1]
            row.append(f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m\u2580")
        lines.append("".join(row) + RESET)
    return lines, None


def render_ascii(path, width=70, crop=False):
    """Brightness-ramp characters, each tinted with its pixel color."""
    px, new_h, err = _load(path, width, 0.5, crop)
    if err:
        return None, err
    lines = []
    for y in range(new_h):
        row = []
        for x in range(width):
            r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            ch = RAMP[int(lum * (len(RAMP) - 1))]
            if ch == " ":
                row.append(" ")
            else:
                row.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
        lines.append("".join(row) + RESET)
    return lines, None


def render_mono(path, width=70, crop=False):
    """Green phosphor brightness ramp. No truecolor required."""
    px, new_h, err = _load(path, width, 0.5, crop)
    if err:
        return None, err
    lines = []
    for y in range(new_h):
        row = []
        for x in range(width):
            r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            ch = RAMP[int(lum * (len(RAMP) - 1))]
            if ch == " ":
                row.append(" ")
            else:
                glow = int(70 + 185 * lum)  # brighter pixels glow harder
                row.append(f"\x1b[38;2;0;{glow};40m{ch}")
        lines.append("".join(row) + RESET)
    return lines, None


STYLES = {"color": render_color, "ascii": render_ascii, "mono": render_mono}


def render(path, width, style="ascii", crop=False):
    return STYLES.get(style, render_ascii)(path, width, crop)


# backwards-compat alias
def render_image(path, width=64):
    return render_color(path, width)
