#!/usr/bin/env python3
"""news-image-01 entry: sums up the world news of Friday 13 November 2026 in one image.

A pure standard-library Python 3 program. It draws a newspaper-style poster
(a masthead, six story panels with captions and a footer ticker) with its own
raster code and a hand-rolled PNG encoder, then writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png). No network, no
third-party packages, fully deterministic: every run writes identical bytes.

The stories, all reported on Friday 13 November 2026:
  1. Ukraine fired about 1,200 drones at Russia overnight, one of its largest
     attacks of the war, as US-led peace talks widened (AP).
  2. The US military downed two Iranian attack drones headed for Bahrain
     (AP).
  3. A global Microsoft 365 outage (Outlook, Teams, Copilot) entered its
     second day (AP).
  4. Nvidia chief executive Jensen Huang resigned; Nvidia shares plunged and
     Wall Street slipped (multiple wire reports).
  5. The FAA halted US departures nationwide for over four hours over a
     communications failure, lifting the ground stop Friday evening.
  6. COP31 in Antalya, Turkiye: the UN chief urged drastic emissions cuts as
     climate finance pledges fell sharply (Reuters / Carbon Brief).
Ticker: China's large Pacific drills near Taiwan (Reuters); Mekelle falls in
Ethiopia (BBC); Trump threatened to double tariffs on Mexico (Reuters).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# --------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 pixels, '#' = ink.
# --------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# --------------------------------------------------------------------------
# Canvas: an RGB bytearray with small raster primitives.
# --------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(color) * (w * h))

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        n = len(row)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + n] = row

    def disc(self, cx, cy, r, color):
        # Filled circle, one horizontal span per row.
        c = bytes(color)
        r2 = r * r
        for dy in range(-r, r + 1):
            yy = cy + dy
            if yy < 0 or yy >= self.h:
                continue
            half = int((r2 - dy * dy) ** 0.5)
            x0, x1 = max(0, cx - half), min(self.w - 1, cx + half)
            if x1 < x0:
                continue
            off = (yy * self.w + x0) * 3
            self.px[off:off + (x1 - x0 + 1) * 3] = c * (x1 - x0 + 1)

    def line(self, x0, y0, x1, y1, color, thick=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, thick // 2)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.disc(x, y, r, color)

    def poly(self, pts, color):
        # Scanline polygon fill.
        ys = [p[1] for p in pts]
        n = len(pts)
        for yy in range(min(ys), max(ys) + 1):
            if yy < 0 or yy >= self.h:
                continue
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(xa + (yy - ya) * (xb - xa) // (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, color)

    def text(self, x, y, s, scale, color):
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                line = glyph[row]
                for col in range(5):
                    if line[col] == "#":
                        self.fill_rect(x + col * scale, y + row * scale,
                                       scale, scale, color)
            x += 6 * scale

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)


# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------
WHITE = (255, 255, 255)
INK = (16, 19, 26)
NAVY = (13, 33, 55)
RED = (217, 35, 35)
LIGHT = (210, 220, 232)


# --------------------------------------------------------------------------
# Scenes. Each draws inside (x, y, w, h) - the panel's picture area.
# --------------------------------------------------------------------------
def drone(c, cx, cy, s, color):
    """A quadcopter silhouette: body, X arms, four rotor discs."""
    c.fill_rect(cx - s // 2, cy - s // 6, s, s // 3, color)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ex, ey = cx + dx * s, cy + dy * (s // 2)
        c.line(cx, cy, ex, ey, color, max(2, s // 6))
        c.disc(ex, ey, s // 3, color)


def scene_ukraine(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (22, 34, 66))                    # night sky
    for i in range(46):                                      # stars
        sx = x + (i * 67 + 23) % w
        sy = y + (i * 41 + 11) % (h // 2)
        c.fill_rect(sx, sy, 2, 2, (200, 210, 235))
    c.disc(x + w - 62, y + 36, 20, (233, 230, 200))          # moon
    c.disc(x + w - 70, y + 30, 17, (22, 34, 66))
    drone(c, x + 92, y + 52, 22, (8, 10, 16))                # drones inbound
    drone(c, x + 205, y + 84, 27, (8, 10, 16))
    drone(c, x + 330, y + 44, 19, (8, 10, 16))
    drone(c, x + 415, y + 96, 24, (8, 10, 16))
    glow = (255, 140, 40)                                    # strike glow
    c.disc(x + 120, y + h - 58, 30, glow)
    c.disc(x + 120, y + h - 58, 17, (255, 200, 90))
    base = y + h
    bx = x                                         # skyline silhouette
    heights = [52, 84, 40, 66, 96, 58, 74, 44, 88, 50, 70, 38, 62]
    i = 0
    while bx < x + w:
        bw = 26 + (i * 13) % 20
        bh = heights[i % len(heights)]
        c.fill_rect(bx, base - bh, bw, bh, (5, 6, 10))
        for wy in range(base - bh + 8, base - 8, 14):        # lit windows
            for wx in range(bx + 5, bx + bw - 5, 11):
                if (wx * 7 + wy * 13) % 5 < 2:
                    c.fill_rect(wx, wy, 3, 4, (255, 205, 92))
        bx += bw + 3
        i += 1


def scene_bahrain(c, x, y, w, h):
    c.fill_rect(x, y, w, h // 2 + 22, (250, 196, 120))       # dusk sky
    c.fill_rect(x, y + h // 2 + 22, w, h - h // 2 - 22, (24, 96, 128))  # sea
    c.disc(x + 66, y + 44, 22, (255, 226, 150))              # low sun
    hull = (38, 42, 50)
    deck = y + h // 2 + 6
    c.poly([(x + 60, deck), (x + 430, deck), (x + 402, deck + 34),
            (x + 92, deck + 34)], hull)                      # tanker hull
    c.fill_rect(x + 96, deck - 16, 210, 16, (176, 60, 48))   # container stacks
    c.fill_rect(x + 120, deck - 30, 90, 14, (60, 110, 170))
    c.fill_rect(x + 224, deck - 30, 70, 14, (70, 150, 90))
    c.fill_rect(x + 356, deck - 38, 34, 38, (232, 232, 226))  # bridge tower
    c.fill_rect(x + 360, deck - 34, 26, 8, (30, 60, 90))
    c.line(x + 330, deck, x + 330, deck - 26, hull, 4)       # mast
    drone(c, x + 150, y + 40, 20, (30, 30, 34))
    drone(c, x + 300, y + 26, 16, (30, 30, 34))
    bx, by = x + 392, y + 40                           # one drone bursts
    for dx, dy in ((0, -13), (9, -9), (13, 0), (9, 9), (0, 13),
                   (-9, 9), (-13, 0), (-9, -9)):
        c.line(bx, by, bx + dx, by + dy, (255, 120, 30), 4)
    c.disc(bx, by, 7, (255, 214, 90))
    for dx, dy in ((6, 18), (15, 28), (-3, 26), (10, 40)):   # falling debris
        c.fill_rect(bx + dx, by + dy, 4, 4, (30, 30, 34))


def scene_microsoft(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (30, 34, 44))
    lx, ly, lw, lh = x + 95, y + 26, 300, 150          # laptop
    c.fill_rect(lx, ly, lw, lh, (150, 158, 170))
    c.fill_rect(lx + 8, ly + 8, lw - 16, lh - 16, (13, 42, 84))  # screen
    c.text(lx + 22, ly + 20, "365", 5, WHITE)
    for dx, dy, r in ((168, 46, 15), (196, 38, 19), (226, 48, 14),
                      (196, 56, 17)):
        c.disc(lx + dx, ly + dy, r, (200, 208, 220))          # cloud
    c.poly([(lx + 196, ly + 58), (lx + 172, ly + 94), (lx + 190, ly + 94),
            (lx + 176, ly + 124), (lx + 208, ly + 86), (lx + 190, ly + 86)],
           RED)                                               # bolt
    c.poly([(lx + 218, ly + 96), (lx + 248, ly + 140), (lx + 188, ly + 140)],
           (245, 180, 40))                                    # warning sign
    c.text(lx + 239, ly + 108, "!", 3, INK)
    c.fill_rect(lx - 14, ly + lh, lw + 28, 10, (110, 118, 130))  # base


def scene_nvidia(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (14, 18, 10))
    for gx in range(x + 30, x + w, 46):                      # faint grid
        c.fill_rect(gx, y + 8, 1, h - 16, (34, 44, 28))
    for gy in range(y + 20, y + h - 10, 34):
        c.fill_rect(x + 10, gy, w - 20, 1, (34, 44, 28))
    pts = [(x + 26, y + 34), (x + 120, y + 58), (x + 205, y + 44),
           (x + 300, y + 96), (x + 385, y + 82), (x + 462, y + 150)]
    for i in range(len(pts) - 1):                            # plunging chart
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 7)
    c.poly([(x + 462, y + 168), (x + 440, y + 138), (x + 474, y + 132)], RED)
    chip = (118, 185, 0)
    cx0, cy0, cs = x + 52, y + 96, 96                        # the chip
    for i in range(6):                                       # pins
        px = cx0 + 8 + i * 15
        c.fill_rect(px, cy0 - 10, 6, 10, (170, 178, 186))
        c.fill_rect(px, cy0 + cs, 6, 10, (170, 178, 186))
        c.fill_rect(cx0 - 10, cy0 + 8 + i * 15, 10, 6, (170, 178, 186))
        c.fill_rect(cx0 + cs, cy0 + 8 + i * 15, 10, 6, (170, 178, 186))
    c.fill_rect(cx0, cy0, cs, cs, chip)
    c.fill_rect(cx0 + 16, cy0 + 16, cs - 32, cs - 32, (86, 138, 0))
    c.text(cx0 + 26, cy0 + 40, "AI", 3, WHITE)


def scene_faa(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (150, 205, 245))
    for cx, cy, r in ((90, 40, 16), (120, 34, 20), (152, 42, 15),
                      (360, 30, 14), (388, 26, 17)):
        c.disc(x + cx, y + cy, r, WHITE)                     # clouds
    c.fill_rect(x, y + h - 26, w, 26, (110, 150, 96))        # ground
    plane = (20, 44, 84)
    c.poly([(x + 70, y + 96), (x + 300, y + 82), (x + 344, y + 92),
            (x + 300, y + 106), (x + 84, y + 112)], plane)   # fuselage
    c.poly([(x + 170, y + 88), (x + 226, y + 44), (x + 252, y + 46),
            (x + 208, y + 90)], plane)                       # wing
    c.poly([(x + 74, y + 98), (x + 46, y + 66), (x + 66, y + 64),
            (x + 96, y + 92)], plane)                        # tail fin
    for i in range(7):                                       # windows
        c.disc(x + 120 + i * 28, y + 93, 4, (190, 226, 250))
    tx = x + w - 74                                          # control tower
    c.poly([(tx, y + h - 26), (tx + 14, y + 66), (tx + 34, y + 66),
            (tx + 48, y + h - 26)], (96, 104, 116))
    c.fill_rect(tx - 6, y + 44, 60, 24, (52, 66, 84))
    c.fill_rect(tx - 6, y + 44, 60, 8, (170, 216, 240))
    c.fill_rect(tx + 18, y + 30, 12, 14, (52, 66, 84))
    ox, oy = x + 56, y + h - 78                              # stop sign
    oct_pts = [(ox + 16, oy), (ox + 38, oy), (ox + 54, oy + 16),
               (ox + 54, oy + 38), (ox + 38, oy + 54), (ox + 16, oy + 54),
               (ox, oy + 38), (ox, oy + 16)]
    c.poly(oct_pts, WHITE)
    shrunk = [(ox + 27 + (px - ox - 27) * 7 // 9,
               oy + 27 + (py - oy - 27) * 7 // 9) for px, py in oct_pts]
    c.poly(shrunk, RED)


def scene_cop31(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (250, 176, 88))                  # hot sky
    c.disc(x + 52, y + 40, 22, (255, 232, 140))              # sun
    for dx, dy in ((0, -34), (24, -24), (34, 0), (24, 24), (0, 34),
                   (-24, 24), (-34, 0), (-24, -24)):
        c.line(x + 52, y + 40, x + 52 + dx, y + 40 + dy, (255, 200, 80), 4)
    gx, gy, gr = x + 168, y + h // 2 + 16, 82                # globe
    c.disc(gx, gy, gr, (42, 110, 180))
    land = (74, 168, 92)
    for cx, cy, r in ((-38, -30, 26), (-8, -44, 20), (30, -18, 24),
                      (-24, 12, 22), (16, 26, 26), (48, 34, 15),
                      (-52, 28, 13)):
        c.disc(gx + cx, gy + cy, r, land)
    c.fill_rect(x, y + h - 20, w, 20, (30, 90, 140))         # sea strip
    tx = x + w - 92                                          # thermometer
    c.fill_rect(tx, y + 26, 16, 118, WHITE)
    c.fill_rect(tx + 3, y + 62, 10, 82, RED)
    c.disc(tx + 8, y + 158, 17, WHITE)
    c.disc(tx + 8, y + 158, 12, RED)
    for i in range(5):
        c.fill_rect(tx + 20, y + 36 + i * 24, 12, 3, WHITE)


# --------------------------------------------------------------------------
# Poster layout
# --------------------------------------------------------------------------
PANELS = [
    (scene_ukraine, (92, 140, 220),
     "UKRAINE: 1,200 DRONES", "AT RUSSIA; TALKS WIDEN"),
    (scene_bahrain, (240, 140, 40),
     "U.S. DOWNS IRAN DRONES", "HEADED FOR BAHRAIN"),
    (scene_microsoft, (90, 160, 230),
     "MICROSOFT 365 OUTAGE", "ENTERS SECOND DAY"),
    (scene_nvidia, (140, 200, 60),
     "NVIDIA CEO RESIGNS", "SHARES PLUNGE 14%"),
    (scene_faa, (80, 190, 120),
     "FAA GROUND STOP", "HALTS U.S. FLIGHTS HOURS"),
    (scene_cop31, (255, 170, 60),
     "COP31 CLIMATE SUMMIT", "FINANCE FIGHT, ANTALYA"),
]


def build_poster():
    c = Canvas(W, H, INK)
    # Masthead
    c.fill_rect(0, 0, W, 104, NAVY)
    c.text_centered(W // 2, 16, "FRIDAY 13 NOVEMBER 2026", 5, WHITE)
    c.text_centered(W // 2, 64, "THE DAY'S WORLD NEWS AT A GLANCE", 2, LIGHT)
    c.fill_rect(0, 98, W, 6, RED)
    # Panels: 2 columns x 3 rows
    pw, ph, gap, mx, top = 490, 276, 12, 16, 116
    cap_h = 64
    for idx, (scene, accent, line1, line2) in enumerate(PANELS):
        px = mx + (idx % 2) * (pw + gap)
        py = top + (idx // 2) * (ph + gap)
        scene(c, px, py, pw, ph - cap_h)
        c.fill_rect(px, py + ph - cap_h, pw, cap_h, INK)     # caption bar
        c.fill_rect(px, py + ph - cap_h, 7, cap_h, accent)
        c.text(px + 20, py + ph - cap_h + 8, line1, 3, WHITE)
        c.text(px + 20, py + ph - cap_h + 36, line2, 3, LIGHT)
        c.fill_rect(px, py, pw, 2, INK)                      # frame
        c.fill_rect(px, py + ph - 2, pw, 2, INK)
        c.fill_rect(px, py, 2, ph, INK)
        c.fill_rect(px + pw - 2, py, 2, ph, INK)
    # Footer ticker: more of the day's news in one line
    c.fill_rect(0, 976, W, 3, RED)
    c.text_centered(W // 2, 988,
                    "ALSO: CHINA DRILLS NEAR TAIWAN | MEKELLE FALLS | "
                    "US TARIFF THREAT ON MEXICO", 2, LIGHT)
    return c


# --------------------------------------------------------------------------
# PNG encoder (filter 0 rows, zlib). Deterministic bytes.
# --------------------------------------------------------------------------
def png_bytes(c):
    raw = bytearray()
    stride = c.w * 3
    for yy in range(c.h):
        raw.append(0)
        raw += c.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build_poster())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
