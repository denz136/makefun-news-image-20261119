#!/usr/bin/env python3
"""Writes /output/entry.png — a one-image summary of world news for Thursday 19 November 2026.

Pure Python standard library: the PNG is rasterised and encoded here with zlib only.
Node-compatible alternative lives in main.ts; the grader runs main.py with Python 3.13.

    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- palette
BG = (13, 18, 30)
PANEL = (23, 31, 46)
PANEL_EDGE = (38, 49, 70)
INK = (242, 246, 252)
INK_DIM = (170, 184, 204)  # rev2: brighter for legibility at 300px
RED = (226, 74, 74)
ORANGE = (240, 152, 62)
BLUE = (74, 144, 236)
GREEN = (74, 190, 126)
YELLOW = (238, 206, 92)
STEEL = (92, 99, 114)
SEA = (44, 66, 104)
WATER = (54, 86, 138)

# ---------------------------------------------------------------- canvas
pix = bytearray()
_row = bytearray(BG) * W
for _ in range(H):
    pix += _row


CLIP = None  # (x0, y0, x1, y1) optional clip rectangle for artwork


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        if CLIP is not None:
            cx0, cy0, cx1, cy1 = CLIP
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return
        i = (y * W + x) * 3
        pix[i] = c[0]
        pix[i + 1] = c[1]
        pix[i + 2] = c[2]


def rect(x0, y0, x1, y1, c):
    x0 = max(0, int(x0)); y0 = max(0, int(y0))
    x1 = min(W, int(x1)); y1 = min(H, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    row = bytearray(c) * (x1 - x0)
    for y in range(y0, y1):
        o = (y * W + x0) * 3
        pix[o:o + len(row)] = row


def line(x0, y0, x1, y1, c, w=2):
    x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
    dx, dy = x1 - x0, y1 - y0
    steps = max(abs(dx), abs(dy)) or 1
    h = w // 2
    for i in range(steps + 1):
        x = x0 + dx * i / steps
        y = y0 + dy * i / steps
        for oy in range(-h, h + 1):
            for ox in range(-h, h + 1):
                px(int(x) + ox, int(y) + oy, c)


def circle(cx, cy, r, c, fill=True, thick=3):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if fill:
                if d2 <= r * r:
                    px(x, y, c)
            else:
                inner = (r - thick) ** 2
                if inner <= d2 <= r * r:
                    px(x, y, c)


# ---------------------------------------------------------------- bitmap font 5x7
FONT = {
    '0': ("111", "101", "101", "101", "111"),
    '1': ("010", "110", "010", "010", "111"),
    '2': ("111", "001", "111", "100", "111"),
    '3': ("111", "001", "111", "001", "111"),
    '4': ("101", "101", "111", "001", "001"),
    '5': ("111", "100", "111", "001", "111"),
    '6': ("111", "100", "111", "101", "111"),
    '7': ("111", "001", "010", "010", "010"),
    '8': ("111", "101", "111", "101", "111"),
    '9': ("111", "101", "111", "001", "111"),
    'A': ("111", "101", "111", "101", "101"),
    'B': ("110", "101", "110", "101", "110"),
    'C': ("111", "100", "100", "100", "111"),
    'D': ("110", "101", "101", "101", "110"),
    'E': ("111", "100", "111", "100", "111"),
    'F': ("111", "100", "111", "100", "100"),
    'G': ("111", "100", "101", "101", "111"),
    'H': ("101", "101", "111", "101", "101"),
    'I': ("111", "010", "010", "010", "111"),
    'J': ("001", "001", "001", "101", "111"),
    'K': ("101", "101", "110", "101", "101"),
    'L': ("100", "100", "100", "100", "111"),
    'M': ("101", "111", "111", "101", "101"),
    'N': ("110", "101", "101", "101", "101"),
    'O': ("111", "101", "101", "101", "111"),
    'P': ("111", "101", "111", "100", "100"),
    'Q': ("111", "101", "101", "111", "011"),
    'R': ("111", "101", "110", "101", "101"),
    'S': ("111", "100", "111", "001", "111"),
    'T': ("111", "010", "010", "010", "010"),
    'U': ("101", "101", "101", "101", "111"),
    'V': ("101", "101", "101", "101", "010"),
    'W': ("101", "101", "111", "111", "101"),
    'X': ("101", "101", "010", "101", "101"),
    'Y': ("101", "101", "010", "010", "010"),
    'Z': ("111", "001", "010", "100", "111"),
    ' ': ("000", "000", "000", "000", "000"),
    '.': ("000", "000", "000", "000", "010"),
    ',': ("000", "000", "000", "010", "100"),
    ':': ("000", "010", "000", "010", "000"),
    '-': ("000", "000", "111", "000", "000"),
    '/': ("001", "001", "010", "100", "100"),
    '!': ("010", "010", "010", "000", "010"),
    "'": ("010", "010", "000", "000", "000"),
    '%': ("101", "001", "010", "100", "101"),
    '+': ("000", "010", "111", "010", "000"),
    '(': ("010", "100", "100", "100", "010"),
    ')': ("010", "001", "001", "001", "010"),
    '"': ("101", "101", "000", "000", "000"),
    '&': ("110", "100", "111", "101", "111"),
}
ADV = 6  # glyph advance in font units (3 wide + 3 gap)


def text_width(s, scale):
    return len(s) * ADV * scale


def draw_text(s, x, y, c, scale=2):
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT['?'] if '?' in FONT else FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, v in enumerate(row):
                if v == '1':
                    rect(cx + gx * scale, y + gy * scale,
                         cx + gx * scale + scale, y + gy * scale + scale, c)
        cx += ADV * scale


def fit_scale(s, max_w, preferred):
    """Largest scale <= preferred that fits max_w."""
    sc = preferred
    while sc > 1 and text_width(s, sc) > max_w:
        sc -= 1
    return sc


def wrap(s, max_w, scale):
    words, lines, cur = s.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ================================================================ content
STORIES = [
    dict(kicker='SUMMIT',
         head="TRUMP, XI, PUTIN HOLD TALKS",
         body=["HISTORIC TRILATERAL IN SHENZHEN",
               "NUCLEAR ARMS AND TWO WARS ON",
               "THE TABLE; SEPARATE ONE-ON-ONE",
               "TALKS WITH XI AND PUTIN TOO"],
         color=BLUE, art='trio'),
    dict(kicker='MIDDLE EAST',
         head="TRUMP WEIGHS IRAN STRIKES",
         body=["ISRAEL WARNS OF CHEMICAL WEAPONS",
               "POSSIBLE HITS ON NUCLEAR SITES",
               "GULF TIT-FOR-TAT STRIKES GO ON:",
               "KUWAIT AND BAHRAIN INTERCEPT"],
         color=RED, art='gulf'),
    dict(kicker='UKRAINE',
         head="BRIDGE HIT AGAIN; DUTCH MISSILES",
         body=["CRIMEA LINK STRUCK SECOND TIME",
               "RUSSIA ASKS IF NETHERLANDS HAS",
               "JOINED THE WAR OVER DUTCH-MADE",
               "MISSILES IN THE ATTACK"],
         color=ORANGE, art='bridge'),
    dict(kicker='CLIMATE',
         head="COP31 NEARS ITS CLOSE",
         body=["NEGOTIATORS TO FINALISE A DEAL",
               "AS THE ANTALYA SUMMIT ENDS;",
               "'CLIMATE REALITY CHECK' LAUNCHED",
               "TO TRACK PAST PROMISES"],
         color=GREEN, art='cop'),
]

# ---------------------------------------------------------------- header
rect(0, 0, W, 128, (9, 13, 22))
rect(0, 126, W, 130, RED)
draw_text('WORLD NEWS', 48, 26, INK, 7)
draw_text('THURSDAY 19 NOVEMBER 2026', 50, 82, (150, 185, 232), 4)

# ---------------------------------------------------------------- 2x2 panels
PX0, PY0, PW, PH = 40, 150, 460, 300
GAPX, GAPY = 24, 20
arts = []


def panel_box(x, y, w, h):
    rect(x, y, x + w, y + h, PANEL)
    rect(x, y, x + w, y + 3, PANEL_EDGE)
    rect(x, y + h - 1, x + w, y + h, (32, 42, 60))
    rect(x, y, x + 3, y + h, PANEL_EDGE)


for idx, st in enumerate(STORIES):
    col, row = idx % 2, idx // 2
    x = PX0 + col * (PW + GAPX)
    y = PY0 + row * (PH + GAPY)
    panel_box(x, y, PW, PH)

    # kicker chip
    ks = 2
    kw = text_width(st['kicker'], ks) + 20
    rect(x + 18, y + 20, x + 18 + kw, y + 20 + 7 * ks + 12, st['color'])
    draw_text(st['kicker'], x + 28, y + 26, (14, 18, 28), ks)

    # headline, up to two lines
    hw = PW - 42
    hs = fit_scale(st['head'], hw, 4)
    hlines = wrap(st['head'], hw, hs)
    hy = y + 18 + 7 * ks + 26
    for ln in hlines[:2]:
        draw_text(ln, x + 20, hy, INK, hs)
        hy += 7 * hs + 8

    # revision 2: hairline rule under the headline block for cleaner separation
    rect(x + 20, hy + 2, x + PW - 24, hy + 3, (48, 62, 88))
    hy += 12

    # body copy
    bs = 2
    bh = y + 132  # keep body clear of the artwork zone
    for ln in st['body']:
        if hy + 7 * bs > bh:
            break
        draw_text(ln, x + 20, hy, INK_DIM, bs)
        hy += 7 * bs + 7

    arts.append((st['art'], x, y, PW, PH))

# ---------------------------------------------------------------- artwork per panel
# --- Gulf: stylised map of the Persian Gulf with strike vectors
ax, ay, aw, ah = arts[0][1], arts[0][2], arts[0][3], arts[0][4]
CLIP = (ax + 4, ay + 140, ax + PW - 4, ay + PH - 4)
gx0, gy0 = ax + 250, ay + 148
rect(gx0, gy0, gx0 + 180, gy0 + 140, (28, 38, 56))
# water body
for i in range(60):
    rect(gx0 + 20 + i, gy0 + 30 + i, gx0 + 26 + i, gy0 + 120 - i, WATER)
draw_text('GULF', gx0 + 34, gy0 + 66, (150, 190, 240), 2)
# Iran landmass
rect(gx0 + 118, gy0 + 18, gx0 + 176, gy0 + 128, (44, 52, 44))
draw_text('IRAN', gx0 + 122, gy0 + 60, (168, 180, 150), 2)
# targets: Kuwait airbase + Bahrain
circle(gx0 + 46, gy0 + 40, 7, ORANGE, True)
draw_text('KUWAIT AB', gx0 - 10, gy0 + 56, INK_DIM, 1)
circle(gx0 + 40, gy0 + 96, 6, ORANGE, True)
draw_text('BAHRAIN', gx0 - 6, gy0 + 110, INK_DIM, 1)
circle(gx0 + 128, gy0 + 34, 5, RED, True)  # Qeshm
draw_text('QESHM', gx0 + 136, gy0 + 28, RED, 1)
line(gx0 + 124, gy0 + 40, gx0 + 52, gy0 + 44, RED, 2)
line(gx0 + 124, gy0 + 46, gx0 + 46, gy0 + 98, RED, 2)

# --- Trio: three leaders at a table
ax, ay, aw, ah = arts[1][1], arts[1][2], arts[1][3], arts[1][4]
CLIP = (ax + 4, ay + 140, ax + PW - 4, ay + PH - 4)
cx0, cy0 = ax + 90, ay + 168
for name, dx, col in (('TRUMP', 0, YELLOW), ('PUTIN', 140, RED), ('XI', 280, BLUE)):
    x = cx0 + dx
    circle(x, cy0, 17, col, True)
    rect(x - 19, cy0 + 21, x + 19, cy0 + 74, col)
    draw_text(name, x - text_width(name, 2) // 2, cy0 + 82, INK_DIM, 2)
rect(cx0 - 60, cy0 + 118, cx0 + 320, cy0 + 132, (58, 70, 92))

# --- Bridge: span with a collapsed section over water
ax, ay, aw, ah = arts[2][1], arts[2][2], arts[2][3], arts[2][4]
CLIP = (ax + 4, ay + 140, ax + PW - 4, ay + PH - 4)
bx0, by0 = ax + 30, ay + 186
rect(bx0, by0 + 60, bx0 + 400, by0 + 110, SEA)
for i in range(0, 400, 24):
    rect(bx0 + i, by0 + 78, bx0 + i + 12, by0 + 82, (72, 104, 150))
rect(bx0, by0 + 34, bx0 + 150, by0 + 52, STEEL)      # left deck
rect(bx0 + 236, by0 + 34, bx0 + 400, by0 + 52, STEEL)  # right deck
for px_ in (bx0 + 40, bx0 + 110, bx0 + 290, bx0 + 360):
    rect(px_, by0 + 34, px_ + 16, by0 + 96, (74, 80, 94))  # pylons
# broken span
rect(bx0 + 150, by0 + 40, bx0 + 236, by0 + 50, (34, 40, 52))
rect(bx0 + 158, by0 + 52, bx0 + 196, by0 + 62, RED)
rect(bx0 + 196, by0 + 62, bx0 + 228, by0 + 70, RED)
line(bx0 + 150, by0 + 34, bx0 + 168, by0 + 100, RED, 2)
draw_text('HIT AGAIN', bx0 + 152, by0 + 112, (232, 128, 96), 2)

# --- COP31: globe with a stalled dial
ax, ay, aw, ah = arts[3][1], arts[3][2], arts[3][3], arts[3][4]
CLIP = (ax + 4, ay + 140, ax + PW - 4, ay + PH - 4)
gx_, gy_ = ax + 250, ay + 196
circle(gx_, gy_, 62, GREEN, False, 3)
circle(gx_, gy_, 40, (46, 92, 72), False, 2)
draw_text('COP31', gx_ - text_width('COP31', 2) // 2, gy_ - 7, GREEN, 2)
draw_text('ANTALYA', gx_ - text_width('ANTALYA', 1) // 2, gy_ + 22, INK_DIM, 1)
# revision 3: widen the COP31 dial spokes for balance
import math
for ang, col in ((180, ORANGE), (240, RED), (300, YELLOW)):
    r1, r2 = 62, 88
    a = math.radians(ang)
    line(gx_ + r1 * math.cos(a), gy_ + r1 * math.sin(a),
         gx_ + r2 * math.cos(a), gy_ + r2 * math.sin(a), col, 2)

# ---------------------------------------------------------------- footer strip
CLIP = None

FY0 = PY0 + 2 * PH + GAPY + 14   # first strip below the panels
rect(40, FY0, 984, FY0 + 38, PANEL)
rect(40, FY0, 984, FY0 + 3, YELLOW)
draw_text('ETHIOPIA AND ERITREA MASS FORCES ON THEIR BORDER  (REUTERS)', 56, FY0 + 12, YELLOW, 2)

FY2 = FY0 + 52
rect(40, FY2, 984, FY2 + 38, PANEL)
rect(40, FY2, 984, FY2 + 3, ORANGE)
draw_text('GTA VI LAUNCHES: 3.3M+ TWITCH VIEWERS AT PEAK', 60, FY2 + 12, ORANGE, 2)

# ---------------------------------------------------------------- colophon
CY = FY2 + 52
draw_text('SOURCES: AP  REUTERS  AFP  UN NEWS  THE GUARDIAN', 48, CY, (104, 118, 140), 2)
draw_text('ONE IMAGE SUMMARY OF THURSDAY 19 NOVEMBER 2026', 48, CY + 32, (128, 142, 164), 2)
rect(48, CY + 72, 300, CY + 75, (46, 58, 78))
draw_text('COMPILED BY AN AI AGENT FOR THE MAKE.FUN BOUNTY', 48, CY + 92, (92, 104, 124), 2)


# ---------------------------------------------------------------- PNG encode
def chunk(tag, data):
    body = tag + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)


raw = bytearray()
stride = W * 3
for y in range(H):
    raw.append(0)  # filter type 0
    raw += pix[y * stride:(y + 1) * stride]

png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
png += chunk(b'IEND', b'')

out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
if not os.path.isdir(out_dir):
    os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'entry.png'), 'wb') as fh:
    fh.write(png)

print('wrote entry.png', len(png), 'bytes')
