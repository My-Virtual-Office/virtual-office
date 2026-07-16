# Screenshots for the deck

Drop a PNG in here named `slide-NN.png` and it **replaces the placeholder automatically** —
no editing, just reload `Presentation.html`. Anything missing keeps showing its brief.

Slides 3 and 13 render their tables in HTML; they need no screenshot.

| File | Slide | Kind | Ratio | What to capture |
|---|---|---|---|---|
| `slide-01.png` | 1 — Title & Team | diagram | 16/9 | Title card — project name + the six of you. A team photo works better than a logo. |
| `slide-02.png` | 2 — The Problem | diagram | 4/3 | One person surrounded by app logos (Slack · Teams · Zoom · Jira · Calendar) with arrows going everywhere. Draw it — a screenshot can't say this. |
| `slide-04.png` | 4 — Our Solution: One Place | diagram | 1/1 | A single ring labelled 'Workspace' with five segments: People · Chat · Tasks · Meetings · Presence. Still no 2D reveal. |
| `slide-05.png` | 5 — Research → User Stories | shot | 4/3 | 3–4 real user-story cards + the arrow Research → User Stories → Features. From Figma if you have it. |
| `slide-06.png` | 6 — Core Collaboration Features | shot | 16/10 | The chat UI: a channel with a thread open, real names and avatars. Use the Northstar demo — never an empty workspace. |
| `slide-07.png` | 7 — Catching Up Without Reading Everything | shot | 16/10 | The Assistant answering 'Catch me up — what did I miss?', with the 'Based on live data' caption visible in frame. |
| `slide-08.png` | 8 — The Personal Desk | shot | 16/10 | My Desk — Today's Agenda with real meetings, tasks, sticky notes, whiteboard. Seed first; an empty desk proves the opposite of your point. |
| `slide-09.png` | 9 — The Biggest Gap: Human Presence 🎯 | live | 16/9 | THE 2D OFFICE — go live. Several avatars, a meeting room, someone's status. Walk across the floor. Fallback screenshot: 1600×900. |
| `slide-10.png` | 10 — From Requirements to Interface | shot | 16/10 | Figma board: wireframe and the shipped screen side by side. The before → after is the whole story. |
| `slide-11.png` | 11 — Why React.js | shot | 4/3 | Component tree or the reusable-components folder + one small Axios interceptor snippet (the auth token). Keep the code readable from the back row. |
| `slide-12.png` | 12 — Real-Time: WebSockets, STOMP & Agora | diagram | 16/9 | Browser ⇄ WebSocket/STOMP ⇄ Gateway ⇄ Chat Service, with a second line for Agora. Or: two browsers, a message landing instantly. |
| `slide-14.png` | 14 — Microservices Architecture | diagram | 16/9 | THE ARCHITECTURE. Clients → Gateway → 9 services → datastores (MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ). Colour-code by concern. Your most important slide. |
| `slide-15.png` | 15 — Identity: Decided Once, at the Edge | diagram | 16/9 | Strip-then-inject: Client (X-User-Id: 1 ← spoofed ✗) → Gateway [verify JWT · strip · inject] → Service (X-User-Id: 64 ✓). |
| `slide-16.png` | 16 — Tasks & Calendar: The Engineering | shot | 4/3 | AutoStatusScheduler.sync() — ~15 lines. Plus the tasks board with Overdue / Today / upcoming bands. |
| `slide-17.png` | 17 — Workspace Service & the AI Bot | live | 16/10 | Type: 'Create a high priority task for Karim…' → then the task appearing on the board. The strongest 15 seconds in the deck. |
| `slide-18.png` | 18 — Chat, Notifications & Rooms | live | 16/9 | Terminal: the Mongo query returning vo1:<iv>:<ciphertext>. Ten seconds, and it ends the argument. Plus the RabbitMQ event flow diagram. |
| `slide-19.png` | 19 — Observability: Knowing When It Breaks | shot | 16/9 | The Grafana dashboard — Virtual Office — Logs & Errors. Filter to one service live so it's obviously real. |
| `slide-20.png` | 20 — Mobile: Why Flutter, and What We Chose to Build | shot | 9/16 | Phone frames: login · channels · chat. A real device beats an emulator. |
| `slide-21.png` | 21 — Mobile: Architecture | diagram | 4/3 | The folder tree (lib/features/chat/...) beside: Screen → Provider → Repository → ApiClient → Gateway. |
| `slide-22.png` | 22 — Mobile: Real-Time & Notifications | live | 16/10 | Two devices. Send on one, land on the other, background it, show the notification arrive. |
| `slide-23.png` | 23 — Live Demo & Close | live | 16/9 | LIVE DEMO. Log in → chat + thread → assistant catch-up → create a task → walk into the 2D office. Have the backup video ready. |

## Tips
- Seed first: `docker compose --profile seed up seed seed-history` — never shoot an empty workspace.
- Shoot at 2× (e.g. 3200×1800) so it stays sharp on a projector.
- `kind=live` means do it on stage; the file here is your backup if the demo dies.
