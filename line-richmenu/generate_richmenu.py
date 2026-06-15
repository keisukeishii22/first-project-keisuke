#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不動産 売買・賃貸 LINE公式アカウント用 リッチメニュー画像ジェネレーター
出力: 2500 x 1686 px (LINEリッチメニュー 大サイズ規格) PNG
左:売買相談 / 右:賃貸相談 の2分割レイアウト
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 2500, 1686
HALF = W // 2

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

def font(size):
    return ImageFont.truetype(FONT_PATH, size)

def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def vgradient(draw, x0, y0, x1, y1, top, bottom):
    """縦方向グラデーションを矩形 [x0,x1) x [y0,y1) に描画"""
    h = y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / max(1, h - 1)
        draw.line([(x0, y), (x1 - 1, y)], fill=lerp(top, bottom, t))

def center_text(draw, cx, y, text, fnt, fill, stroke_width=0, stroke_fill=None, spacing=0):
    """中央寄せでテキスト描画。spacingで字間を広げる(主にタイトル用)"""
    if spacing == 0:
        bbox = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke_width)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2 - bbox[0], y), text, font=fnt, fill=fill,
                  stroke_width=stroke_width, stroke_fill=stroke_fill)
        return
    # 字間あり
    widths = []
    for ch in text:
        b = draw.textbbox((0, 0), ch, font=fnt, stroke_width=stroke_width)
        widths.append(b[2] - b[0])
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        b = draw.textbbox((0, 0), ch, font=fnt, stroke_width=stroke_width)
        draw.text((x - b[0], y), ch, font=fnt, fill=fill,
                  stroke_width=stroke_width, stroke_fill=stroke_fill)
        x += wch + spacing

# ---- ベース画像 ----
img = Image.new("RGB", (W, H), (255, 255, 255))
draw = ImageDraw.Draw(img)

# 左:売買 ネイビー / 右:賃貸 エメラルド
NAVY_TOP, NAVY_BOT = (38, 64, 102), (12, 24, 44)
TEAL_TOP, TEAL_BOT = (20, 150, 132), (7, 74, 66)
GOLD = (210, 178, 110)   # 上品なゴールドアクセント
WHITE = (255, 255, 255)
SOFT = (236, 240, 245)

vgradient(draw, 0, 0, HALF, H, NAVY_TOP, NAVY_BOT)
vgradient(draw, HALF, 0, W, H, TEAL_TOP, TEAL_BOT)

# ---- 半透明の円形バッジ(アイコン背景) ----
def badge(cx, cy, r):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 26))
    od.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 90), width=6)
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))

ICON_CY = 560
BADGE_R = 250
badge(625, ICON_CY, BADGE_R)
badge(1875, ICON_CY, BADGE_R)
draw = ImageDraw.Draw(img)

LW = 16  # アイコン線幅

# ---- 左:家アイコン(売買) ----
def house(cx, cy):
    s = 300
    bw = s * 0.72          # 本体幅
    bh = s * 0.52          # 本体高さ
    roof_h = s * 0.40
    left = cx - bw / 2
    right = cx + bw / 2
    body_top = cy - bh / 2 + roof_h * 0.25
    body_bot = body_top + bh
    apex = (cx, body_top - roof_h)
    # 屋根
    eave = bw * 0.16
    draw.line([(left - eave, body_top), apex], fill=WHITE, width=LW, joint="curve")
    draw.line([apex, (right + eave, body_top)], fill=WHITE, width=LW, joint="curve")
    # 本体
    draw.line([(left, body_top), (left, body_bot)], fill=WHITE, width=LW)
    draw.line([(right, body_top), (right, body_bot)], fill=WHITE, width=LW)
    draw.line([(left, body_bot), (right, body_bot)], fill=WHITE, width=LW)
    # ドア
    dw, dh = bw * 0.24, bh * 0.55
    dl = cx - dw / 2
    draw.line([(dl, body_bot), (dl, body_bot - dh)], fill=WHITE, width=LW)
    draw.line([(dl + dw, body_bot), (dl + dw, body_bot - dh)], fill=WHITE, width=LW)
    draw.line([(dl, body_bot - dh), (dl + dw, body_bot - dh)], fill=WHITE, width=LW)
    # 窓
    win = bw * 0.16
    wx = cx + bw * 0.18
    wy = body_top + bh * 0.30
    draw.rectangle([wx, wy, wx + win, wy + win], outline=WHITE, width=int(LW * 0.7))

house(625, ICON_CY + 20)

# ---- 右:鍵アイコン(賃貸) ----
def key(cx, cy):
    # 斜め配置のシンプルな鍵
    ring_r = 100
    ring_cx, ring_cy = cx - 100, cy - 100
    draw.ellipse([ring_cx - ring_r, ring_cy - ring_r, ring_cx + ring_r, ring_cy + ring_r],
                 outline=WHITE, width=LW)
    # 持ち手の穴(鍵だと分かるように)
    hr = 34
    draw.ellipse([ring_cx - hr, ring_cy - hr, ring_cx + hr, ring_cy + hr],
                 outline=WHITE, width=int(LW * 0.7))
    # シャフト(軸)
    import math
    ang = math.radians(45)
    dx, dy = math.cos(ang), math.sin(ang)
    sx = ring_cx + dx * ring_r
    sy = ring_cy + dy * ring_r
    ex = sx + dx * 250
    ey = sy + dy * 250
    draw.line([(sx, sy), (ex, ey)], fill=WHITE, width=LW)
    # 歯(2本) 軸の片側に出す
    px, py = -dy, dx  # 垂直方向
    for off in (130, 195):
        bx = ring_cx + dx * (ring_r + off)
        by = ring_cy + dy * (ring_r + off)
        draw.line([(bx, by), (bx + px * 75, by + py * 75)], fill=WHITE, width=LW)

key(1875, ICON_CY + 20)

# ---- テキスト ----
title_f = font(168)
en_f = font(60)
hint_f = font(58)

TITLE_Y = 980
# ゴールドのアクセント短線(タイトル上)
def accent(cx):
    draw.line([(cx - 70, TITLE_Y - 56), (cx + 70, TITLE_Y - 56)], fill=GOLD, width=8)

accent(625)
accent(1875)

center_text(draw, 625, TITLE_Y, "売買相談", title_f, WHITE, spacing=12)
center_text(draw, 1875, TITLE_Y, "賃貸相談", title_f, WHITE, spacing=12)

center_text(draw, 625, TITLE_Y + 230, "B U Y  &  S E L L", en_f, SOFT)
center_text(draw, 1875, TITLE_Y + 230, "R E N T", en_f, SOFT)

# ---- 下部タップ誘導 ----
PILL_Y = 1430
def pill(cx, label):
    pw, ph = 470, 96
    x0, y0 = cx - pw / 2, PILL_Y
    x1, y1 = cx + pw / 2, PILL_Y + ph
    draw.rounded_rectangle([x0, y0, x1, y1], radius=ph / 2,
                           fill=None, outline=GOLD, width=5)
    center_text(draw, cx, PILL_Y + 18, label, hint_f, WHITE)

pill(625, "タップして相談する")
pill(1875, "タップして相談する")

# ---- 中央の仕切り線 ----
draw.line([(HALF, 110), (HALF, H - 110)], fill=(255, 255, 255), width=4)

img.save("/home/user/first-project-keisuke/line-richmenu/richmenu_2500x1686.png", "PNG")
print("saved richmenu_2500x1686.png")
