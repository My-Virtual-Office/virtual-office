"""Compose screenshots/ into one image per slide  (python3 build-shots.py).

Run this after adding or replacing anything in screenshots/, then re-run
build-deck.py. shots/*.png are generated and gitignored — this file is the
source of truth for how they are made.

Turn the raw captures into one image per slide.

Layout is a justified row: every image in a row gets the SAME height, and width
proportional to its aspect ratio. A 16:9 app screenshot next to a 9:16 phone
therefore reads at the same scale instead of the phone bullying the screenshot.

The canvas height falls out of the layout, and we write the resulting ratio to
shot-ratios.json so the deck's figure slot matches exactly — object-fit: cover
then has nothing left to crop.
"""
import json, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
SRC, OUT = ROOT / "screenshots", ROOT / "shots"
OUT.mkdir(exist_ok=True)

BG, RULE, MUTED = (248, 248, 248), (224, 224, 224), (74, 73, 74)
PAD, LAB = 16, 48
CAP_PX = 28          # ~14px once the composite is scaled into the slide's column

def font(sz, bold=True):
    # Captions sit under a screenshot on a projector — thin grey at 14px reads as
    # a smudge from the back row. Bold, and darker than the usual muted.
    for c in (("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else
              ("/usr/share/fonts/TTF/DejaVuSans.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if pathlib.Path(c).exists():
            return ImageFont.truetype(c, sz)
    return ImageFont.load_default()

def load(rel):
    return Image.open(SRC / rel).convert("RGB")

ratios = {}

def _lay(specs, W, cap_h=None):
    """Justify one row to width W: shared height, widths ∝ aspect ratio."""
    h = int((W - PAD * (len(specs) + 1)) / sum(im.width / im.height for im, _ in specs))
    if cap_h:
        h = min(h, cap_h)
    ims = [(im.resize((max(1, int(h * im.width / im.height)), h), Image.LANCZOS), l)
           for im, l in specs]
    return ims, h, (LAB if any(l for _, l in specs) else 0)

def _paint(c, ims, y, W):
    d, f = ImageDraw.Draw(c), font(CAP_PX)
    total = sum(i.width for i, _ in ims) + PAD * (len(ims) - 1)
    x = (W - total) // 2
    for im, l in ims:
        d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=RULE, width=1)
        c.paste(im, (x, y))
        if l:
            d.text((x + 1, y + im.height + 10), l, font=f, fill=MUTED)
        x += im.width + PAD

def _save(c, n):
    c.save(OUT / f"slide-{n:02d}.png", optimize=True)
    ratios[str(n)] = f"{c.width}/{c.height}"
    print(f"  slide-{n:02d}.png  {c.width}x{c.height}   ar={c.width / c.height:.2f}")

def row(n, specs, W=1600, cap_h=None):
    """One justified row."""
    ims, h, lab = _lay(specs, W, cap_h)
    total = sum(i.width for i, _ in ims) + PAD * (len(ims) - 1)
    W = min(W, total + PAD * 2)          # no dead space: the slot's ratio is the row's ratio
    c = Image.new("RGB", (W, h + PAD * 2 + lab), BG)
    _paint(c, ims, PAD, W)
    _save(c, n)

def stack(n, rows, W=1600):
    """Several justified rows, one above the other.

    Each row is justified to the SAME width, so a hero row of one or two large
    captures sits over a row of smaller ones without either being cropped. Five
    captures in a single row would shrink them all past reading distance.
    """
    laid = [_lay(specs, W) for specs in rows]
    H = PAD + sum(h + lab + PAD for _, h, lab in laid)
    c = Image.new("RGB", (W, H), BG)
    y = PAD
    for ims, h, lab in laid:
        _paint(c, ims, y, W)
        y += h + lab + PAD
    _save(c, n)

# ── 6 · chat, threads, voice — the parity slide ─────────────────────────────
row(6, [(load("website/chat.png"), "Channel + messages"),
        (load("website/thread.png"), "Thread"),
        (load("website/voice-channel.png"), "Voice rooms")])

# ── 8 · the personal desk ───────────────────────────────────────────────────
row(8, [(load("website/my-desk.png"), None)], W=1500)

# ── 9 · human presence: the floor, who's on it, and the rooms you walk into ─
# Top row carries the argument (a floor with real people at real desks, and the
# presence list). Bottom row answers "and then what?" — the places you can walk
# into. Five in one row would make every one of them unreadable.
stack(9, [[(load("website/2d-plane-office-room.png"), "The floor — real people at real desks"),
           (load("website/2d-plane-how-are-online.png"), "Who's online")],
          [(load("website/2d-plane-meeting-room.png"), "Meeting room"),
           (load("website/2d-plane-ceo-room.png"), "CEO room"),
           (load("website/2d-plane-chill-zone.png"), "Chill zone")]])

# ── 10 · requirements -> interface: the actual design file ──────────────────
row(10, [(load("website/figma.png"), None)], W=1500)

# ── 20 · mobile: auth (login · register · OTP reset) ────────────────────────
row(20, [(load("mobile/mobile-login.jpeg"), "Login"),
         (load("mobile/mobile-create-account.jpeg"), "Create account"),
         (load("mobile/mobile-forget-password.jpeg"), "Forgot password — OTP")])

# ── 22 · mobile: real-time chat ─────────────────────────────────────────────
row(22, [(load("mobile/mobile-channels.jpeg"), "Channels"),
         (load("mobile/mobile-direct-message.jpeg"), "Direct message — live"),
         (load("mobile/mobile-create-room.jpeg"), "Create room")])

# ── 23 · mobile: the workspace itself (new slide) ───────────────────────────
row(23, [(load("mobile/mobile-workspace.jpeg"), "Workspace"),
         (load("mobile/mobile-create-channel.jpeg"), "Create channel"),
         (load("mobile/mobile-room.jpeg"), "Rooms — join from your pocket")])

(ROOT / "shot-ratios.json").write_text(json.dumps(ratios, indent=1))
print("wrote shot-ratios.json")
