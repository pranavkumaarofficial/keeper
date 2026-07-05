#!/usr/bin/env python3
"""Generate original stylized diving-keeper images bundled with the package.

These are simple geometric silhouettes drawn from scratch (no photos), so they
ship freely with the package and give `keeper` something colorful to render on a
fresh install. Run:  python tools/make_samples.py
"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "keeper", "images")
os.makedirs(OUT, exist_ok=True)

W, H = 240, 300


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_keeper(bg_top, bg_bot, jersey, name):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)

    # vertical gradient background
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(bg_top, bg_bot, y / H))

    skin = (232, 194, 160)
    glove = (245, 230, 60)

    # trailing legs (two diagonal capsules, lower-left)
    for dx in (-14, 8):
        d.line([(70 + dx, 210), (30 + dx, 275)], fill=jersey, width=20)
        d.line([(70 + dx, 210), (30 + dx, 275)], fill=jersey, width=20)
    # boots
    d.ellipse([12, 262, 46, 286], fill=(30, 30, 34))
    d.ellipse([34, 262, 68, 286], fill=(30, 30, 34))

    # torso — a thick diagonal from lower-left hip to upper-right shoulder
    d.line([(78, 205), (168, 120)], fill=jersey, width=54)
    d.ellipse([56, 182, 104, 228], fill=jersey)      # hip cap
    d.ellipse([146, 96, 194, 144], fill=jersey)      # shoulder cap

    # reaching arms (skin) up toward the ball, top-right
    d.line([(170, 120), (210, 66)], fill=skin, width=17)
    d.line([(160, 132), (206, 88)], fill=skin, width=17)
    # gloves
    d.ellipse([198, 52, 226, 80], fill=glove)
    d.ellipse([194, 74, 222, 102], fill=glove)

    # head + focused eye, just below the shoulder
    d.ellipse([150, 150, 196, 196], fill=skin)
    d.ellipse([176, 166, 186, 176], fill=(30, 30, 34))  # eye

    # the ball, top-right corner
    bx, by, br = 218, 44, 20
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=(245, 245, 245))
    for a in ((-8, -6), (7, -4), (0, 9)):
        d.polygon([(bx + a[0], by + a[1]), (bx + a[0] + 6, by + a[1] - 2),
                   (bx + a[0] + 3, by + a[1] + 6)], fill=(30, 30, 34))

    path = os.path.join(OUT, name)
    img.save(path)
    print("wrote", os.path.relpath(path))


# three kit colorways
draw_keeper((18, 46, 92), (8, 20, 44), (210, 44, 44), "keeper_red.png")
draw_keeper((14, 60, 40), (6, 24, 16), (240, 240, 245), "keeper_white.png")
draw_keeper((60, 20, 70), (20, 8, 30), (250, 190, 30), "keeper_gold.png")

print("done — 3 sample images generated")
