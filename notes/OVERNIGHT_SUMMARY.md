# Overnight work — summary, UI/UX recommendations & what's next

Everything below was built, committed (per-feature, so you can roll back any single one),
deployed to your local stack, and — where possible — verified end-to-end. Nothing was pushed
to any remote.

> **Final status:** all requested features shipped. The whole office suite (reserved desks, room
> types, spotlight, knock‑to‑enter, admin room editor), the Google‑Calendar week grid, meeting
> auto‑status, and 1‑click reactions are live. A full‑stack smoke test passed — **all 19 containers
> up and every service (auth, workspace, chat, calendar, tasks, notifications, users, layout) +
> all 3 frontends returned 200.** Auto‑status was verified live (a busy meeting flipped the desk to
> DND / 📅 "In a meeting"). Disk sits at 91% (23 GB free).

---

## 1) What shipped while you slept

### Tasks (ClickUp-style) — NEW `tasks-service` + board
- **Backend** (`tasks-service`, port 8085, Postgres `tasks` schema): full task CRUD, per‑workspace
  sequential `#task-number`, search (`q`), filter by assignee/status, `GET /mine`,
  `GET /by-number/{ws}/{n}`, partial `PATCH` (drag‑move status / reassign). Assignment fires an
  **in‑app notification** to the assignee; due‑soon **task reminders** fire once before the due date.
  *Commits `0869b12`, `22c5b94`.*
- **Frontend** — a **Tasks** sidebar view with two boards: **Today · Tomorrow · Next** (date swimlanes)
  and **Tasks per person**, each with To do / In progress / Complete columns. Drag cards between
  statuses, search, "My tasks" filter, add/edit modal (title, description, status, priority, assignee,
  due date, reminder). *Commit `5368649`.*
- **`#<number>` in chat** renders a clickable task pill → opens the board focused on that task.
  *Commit `b74b382`.*
- **Verified:** create → `#1`, list, PATCH status, `/mine`, task‑number all green.

### Meeting reminders — email + pop-up + attendees
- `calendar-service` events gained `reminderMinutes` + **attendees** (`userId→email`). A scheduler
  publishes a reminder to the **owner and every attendee** once before start.
- `notifications-service` now handles **MEETING_REMINDER** (in‑app **and** email) and
  **WORKSPACE_INVITE** / **TASK_*** types, with branded HTML email templates.
- Web: a **reminder selector** + **attendee picker** in the meeting form.
- **Verified end‑to‑end:** created an event with a reminder → the scheduler fired → an in‑app
  notification was persisted (unread count went to 1) + email dispatched via your Gmail SMTP.
  *Commits `0dec912`, `fc8e55e`.*

### Notification center (live)
- A **bell** (top‑right) with unread badge, a dropdown inbox (mark‑all‑read), and **live pop‑up
  toasts** over a WebSocket. Gateway now routes `/api/notifications/**` and the WS handshake.
  *Commit `fc8e55e`; 1‑based inbox fix `57af35b`.*

### Invitations
- **Invite emails** now actually send: on invite, `workspace-service` publishes `WORKSPACE_INVITE`
  → branded email with the join link. *Commit `858303c`.*
- **Invitations manager** (People → Invitations): list all invites with status, **copy link**, and
  **revoke** (deactivates the link). *Commit `77c25dd`.*
- Fixed the **Invalid invitation** bug — the gateway had no `/api/invitations` route (accept was 404).
  Also fixed the dead **Invite Member** button in the members panel. *Commits `223becd`, `b2bedfd`.*

### Direct messages / chat
- **DM `+`** now opens a **searchable people picker** (name/title/email, presence dots) instead of a
  numeric‑ID prompt. *Commit `f6ccff3`.*
- **Scheduled messages** — a clock in the composer schedules a message for later; a backend
  dispatcher delivers it even if your tab is closed. *Commits `43cd914`, `a127b9d`.*

### Virtual office (SkyOffice)
- **Presence bug fixed** — empty `fullName` made players invisible to others (roster showed "0").
  Names now fall back to `User {id}`, so **everyone sees each other**, plus **join/leave toasts**.
  *Commit `bfebfcc`.*
- **Reserved desks** — "Claim desk here" reserves your spot; you spawn there and others can't sit at
  it ("<name>'s desk — reserved"). *Backend `06e1e03`, client `5b46025`; test fix `fc906d8`.*
- **Room types + zone overlays** — Meeting / Collaboration / Lounge / Focus rooms drawn as labelled
  areas; walking in shows a room banner. Rooms come from the backend layout when set, else sensible
  defaults on the map. *Commit `3b41e9a`.*
- **Spotlight / broadcast** — one presenter at a time (server‑authoritative). A golden ring follows
  the presenter, everyone sees a live "X is presenting" banner, "🔴 Present" toggles it, and
  "Go to stage" jumps the camera. Auto‑released when the presenter leaves. *Commit `3b41e9a`.*
- **Knock‑to‑enter** for private Focus rooms — press **K** (or the banner button) to knock; occupants
  get an Admit/Decline card; admit unlocks the room for you. *Commit `3b41e9a`.*
- **Admin room/layout editor** — admins get an "🛠 Edit rooms" side panel to add / rename / retype /
  delete rooms and **drag them in the office** (live preview), persisted to the backend layout so
  everyone sees the same rooms. *Commit `f4ad527`.*
- Earlier: who's‑here roster + follow, emotes bar, presence rings, floating custom‑status labels,
  "Go to my desk", shadows/vignette/smooth camera, subtle proximity voice ring.

### Calendar / meetings — week grid + auto-status
- **Google‑Calendar week grid** — the Meetings modal now has a **Week** view beside List: a 7‑day
  hour grid where you **drag to pick** a meeting's start→end (snaps to 15 min), events render as
  positioned blocks, a red now‑line, and Today / prev / next week nav. The create form (title,
  attendees→emails, reminder) sits alongside and reflects the picked slot. *Commit `97e2a43`.*
- **Auto‑status from meetings** — while your own **busy** event runs, your Desk shows **"In a meeting"**
  (DND + 📅); when it ends it reverts to Active — but only if the status still carries our marker, so
  a status you changed by hand is never clobbered. Server‑to‑server via workspace‑service's internal
  API. *Commit `9273c78`.*

### Power-user UX
- **Ctrl/Cmd+K command palette** — jump to channels, people, tasks, and quick actions
  (Tasks / People / Meetings / Enter Office) with keyboard nav. *Commit `f7405a6`.*
- **1‑click quick reactions** — a frequent‑emoji row (👍 ✅ 😂 ❤️ 🎉) on the message hover
  toolbar reacts in one click, beside the full emoji picker. *Commit `28987b7`.*

### Observability
- **Loki + Promtail + Grafana** centralized logging. Promtail ships **every container's** stdout to
  Loki; Grafana (**http://localhost:3005**, admin/admin) has the Loki datasource pre‑provisioned.
  Verified: all 14 services are shipping logs.

---

## 2) How to try the highlights
- Hard‑refresh **http://localhost:3001**.
- **Ctrl/Cmd+K** → command palette.
- Sidebar **Tasks** → add a task, drag it across columns, switch to "Tasks per person".
- In a message type `#1` → task pill; click it.
- **Meetings** → add one with a reminder + invite a teammate.
- **People → Invitations** → create/revoke invites (email is sent).
- **Bell** (top‑right) shows notifications live.
- **Enter Virtual Office** → "Claim desk here"; open a 2nd window to see each other + join toasts.
  - Walk into a room → room banner. Walk into the **Focus Room** while someone's inside → press **K**
    to knock; they get an Admit card.
  - Click **🔴 Present** → everyone sees the "presenting" banner + a golden ring on you; others get
    a "Go to stage" button.
  - As an **admin**, click **🛠 Edit rooms** → add/drag/rename rooms → Save (everyone sees them).
- **Meetings → Week** → drag on the grid to create a meeting; tick "Set me to In a meeting" and your
  office status auto‑flips while it runs.
- **Grafana** http://localhost:3005 → Explore → Loki → `{service="chat-service"}`.

---

## 3) UI/UX recommendations (researched: Slack, Linear, ClickUp, Gather, Huly)

**Already added the #1 pattern** (command palette). Next, in priority order:

**High value / low effort**
1. **Keyboard shortcuts everywhere** — `↑/↓` history edit, `e` edit, `t` thread, `⌘↵` send, `?`
   shortcut cheatsheet. Linear's speed comes from this.
2. **Slash commands** in the composer (`/dm`, `/task`, `/remind`, `/status`, `/away`).
3. **Message hover reactions** with a frequent‑emoji row (you have the ⋮ menu; add 1‑click 👍✅😂).
4. **Unread/mention affordance polish** — a jump‑to‑unread divider you already have; add a
   "N new messages ↓" floating pill and a global "Unreads" view.
5. **Empty states & onboarding nudges** — first‑run tips ("Press ⌘K", "Invite your team").
6. **Optimistic UI** on send/react/status so nothing feels laggy.

**Medium**
7. **Rich text / markdown** in messages (bold, code, lists) + code blocks with copy.
8. **Message actions: pin, bookmark/save, copy link, forward** (you have pin + copy link).
9. **Threads as a first‑class inbox** ("Threads" view of everything you're in).
10. **Presence everywhere** — show the office/away/DND dot on every avatar consistently (partly done).
11. **Global search** across messages + tasks + people (you have per‑surface search).
12. **Density & theme** — a compact mode; you already have multi‑theme.

**Delight**
13. **Drag‑drop file upload** anywhere + paste‑to‑upload (you have the paperclip).
14. **Typing indicators** and **read receipts** in DMs.
15. **Huddle / quick‑call** button in a channel (you have the office for spatial calls).

## 4) Missing features / tricks worth adding
- **Calendar week‑grid view** (drag start→end like Google Calendar) — the meeting form works; the
  visual grid is the polish.
- **Task ↔ chat/office deep links** (task → "discuss in #channel", office desk → your tasks).
- **@here / @channel** mentions + notification preferences (mute channel, mute DMs, DND schedule).
- **Guest links** for a single channel or the office.
- **Analytics dashboards in Grafana** (now that logs flow): error rates, message volume, active users.
- **Auth hardening for prod** (rotate the committed JWT/Agora/Gmail secrets in `.env`).

## 5) Big items — now DONE (were previously deferred)
All three large items from the earlier plan are now built, committed, and deployed:
- ✅ **Admin office layout/room editor** — add/rename/retype/delete + drag rooms, persisted via the
  backend layout (`PUT /layout`). *Commit `f4ad527`.*
- ✅ **Room types + knock‑to‑enter + spotlight** — room zones with types, private‑room knock/admit,
  and one‑to‑all spotlight broadcast. *Commit `3b41e9a`.*
- ✅ **Calendar auto‑status from meetings** — "In a meeting" during busy events, marker‑safe revert.
  *Commit `9273c78`.*

### Still open / nice-to-have (not yet built)
- **Backend‑driven map** — the office still renders the bundled Tiled map; rooms are logical overlays
  on top. Fully switching to `mapBuilder.ts` (backend tiles) is optional polish.
- **Private‑room voice isolation** — knock currently gates access + shows banners; wiring it to
  room‑service so a private room gets its own Agora channel is the deeper follow‑up.
- **UI/UX polish backlog** in §3 (keyboard shortcuts, slash commands, 1‑click reactions, threads
  inbox, global search, optimistic UI).
