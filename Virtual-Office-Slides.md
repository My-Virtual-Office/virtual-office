# Virtual Office — Graduation Defense Deck

> **Working document.** We refine the content here in Markdown. When it's final,
> I regenerate `Virtual-Office-Deck.html` from it.
>
> - Each slide has **On slide** (the bullets that appear) and **Talk track** (what you say — not shown).
> - `🔸[ ... ]` = a placeholder you need to fill in.
> - Edit freely; tell me what to change and I'll keep both this file and the HTML in sync.

**Deck at a glance:** 22 slides · ~15–20 min defense · HTML (light/dark, offline) · print-to-PDF supported.

---

## Table of contents

| # | Slide | Section |
|---|-------|---------|
| 1 | Title | — |
| 2 | Agenda | — |
| 3 | The Problem | Motivation |
| 4 | Our Solution | The Idea |
| 5 | Objectives & Scope | — |
| 6 | System Overview | Architecture |
| 7 | Architecture & Security | Architecture |
| 8 | Cross-cutting Patterns | Architecture |
| 9 | Backend Microservices | Backend |
| 10 | Communication & Data | Backend |
| 11 | The 2D Virtual Office | Clients |
| 12 | Proximity Communication | Clients |
| 13 | Web Client | Clients |
| 14 | Mobile Client | Clients |
| 15 | Technology Stack | — |
| 16 | Testing & Observability | — |
| 17 | Live Demo | — |
| 18 | Evaluation | Wrap-up |
| 19 | Lessons Learned | Wrap-up |
| 20 | Future Work | Wrap-up |
| 21 | Conclusion | Wrap-up |
| 22 | Thank You / Q&A | — |

---

## Slide 1 — Title

**On slide**
- **Virtual Office**
- An all-in-one, **spatial** team-collaboration platform — one place instead of a dozen apps.
- Tech chips: Microservices · Spring Boot · Phaser · Colyseus · React · Flutter · WebRTC · Agora · RabbitMQ
- Presented by · 🔸[ Your name & team ]
- Supervised by · 🔸[ Supervisor ]
- Department · University · 🔸[ Department, University ] · 2026

**Talk track:** One line — "We built a virtual office: a single spatial place where a remote team works together, instead of juggling a dozen apps."

---

## Slide 2 — Agenda

**On slide**
- Jump-list of the 16 main topics (problem → solution → architecture → clients → evaluation).

**Talk track:** 10 seconds — "Here's the path: the problem, our solution, the architecture, the three clients, then evaluation and what's next."

---

## Slide 3 — The Problem *(Motivation)*

**On slide**
- Remote & hybrid work scattered the workplace across disconnected tools — meetings, chat, tasks, calendars, files.
- This fragmentation erodes the two things a physical office gives a team for free:
- **Presence** — knowing who is around and available right now.
  - *Status dots in five apps don't tell you the room is warm.*
- **Spontaneity** — the ability to walk up to a colleague and just start talking.
  - *Scheduling a call to ask a 20-second question kills the conversation.*
- Existing tools (Slack, Zoom, Gather) each solve a slice — none give a team a single, shared **place**.

**Talk track:** Sell the pain. Everyone has felt tab-fatigue and "should I really book a meeting for this?".

---

## Slide 4 — Our Solution *(The Idea)*

**On slide**
- A digital headquarters your team lives in — the whole working day under one roof.
- **2D virtual office** — avatars move around and fall into proximity voice/video/screen-share the moment they get close.
- **Full collaboration surface** — workspaces, channels, DMs, threads, room calls, live notifications (Slack-style, web).
- **In your pocket** — a Flutter app carries the conversation to phones with push across every app state.

**Talk track:** The one-sentence thesis of the project: presence + spontaneity, recreated online, with the rest of the workday folded into the same place.

---

## Slide 5 — Objectives & Scope

**On slide**
- **Objectives**
  - Give a distributed team a single **place**, not a pile of apps.
  - Recreate **presence** and **proximity conversation** online.
  - Build it as a properly architected, multi-client **real-time** system.
  - Unify identity, workspaces, messaging, rooms & notifications.
- **Scope boundaries**
  - *In:* 2D office, chat, rooms, proximity media, workspaces, notifications — across web, mobile & the game client.
  - *Roadmap:* tasks & calendar services are scaffolded; mobile covers chat first.
  - *Out:* production-grade secret management & platform-wide RBAC (noted honestly as future work).

**Talk track:** Being explicit about scope shows engineering maturity — you know exactly what's done vs. deferred.

---

## Slide 6 — System Overview *(Architecture)*

**On slide** — layered topology diagram:
- **Clients:** 2D Office (Phaser · Colyseus) · Web (React) · Mobile (Flutter)
- **Edge:** API Gateway — single entry · validates JWT · injects identity headers
- **Services (Spring Boot):** User · Workspace · Chat · Room · Notifications · *(Tasks · Calendar — roadmap)*
- **Data & messaging:** MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ (event bus)

**Talk track:** "Three clients, one gateway, a fleet of small services, each with its own database." Point at the diagram top-to-bottom.

---

## Slide 7 — Architecture & Security

**On slide**
- The gateway is the single front door. Microservices style so each concern scales independently behind one edge.
- **Edge-validated identity** — gateway verifies the JWT once, then injects trusted headers `X-User-Id` / `X-User-Role` / `X-User-Email` that services trust.
  - *Auth logic removed from five services at a stroke; the edge strips spoofable headers.*
- **Per-service databases** — no shared schema; services cross-reference by stored foreign keys.
- **Internal API** — server-to-server calls (office server → workspace) bypass the public edge, guarded by `X-Internal-Token`.

**Talk track:** The "validate once at the edge, everyone downstream trusts it" pattern is a highlight — expect a question on header spoofing; the answer is the edge strips them.

---

## Slide 8 — Cross-cutting Patterns

**On slide** — four cards:
- **Ticket-based WebSocket handshake** — sockets can't carry auth headers, so clients trade a short-lived Redis ticket for a connection. One recipe, every client.
- **The `{action, payload}` envelope** — every real-time message shares one shape, so each client needs only one dispatch loop.
- **Event-driven side effects** — services emit events onto RabbitMQ instead of calling each other; delivery is idempotent.
- **Polyglot persistence** — relational for workspaces, documents for messages, Redis for ephemeral presence & tickets.

**Talk track:** These four decisions are what makes the system *coherent* rather than five apps in a trench coat. This is the "engineering depth" slide.

---

## Slide 9 — Backend Microservices *(Backend)*

**On slide** — service cards (⚠️ verify ports — see note at bottom of file):
- **Gateway API** `:8080` — single entry; routes, validates identity, propagates headers.
- **User Service** `:8081` — authentication, accounts, JWT issuing. MySQL.
- **Workspace Service** `:8087` — companies, desks, teams, roles, invitations, editable 2D map. PostgreSQL.
- **Chat Service** `:8084` — channels, DMs, threads, mentions, edits, read receipts, typing. MongoDB.
- **Room Service** `:8086` — mints media tokens & computes proximity voice groups; never carries media.
- **Notification Service** `:8082` — transactional e-mail + real-time in-app delivery, driven by events.
- *Roadmap:* `tasks` + `calendar` are scaffolded; notifications already consumes their events.

**Talk track:** Walk the six quickly; dwell on Workspace (the "office model") and Room (proximity brain).

---

## Slide 10 — Communication & Data *(Backend)*

**On slide**
- **Synchronous · internal REST** — direct lookups/validations behind the edge (office server asks workspace for a member's desk & status); guarded by the internal token.
- **Asynchronous · RabbitMQ bus** — side effects flow as `NotificationEvent`s; survives outages; idempotent delivery. Cost: eventual consistency.
- **Polyglot persistence** — MySQL users · PostgreSQL workspace · MongoDB messages · Redis presence & tickets.

**Talk track:** "Synchronous when you must, asynchronous when you can." The trade-off (resilience vs. immediacy) is a good thing to say out loud.

---

## Slide 11 — The 2D Virtual Office *(Clients — SkyOffice)*

**On slide**
- Built on **Phaser** with an **authoritative Colyseus** server — server owns the truth, client predicts and interpolates.
- Avatars walk a tile-mapped office across floors, sit at **per-person desks**, gather at whiteboards.
- **Client-side prediction** keeps your movement instant; **remote interpolation** smooths everyone else.
- **Server-authoritative interactive objects** — computers & whiteboards claimed/released consistently for all.
- A React + Redux overlay renders the UI on top of the game canvas.

**Talk track:** This is the wow-factor slide — ideally back it with a screenshot or live demo. Emphasize "authoritative server" (anti-cheat / consistency).

---

## Slide 12 — Proximity Communication *(Clients)*

**On slide**
- The defining interaction: move near someone and voice/video/screen-share open automatically.
- **Room service computes voice groups** from avatar positions — who hears whom depends on where you stand.
- It **mints short-lived media tokens** but **never carries the media** — audio/video flow peer-to-peer.
- Media transport: **WebRTC** (office client) and **Agora** (web room calls).
- Walk away and the call quietly ends — no hang-up, no scheduling.

**Talk track:** This is the heart of "spontaneity." The clever bit: the backend decides *grouping*, never touches *media*.

---

## Slide 13 — Web Client *(Clients)*

**On slide**
- A **React** SPA delivering the persistent, async half of the platform.
- **Three STOMP connections** — separate live channels for chat, presence & notifications, over the shared ticket handshake.
- **Room calls over Agora** — voice & video meeting rooms.
- **Workspaces & channels** — channels, DMs, threads, mentions, edits.
- **Live notification centre** — in-app alerts the moment backend events fire.

**Talk track:** The "familiar Slack-style" surface — reassures the panel this is a complete product, not just the game.

---

## Slide 14 — Mobile Client *(Clients)*

**On slide**
- A **Flutter** client bringing messaging to phones, with **Provider** for state.
- **Dual-transport repository** — one data layer speaks REST and the real-time socket, hiding transport from the UI.
- **Optimistic delivery** — messages appear instantly and reconcile with the server; feels fast on flaky networks.
- Threads & **read receipts**, matching web semantics.
- **Push notifications across every app state** — foreground, background, terminated.

**Talk track:** "Cross-state push" is genuinely hard on mobile — worth naming as an engineering highlight.

---

## Slide 15 — Technology Stack

**On slide** — grouped tags:
- **Clients:** React · Redux · Flutter · Phaser · Colyseus · TypeScript
- **Real-time & media:** WebSocket · STOMP · WebRTC · Agora · Colyseus rooms
- **Backend:** Java 21 · Spring Boot · Spring Cloud Gateway · Maven · JWT
- **Data & messaging:** MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ
- **Infrastructure:** Docker · Docker Compose · Nginx · one-command stack
- **Observability:** Prometheus · Grafana · Loki · Promtail

**Talk track:** Don't read every tag — say "polyglot on purpose: right tool per job," and let them scan.

---

## Slide 16 — Testing & Observability

**On slide**
- **One-command demo stack** — Docker Compose boots every service, database, the bus and all three clients together.
- **Seeded demonstration data** drives the whole system through a realistic scenario end-to-end.
- **Metrics pipeline** — services expose Prometheus metrics; **Grafana** dashboards visualise them; **Loki + Promtail** centralise logs.
- Testing focused on the critical real-time flows — the ticket handshake, the message envelope, proximity grouping.

**Talk track:** Grafana runs at `localhost:3005` (admin/admin) — mention you can show a live dashboard.

---

## Slide 17 — Live Demo

**On slide**
- Let's step inside the office.
- Two avatars meet → a proximity call opens → a message lands on the phone as a push notification — the system working as one.

**Talk track:** Have a recorded screen-capture ready as a fallback in case the live demo misbehaves. Keep it under ~3 minutes.

---

## Slide 18 — Evaluation *(Wrap-up)*

**On slide**
- **Delivered**
  - Real-time multiplayer office with prediction, interpolation & proximity P2P media.
  - Complete messaging — threads, mentions, edits, read receipts, idempotent delivery — on web *and* mobile.
  - Rich workspace & identity layer with an editable 2D map.
  - Unified notifications spanning e-mail & in-app.
- **Known limitations**
  - Tasks & calendar are unimplemented scaffolds; shared library is a placeholder.
  - Mobile covers chat only; office runs as an integrated demo, not yet fully live in steady state.
  - Some secrets are config defaults; a few web features are partially wired.

**Talk track:** Honesty scores points. State limitations plainly — you clearly understand them, and they map onto the roadmap.

---

## Slide 19 — Lessons Learned *(Wrap-up)*

**On slide** — four cards:
- **Uniform patterns pay compound dividends** — one ticket handshake + one envelope meant each new client needed one recipe and one dispatch loop.
- **Async decoupling buys resilience, costs immediacy** — events survive outages, but clients must tolerate eventual consistency.
- **Security is easiest in one place** — validate identity once at the edge; every service trusts it (edge strips spoofable headers).
- **Fit the store to the data** — relational, document & in-memory stores each simplified the service using them.

**Talk track:** These are *your* engineering takeaways — speak from experience, not the textbook.

---

## Slide 20 — Future Work *(Wrap-up)*

**On slide**
- **Complete tasks & calendar** — largest functional gaps; notifications already consumes their events.
- **Fully integrate the office live** — boot rooms from workspace config, stream positions to the proximity engine in steady state.
- **Broaden mobile** beyond chat — workspaces, rooms, a real JWT login.
- **Harden for production** — secret manager, platform-level RBAC, server-side authorisation.
- **Reliability & observability** — dead-letter queues, presence reaper, distributed tracing & alerting.

**Talk track:** Frame it as "breadth & hardening, not a change of direction" — the architecture already supports all of it.

---

## Slide 21 — Conclusion *(Wrap-up)*

**On slide**
- We rebuilt what an office gives for free: avatars share a live space, conversations begin by proximity, and messaging/rooms/workspaces/notifications surround that space — across web, mobile & a game client over a coherent microservices backend.
- The project proves four very different concerns — a real-time game, a Slack-style chat system, a microservices identity layer, and peer-to-peer media — integrate into **one coherent product**.
- It stands as a demonstration, and as a foundation ready to be carried further.

**Talk track:** Land the plane: restate the thesis (presence + spontaneity) and the proof (four concerns, one product).

---

## Slide 22 — Thank You / Q&A

**On slide**
- Thank you.
- Questions & discussion welcome.
- 🔸[ your.email@example.com ]

**Talk track:** Breathe. Invite questions.

---

## ⚠️ Notes & open questions to resolve

1. **Placeholders to fill:** team names, supervisor, department/university (slide 1), contact email (slide 22).
2. **Service ports — pick one source of truth.** `backend/README.md` lists User `:8081`; `docker-compose.yml` maps User `:8091`. The deck currently uses the README values. Confirm which the panel will actually see, or drop ports from the slide entirely.
3. **Screenshots:** slides 11 (2D office), 13 (web), 14 (mobile), 16 (Grafana) would land harder with a real image. Send images and I'll embed them.
4. **Length:** 22 slides ≈ 15–20 min. If your slot is shorter, candidates to merge/cut: 7+8 (architecture), 9+10 (backend), 19+20 (lessons+future).
5. **Team roles slide?** Some defenses want a "who did what" slide — add one after Title if required.
