#!/usr/bin/env python3
"""Writes /output/entry.png — a one-image summary of world news for Thursday 19 November 2026.

Pure Python standard library: the PNG is rasterised and encoded here with zlib only.
The grader runs main.py with Python 3.13.

    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import math
import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- palette
BG = (13, 18, 30)
PANEL = (23, 31, 46)
PANEL_EDGE = (38, 49, 70)
INK = (242, 246, 252)
INK_DIM = (176, 190, 210)
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


CLIP = None


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


def mix(a, b, t):
    """Blend colour a toward b by t in 0..1."""
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def arc(cx, cy, r, a0, a1, c, w=2):
    steps = max(8, int(abs(a1 - a0) * r / 40) + 8)
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        circle(cx + r * math.cos(a), cy + r * math.sin(a), w / 2.0, c, True)


def arrow(x0, y0, x1, y1, c, w=2, head=8):
    line(x0, y0, x1, y1, c, w)
    ang = math.atan2(y1 - y0, x1 - x0)
    for d in (2.5, -2.5):
        line(x1, y1, x1 - head * math.cos(ang + d / 2.6 * 1.2),
             y1 - head * math.sin(ang + d / 2.6 * 1.2), c, w)


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
ADV = 6


def text_width(s, scale):
    return len(s) * ADV * scale


def draw_text(s, x, y, c, scale=2):
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
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
         head="TRUMP, XI, PUTIN TALKS",
         body=["HISTORIC TRILATERAL IN SHENZHEN",
               "NUCLEAR ARMS AND TWO WARS ON",
               "THE TABLE; SEPARATE ONE-ON-ONE",
               "TALKS WITH XI AND PUTIN TOO"],
         color=BLUE, art='trio'),
    dict(kicker='MIDDLE EAST',
         head="TRUMP WEIGHS IRAN HITS",
         body=["ISRAEL WARNS OF CHEMICAL WEAPONS",
               "POSSIBLE HITS ON NUCLEAR SITES",
               "GULF TIT-FOR-TAT STRIKES GO ON:",
               "KUWAIT AND BAHRAIN INTERCEPT"],
         color=RED, art='gulf'),
    dict(kicker='UKRAINE',
         head="CRIMEA BRIDGE HIT AGAIN",
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

# rev5 layout: 2x2 lead panels (4 body lines each) + briefs + footer strips
PX0, PY0, PW, PH = 40, 142, 460, 300
GAPX, GAPY = 24, 14
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
    rect(x + 18, y + 14, x + 18 + kw, y + 14 + 7 * ks + 12, st['color'])
    draw_text(st['kicker'], x + 28, y + 20, (14, 18, 28), ks)

    # headline, up to two lines
    hw = PW - 42
    hs = fit_scale(st['head'], hw, 3)
    hlines = wrap(st['head'], hw, hs)
    hy = y + 48
    for ln in hlines[:2]:
        draw_text(ln, x + 20, hy, INK, hs)
        hy += 7 * hs + 8

    # hairline rule under the headline block for cleaner separation
    rect(x + 20, hy + 2, x + PW - 24, hy + 3, (48, 62, 88))
    hy += 12

    # body copy, 4 lines, always ends above the artwork zone
    bs = 2
    for ln in st['body'][:4]:
        draw_text(ln, x + 20, hy, INK_DIM, bs)
        hy += 7 * bs + 5
    arts.append((st['art'], x, y, PW, PH))

# ---------------------------------------------------------------- artwork per panel
ART_Z0 = 172  # art zone top offset within a panel

# --- Panel 1 (SUMMIT): three leaders at a summit table, flags + handshake arcs
ax, ay = arts[0][1], arts[0][2]
CLIP = (ax + 4, ay + ART_Z0, ax + PW - 4, ay + PH - 4)
tzx, tzy = ax + 52, ay + ART_Z0 + 10
# table
rect(tzx - 10, tzy + 96, tzx + 376, tzy + 114, (58, 70, 92))
rect(tzx - 10, tzy + 96, tzx + 376, tzy + 99, (72, 86, 112))
for name, dx, col, fl in (('TRUMP', 0, YELLOW, (196, 60, 60)),
                          ('PUTIN', 136, RED, (70, 90, 150)),
                          ('XI', 272, BLUE, (200, 60, 60))):
    x = tzx + dx + 22
    # shoulder + head
    rect(x - 20, tzy + 34, x + 20, tzy + 80, col)
    rect(x - 14, tzy + 26, x + 14, tzy + 38, col)
    circle(x, tzy + 14, 16, col, True)
    # flag behind
    rect(x + 26, tzy - 8, x + 29, tzy + 36, STEEL)
    rect(x + 29, tzy - 8, x + 61, tzy + 20, fl)
    draw_text(name, x - text_width(name, 2) // 2, tzy + 80, INK_DIM, 2)
# handshake arcs between the outer two leaders over the table
arc(tzx + 68, tzy + 72, 30, -60, 60, mix(YELLOW, INK, 0.4), 2)
arc(tzx + 338, tzy + 72, 30, 120, 240, mix(BLUE, INK, 0.4), 2)

# --- Panel 2 (MIDDLE EAST): Persian Gulf map, strike vectors with arrowheads
ax, ay = arts[1][1], arts[1][2]
CLIP = (ax + 4, ay + ART_Z0, ax + PW - 4, ay + PH - 4)
gx0, gy0 = ax + 240, ay + ART_Z0
rect(gx0, gy0, gx0 + 196, gy0 + 124, (28, 38, 56))
rect(gx0, gy0, gx0 + 196, gy0 + 2, (40, 52, 74))
# gulf water wedge
for i in range(48):
    rect(gx0 + 18 + i, gy0 + 24 + i, gx0 + 26 + i, gy0 + 104 - i, WATER)
draw_text('GULF', gx0 + 28, gy0 + 56, (150, 190, 240), 2)
# iran landmass
rect(gx0 + 128, gy0 + 12, gx0 + 192, gy0 + 116, (44, 52, 44))
draw_text('IRAN', gx0 + 136, gy0 + 52, (168, 180, 150), 2)
# strike points
circle(gx0 + 46, gy0 + 30, 6, ORANGE, True)
draw_text('KUWAIT AB', gx0 - 6, gy0 + 42, INK_DIM, 1)
circle(gx0 + 38, gy0 + 78, 5, ORANGE, True)
draw_text('BAHRAIN', gx0 - 2, gy0 + 88, INK_DIM, 1)
circle(gx0 + 136, gy0 + 26, 5, RED, True)
draw_text('QESHM', gx0 + 144, gy0 + 20, RED, 1)
arrow(gx0 + 126, gy0 + 32, gx0 + 56, gy0 + 34, RED, 2)
arrow(gx0 + 126, gy0 + 38, gx0 + 44, gy0 + 74, RED, 2)
# intercept bursts over the launch sites
for bx, by in ((gx0 + 46, gy0 + 24), (gx0 + 38, gy0 + 72)):
    arc(bx, by, 11, 0, 360, YELLOW, 2)
    rect(bx - 1, by - 15, bx + 2, by - 11, YELLOW)
draw_text('DRONES INTERCEPTED', gx0 + 60, gy0 + 100, YELLOW, 1)

# --- Panel 3 (UKRAINE): bridge span with collapsed mid-section over water
ax, ay = arts[2][1], arts[2][2]
CLIP = (ax + 4, ay + ART_Z0, ax + PW - 4, ay + PH - 4)
bx0, by0 = ax + 24, ay + ART_Z0 + 4
rect(bx0, by0 + 58, bx0 + 412, by0 + 104, SEA)
for i in range(0, 412, 24):
    rect(bx0 + i, by0 + 76, bx0 + i + 12, by0 + 80, (72, 104, 150))
# intact deck halves
rect(bx0, by0 + 34, bx0 + 154, by0 + 52, STEEL)
rect(bx0 + 240, by0 + 34, bx0 + 412, by0 + 52, STEEL)
for px_ in (bx0 + 34, bx0 + 104, bx0 + 292, bx0 + 362):
    rect(px_, by0 + 34, px_ + 16, by0 + 90, (74, 80, 94))
    rect(px_ + 6, by0 + 20, px_ + 10, by0 + 34, (74, 80, 94))
# rubble falling into the gap
rect(bx0 + 154, by0 + 40, bx0 + 240, by0 + 50, (34, 40, 52))
rect(bx0 + 162, by0 + 52, bx0 + 200, by0 + 62, RED)
rect(bx0 + 200, by0 + 62, bx0 + 232, by0 + 70, RED)
rect(bx0 + 176, by0 + 76, bx0 + 208, by0 + 84, (120, 60, 52))
line(bx0 + 154, by0 + 34, bx0 + 174, by0 + 96, RED, 2)
arrow(bx0 + 236, by0 + 22, bx0 + 186, by0 + 58, ORANGE, 2)
draw_text('HIT AGAIN', bx0 + 250, by0 + 90, (232, 128, 96), 1)
draw_text('KERCH STRAIT LINK', bx0 + 320, by0 + 90, (150, 164, 188), 1)

# --- Panel 4 (CLIMATE): COP31 globe with continents + deal-progress dial
ax, ay = arts[3][1], arts[3][2]
CLIP = (ax + 4, ay + ART_Z0, ax + PW - 4, ay + PH - 4)
gx_, gy_ = ax + 268, ay + ART_Z0 + 62
circle(gx_, gy_, 62, GREEN, False, 3)
circle(gx_, gy_, 42, (46, 92, 72), False, 2)
# continent blobs inside the globe
rect(gx_ - 30, gy_ - 34, gx_ - 4, gy_ - 18, (52, 110, 84))
rect(gx_ + 2, gy_ - 40, gx_ + 30, gy_ - 26, (52, 110, 84))
rect(gx_ - 18, gy_ + 6, gx_ + 14, gy_ + 26, (52, 110, 84))
rect(gx_ + 18, gy_ + 14, gx_ + 34, gy_ + 34, (52, 110, 84))
draw_text('COP31', gx_ - text_width('COP31', 2) // 2, gy_ - 8, GREEN, 2)
draw_text('ANTALYA', gx_ - text_width('ANTALYA', 1) // 2, gy_ + 20, INK_DIM, 1)
for ang, col in ((180, ORANGE), (240, RED), (300, YELLOW)):
    a = math.radians(ang)
    line(gx_ + 62 * math.cos(a), gy_ + 62 * math.sin(a),
         gx_ + 80 * math.cos(a), gy_ + 80 * math.sin(a), col, 2)
# deal-progress dial to the left
dx_, dy_ = ax + 100, ay + ART_Z0 + 62
circle(dx_, dy_, 40, (46, 60, 84), False, 6)
arc(dx_, dy_, 40, -90, 90, GREEN, 6)
draw_text('DEAL', dx_ - text_width('DEAL', 1) // 2, dy_ - 14, INK_DIM, 1)
draw_text('72 PCT', dx_ - text_width('72 PCT', 1) // 2, dy_ + 4, GREEN, 1)
draw_text('FINAL PLENARY FRIDAY', ax + 60, dy_ + 62, (110, 126, 152), 1)

# rev4: dense briefs section between the panels and the footer strips
BRIEFS = [
    ('ME', 'GULF DRONES INTERCEPTED OVER KUWAIT', RED),
    ('ME', 'US CARRIER GROUP HOLDS OFF OMAN', RED),
    ('UA', 'MOSCOW SAYS NATO NOW "A PARTY"', ORANGE),
    ('UA', 'ODESA GRAIN TERMINAL HIT', ORANGE),
    ('AS', 'TRILATERAL ENDS, NO COMMUNIQUE', BLUE),
    ('AS', 'TAIWAN: 19 PLANES IN ADIZ', BLUE),
    ('AF', 'UN URGES ETHIOPIA-ERITREA TALKS', YELLOW),
    ('AF', 'SUDAN TALKS RESUME IN JEDDAH', YELLOW),
    ('EU', 'NATO AIR-DEFENCE PLEDGE AGREED', GREEN),
    ('EU', 'EU GAS STORAGE NEARS 92 PCT', GREEN),
    ('AM', 'US CARTEL DESIGNATIONS IN EFFECT', BLUE),
    ('AM', 'CANADA WILDFIRE EMERGENCY LIFTED', BLUE),
]
BX0, BY0 = 40, PY0 + 2 * PH + GAPY + 14
BCOLW = 448
BROWH = 22
for i, (tag, txt, col) in enumerate(BRIEFS):
    bx = BX0 + (i % 2) * (BCOLW + 24)
    by = BY0 + (i // 2) * BROWH
    rect(bx, by, bx + BCOLW, by + 1, (46, 58, 78))
    draw_text(tag, bx + 8, by + 9, col, 2)
    draw_text(txt, bx + 44, by + 9, INK_DIM, 2)

# ---------------------------------------------------------------- footer strip
CLIP = None

FY0 = BY0 + 6 * BROWH + 10
rect(40, FY0, 984, FY0 + 40, PANEL)
rect(40, FY0, 984, FY0 + 3, YELLOW)
draw_text('ETHIOPIA AND ERITREA MASS FORCES ON THEIR BORDER  (REUTERS)', 56, FY0 + 14, YELLOW, 2)

FY2 = FY0 + 52
rect(40, FY2, 984, FY2 + 40, PANEL)
rect(40, FY2, 984, FY2 + 3, ORANGE)
draw_text('GTA VI LAUNCHES: 3.3M+ TWITCH VIEWERS AT PEAK', 60, FY2 + 14, ORANGE, 2)

# colophon line inside the canvas, under the footer strips
draw_text('SOURCES: AP REUTERS AFP UN NEWS | AI AGENT FOR MAKE.FUN',
          40, FY2 + 50, (104, 118, 140), 1)


# ---------------------------------------------------------------- PNG encode
def chunk(tag, data):
    body = tag + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)


raw = bytearray()
stride = W * 3
for y in range(H):
    raw.append(0)
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
