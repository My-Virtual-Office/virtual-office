# Virtual Office — Work Split & Presentation Ownership

Team of 6 — **3 backend · 2 frontend · 1 mobile**. Each owns a coherent slice of the project and presents it, so everyone shows clear impact.

---

## Ownership map

### Backend (3)
| # | Owner | Owns (services) | Features | FRs |
|---|---|---|---|---|
| **BE-1** | `[ name ]` | `user-service` · `gateway-api` | Auth, register/login, OTP reset, password hashing, profiles + avatars; the edge — JWT validation, header injection, ticket-based WebSocket auth | 01–07, 40 |
| **BE-2** | `[ name ]` | `workspace-service` · `room-service` | Workspaces, teams, roles, invitations, member directory, desks & presence, the editable 2D map API, session-config; voice/video rooms, media tokens, proximity voice groups | 08–15, 25–28 |
| **BE-3** | `[ name ]` | `chat-service` · `notification-service` | Channels, DMs, threads, mentions, edits, read receipts, typing, idempotent delivery; notifications — domain events → email + in-app + push | 16–24, 34–37 |

### Frontend (2)
| # | Owner | Owns | Features | FRs |
|---|---|---|---|---|
| **FE-1** | `[ name ]` | 2D office — Phaser client + Colyseus server | Avatars, real-time movement (prediction/interpolation), sit/interact, proximity voice/video UX, in-world chat, map rendering | 29–33 |
| **FE-2** | `[ name ]` | Web client — React | Workspace/channel/DM/thread UI, room calls (Agora), notification centre, map-editor UI | 38, 13 (UI) |

### Mobile (1)
| # | Owner | Owns | Features | FRs |
|---|---|---|---|---|
| **MO-1** | `[ name ]` | Mobile app — Flutter | Messaging, optimistic delivery, read receipts, threads, cross-state push, Provider state, dual-transport repository | 39 |

---

## Presentation running order (~15 min · 6 presenters ≈ 2 min each)

**Shared open** — *[Presenter A]*
1. Title + **Team & roles**
2. The Problem
3. The Solution + pillars
4. Scenario (screenshots)
5. System Overview

**Per-person blocks** — each presents their own slice:
6. **BE-1** — Identity & the Gateway
7. **BE-2** — Workspaces, Rooms & Proximity
8. **BE-3** — Messaging & Notifications
9. **FE-2** — Web Client
10. **FE-1** — 2D Virtual Office *(visual peak)*
11. **MO-1** — Mobile App

**Shared close** — *[Presenter B]*
12. Evaluation
13. Lessons + Future Work
14. Conclusion + Q&A

---

## Notes
- **Order logic:** backend foundation → web → office (save the visual wow) → mobile.
- **Speaking balance:** give the intro (5) and close (3) to two *different* people (e.g., FE-2 opens, BE-1 closes) so all six speak beyond their block.
- **Assumption:** the Colyseus server sits with FE-1 (built the game). If a backend dev built it, move it to BE.
- Slot too tight for 6 handoffs? Merge intro+close to one MC and give each dev exactly 1 slide.

---

# Valuable points — what each team shows

## 🖥 Backend team (3)
- **Real microservices** — 6 independent Spring Boot services, each with its own database (no shared schema).
- **Security in one place** — the gateway validates the JWT once and injects trusted identity headers; every service trusts the edge.
- **Ticket-based WebSocket auth** — solved the "sockets can't carry headers" problem with short-lived Redis tickets — one recipe reused by all three clients.
- **Event-driven & resilient** — services talk through a RabbitMQ event bus, not direct calls; delivery is idempotent, so retries never duplicate.
- **Proximity voice engine** — computes who-hears-whom from avatar positions and mints media tokens **without ever carrying the media**.
- **Complete messaging backend** — channels, DMs, threads, mentions, edits, read receipts, typing, idempotency — the `{action, payload}` envelope.
- **Rich org model** — workspaces, teams, roles, tokenized invitations, an editable 2D map, and an internal API that drives the office.
- **Unified notifications** — one service turns domain events into email + in-app + push.
- **Polyglot persistence** — MySQL, PostgreSQL, MongoDB, Redis — the right store for each job.

## 🎮 Frontend team (2)
- **Real-time multiplayer office** — Phaser + an **authoritative Colyseus server**: the server owns the truth, the client predicts and interpolates.
- **Smooth motion at scale** — client-side prediction keeps your avatar instant; remote interpolation smooths everyone else.
- **Proximity-driven media UX** — voice/video/screen-share start and stop automatically as avatars move — no dialing, no hanging up.
- **A living world** — sit on chairs, use computers & whiteboards, per-person desks, in-world chat bubbles.
- **Full Slack-style web client (React)** — workspaces, channels, DMs, threads, mentions, edits.
- **Three concurrent real-time channels** — separate STOMP connections for chat, presence, and notifications.
- **Voice/video room calls** — powered by Agora, with live mute/camera/screen-share state.
- **Live notification centre** and a **map-editor UI** on top of a React + Redux overlay.

## 📱 Mobile team (1)
- **Cross-platform Flutter app** bringing the messaging experience to phones.
- **Dual-transport repository** — one data layer speaks both REST and the real-time socket; the UI never knows which.
- **Optimistic delivery** — messages appear instantly and reconcile with the server, so it feels fast on flaky networks.
- **Read receipts & threads** — matching the web's semantics.
- **Cross-state push notifications** — delivered in foreground, background, **and** terminated states (genuinely hard on mobile).
- **Provider-based state management** with a clean, testable architecture.
