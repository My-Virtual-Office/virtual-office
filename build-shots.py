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

BG, RULE, MUTED = (248, 248, 248), (224, 224, 224), (110, 109, 110)
PAD, LAB = 16, 30

def font(sz):
    for c in ("/usr/share/fonts/TTF/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if pathlib.Path(c).exists():
            return ImageFont.truetype(c, sz)
    return ImageFont.load_default()

def load(rel):
    return Image.open(SRC / rel).convert("RGB")

ratios = {}

def row(n, specs, W=1600, cap_h=None):
    """specs: [(image, label)]. Same height for all; width ∝ aspect ratio."""
    labelled = any(l for _, l in specs)
    lab = LAB if labelled else 0
    avail = W - PAD * (len(specs) + 1)
    h = int(avail / sum(im.width / im.height for im, _ in specs))
    if cap_h:
        h = min(h, cap_h)
    ims = [(im.resize((max(1, int(h * im.width / im.height)), h), Image.LANCZOS), l)
           for im, l in specs]
    total = sum(i.width for i, _ in ims) + PAD * (len(ims) - 1)
    W = min(W, total + PAD * 2)          # no dead space: the slot's ratio is the row's ratio
    H = h + PAD * 2 + lab
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    f = font(16)
    x = (W - total) // 2
    for im, l in ims:
        d.rectangle([x - 1, PAD - 1, x + im.width, PAD + im.height], outline=RULE, width=1)
        c.paste(im, (x, PAD))
        if l:
            d.text((x + 1, PAD + im.height + 7), l, font=f, fill=MUTED)
        x += im.width + PAD
    c.save(OUT / f"slide-{n:02d}.png", optimize=True)
    ratios[str(n)] = f"{W}/{H}"
    print(f"  slide-{n:02d}.png  {W}x{H}   ar={W/H:.2f}")

# ── 6 · chat, threads, voice — the parity slide ─────────────────────────────
row(6, [(load("website/chat.png"), "Channel + messages"),
        (load("website/thread.png"), "Thread"),
        (load("website/voice-channel.png"), "Voice rooms")])

# ── 8 · the personal desk ───────────────────────────────────────────────────
row(8, [(load("website/my-desk.png"), None)], W=1500)

# ── 9 · human presence: the floor, and who's on it ──────────────────────────
row(9, [(load("website/2d-plane-office-room.png"), "The floor — real people at real desks"),
        (load("website/2d-plane-how-are-online.png"), "Who's online")])

# ── 18 · rooms you can walk into ────────────────────────────────────────────
row(18, [(load("website/2d-plane-meeting-room.png"), "Meeting room"),
         (load("website/2d-plane-ceo-room.png"), "CEO room"),
         (load("website/2d-plane-chill-zone.png"), "Chill zone")], cap_h=470)

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
