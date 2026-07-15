# Virtual Office — Defence Deck (23 slides)

English translation of `flow.md`, restructured into 22 slides.
(17 was the target. Observability plus three splits — AI/Desk, Identity/Tasks, and Mobile ×3 — took it to 22. See "If 22 is too many".)
Each slide: **Who** presents · **Say** (talking points) · **Show** (visuals).

> ⚠️ **Read "Corrections" at the bottom first.** Three things in `flow.md` don't
> match the code that actually runs. Presenting them as-is invites a question you
> can't answer.

**Team:** Mousa · Rokaya · Sersawy · Nadine · Khalwsh · Khaled Qenawy (Mobile)
**Rule from `flow.md`:** do **not** mention the 2D Plane before slide 9. It is the reveal.

---

## PART 1 — The Story (soft section)

### Slide 1 — Title & Team
**Who:** Mousa
**Time:** ~30s
**How:**
- Don't linger
- Names, roles, one line on the product, then move
- The panel is deciding whether you're organised — brisk says yes
**Say:**
- Project name, one line of what it is: *"a virtual office that puts your people, chat, tasks and meetings in one place."*
- Introduce the team and what each person owned: Frontend, Backend, Mobile.
-  the problem → what we built → how it works → demo.Say the agenda in one sentence:

**Show:** Title, team names + roles, university/supervisor. Keep it clean — no product screenshots yet.

---

### Slide 2 — The Problem
**Who:** Mousa
**Time:** ~1m
**How:**
- The only slide where you're allowed to be human before you're technical
- Slow down on the four pains
- Land the closing line, then **pause for a beat** — silence sells it
**Say:**
- Remote and hybrid work broke something that the office gave us for free.
- Four concrete pains (from our research, not opinion):
  1. You can't tell who is online or available right now.
  2. Constant switching between apps to do one job.
  3. No sense of *being somewhere* with your team.
  4. Conversations, meetings and tasks scattered across different tools.
- Land it with a human sentence: *"You can be in five tools all day and still not know what your team is doing."*

**Show:** A simple visual of the fragmentation — one person surrounded by app logos (Slack, Teams, Zoom, Jira, Google Calendar) with arrows going everywhere.

---

### Slide 3 — Where Existing Tools Fall Short
**Who:** Mousa
**Time:** ~1m
**How:**
- Be genuinely fair to Slack/Teams/Discord — give them their ticks out loud
- Rubbishing them reads as naive
- Conceding their strengths makes the gap you found credible
**Say:**
- We studied the leaders honestly — they are good at what they do:
  - **Slack** — excellent chat, but tasks and meetings live elsewhere; no presence beyond a green dot.
  - **Microsoft Teams** — broad, but heavy, and the pieces feel bolted together.
  - **Discord** — great voice presence, built for communities, not for work.
- The common gap: **none of them give you a workplace.** They give you channels.
- Do **not** mention the 2D plane yet — just plant that "presence" is the missing piece.

**Show:** Comparison table — rows: Chat / Threads / Tasks / Meetings / Presence / One place. Columns: Slack, Teams, Discord, **Ours**. Be fair: give them their ticks.

---

### Slide 4 — Our Solution: One Place
**Who:** Mousa
**Time:** ~45s · **Then hand to:** Rokaya
**How:**
- This is a promise, not a feature list
- Say the workflow sentence (message → task → deadline → meeting), then stop
- **Do not preview the 2D plane**
**Say:**
- We built one product that combines: **people & teams · tasks · meetings · conversations · the workspace itself.**
- The thesis: these aren't five features, they're one workflow. A message becomes a task, a task has a deadline, the deadline becomes a meeting, the meeting happens with the same people.
- Hand over: *"Rokaya will show how we got to this from real user research."*

**Show:** One diagram: a single ring labelled *Workspace* with five segments (People, Chat, Tasks, Meetings, Presence). Still no 2D reveal.

---

### Slide 5 — Research → User Stories
**Who:** Rokaya
**Time:** ~45s
**How:**
- The point is *we didn't guess*
- Quote one real user story word-for-word — more convincing than describing a method
**Say:**
- We analysed Slack, Teams and Discord for strengths and weaknesses.
- We studied what actually goes wrong for remote employees (the four pains from slide 2).
- We turned findings into **user stories**, e.g. *"As an employee returning from leave, I want to catch up on a channel without reading 200 messages."*
- Those stories drove every feature we built — nothing is here because it looked nice.

**Show:** 3–4 real user-story cards, and an arrow: *Research → User Stories → Features*. If you have a persona/journey artefact from Figma, this is where it belongs.

---

### Slide 6 — Core Collaboration Features
**Who:** Rokaya
**Time:** ~45s · **Then hand to:** Sersawy
**How:**
- Go fast — this is table stakes and everyone knows it
- The bridge line is the only sentence that matters: *"this gets us to parity, it doesn't solve the gaps"*
**Say:**
- We started with what every team needs before anything clever:
  1. **Chat** — channels, DMs, public and private.
  2. **Threads** — keep a side discussion out of the main channel.
  3. **Voice calls** — talk without leaving the product.
- Then say the honest bridge: *"This gets us to parity. It doesn't solve the gaps. The next slides are what we added."*

**Show:** Screenshot of the real chat UI — a channel with threads, real names and avatars. Use the seeded demo (Northstar Software) so it looks like a real company, not an empty app.

---

### Slide 7 — Catching Up Without Reading Everything
**Who:** Sersawy
**Time:** ~1m 15s
**How:**
- **Type it live**
- While it's thinking, say the unread-cursor detail — the sentence that separates you from a ChatGPT wrapper
- Then point at the *"based on live data"* caption
**Say:**
- We didn't only build tools for *work*, we built for the *person doing the work*. Two examples — this one and the next.
- The problem: you join a conversation late, or come back from leave to 200 unread messages. Nobody actually reads them. People scroll to the bottom and quietly hope they didn't miss anything important.
- So we let you **ask instead of read**: *"Catch me up — what did I miss?"*
- **The detail worth stressing:** it summarises only what **you** actually haven't read — it uses your real unread position, not "the last 50 messages". The answer is about *your* gap, not a generic recap. And reading it doesn't mark anything read, so your unread badges survive.
- It can't invent anything: the assistant doesn't get a data dump, it calls the same APIs you would, with your own permissions. Every answer says which live data it read.

**Show:** The **Assistant** answering *"Catch me up — what did I miss?"* on a channel with real unread. Point at the caption underneath — *"Based on live data — read your unread messages"* — that's the difference between a summary and a guess. Best done **live**; the seeded workspace has three months of history behind it.

---

### Slide 8 — The Personal Desk
**Who:** Sersawy
**Time:** ~45s · **Then hand to:** Nadine
**How:**
- Short and warm
- End on the bridge line and hand over
- **Don't explain the 2D plane yourself** — it's Nadine's reveal, you'd spend her ammunition
**Say:**
- In a real office, everyone has a desk they make theirs — notes, photos, stickers, a mug. That isn't decoration; it's what makes a place *yours*.
- Remote tools give you a list of channels. Nothing in Slack belongs to you.
- So we built **My Desk**: your tasks, today's agenda pulled from the calendar, sticky notes, a whiteboard, a focus timer — one place that's yours, not the company's.
- Why it matters: **belonging is a feature.** People stay where they feel present.
- **Bridge to Nadine (say it, it sets up the reveal):** *"A desk makes the workspace yours. But a desk on its own is still a room with one person in it — and that's the real problem."*

**Show:** **My Desk** — Today's Agenda with real meetings, tasks, sticky notes, the whiteboard. Use the seeded demo so the agenda is full; an empty desk proves the opposite of your point.

---

### Slide 9 — The Biggest Gap: Human Presence
**Who:** Nadine
**Time:** ~1m 30s
**How:**
- **The moment — slow right down**
- Make them picture a real office *first*: looking up, walking over
- Then show it — walk the avatar live
- Don't apologise for it looking like a game — say the *"not a game"* line with conviction and let it sit
**Say:** *(This is the reveal — slow down here.)*
- The biggest gap isn't features. It's that **you can't see your colleagues.**
- In a real office: you look up, see who's at their desk, walk over, ask a question. It takes five seconds and no one schedules it.
- In Slack: search the person → open a DM → type → wait → maybe call. Spontaneity is gone.
- So we built the **2D Plane** — a virtual office you actually move around in. You can:
  1. See who's in the office, 2. where they are and their status, 3. move around,
  4. walk up to someone and start talking, 5. enter meeting rooms, 6. feel your team is in the same place.
- **The key line:** *"This is not a game and it's not decoration. It's the part that brings back the human interaction the other tools removed."*

**Show:** The 2D office — several avatars, a meeting room, someone's status. **Best option: go live for 20 seconds** and walk your avatar across the floor into a room. A moving demo lands this far harder than a screenshot.

---

## PART 2 — How We Built It (technical section)

### Slide 10 — From Requirements to Interface
**Who:** Rokaya
**Time:** ~45s
**How:**
- Wireframe and final, side by side
- One sentence on principles — don't recite all four, the slide already shows them
**Say:**
- How user stories became real screens.
- Design principles we held to: simplicity, clear elements, features easy to reach, one consistent experience across pages.
- Show the evolution: wireframe → final UI.

**Show:** Figma board — wireframes next to the shipped screen, side by side. The "before → after" is the story.

---

### Slide 11 — Why React.js
**Who:** Rokaya
**Time:** ~1m · **Then hand to:** Nadine
**How:**
- Nobody will challenge React — don't defend it
- Spend the time on reusable components and Axios
- Land the cliffhanger — that *is* the handoff
**Say:**
- **Single Page Application** — navigation is instant, no full page reload.
- **React Router v7** — organised routing across the app.
- **Reusable components** — buttons, forms, modals, cards, navigation built once, used everywhere. Less duplicated code, one consistent look, easier maintenance.
- **Axios** — all HTTP to the backend: login, creating channels, fetching data, creating/updating/deleting tasks. It also gave us one place for error handling and auth tokens.
- **End on the cliffhanger:** *"But HTTP has a limit — you have to ask for data. Messages and notifications need to arrive on their own."* → hands to Nadine.

**Show:** A component tree or a folder screenshot showing reusable components; one Axios interceptor snippet (auth token). Keep code small and readable.

---

### Slide 12 — Real-Time: WebSockets, STOMP & Agora
**Who:** Nadine
**Time:** ~1m
**How:**
- One idea: HTTP you *ask*, WebSocket it *arrives*
- If you can: two browsers and a message landing beats any diagram
**Say:**
- For anything live we use **WebSockets** instead of HTTP polling — one permanent connection, data flows both ways, no repeated requests.
- We use the **STOMP** protocol via `@stomp/stompjs` on top of it.
- What runs on it: new messages appear instantly, conversations update live, user presence, and activity inside the virtual office.
- That same connection gave us **real-time notifications**: new message, task assigned to you, workspace updates, activity that concerns you.
- **Agora SDK** for voice and video — we didn't rebuild WebRTC from scratch; we own the experience (rooms, permissions), Agora owns the transport quality.

**Show:** Diagram: Browser ⇄ WebSocket/STOMP ⇄ Gateway ⇄ Chat Service, with a second line for Agora. If you can, show two browsers side by side and a message landing instantly.

---

### Slide 13 — The 2D Office: Why a Game Engine
**Who:** Nadine
**Time:** ~1m 30s · **Then hand to:** Khalwsh
**How:**
- Densest slide in the deck
- Open with: *"a floor plan with people on it **is** a game loop"*
- **The chat-vs-movement table is the whole slide** — if short on time, cut everything else and keep it
**Say:**
- Slide 9 was the *why*. This is the *how* — and it's the one part of the stack that isn't a normal web app.
- **Phaser 3** — an actual 2D game engine, because a floor plan with people walking on it **is** a game loop: 60fps rendering, a **Tiled** tilemap with collision, sprite animation, a camera that follows your character. Building that from DOM elements would be a fight you lose; Phaser gives it away.
- **Colyseus** — an authoritative multiplayer server. It runs as its **own Node service**, separate from the Spring backend.
- **The question you will be asked — have this ready:** *"You already have WebSockets for chat. Why a second realtime stack?"* Because they are **opposite problems**:
  | | Chat | Movement |
  |---|---|---|
  | Every event matters? | **Yes** — never lose a message | **No** — a late position is *garbage*, drop it |
  | Order matters? | Yes | Only the newest one matters |
  | Store it? | Forever, in MongoDB | Never |
  | Rate | A few per minute | ~60 per second |
  - So: **STOMP + MongoDB** for chat; **Colyseus** for the world. Pushing 60 positions/second through the chat broker would flood it with data nobody keeps. **Different guarantees demand different transports** — that's the answer, and it's a design decision, not an accident.
- **How the world syncs:** the server owns `OfficeState`. `@type` decorators on the schema make Colyseus send **binary deltas** — only what changed, not the whole world. A `Player` carries `x, y, anim, status, floor`; the decorators *are* the network protocol.
- **Multi-tenancy in one line:** `gameServer.define(WORKSPACE, SkyOffice).filterBy(['workspaceId'])` — everyone with the same `workspaceId` lands in the same room, and two companies can never see each other. One line, complete isolation.
- **React and Phaser share the screen:** Phaser renders the canvas; a **React + Redux** HUD draws the UI on top of it. Two rendering systems, one page.
- **Proximity becomes media** — walk up to someone, or into a meeting room, and the call connects (**Agora**, with PeerJS behind the earlier prototype). *That's the slide 9 promise, delivered: you don't dial anyone, you walk over.*
- It works on a phone too — `react-joystick-component` for touch.

**Show:** **Go live.** Walk the avatar across the floor, bump into a wall (collision is instant proof it's a real engine), enter a room, and let the call connect. Second best: the `OfficeState` schema — ten lines of `@type` decorators — beside the office screenshot, and say *"this is the entire network protocol."*

---

### Slide 14 — Microservices Architecture
**Who:** Khalwsh
**Time:** ~1m 30s
**How:**
- Your biggest technical slide — don't rush it
- **Trace one request across the diagram out loud**
- If asked *"why not a monolith?"* — honest answer: a monolith ships faster; we wanted independent deploys and per-service scaling, and the AI service later proved it (zero auth work)
**Say:**
- Instead of one big application, the backend is a set of independent services, each owning one part of the system.
- **API Gateway** — a single entry point for the web and mobile clients; it validates the JWT once at the edge, then routes each request to the right service.
- The services: **User** (accounts + authentication), **Workspace**, **Chat**, **Notifications**, **Calendar**, **Tasks**, **Room**, **AI** — plus a realtime **Office server** for the 2D plane.
- Why it was worth it: separate responsibilities, develop and deploy each independently, easier to test and maintain, scales per service, and one service failing doesn't take the system down.
- Mention the whole thing runs with **Docker Compose** — ~20 containers, one command.

**Show:** **The architecture diagram — your most important technical slide.** Clients → Gateway → services → datastores (MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ). Colour-code by concern. Have this on screen while you talk; don't rush it.

---

### Slide 15 — Identity: Decided Once, at the Edge
**Who:** Mousa
**Time:** ~1m
**How:**
- Strip-then-inject is the whole idea — say it once, clearly, and point at the diagram
- **Don't recite JWT internals** — nobody asked, and it invites a question you don't want
**Say:**
- Registration, login and identity live in **user-service**. Passwords are hashed with **BCrypt** — we never store a password, not even encrypted.
- On login we issue a **JWT (HS256)**, signed with a secret shared only between user-service and the gateway.
- **The gateway is the only place identity is decided.** On every request it:
  1. **validates** the token,
  2. **strips** any `X-User-*` header the client sent — so a client can never claim to be someone else,
  3. **injects** the trusted `X-User-Id / X-User-Role / X-User-Email` from the verified token.
- Downstream services never parse a JWT. They trust those headers *precisely because only the gateway can set them*. That's why there is no auth code duplicated across nine services — and why adding the AI service later cost us zero auth work.
- **Two levels of authorization:**
  - **Account level** (`USER` / `ADMIN`) — from the token.
  - **Workspace level** (`OWNER` > `ADMIN` > `MEMBER` > `GUEST`) — resolved per workspace from your membership. You can be an admin in one workspace and a guest in another; the token doesn't decide that.
- Password reset is **OTP over email** — no reset links to leak or replay.
- **The line:** *"Identity is decided once, at the edge. Every service trusts the gateway and nothing else."*

**Show:** A diagram of strip-then-inject: `Client (X-User-Id: 1 ← spoofed ✗)` → `Gateway [verify JWT · strip · inject]` → `Service (X-User-Id: 64 ✓)`. If asked for code, `AuthGatewayFilter` is ~40 readable lines — the strip is the interesting part, so have it open.

---

### Slide 16 — Tasks & Calendar: The Engineering
**Who:** Mousa
**Time:** ~1m 15s · **Then hand to:** Sersawy
**How:**
- **Skip the CRUD** — create/assign/deadline isn't interesting, and the slide already says it
- Go straight to auto-status and the idempotency flags
- Your best line: *"we only revert if the status still carries our marker"*
**Say:**
- Both are Spring Boot + **Spring Data JPA on PostgreSQL**, each with its own schema. Relational on purpose: tasks and events have real relationships and we query them by assignee, status and date range.
- **Human task numbers.** Tasks are `#42`, not a UUID — `max(taskNumber) + 1` per workspace, so numbers are per-company and someone can say *"take a look at 42"* in chat and be understood. *(Honest trade-off: it's a read-then-write, so under real concurrency it needs the transaction plus a unique constraint to stay safe.)*
- **Event-driven, not blocking.** Assign a task → Task Service publishes an event to **RabbitMQ** → Notification Service consumes it and sends. Task Service never waits for an email. If notifications are down, tasks still work — that's the whole point of the queue.
- **Scheduled jobs** (`@Scheduled`, 60s tick) — this is where the calendar gets interesting:
  - **Task reminders** before a deadline.
  - **Meeting reminders** before an event.
  - **Auto-status** — when a meeting starts we flip your desk to *"In a meeting 📅"*, and revert it when it ends. **Your calendar drives your presence; you never have to tell people you're busy.** That's the feature that ties Calendar to the virtual office.
- **The two details worth stressing — examiners ask about exactly this:**
  1. **Every job is idempotent.** `statusApplied`, `statusCleared` and `reminderSentAt` flags mean a reminder is never sent twice. If a call fails we simply *don't* set the flag, and the next tick retries. No retry queue, no duplicate emails.
  2. **We don't clobber the user.** When a meeting ends we only revert your status *if it still carries our marker*. Set your own status mid-meeting and we leave it alone. A scheduler that overwrites a human's choice is a bug, not a feature.
- Plus the unglamorous parts that keep it honest: `@NotNull` / `@NotBlank` validation at each service edge, enums normalised on input, and space membership checked before you can put a task on someone's board.

**Show:** `AutoStatusScheduler.sync()` — about 15 readable lines: find started meetings → set status → mark applied. Then, if you can, the payoff live: a meeting starts and the avatar flips to *"In a meeting"* on its own. If the timing is risky, show the tasks board (Overdue / Today / upcoming bands, ~60 tasks) plus the RabbitMQ flow instead.

---

### Slide 17 — Chat, Notifications & Rooms
**Who:** Khalwsh
**Time:** ~1m 30s · **Then hand to:** Sersawy
**How:**
- Three services *and* encryption — budget it: ~30s chat/Redis/Mongo · ~20s RabbitMQ · ~40s encryption
- **Run the Mongo ciphertext query live** — ten seconds, and it ends the argument
**Say:**
- **Chat Service** — DMs, channels, threads, group conversations, delivered live.
  - **WebSocket** for instant delivery, no refresh.
  - **Redis** for fast/temporary data: presence, online status, and coordinating between multiple instances of the service.
  - **MongoDB** because messages are non-relational, high-volume, and need flexible storage.
- **🔒 Direct messages are end-to-end encrypted — we can't read them, and neither can our server.**
  - Each browser generates an **ECDH P-256** keypair. The **private key never leaves the device**; only the public half is published.
  - To send a DM we derive a shared secret with the recipient's public key and encrypt with **AES-GCM-256** *in the browser*. MongoDB stores `vo1:<iv>:<ciphertext>` and nothing else.
  - Why the server can't decrypt: ECDH lets two people derive the *same* secret from their own private key and the other's public key. That secret is never transmitted, and we only ever hold public keys.
  - **The trade-off — say this out loud, it's the strongest point on the slide:** we encrypt **DMs only**. Channels stay readable *on purpose*, because search, the three-month history and the AI summaries Sersawy showed on slide 7 all need plaintext. Encrypting everything would have silently broken the catch-up feature from slide 7. **Signal and Slack split exactly the same way** — Signal is E2E with no server-side AI; Slack is server-readable and has both. We chose per-surface rather than pretending.
  - Known limits (own them before you're asked): the key lives in one browser, so no multi-device or key backup; static ECDH means no forward secrecy; and public keys are trust-on-first-use.
- **Notification Service** — email, in-app pop-ups, and real-time.
  - **RabbitMQ** for async communication: when a task is assigned, Task Service publishes an event and Notification Service consumes it. Task Service doesn't wait, and the two services aren't tightly coupled.
  - Templates per notification type (task assigned, meeting soon, added to workspace, new message).
- **Room Service** — meeting and voice rooms, who's inside, joining and leaving, and linking a room to a place in the virtual office. **Agora** provides the call transport; we own rooms and permissions.

**Show:** Two things, in this order:
1. **The encryption proof — do this live, it takes 10 seconds and it is unarguable.** Send a DM in the UI, then run the query below on stage and show the same message as ciphertext straight out of the database. Saying "it's encrypted" is a claim; showing the row is evidence.
   ```bash
   docker compose exec -T mongo mongosh -u root -p rootpassword \
     --authenticationDatabase admin --quiet --eval '
     const d = db.getSiblingDB("chat_service");
     const dms = d.channels.find({type:"DIRECT"},{_id:1}).toArray().map(c=>c._id);
     d.messages.find({channelId:{$in:dms}, content:/^vo1:/}).limit(3).forEach(m => print(m.content));'
   ```
   Backup if the terminal is risky: `node website/e2e-dm-test.mjs` — 9 checks, including that an unrelated key **cannot** decrypt and that tampered ciphertext is rejected. See `ENCRYPTION.md` for the diagram.
2. **RabbitMQ event flow** (Task Service → queue → Notification Service → user), then trigger a live notification if you can.

---

### Slide 18 — Workspace Service & the AI Bot
**Who:** Sersawy
**Time:** ~1m 15s · **Then hand to:** Khalwsh
**How:**
- **Create the task from a sentence, live**
- While it runs, say the context + permissions point — that's the actual content
- The task appearing on the board is the applause moment
**Say:**
- **Workspace Service** — the backbone. It creates the workspace, adds/removes members, splits people into **teams**, manages channels and rooms, sets roles and permissions, and connects people to their tasks, meetings and conversations. It also holds the virtual office layout.
- One place instead of five apps — that's this service's job.
- **AI Bot** — it can summarise a long conversation, pull out the decisions, tell you which tasks were mentioned, answer questions about the workspace, and create tasks and meetings from plain language.
- **Say the hard part out loud (examiners like this):** the real challenge was **context** — giving the model only the data that belongs to this user and this conversation, so the answer is accurate and grounded. We solved it with **function calling**: the model doesn't get a data dump, it calls the same APIs a user would, **using that user's own token** — so it can never see anything the person couldn't see themselves.

**Show:** The Assistant creating a task from a sentence — type *"Create a high priority task for Karim to fix the analytics bug, due Thursday"* → then show the task appearing on the board. **That before/after is the strongest 15 seconds in the deck.**

---

### Slide 19 — Observability: Knowing When It Breaks
**Who:** Sersawy
**Time:** ~1m · **Then hand to:** Khaled Qenawy
**How:**
- **Tell it as a story, not a feature**
- Open with: *"we built the dashboard, and it immediately showed us 200 errors an hour nobody had noticed…"*
- The callback is the punch — say *"the one Khalwsh just showed you"*
**Say:**
- Twenty containers across nine services. When something breaks, *"check the logs"* means nine `docker logs` commands and guessing which one.
- So every container ships its stdout to **Loki** via **Promtail**, and we read it all from one **Grafana** dashboard: errors and warnings per service, log volume, and a searchable stream across the whole system.
- **The line that makes this land — it's a true story, tell it:** the dashboard paid for itself the day we built it. It immediately showed ~200 gateway errors an hour that nobody had noticed from the UI. Following them found a real bug — in the Notification Service Khalwsh just described: a route (`DELETE /{id}`) was also matching `/api/notifications/connect` and swallowing the **WebSocket handshake**, so the real-time notifications you just heard about had been silently broken. The app looked fine. The logs didn't.
- The point for the panel: *"You can't fix what you can't see. Centralised logging is how we found bugs the UI was hiding."*
- If asked why not Prometheus/metrics too: honest answer — logs first, because they told us *what* broke; metrics would tell us *how often*. It's the natural next step.

**Show:** The **Grafana dashboard** (http://localhost:3005 → *Virtual Office — Logs & Errors*), live. Filter to one service to show it's real, not a picture. If you can, show the errors-by-service panel with a real spike in it.

---

### Slide 20 — Mobile: Why Flutter, and What We Chose to Build
**Who:** Khaled Qenawy
**Time:** ~45s
**How:**
- **Own the scope in your first breath**
- Confidence about a deliberate limit reads as judgement
- Hedging reads as a gap you're hiding
**Say:**
- **Flutter** — one codebase, and we ship **Android, iOS and web** from it. For a team our size that's the difference between having a mobile app and not having one.
- **Be upfront about scope — this is a strength, not an apology:** we went **deep on chat** rather than shallow on everything. On the phone you can connect to your workspace, browse channels and DMs, read and send messages, follow threads, and get notified.
- The reasoning: chat is the thing you actually need on a phone. Nobody plans a sprint on a 6-inch screen — but everyone answers a message from one. So we built the part that earns its place in your pocket.
- Tasks, calendar and calls are on the web today. The backend APIs are already there and shared — those are screens we haven't built yet, not architecture we're missing.

**Show:** The app running on a real device or emulator — channels list → open a chat → send a message. If you can, send from the web and let it land on the phone in front of them.

---

### Slide 21 — Mobile: Architecture
**Who:** Khaled Qenawy
**Time:** ~45s
**How:**
- The payoff line: *"same APIs as the web — no mobile backend"*
- Everything else on this slide is supporting evidence for it
**Say:**
- **Feature-first structure**, not type-first: `core/` (theme, constants) and `features/chat/` — and inside that, `api / models / repositories / providers / screens / services / widgets`. Adding "tasks" tomorrow means adding one folder, not touching six.
- **Layered, with one job each:**
  - `chat_api_client` — talks HTTP, knows nothing about the UI.
  - `chat_repository` — the single source of data for the feature.
  - **Providers** — state. We use **Provider** (`ChangeNotifier`) and split it by concern rather than one god-object: `connection`, `channel`, `message`, `thread`, `thread_message`. A new message rebuilds the message list, not the whole screen.
  - **Screens/widgets** — dumb, they render what the provider holds.
- **`shared_preferences`** stores the JWT so you stay signed in.
- **The point to land:** the phone calls **the same backend APIs as the web** — no mobile BFF, no special endpoints, no second auth path. **That's the payoff from slide 13:** because identity is settled at the gateway and services are independent, a second client was almost free.

**Show:** The folder tree (`lib/features/chat/...`) beside a one-line diagram: `Screen → Provider → Repository → ApiClient → Gateway`. Keep it to one arrow chain.

---

### Slide 22 — Mobile: Real-Time & Notifications
**Who:** Khaled Qenawy
**Time:** ~45s · **Then hand to:** the whole team
**How:**
- Two devices: send on one, land on the other
- Background the app, show the notification arrive
- Say *"same STOMP contract as the browser"* **while it's happening**, not before
**Say:**
- The phone speaks the **same realtime protocol as the browser**: **STOMP over WebSocket**, via `stomp_dart_client` — the web uses `@stomp/stompjs`, different language, identical contract.
- **This is the architectural point of the whole mobile section:** we didn't build a mobile realtime stack. We reused the one that already existed. One contract, two clients, and a message published once reaches both.
- **`uuid`** generates a `clientMessageId` on every send — so if the connection drops and a send retries, the server can recognise the duplicate instead of posting your message twice. Idempotency belongs on the client too, not just the server.
- **`awesome_notifications`** raises a real device notification when a message arrives while you're not looking at the screen.
- Honest and forward-looking: voice/video isn't on mobile yet — that's an Agora SDK integration, and Room Service already handles rooms and permissions. It's the next screen, not the next architecture.

**Show:** Two devices side by side — or the web on the projector and the phone in your hand. Send a message on one, watch it land on the other, then background the app and show the notification arrive. **That's the strongest 10 seconds mobile has** — do it live.

---

### Slide 23 — Live Demo & Close
**Who:** All (one driver, one narrator)
**Time:** ~3m
**How:**
- **One driver, one narrator — never both talking**
- Rehearse the exact click path until it's muscle memory
- End on the 2D office, deliver the closing line, then **stop talking**
- Don't trail off into *"so, yeah"*
**Say:**
- Run the story in 2–3 minutes, in this order:
  1. Log in → the workspace is alive (real people, months of history).
  2. Chat + thread → a real conversation.
  3. Ask the Assistant *"catch me up"* → grounded summary.
  4. Create a task from a sentence → it appears on the board.
  5. **Walk into the 2D office** → end on the thing nobody else has.
- Close on the sentence you opened with: *"Your people, your chat, your tasks, your meetings — in one place you can actually walk into."*
- Then: questions.

**Show:** Live app. **Have a recorded video as backup** — wifi fails at exactly the wrong moment.

---

## How to present this

**Total: ~25 minutes** (23 slides, demo included). Check your actual limit — if it's 20, take the cuts listed below *before* the day, not live on stage.

**Five rules:**
1. **Never read the slide.** The panel can read. The slide is the evidence; you are the argument. The **Say** notes are talking points, not a script — say them in your own words.
2. **One voice at a time.** Six presenters means five handoffs — each one is a chance to look disorganised. Each speaker ends with a sentence that *hands over* (they're written in the notes). Practise the handoffs specifically; they're what falls apart.
3. **Live beats screenshots, rehearsed beats live.** Slides 7, 9, 17, 18, 22 and 23 have live moments. Each one needs the exact click path rehearsed. **Record a backup video of the demo** — the wifi will fail exactly once, and it will be on stage.
4. **Seed the demo before you walk in.** `docker compose --profile seed up seed seed-history`. An empty workspace destroys every claim you just made; the Northstar demo has 15 people and three months of history.
5. **Volunteer your limits.** No forward secrecy, mobile is chat-only, `max(taskNumber)+1` races under load. Saying it first reads as command of the material. Getting caught reads as the opposite.

**The four slides that decide your grade:** 9 (the 2D reveal), 14 (architecture), 17 (AI creating a real task), 23 (demo). If you rehearse nothing else, rehearse those.

**Pre-flight, day of:**
```bash
docker compose up -d && docker compose --profile seed up seed seed-history
curl -s -o /dev/null -w "web %{http_code}\n" http://localhost:3001    # 200
curl -s http://localhost:8089/actuator/health                          # {"status":"UP"}
```
Then: log in as `maya.hassan@northstar.io` / `Northstar@2026`, ask the assistant one question to confirm the AI quota is alive, and open the 2D office once so it's warm.

---

## ⚠️ Corrections — `flow.md` vs the code that actually runs

I checked these against the repo. Fix them before you present:

> Correction to an earlier note of mine: I claimed the Flutter app wasn't in the repo. **It is** — `Mobile_application/` (package `virtual_office`, Android + iOS + web). My search missed it.
>
> **But `flow.md` over-claims what the mobile app does, and this one will get you caught.** It says the phone can follow **tasks**, see **meetings and the calendar**, and join **voice/video calls**. None of that exists: `lib/features/` contains **`chat` only** — 0 dart files mention task, calendar, meeting or agora, and there's no Agora dependency in `pubspec.yaml`. What genuinely works: connect, channels, DMs, messages, threads, notifications.
>
> Slides 19–21 are written to the truth, and framed as a deliberate choice ("deep on chat, not shallow on everything") — which is both honest and a better answer than an apology. **Do not read the old mobile list from `flow.md` out loud.** "Show me tasks on the phone" is the easiest question in the world to ask.

| `flow.md` says | Reality | What to do |
|---|---|---|
| **"Security Service"** is a service that handles signup/login/auth | **It does not exist.** There is no `security-service` module. Auth lives in **`user-service`** (`AuthController`), and the **gateway** validates the JWT at the edge. | Don't put a "Security Service" box on the architecture diagram. Present it as a *concern*: "authentication in user-service, enforced at the gateway." If an examiner asks to see the service, you'd have nothing to open. |
| **"NGINX / API Gateway"** | The API gateway is **Spring Cloud Gateway** (`gateway-api`). **NGINX** serves the built frontends and proxies `/api` to it. Two different things. | Say it precisely: "NGINX serves the frontend; Spring Cloud Gateway is the API gateway." Being precise here reads as competence. |
| **"9 services"** incl. Security | Actually deployed: gateway-api, user, workspace, chat, room, notifications, calendar, tasks, **ai**, + skyoffice-server (2D realtime). Plus MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ, Loki/Promtail/Grafana, 2 frontends = **~20 containers**. | Count what's real. "8 business services behind a gateway, plus a realtime office server" is both true and more impressive. |

Also worth knowing:
- `backend/notification-service/` is an **empty leftover** (0 files) next to the real `notifications-service/`. Delete it before anyone browses the repo and asks.
- **`flow.md` never mentions two things you actually built** and that examiners will reward:
  - **End-to-end encrypted DMs** — now on **slide 16**, inside Khalwsh's Chat Service section, where it belongs. It also sets up a deliberate callback to slide 16: encrypting channels too would have broken the AI summaries Sersawy just demoed. Examiners probe for exactly that kind of conscious trade-off.
  - **Observability** — now **slide 17**, its own slide, with the real story of the bug it caught.

## If 22 is too many
The target was 17; Observability plus three splits took it to 22. Cuts, in order of preference:
1. **Merge 2 + 3** (The Problem / Where Existing Tools Fall Short). They're the same argument told twice — the four pains *are* the gaps. One slide: four pains on the left, comparison table on the right. Worth doing regardless of the limit.
2. **Fold 10 into 11** (Figma into React) — "here's the design, here's how we built it." Weaker, because wireframe → UI deserves its own beat.
3. **Merge 5 into 6** (Research → Core Features) — the user stories can be one line above the feature list.
4. **Merge 20 into 19** (Mobile architecture into Why Flutter). Keep 21 (real-time) separate — the "same STOMP contract as the web" point is the whole reason mobile was cheap to build, and it's the only mobile slide with a live moment in it.

All four lands you at 18. For 17, also fold 10 into 11.

Do **not** cut the demo or slide 9 (the 2D reveal). Those are the two slides people remember. And now that 7 and 8 are separate, don't re-merge them — they're different arguments: 7 is about information overload, 8 is about belonging. Together they were one crowded slide making neither point.

## Speaker load
| Person | Slides |
|---|---|
| Mousa | 1, 2, 3, 4, **15 — Identity**, **16 — Tasks & Calendar** |
| Rokaya | 5, 6, 10, 11 |
| Nadine | 9, 12, **13 — 2D engine** |
| Khalwsh | 14, 17 |
| Khaled Qenawy | **20, 21, 22 — Mobile** |
| Sersawy | 7, 8, **18 — AI**, **19 — Observability** |
| All | 23 — Demo |

Mousa carries six, Khaled Qenawy three, Nadine two — but Nadine has slide 9, the 2D reveal — the moment the whole pitch turns on. Load is about weight, not count. If Mousa is stretched, slide 15 is the most natural one to hand to Khalwsh (it is backend engineering, and it pairs with his slide 17).

