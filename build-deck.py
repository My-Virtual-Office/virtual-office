#!/usr/bin/env python3
"""
Build Presentation.html from Presentation-17-Slides.md.

The markdown stays the source of truth for content; this only adds the
presentation layer (speaker hand-offs, tech chips, visual placeholders) and
renders the deck. Re-run after editing the markdown.
"""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).parent
MD = ROOT / "Presentation-17-Slides.md"

# ── people ───────────────────────────────────────────────────────────────────
PEOPLE = {
    "Mousa":         ("MO", "Backend · Security & Services"),
    "Rokaya":        ("RO", "Frontend · UI/UX"),
    "Sersawy":       ("SE", "Backend · Workspace, AI & Platform"),
    "Nadine":        ("NA", "Frontend · Real-Time & the 2D Office"),
    "Khalwsh":       ("KH", "Backend · Architecture & Chat"),
    "Khaled Qenawy": ("KQ", "Mobile · Flutter"),
    "All":           ("VO", "The whole team"),
}

# One line the CURRENT speaker uses to hand over — shown bottom-right.
HANDOFF = {
    4:  "takes the research — how we turned interviews into what we built",
    6:  "shows what we added for the person, not just the work",
    8:  "on the gap nobody else has closed",
    11: "on why HTTP wasn't enough",
    13: "opens the backend",
    16: "on the workspace and the AI bot",
    17: "on chat, notifications and rooms",
    18: "on how we know when any of it breaks",
    19: "takes it to the phone",
    22: "— demo time",
}

# ── tech chips (brand colours; no fake logos) ────────────────────────────────
TECH_COLOR = {
    "React": "#61DAFB", "Redux": "#764ABC", "React Router": "#CA4245", "Axios": "#5A29E4",
    "Phaser": "#CC3333", "Colyseus": "#8B5CF6", "Tiled": "#8A9BA8",
    "Spring Boot": "#6DB33F", "Spring Cloud Gateway": "#6DB33F", "Spring Security": "#6DB33F",
    "Spring Data JPA": "#6DB33F", "Java": "#E76F00",
    "Docker": "#2496ED", "MySQL": "#4479A1", "PostgreSQL": "#4169E1", "MongoDB": "#47A248",
    "Redis": "#DC382D", "RabbitMQ": "#FF6600", "Node.js": "#339933",
    "Flutter": "#02569B", "Dart": "#0175C2", "Provider": "#02569B",
    "Grafana": "#F46800", "Loki": "#FBBF24", "Promtail": "#FBBF24",
    "Agora": "#099DFD", "WebSocket": "#7A7A7A", "STOMP": "#7A7A7A", "WebRTC": "#333333",
    "JWT": "#D63AFF", "BCrypt": "#7A7A7A", "WebCrypto": "#2F6F4F",
    "Figma": "#F24E1E", "Slack": "#4A154B", "Discord": "#5865F2", "Microsoft Teams": "#6264A7",
    "OpenAI": "#10A37F", "Groq": "#F55036", "Function calling": "#10A37F",
    "Tiled tilemap": "#8A9BA8", "shared_preferences": "#02569B", "stomp_dart_client": "#02569B",
    "awesome_notifications": "#02569B",
}
TECH = {
    3:  ["Slack", "Microsoft Teams", "Discord"],
    5:  ["Figma"],
    7:  ["Groq", "Function calling"],
    10: ["Figma"],
    11: ["React", "React Router", "Axios"],
    12: ["WebSocket", "STOMP", "Agora"],
    13: ["Phaser", "Colyseus", "Tiled tilemap", "React", "Redux"],
    14: ["Spring Boot", "Spring Cloud Gateway", "Docker", "MySQL", "PostgreSQL", "MongoDB", "Redis", "RabbitMQ"],
    15: ["JWT", "BCrypt", "Spring Security"],
    16: ["Spring Data JPA", "PostgreSQL", "RabbitMQ"],
    17: ["Node.js", "Groq", "Function calling"],
    18: ["MongoDB", "Redis", "RabbitMQ", "WebSocket", "Agora", "WebCrypto"],
    19: ["Loki", "Promtail", "Grafana"],
    20: ["Flutter", "Dart"],
    21: ["Flutter", "Provider", "shared_preferences"],
    22: ["stomp_dart_client", "awesome_notifications"],
}

# Two slides carry a table as their actual argument — render it, don't ask for a
# screenshot of one. (Slide 13's table was being dropped by the parser entirely.)
TABLES = {
 3: {"head": ["", "Slack", "Teams", "Discord", "Ours"],
     "rows": [["Chat", "y", "y", "y", "y"], ["Threads", "y", "y", "~", "y"],
              ["Tasks", "n", "~", "n", "y"], ["Meetings", "n", "y", "y", "y"],
              ["Presence", "~", "~", "y", "y"], ["One place", "n", "~", "n", "y"]]},
 13: {"head": ["", "Chat", "Movement"],
      "rows": [["Every event matters?", "Yes — never lose one", "No — a late one is garbage"],
               ["Order matters?", "Yes", "Only the newest"],
               ["Store it?", "Forever (MongoDB)", "Never"],
               ["Rate", "A few / minute", "~60 / second"],
               ["So", "STOMP + MongoDB", "Colyseus"]]},
}

# ── visual placeholders: what to capture, and how ────────────────────────────
# kind: shot (screenshot) · diagram (draw it) · live (do it on stage)
VISUAL = {
 1:  ("diagram", "Title card — project name + the six of you. A team photo works better than a logo.", "16/9"),
 2:  ("diagram", "One person surrounded by app logos (Slack · Teams · Zoom · Jira · Calendar) with arrows going everywhere. Draw it — a screenshot can't say this.", "4/3"),
 3:  ("diagram", "Comparison table. Rows: Chat · Threads · Tasks · Meetings · Presence · One place. Columns: Slack · Teams · Discord · Ours. Give them their ticks honestly.", "4/3"),
 4:  ("diagram", "A single ring labelled 'Workspace' with five segments: People · Chat · Tasks · Meetings · Presence. Still no 2D reveal.", "1/1"),
 5:  ("shot", "3–4 real user-story cards + the arrow Research → User Stories → Features. From Figma if you have it.", "4/3"),
 6:  ("shot", "The chat UI: a channel with a thread open, real names and avatars. Use the Northstar demo — never an empty workspace.", "16/10"),
 7:  ("shot", "The Assistant answering 'Catch me up — what did I miss?', with the 'Based on live data' caption visible in frame.", "16/10"),
 8:  ("shot", "My Desk — Today's Agenda with real meetings, tasks, sticky notes, whiteboard. Seed first; an empty desk proves the opposite of your point.", "16/10"),
 9:  ("live", "THE 2D OFFICE — go live. Several avatars, a meeting room, someone's status. Walk across the floor. Fallback screenshot: 1600×900.", "16/9"),
 10: ("shot", "Figma board: wireframe and the shipped screen side by side. The before → after is the whole story.", "16/10"),
 11: ("shot", "Component tree or the reusable-components folder + one small Axios interceptor snippet (the auth token). Keep the code readable from the back row.", "4/3"),
 12: ("diagram", "Browser ⇄ WebSocket/STOMP ⇄ Gateway ⇄ Chat Service, with a second line for Agora. Or: two browsers, a message landing instantly.", "16/9"),
 13: ("shot", "The OfficeState schema — ten lines of @type decorators — beside the office. Say: 'this is the entire network protocol.'", "4/3"),
 14: ("diagram", "THE ARCHITECTURE. Clients → Gateway → 9 services → datastores (MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ). Colour-code by concern. Your most important slide.", "16/9"),
 15: ("diagram", "Strip-then-inject: Client (X-User-Id: 1 ← spoofed ✗) → Gateway [verify JWT · strip · inject] → Service (X-User-Id: 64 ✓).", "16/9"),
 16: ("shot", "AutoStatusScheduler.sync() — ~15 lines. Plus the tasks board with Overdue / Today / upcoming bands.", "4/3"),
 17: ("live", "Type: 'Create a high priority task for Karim…' → then the task appearing on the board. The strongest 15 seconds in the deck.", "16/10"),
 18: ("live", "Terminal: the Mongo query returning vo1:<iv>:<ciphertext>. Ten seconds, and it ends the argument. Plus the RabbitMQ event flow diagram.", "16/9"),
 19: ("shot", "The Grafana dashboard — Virtual Office — Logs & Errors. Filter to one service live so it's obviously real.", "16/9"),
 20: ("shot", "Phone frames: login · channels · chat. A real device beats an emulator.", "9/16"),
 21: ("diagram", "The folder tree (lib/features/chat/...) beside: Screen → Provider → Repository → ApiClient → Gateway.", "4/3"),
 22: ("live", "Two devices. Send on one, land on the other, background it, show the notification arrive.", "16/10"),
 23: ("live", "LIVE DEMO. Log in → chat + thread → assistant catch-up → create a task → walk into the 2D office. Have the backup video ready.", "16/9"),
}


def parse():
    s = MD.read_text()
    body = s[s.index("## PART 1"): s.index("## How to present this")]
    slides = []
    for blk in re.split(r"(?=^### Slide \d+ — )", body, flags=re.M)[1:]:
        n, title = re.match(r"### Slide (\d+) — (.*)", blk).groups()
        who = (re.search(r"\*\*Who:\*\* (.*)", blk) or [None, ""])[1].strip()
        who = re.sub(r"\s*\(.*?\)\s*$", "", who)   # "All (one driver…)" -> "All"
        time = (re.search(r"\*\*Time:\*\* (.*)", blk) or [None, ""])[1].strip()
        time = time.split("·")[0].strip()   # drop the "· **Then hand to:** X" tail
        how = re.findall(r"^- (.*)$", blk[blk.index("**How:**"): blk.index("**Say:**")], re.M)
        say_end = blk.index("**Show:**") if "**Show:**" in blk else len(blk)
        say = re.findall(r"^- (.*)$", blk[blk.index("**Say:**"): say_end], re.M)
        slides.append(dict(n=int(n), title=title.strip(), who=who, time=time, how=how, say=say))
    return slides


def md(t: str) -> str:
    """The tiny bit of markdown the notes actually use."""
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def build():
    slides = parse()
    data = []
    for i, sl in enumerate(slides):
        n = sl["n"]
        nxt = slides[i + 1]["who"] if i + 1 < len(slides) else None
        kind, desc, ratio = VISUAL.get(n, ("diagram", "", "16/9"))
        if n in TABLES: kind = "table"
        data.append({
            "n": n, "title": sl["title"], "who": sl["who"],
            "initials": PEOPLE.get(sl["who"], ("??", ""))[0],
            "role": PEOPLE.get(sl["who"], ("", ""))[1],
            "time": sl["time"],
            "bullets": [md(b) for b in sl["say"]],
            "notes": [md(h) for h in sl["how"]],
            "tech": [{"name": t, "color": TECH_COLOR.get(t, "#7A7A7A")} for t in TECH.get(n, [])],
            "visual": {"kind": kind, "desc": desc, "ratio": ratio, "table": TABLES.get(n)},
            "next": None if not nxt or nxt == sl["who"] else {
                "name": nxt, "initials": PEOPLE.get(nxt, ("??", ""))[0],
                "role": PEOPLE.get(nxt, ("", ""))[1],
                "hint": HANDOFF.get(n, ""),
            },
        })
    tpl = (ROOT / "deck-template.html").read_text()
    out = tpl.replace("/*__SLIDES__*/", json.dumps(data, ensure_ascii=False, indent=1))
    (ROOT / "Presentation.html").write_text(out)
    print(f"Presentation.html — {len(data)} slides, {len(out)//1024} KB")


if __name__ == "__main__":
    build()
