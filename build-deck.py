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
    "Sersawy":       ("SE", "Backend · Workspace, AI & the 2D Office"),
    "Nadine":        ("NA", "Frontend · Real-Time"),
    "Khalwsh":       ("KH", "Backend · Architecture & Chat"),
    "Khaled Qenawy": ("KQ", "Mobile · Flutter"),
    "All":           ("VO", "The whole team"),
}

# One line the CURRENT speaker uses to hand over — shown bottom-right.
HANDOFF = {
    4:  "how research became what we built",
    6:  "what we added for the employee",
    8:  "the gap nobody else has closed",
    9:  "how all of it got designed",   # 2D reveal -> Rokaya on Figma/UI
    11: "why HTTP wasn't enough",
    12: "the backend",
    13: "identity, tasks and the calendar",
    15: "chat, notifications and rooms",
    16: "the workspace and the AI bot",
    19: "the phone",
    23: "the demo",
}

# ── tech logos ───────────────────────────────────────────────────────────────
# Real brand marks (official paths, via simple-icons — CC0), inlined so nothing
# is fetched at render time. Java, Slack, Groq, Phaser, Colyseus and Loki have no
# icon in the set: those keep the plain colour dot rather than a logo we invented.
LOGOS = json.loads((ROOT / "deck-logos.json").read_text())
# Composites are laid out at whatever ratio their contents imply (see
# scratchpad/compose.py). The figure slot adopts it, so object-fit: cover
# has nothing to crop.
SHOT_AR = json.loads((ROOT / "shot-ratios.json").read_text())

# ── tech chips (brand colour when there's no logo) ───────────────────────────
TECH_COLOR = {
    "React": "#61DAFB", "Redux": "#764ABC", "React Router": "#CA4245", "Axios": "#5A29E4",
    "Phaser": "#CC3333", "Colyseus": "#8B5CF6", "Tiled": "#8A9BA8",
    "Spring Boot": "#6DB33F", "Spring Cloud Gateway": "#6DB33F", "Spring Security": "#6DB33F",
    "Spring Data JPA": "#6DB33F", "Java": "#E76F00",
    "Docker": "#2496ED", "MySQL": "#4479A1", "PostgreSQL": "#4169E1", "MongoDB": "#47A248",
    "Redis": "#DC382D", "RabbitMQ": "#FF6600", "Node.js": "#339933",
    "Flutter": "#02569B", "Dart": "#0175C2", "Provider": "#02569B",
    "Grafana": "#F46800", "Loki": "#FBBF24", "Promtail": "#FBBF24", "Prometheus": "#E6522C",
    "Agora": "#099DFD", "WebSocket": "#7A7A7A", "STOMP": "#7A7A7A", "WebRTC": "#333333",
    "JWT": "#D63AFF", "BCrypt": "#7A7A7A", "WebCrypto": "#2F6F4F",
    "Figma": "#F24E1E", "Slack": "#4A154B", "Discord": "#5865F2", "Microsoft Teams": "#6264A7",
    "OpenAI": "#10A37F", "Groq": "#F55036", "Function calling": "#10A37F",
    "Tiled tilemap": "#8A9BA8", "shared_preferences": "#02569B", "stomp_dart_client": "#02569B",
    "awesome_notifications": "#02569B", "Flyway": "#CC0200",
}
# A big brand mark, rotated, ghosted into the corner — the slide's "signature".
# Dense graphs need the room: these slides give the visual most of the width
# and squeeze the bullets, instead of fitting a 5-rank graph into half a slide.
WIDE = {13, 16}

MARKS = {5: "Figma", 10: "Figma", 11: "React", 12: "Agora", 13: "Spring Boot", 14: "JWT",
         15: "Spring Boot", 16: "MongoDB", 17: "Node.js", 18: "Phaser", 19: "Grafana",
         20: "Flutter", 21: "Flutter", 22: "Flutter", 23: "Flutter"}

TECH = {
    3:  ["Slack", "Microsoft Teams", "Discord"],
    5:  ["Figma"],
    7:  ["Groq", "Function calling"],
    10: ["Figma"],
    11: ["React", "React Router", "Axios"],
    12: ["WebSocket", "STOMP", "Agora"],
    18: ["Phaser", "Colyseus", "Tiled tilemap", "React", "Redux"],
    13: ["Spring Boot", "Spring Cloud Gateway", "Docker", "MySQL", "PostgreSQL", "MongoDB", "Redis", "RabbitMQ"],
    14: ["JWT", "BCrypt", "Spring Security"],
    15: ["Spring Data JPA", "PostgreSQL", "Flyway", "RabbitMQ"],
    17: ["Node.js", "Groq", "Function calling", "PostgreSQL", "Flyway"],
    16: ["MongoDB", "Redis", "RabbitMQ", "WebSocket", "WebCrypto"],
    19: ["Loki", "Promtail", "Prometheus", "Grafana"],
    20: ["Flutter", "Dart"],
    21: ["Flutter", "Provider", "shared_preferences"],
    22: ["stomp_dart_client", "awesome_notifications"],
}

# Hand-built diagrams. Anything that isn't a real screenshot of the product is
# drawn here in HTML/CSS — a dashed box saying "draw this" is a promise, not a
# slide. Components carry their tech's brand colour.
def svg(name: str) -> str:
    """Inline a rendered mermaid diagram. Source: diagrams/<name>.mmd."""
    raw = (ROOT / "shots" / f"{name}.svg").read_text()
    raw = re.sub(r"<\?xml.*?\?>", "", raw, flags=re.S)          # drop the XML prolog
    raw = re.sub(r'\s(width|height)="[^"]*"', "", raw, count=2)  # let CSS size it
    return raw


def box(label, tech=None, cls="", port=None):
    """port: the port the thing actually listens on (read off docker-compose.yml)."""
    t = f'<i class="dg-t" style="--c:{tech}"></i>' if tech else ""
    pt = f'<code>:{port}</code>' if port else ""
    return f'<div class="dg-box {cls}">{t}<span>{label}</span>{pt}</div>'

C = dict(react="#61DAFB", flutter="#02569B", phaser="#CC3333", spring="#6DB33F", node="#339933",
         mysql="#4479A1", pg="#4169E1", mongo="#47A248", redis="#DC382D", rabbit="#FF6600",
         docker="#2496ED", grafana="#F46800", loki="#FBBF24", agora="#099DFD", ai="#10A37F",
         slack="#4A154B", teams="#6264A7", discord="#5865F2", zoom="#2D8CFF", jira="#0052CC", gcal="#4285F4")

DIAGRAMS = {


# ── 4 · one place ────────────────────────────────────────────────────────────
4: '''<div class="dg dg-hub">
  <div class="hub-grid">
    <span class="hub-n on">People</span><span class="hub-n on">Chat</span><span class="hub-n on">Tasks</span>
    <span class="hub-c">Workspace</span>
    <div class="hub-row"><span class="hub-n on">Meetings</span><span class="hub-n on">Presence</span></div>
  </div>
  <div class="dg-cap">Not five features. One workflow.</div>
</div>''',

# ── 12 · realtime ────────────────────────────────────────────────────────────
12: f'''<div class="dg dg-flow">
  <div class="dg-lane"><b class="dg-lane-t">HTTP — you ask</b>
    <div class="dg-row">{box("Browser", C['react'])}<i class="dg-a">request →</i>{box("Gateway", C['spring'])}
      <i class="dg-a">← response</i></div></div>
  <div class="dg-lane hot"><b class="dg-lane-t">WebSocket / STOMP — it arrives</b>
    <div class="dg-row">{box("Browser", C['react'])}<i class="dg-a dg-a2">⇄ persistent ⇄</i>{box("Gateway", C['spring'])}
      <i class="dg-a dg-a2">⇄</i>{box("Chat", C['spring'])}</div>
    <div class="dg-sub">messages · presence · office activity · notifications</div></div>
  <div class="dg-row dg-side">{box("Agora SDK", C['agora'])}<i class="dg-a">voice / video — we didn't rebuild WebRTC</i></div>
</div>''',

# ── 13 · the architecture ────────────────────────────────────────────────────
13: f'''<div class="dg dg-arch">
  <div class="dg-tier"><span class="dg-tier-l">clients</span><div class="dg-row">
    {box("Web", C['react'], port="3001")}{box("Mobile", C['flutter'])}{box("2D Office", C['phaser'], port="5000")}</div></div>
  <i class="dg-v">↓</i>
  <div class="dg-gate">{box("API Gateway", C['spring'], "wide", port="8080")}<small>one door · validates the JWT once · injects identity</small></div>
  <i class="dg-v">↓</i>
  <div class="dg-tier"><span class="dg-tier-l">services</span><div class="dg-grid">
    {box("User", C['spring'], port="8091")}{box("Workspace", C['spring'], port="8087")}{box("Chat", C['spring'], port="8084")}{box("Notif", C['spring'], port="8082")}
    {box("Calendar", C['spring'], port="8083")}{box("Tasks", C['spring'], port="8085")}{box("Room", C['spring'], port="8086")}{box("AI", C['ai'], port="8089")}
    {box("Office", C['node'], port="2567")}</div></div>
  <i class="dg-v">↓</i>
  <div class="dg-tier"><span class="dg-tier-l">data</span><div class="dg-row">
    {box("MySQL", C['mysql'])}{box("Postgres", C['pg'])}{box("Mongo", C['mongo'])}
    {box("Redis", C['redis'])}{box("RabbitMQ", C['rabbit'])}</div></div>
  <div class="dg-cap">{box("Docker Compose", C['docker'], "dg-ghost")} ~20 containers · one command</div>
</div>''',

# ── 14 · identity at the edge ────────────────────────────────────────────────
14: f'''<div class="dg dg-auth">
  <div class="dg-row">
    <div class="dg-box bad"><span>Client</span><code>X-User-Id: 1</code><small>spoofed</small></div>
    <i class="dg-a">→</i>
    <div class="dg-gatebox">{box("Gateway", C['spring'])}
      <ol><li>verify JWT</li><li class="strike">strip <code>X-User-*</code></li><li>inject trusted</li></ol></div>
    <i class="dg-a">→</i>
    <div class="dg-box good"><span>Service</span><code>X-User-Id: 64</code><small>trusted</small></div>
  </div>
  <div class="dg-cap">Services never parse a JWT. They trust the gateway — because only it can set these.</div>
</div>''',

# ── 21 · mobile layers ───────────────────────────────────────────────────────
21: f'''<div class="dg dg-layers">
  <div class="dg-chain">
    {box("Screen", C['flutter'])}<i class="dg-a">→</i>{box("Provider", C['flutter'])}<i class="dg-a">→</i>
    {box("Repository", C['flutter'])}<i class="dg-a">→</i>{box("ApiClient", C['flutter'])}
    <i class="dg-a">→</i>{box("Gateway", C['spring'])}
  </div>
  <div class="dg-tree"><b>lib/</b>
    <div>├── core/ <small>theme · constants</small></div>
    <div>└── features/chat/</div>
    <div class="in">├── api/ · models/ · repositories/</div>
    <div class="in">├── providers/ <small>connection · channel · message · thread</small></div>
    <div class="in">└── screens/ · services/ · widgets/</div>
  </div>
  <div class="dg-cap">Same APIs as the web. No mobile backend.</div>
</div>''',
}

# ── 1 · the title card is the product: six desks on a floor ──────────────────
# A logo says nothing a title already said. The deck is about a 2D office, so
# the title card IS one — the team, at their desks, grouped by what they built.
TEAM = [("Rokaya Othman", "frontend"), ("Nadine Mohsen", "frontend"),
        ("Abdelrahman Sersawy", "backend"), ("Ahmed Mousa", "backend"),
        ("Khalid Labib", "backend"), ("Khaled Qenawy", "mobile")]
ZONE = {"frontend": ("Frontend", C['react']), "backend": ("Backend", C['spring']),
        "mobile": ("Mobile", C['flutter'])}

def _desk(name, zone):
    ini = "".join(w[0] for w in name.split()[:2]).upper()
    return (f'<div class="tc-p" style="--c:{ZONE[zone][1]}"><span class="tc-av">{ini}</span>'
            f'<span class="tc-n">{name}</span><i class="tc-desk"></i></div>')

DIAGRAMS[1] = '<div class="dg dg-title"><div class="tc-floor">' + "".join(
    f'<div class="tc-zone"><span class="tc-zl" style="--c:{ZONE[z][1]}">{ZONE[z][0]}</span>'
    + "".join(_desk(n, zz) for n, zz in TEAM if zz == z) + '</div>'
    for z in ("frontend", "backend", "mobile")
) + '</div><p class="dg-cap">Six people · three clients · one workspace</p></div>'

# ── 2 · the office gave you five things free. Remote took all five. ──────────
# Framed as a loss, not a complaint — that's why the left column is struck out.
GAVE = ["Faster communication", "Better collaboration", "Visible work status",
        "Clear tasks & accountability", "Real interaction"]
LEFT = ["Disconnected tools", "Constant context switching", "No spontaneous talk",
        "Can't see who's available", "No shared place to be"]
DIAGRAMS[2] = ('<div class="dg dg-ledger"><div class="led gone"><b class="led-h">onsite gave you</b><ul>'
    + "".join(f"<li>{x}</li>" for x in GAVE)
    + '</ul></div><i class="led-a"><span>remote</span>→</i>'
    + '<div class="led bad"><b class="led-h">remote left you</b><ul>'
    + "".join(f"<li>{x}</li>" for x in LEFT)
    + '</ul></div><p class="dg-cap">Five tools. One job. No idea what the team is doing.</p></div>')

# ── 11 · reusable components + the axios interceptor ─────────────────────────
DIAGRAMS[11] = f'''<div class="dg dg-code">
  <div class="dg-tree">
    <b>components/</b>
    <div>├── <b>Button</b>.jsx</div><div>├── <b>Modal</b>.jsx</div>
    <div>├── <b>Card</b>.jsx</div><div>└── <b>Nav</b>.jsx</div>
    <div class="dg-tree-note">built once · used on every page</div>
  </div>
  <pre class="dg-pre"><span class="c">// one place for the token, every request</span>
axios.interceptors.request.use(cfg =&gt; {{
  cfg.headers.<b>Authorization</b> = `Bearer ${{token}}`
  return cfg
}})</pre>
</div>'''

# ── 15 · the scheduler, and the board it drives ──────────────────────────────
DIAGRAMS[15] = '''<div class="dg dg-code">
  <pre class="dg-pre"><b>@Scheduled</b>(fixedDelay = 60_000)
void <b>sync</b>() {
  applyForStartedMeetings(now);  <span class="c">// -&gt; "In a meeting"</span>
  revertForEndedMeetings(now);   <span class="c">// only if our marker</span>
}
<span class="c">// fails? don't set the flag. next tick retries.</span></pre>
  <figure class="obs-shot"><img src="shots/slide-15-tasks.png" alt="" onerror="this.closest('figure').remove()">
    <figcaption>day bands · <b>#97</b>, <b>#94</b> — human numbers, not UUIDs</figcaption></figure>
</div>'''

# ── 16 · the ciphertext, and the queue ───────────────────────────────────────
DIAGRAMS[16] = f'''<div class="dg dg-code">
  <pre class="dg-pre term"><span class="p">&gt;</span> db.messages.find({{content: /^vo1:/}})
<span class="ct">vo1:TzO44O2p++/WL3yy:YHdQoK4tYMtycnZBfodXR5RX8…</span>
<span class="c">// what the server has. no key. that's the whole point.</span></pre>
  <div class="dg-row dg-q">
    {box("Task Service", C['spring'])}<i class="dg-a">publish →</i>
    {box("RabbitMQ", C['rabbit'])}<i class="dg-a">→ consume</i>
    {box("Notification", C['spring'])}
  </div>
  <div class="dg-cap">Task Service never waits for an email.</div>
</div>'''

# ── 19 · both dashboards, both real ─────────────────────────────────────────
DIAGRAMS[19] = '''<div class="dg dg-obs">
  <figure class="obs-shot"><img src="shots/slide-19.png" alt="" onerror="this.closest('figure').remove()">
    <figcaption><b>Loki</b> — logs: <i>what happened</i></figcaption></figure>
  <figure class="obs-shot"><img src="shots/slide-19-metrics.png" alt="" onerror="this.closest('figure').remove()">
    <figcaption><b>Prometheus</b> — metrics: <i>how often, how slow</i></figcaption></figure>
</div>'''

# ── 5 · research became requirements, requirements became features ───────────
# No invented user stories here: the pains are the five from the problem slide
# (their own research), the features are ones that actually shipped.
DIAGRAMS[5] = f'''<div class="dg dg-pipe">
  <div class="dg-stage"><span class="dg-stage-l">studied</span>
    <div class="dg-row">{box("Slack", C['slack'])}{box("Teams", C['teams'])}{box("Discord", C['discord'])}</div></div>
  <i class="dg-v">↓</i>
  <div class="dg-stage"><span class="dg-stage-l">named the pain</span>
    <div class="dg-pains"><span>can't see who's free</span><span>context switching</span>
      <span>no spontaneous talk</span><span>nothing is one place</span></div></div>
  <i class="dg-v">↓</i>
  <div class="dg-stage"><span class="dg-stage-l">wrote user stories</span>
    <div class="dg-story">“As a remote employee I want to <b>see who is available</b>
      so I can ask a quick question without booking a meeting.”</div></div>
  <i class="dg-v">↓</i>
  <div class="dg-stage"><span class="dg-stage-l">built</span>
    <div class="dg-row">{box("Presence", C['spring'])}{box("2D floor", C['phaser'])}
      {box("Tasks", C['spring'])}{box("Assistant", C['ai'])}</div></div>
  <div class="dg-cap">Every feature traces back to a pain. Nothing is here because it looked nice.</div>
</div>'''

# ── 7 · the assistant, answering for real ────────────────────────────────────
# Verbatim from the running assistant (workspace 49, as Maya). Drawn, not a
# screenshot — but the words are the model's, not ours.
DIAGRAMS[7] = '''<div class="dg dg-ai">
  <div class="ai-q">Summarise what I missed in #general today.</div>
  <div class="ai-a">
    <div class="ai-a-h"><span class="ai-dot"></span>Assistant</div>
    <ul>
      <li>Karim: the analytics <b>timezone bug is back</b> on staging.</li>
      <li>Karim asked <b>@maya to approve the RC cut</b> for tomorrow morning.</li>
      <li>Karim off Thursday — Salma covers the calendar-sync load test.</li>
      <li>Lina: launch-day runbook is pinned, everyone knows their role.</li>
    </ul>
  </div>
  <div class="ai-foot"><code>tools used: read_channel</code>
    <span>Real answer, real data — your cursor, your permissions.</span></div>
</div>'''

# ── 17 · function calling: the assistant borrows YOUR token ──────────────────
DIAGRAMS[17] = f'''<div class="dg dg-fc">
  <div class="dg-row">{box("You", C['react'])}<i class="dg-a">“create a high-priority task for Karim” →</i></div>
  <div class="dg-row">{box("AI Service", C['node'], port="8089")}<i class="dg-a">↔ tool call ↔</i>{box("Model", C['ai'])}</div>
  <div class="dg-row">{box("Gateway", C['spring'], port="8080")}<i class="dg-a">← your bearer token, forwarded</i></div>
  <div class="dg-row">{box("Tasks", C['spring'], port="8085")}{box("Calendar", C['spring'], port="8083")}
    {box("Chat", C['spring'], port="8084")}{box("Workspace", C['spring'], port="8087")}</div>
  <div class="dg-cap"><b>No service account.</b> The assistant can only see and do
    what you could do yourself — same APIs, same permissions.</div>
</div>'''

# ── 24 · the run sheet, so nobody freezes ────────────────────────────────────
DIAGRAMS[24] = '''<div class="dg dg-run">
  <ol class="run">
    <li><b>Log in</b> — the workspace is already alive. 15 people, real history.</li>
    <li><b>Chat + thread</b> — open #general, open a thread, send one message.</li>
    <li><b>“Catch me up”</b> — the assistant answers from the real cursor.</li>
    <li><b>Create a task from a sentence</b> — watch it land on the board.</li>
    <li><b>Walk into the 2D office</b> — end here. Always end here.</li>
  </ol>
  <div class="dg-cap">Backup video ready. If a step stalls, move on — never debug on stage.</div>
</div>'''

# ── 13 · the service topology (diagrams/topology.mmd) ───────────────────────
DIAGRAMS[13] = f'''<div class="dg dg-graph">{svg("topology")}
  <div class="dg-cap"><b>Each service owns its own store.</b> Services talk over the
    gateway or the broker — no shared tables, no back doors.</div></div>'''

# ── 16 · the ciphertext, then async integration (diagrams/rabbitmq.mmd) ─────
DIAGRAMS[16] = f'''<div class="dg dg-graph">
  <pre class="dg-pre term"><span class="p">&gt;</span> db.messages.find({{content: /^vo1:/}})
<span class="ct">vo1:TzO44O2p++/WL3yy:YHdQoK4tYMtycnZBfodXR5RX8…</span></pre>
  {svg("rabbitmq")}
  <div class="dg-cap"><b>Two consumers own the topology</b> — notifications and chat.
    Every other service only produces.</div></div>'''

# Two slides carry a table as their actual argument — render it, don't ask for a
# screenshot of one. (Slide 13's table was being dropped by the parser entirely.)
TABLES = {
 3: {"head": ["", "Slack", "Teams", "Discord", "Ours"],
     "rows": [["Chat", "y", "y", "y", "y"], ["Threads", "y", "y", "~", "y"],
              ["Tasks", "n", "~", "n", "y"], ["Meetings", "n", "y", "y", "y"],
              ["Presence", "~", "~", "y", "y"], ["One place", "n", "~", "n", "y"]]},
 18: {"head": ["", "Chat", "Movement"],
      "rows": [["Every event matters?", "Yes — never lose one", "No — a late one is garbage"],
               ["Order matters?", "Yes", "Only the newest"],
               ["Store it?", "Forever (MongoDB)", "Never"],
               ["Rate", "A few / minute", "~60 / second"],
               ["So", "STOMP + MongoDB", "Colyseus"]]},
}

# Short cues shown ON the slide. The full talking points stay in the markdown
# and live behind the N key — a slide should jog your memory, not be read out.
CUES = {
 1: ["Who we are — Frontend · Backend · Mobile", "Agenda: problem → what → how → demo"],
 2: ["The office gave five things **free**", "Fast talk · collaboration · visible status · ownership · real interaction",
     "**Remote took all five**", "Five disconnected tools in their place",
     "*“Five tools all day, still don't know what the team is doing”*"],
 3: ["Studied them honestly — they're good at their job", "**None give you a workplace.** They give you channels",
     "Presence is the missing piece"],
 4: ["People · Tasks · Meetings · Chat · Workspace", "Not five features — **one workflow**",
     "Message → task → deadline → meeting → same people"],
 5: ["Analysed Slack · Teams · Discord", "Studied real remote pain", "→ user stories drove every feature",
     "*“Nothing here because it looked nice”*"],
 6: ["Chat · Threads · Voice calls", "**Parity — not the answer** →"],
 7: ["Built for the person, not just the work", "200 unread → nobody actually reads them",
     "**Ask instead of read**", "Only *your* unread — real cursor, not “last 50”",
     "Reading it doesn't mark it read", "Can't invent — same APIs, your permissions"],
 8: ["Real office: your desk is *yours*", "Slack gives you channels. Nothing belongs to you",
     "My Desk — tasks · agenda · notes · whiteboard", "**Belonging is a feature**",
     "→ *“still a room with one person in it”*"],
 9: ["You can't **see** your colleagues", "Real office: look up → walk over → 5 seconds",
     "Slack: search → DM → type → wait → maybe call", "**The 2D Plane** — see · move · walk up · join a room",
     "*“Not a game. Not decoration.”*"],
 10:["Stories → screens", "Simple · clear · reachable · consistent", "Wireframe → final"],
 11:["SPA — instant, no reload", "React Router v7", "Reusable: buttons · forms · modals · cards",
     "Axios — one place for errors + tokens", "**But HTTP: you have to ask** →"],
 12:["HTTP you *ask* · WebSocket it *arrives*", "STOMP via `@stomp/stompjs`",
     "Messages · presence · office activity", "Same pipe → real-time notifications",
     "Agora for voice/video — we didn't rebuild WebRTC"],
 18:["**Phaser 3** — a floor plan **is** a game loop",
     "**Colyseus** — authoritative, its own Node service", "*“Why two realtime stacks?”* → **opposite problems** →",
     "`@type` decorators = binary deltas = **the protocol**",
     "`filterBy(workspaceId)` → one room per company", "Phaser canvas + React HUD, one page",
     "Proximity → the call connects. You walk over", "Joystick for touch"],
 13:["Not one app — independent services", "**Gateway** — one door, validates the JWT once",
     "User · Workspace · Chat · Notif · Calendar · Tasks · Room · AI · +Office",
     "Separate · deploy alone · scale alone · **fail alone**", "~20 containers, one command"],
 14:["BCrypt — we never store a password", "JWT (HS256), shared only gateway ↔ user-service",
     "**Strip** client `X-User-*` · **inject** trusted", "Services never parse a JWT",
     "Account role **vs** workspace role", "OTP reset — no links to leak", "Register → **RabbitMQ** → welcome. Never blocks signup",
     "*“Decided once, at the edge”*"],
 15:["Spring Data JPA on PostgreSQL", "**`#42`, not a UUID** — max+1 per workspace", "**Flyway** — schema is versioned, not hand-run SQL",
     "Assign → RabbitMQ → Notification. **Never waits**", "`@Scheduled` 60s — reminders + **auto-status**",
     "Meeting starts → *“In a meeting ”* by itself", "**Idempotent** — flags, never double-send",
     "**Never clobber a human's own status**"],
 17:["Workspace = the backbone", "Members · teams · channels · roles · office layout",
     "AI: summarise · decisions · create · answer", "**The hard part was context**",
     "Function calling — same APIs, **your** token"],
 16:["Chat: DMs · channels · threads, live", "WebSocket · **Redis** presence · **Mongo** volume",
     " **DMs are E2E — we can't read them**", "ECDH → AES-GCM **in the browser**",
     "Server stores `vo1:<iv>:<ct>` and nothing else", "**Trade-off: DMs only** — channels feed search + AI",
     "Limits: one device · no forward secrecy · TOFU", "Notif: **RabbitMQ** — Task never waits",
     "Rooms: we own the permissions"],
 19:["20 containers, 9 services → nine `docker logs`?", "**Loki** ← Promtail ← every container",
     "One **Grafana** dashboard", "**Paid off day one:** ~200 errors/hr nobody saw",
     "→ the WS handshake bug Khalwsh just described", "*“App looked fine. Logs didn't.”*",
     "**Prometheus** — 8 services scraped · p95 · error ratio",
     "Logs say *what*. Metrics say *how often, how slow*"],
 20:["One codebase → Android · iOS · web", "**Deep on chat, not shallow on everything**",
     "Nobody plans a sprint on a 6-inch screen", "Tasks/calendar/calls = screens, not architecture"],
 21:["Feature-first: `core/` + `features/chat/`", "Screen → Provider → Repository → ApiClient",
     "Provider **split by concern**, not one god-object", "`shared_preferences` holds the JWT",
     "**Same APIs as web. No mobile backend.**"],
 23:["Five tabs: Channels · DMs · **Rooms** · Workspace · Profile", "Not a chat window — **the workspace**",
     "Create a channel on the phone → it's in the browser's list", "Join a voice room from your pocket",
     "**No mobile backend** — same gateway, same JWT, same permissions"],
 22:["**Same STOMP contract as the browser**", "`stomp_dart_client` ↔ `@stomp/stompjs`",
     "We reused the realtime stack, didn't rebuild it", "`uuid` → clientMessageId → idempotent retries",
     "`awesome_notifications` on the device", "Calls next: Agora SDK — Rooms already handles it"],
 24:["Login → the workspace is **alive**", "Chat + thread", "*“Catch me up”*",
     "Create a task from a sentence", "**Walk into the 2D office**",
     "*“…one place you can actually walk into.”*"],
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
 10: ("shot", "The Figma file itself: the design system and component tree on the left, the shipped screen in the frame.", "16/10"),
 11: ("diagram", "Component tree or the reusable-components folder + one small Axios interceptor snippet (the auth token). Keep the code readable from the back row.", "4/3"),
 12: ("diagram", "Browser ⇄ WebSocket/STOMP ⇄ Gateway ⇄ Chat Service, with a second line for Agora. Or: two browsers, a message landing instantly.", "16/9"),
 18: ("shot", "The OfficeState schema — ten lines of @type decorators — beside the office. Say: 'this is the entire network protocol.'", "4/3"),
 13: ("diagram", "THE ARCHITECTURE. Clients → Gateway → 9 services → datastores (MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ). Colour-code by concern. Your most important slide.", "16/9"),
 14: ("diagram", "Strip-then-inject: Client (X-User-Id: 1 ← spoofed ✗) → Gateway [verify JWT · strip · inject] → Service (X-User-Id: 64 ✓).", "16/9"),
 15: ("diagram", "AutoStatusScheduler.sync() — ~15 lines. Plus the tasks board with Overdue / Today / upcoming bands.", "4/3"),
 17: ("live", "Type: 'Create a high priority task for Karim…' → then the task appearing on the board. The strongest 15 seconds in the deck.", "16/10"),
 16: ("diagram", "Terminal: the Mongo query returning vo1:<iv>:<ciphertext>. Ten seconds, and it ends the argument. Plus the RabbitMQ event flow diagram.", "16/9"),
 19: ("shot", "The Grafana dashboard — Virtual Office — Logs & Errors. Filter to one service live so it's obviously real.", "16/9"),
 20: ("shot", "Phone frames: login · channels · chat. A real device beats an emulator.", "9/16"),
 21: ("diagram", "The folder tree (lib/features/chat/...) beside: Screen → Provider → Repository → ApiClient → Gateway.", "4/3"),
 22: ("shot", "Channels · a live DM · creating a room — on the device.", "16/10"),
 23: ("shot", "Four phones: Workspace · Create channel · Rooms (with Join) · Profile. The five-tab nav is the point.", "16/10"),
 24: ("live", "LIVE DEMO. Log in → chat + thread → assistant catch-up → create a task → walk into the 2D office. Have the backup video ready.", "16/9"),
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


def lint_classes(tpl: str):
    """Chrome classes are defined before the diagram kit and are positioned; a
    diagram reusing one inherits that positioning and collapses. Catch it here,
    not in a screenshot at 2am."""
    chrome_css = tpl[: tpl.index("/* ── diagram kit")]
    chrome = set(re.findall(r"^\.([a-z][\w-]*)\{", chrome_css, re.M))
    used = set()
    for html_ in DIAGRAMS.values():
        for attr in re.findall(r'class="([^"]+)"', html_):
            used |= set(attr.split())
    clash = sorted(c for c in used & chrome if not c.startswith("dg"))
    if clash:
        raise SystemExit(
            f"Diagram markup reuses chrome class(es) {clash}. The chrome is positioned — "
            f"your boxes will stack on top of each other. Rename them (dg-*).")


def build():
    tpl = (ROOT / "deck-template.html").read_text()
    lint_classes(tpl)
    slides = parse()
    data = []
    for i, sl in enumerate(slides):
        n = sl["n"]
        nxt = slides[i + 1]["who"] if i + 1 < len(slides) else None
        kind, desc, ratio = VISUAL.get(n, ("diagram", "", "16/9"))
        ratio = SHOT_AR.get(str(n), ratio)
        if n in TABLES: kind = "table"
        if n in DIAGRAMS: kind = "diagram-built"
        data.append({
            "n": n, "title": sl["title"], "who": sl["who"],
            "initials": PEOPLE.get(sl["who"], ("??", ""))[0],
            "role": PEOPLE.get(sl["who"], ("", ""))[1],
            "time": sl["time"],
            # On the slide: terse cues. Behind N: the full talking points and the
            # delivery notes. A slide is a memory jog, not a script.
            "bullets": [md(b) for b in CUES.get(n, sl["say"])],
            "notes": [md(h) for h in sl["how"]],
            "script": [md(b) for b in sl["say"]],
            "tech": [{"name": t,
                      "color": LOGOS.get(t, {}).get("hex") or TECH_COLOR.get(t, "#7A7A7A"),
                      "path": LOGOS.get(t, {}).get("path")} for t in TECH.get(n, [])],
            "mark": ({"key": MARKS[n], **LOGOS.get(MARKS[n], {})} if n in MARKS else None),
            "wide": n in WIDE,
            "visual": {"kind": kind, "desc": desc, "ratio": ratio, "table": TABLES.get(n),
                       "html": DIAGRAMS.get(n)},
            "next": None if not nxt or nxt == sl["who"] else {
                "name": nxt, "initials": PEOPLE.get(nxt, ("??", ""))[0],
                "hint": HANDOFF.get(n, ""),
            },
        })
    missing = [d["n"] for d in data if d["next"] and not d["next"]["hint"]]
    if missing:
        raise SystemExit(
            f"HANDOFF is missing a hint for slide(s) {missing}. Every hand-off must say what the "
            f"next person covers, or the card reads '…and now, <name>.' and dies.")

    out = tpl.replace("/*__SLIDES__*/", json.dumps(data, ensure_ascii=False, indent=1))
    (ROOT / "Presentation.html").write_text(out)
    print(f"Presentation.html — {len(data)} slides, {len(out)//1024} KB")


if __name__ == "__main__":
    build()
