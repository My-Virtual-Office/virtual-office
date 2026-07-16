# Virtual Office — Slack-grade Chat & Workspaces: Strong Design Plan

Legend: ✅ exists · 🟡 partial · 🔨 build. Effort: S/M/L/XL.

## Grounding (verified in code by audit)
**workspace-service (Postgres) — membership = `Desk`:**
- `Desk` ALREADY has: `userId, workspaceId, role, isActive, fullName, nickName, **title**, workEmail, phone, **personalImageUrl**, bio, avatarCharacter, timezone, status/statusEmoji/statusCustomText, positionX/Y, isOnline, lastSeenAt, **teamId**, inviteStatus, invitedBy, joinedAt`. → title & team already modeled; **no migration needed**.
- Members list: `GET /api/workspace/{id}/desks` → paginated `DeskResponse` (name, title, teamId, picture, role, presence). ✅
- Teams: CRUD `/api/workspace/{id}/teams` (name, description). Only member link = `Desk.teamId`; **no assign-to-team endpoint**. 🟡
- Roles: `GUEST(0) < MEMBER(1) < ADMIN(2) < OWNER(3)`, `atLeast()`. `WorkspaceAccessGuard.requireRole`.
- Invitations: `POST /{ws}/invitations` (ADMIN), `POST /api/invitations/accept?token`, `/decline`. Accept creates/reactivates a Desk. Invite carries email+role (**no teamId, no name**). 🟡
- Workspace create: makes OWNER desk + fires `WORKSPACE_CHANNEL_CREATE` (payload: workspaceId, name, ownerId, members=[ownerId]).
- `GET /api/workspace/mine` = every workspace the caller has an active desk in.

**user-service (MySQL):** `GET /api/users` (id, firstName, lastName, email — **no pictures**), `GET /api/users/me`, `/me/photo` (self only). **No get-by-id, no batch, no photo-by-id.** Titles/teams are NOT here (they're on Desk).

**chat-service (Mongo):**
- `Message`: channelId, senderId, senderRole, content, type(TEXT/SYSTEM), threadId, replyToId, mentions[], deleted, clientMessageId, timestamps. No reactions/pins/attachments/edited-flag.
- `Channel`: name, type(GROUP/DIRECT/ROOM), workspaceId, **flat members[]**, dmKey, canonical, createdBy. **No visibility/allowedTeams/allowedPersons/moderators.**
- Threads ✅ (one level). Mentions stored-only 🟡. Read cursor forward-only (no mark-unread) 🟡. Reactions/pins/permalink ❌.
- STOMP in: `/app/chat/send`, `/app/chat/typing`. Events out: `NEW_MESSAGE, EDIT_MESSAGE, DELETE_MESSAGE, TYPING, THREAD_DELETED`. Topics `/topic/channel/{id}`, `/topic/thread/{id}`.
- Default provisioning creates ONE `#general` (canonical). Join is open to any member.

---

# PHASE 0 — Membership, onboarding & workspace URLs (unblocks chat) — S/M
**Goal:** every chat user has a real workspace membership; URL-addressable workspaces.
- 0.1 🔨(S) Frontend: drop hardcoded `workspaceId=100`/`members=[1,2,3]`. Resolve via `GET /api/workspace/mine`; use its id for channel list/create/DM; channel-create `members=[currentUserId]` (backend dedups). *(in progress, paused)*
- 0.2 🔨(M) **Onboarding screen** at `/onboarding` when `/mine` is empty:
  - **Create workspace** → form (name → auto-slug + timezone) → `POST /api/workspace` → becomes OWNER.
  - **Join workspace** → paste invite link/token → `POST /api/invitations/accept?token=` → becomes MEMBER.
- 0.3 🔨(M) **Workspace URL routing**: `/workspace?work_name=<slug>` (React Router). Opening it selects that workspace (match slug from `/mine`); switching workspace updates the URL. Guard: if not a member → onboarding/join.
- 0.4 🔨(S) Rail workspace switcher shows real `/mine` workspaces (logo/initial), click switches + updates URL.
- **DoD:** new account → onboarding → create/join → lands in a workspace → can create channel + send message with no 403.

# PHASE 1 — Workspace initialization: default channels + join feed — M (backend)
- 1.1 🔨(M) Provision **two** default channels on workspace create: `#general` + `#join`. Extend `WorkspaceChannelListener` (or emit two events / a multi-channel create) so both are canonical-tagged per workspace. Backfill idempotently.
- 1.2 🔨(M) **Join announcements**: when `memberAdded` fires (invite accept), chat-service posts a `SYSTEM` message ("X joined the workspace") to `#join` (and optionally `#general`). Needs the joiner's display name (from Desk.fullName via a lookup or carried in the event).
- 1.3 🟢(S) optional `#random`.
- **DoD:** creating a workspace shows `#general` + `#join`; a new member triggers a visible "joined" message.

# PHASE 2 — People & Teams panel — S/M (mostly wiring)
**Backend (small):**
- 2.1 🔨(S) `PUT /api/workspace/{id}/members/{userId}` (ADMIN) → set `role`, `title`, `teamId` on a Desk (admin management + assign-to-team). Reuses `WorkspaceAccessGuard.requireRole(ADMIN)`.
- 2.2 ✅ Member list `GET /{id}/desks`, Teams CRUD `GET/POST/PUT/DELETE /{id}/teams` already exist.
- 2.3 ⚖️ Names/pictures come from **DeskResponse** (`fullName`, `personalImageUrl`) — **no user-service batch needed** (fallback to initials avatar when empty).
**Frontend:**
- 2.4 🔨(M) Replace dummy MembersList with **People & Teams** panel, tabs **People | Teams**:
  - People: cards = avatar, name, **title**, **team chip**, role badge, presence dot (isOnline).
  - Teams: fetch teams; group desks by `teamId`; each team section lists its people + an **Unassigned** group.
  - Admin (role ≥ ADMIN): **＋ Add person to team** + manage modal (role/title/team) → `PUT .../members/{userId}`. Create/rename/delete teams → Teams CRUD. Keep **Invite Member** (→ invitation flow).
- **DoD:** panel shows real members with title+team+picture; admin can assign a person to a team and it persists.

# PHASE 3 — Channel access control & creation — L (backend + frontend)
**Backend (chat-service Channel + auth):**
- 3.1 🔨(L) Extend `Channel`: `visibility` (PUBLIC/PRIVATE), `allowedTeamIds: List<Long>`, `allowedUserIds: List<Integer>`, `moderatorIds: List<Integer>`. Migration = none (Mongo); add to model/DTO/mapper.
- 3.2 🔨(M) **Access resolution**: a user may access a channel if PUBLIC, OR in `members`, OR in `allowedUserIds`, OR their `Desk.teamId ∈ allowedTeamIds`. chat-service needs the user's teamId/teams → new internal endpoint `GET /api/internal/workspace/{id}/members/{userId}` returning role+teamId (extend `MemberRoleResponse`), called via `WorkspaceClient`.
- 3.3 🔨(M) Enforce on read/post/join (replace flat `isMember` with `canAccess`). Moderators can edit/delete others' messages + manage the channel.
- 3.4 🔨(M) **Create-channel API/flow**: choose visibility + access (all / specific teams / specific persons) + moderators. Expand `CreateChannelRequest` + `createGroupChannel`.
**Frontend:**
- 3.5 🔨(M) Create-channel modal (replaces the simple name prompt): name, description, visibility, access selector (teams/persons/all), moderators.
- **DoD:** an admin creates a private channel scoped to "Backend team"; only backend-team members see/join/post; a moderator can moderate.

# PHASE 4 — Rich chat features — L/XL (split into 4a/4b)
### 4a (core, higher value)
- 4.9 🔨(S, FE) **Day grouping**: date dividers between days + collapse consecutive same-author messages (Slack style). MessagesList only.
- 4.1 🔨(L) **Emoji reactions**: `Message.reactions: Map<emoji, List<userId>>`; REST `POST/DELETE /messages/{id}/reactions`; new WS event `REACTION`; picker + counts in UI.
- 4.3 🔨(M) **Threads UI**: right-side thread panel using existing thread endpoints (`/channels/{id}/threads`, `/threads/{id}/messages`); reply composer; unread per thread.
- 4.8 ✅ Delete message (works).
### 4b (secondary)
- 4.5 🔨(L) **Mentions**: `@user` / `#channel` autocomplete in composer; server parses content → `mentions[]`; notification via notifications-service; render highlighted; new `MENTION` signal.
- 4.2 🔨(M) **Permalink + @ref**: `GET /messages/{id}` single fetch; "Copy link" → `/workspace?...&msg=<id>`; render `@ref` chips that jump/scroll to a message.
- 4.6 🔨(M) **Mark unread**: allow moving the read cursor backward (relax the forward-only Lua) or store an explicit "unread marker"; "Mark unread" menu item + unread state.
- 4.10 🔨(M) **Pins**: `Message.pinned` + `pinnedBy/at`; `POST/DELETE /messages/{id}/pin`; `GET /channels/{id}/pins`; pinned list UI.
- 4.7 🔨(S) Show **team + title** on message hovercards (uses Phase 2 data).

# PHASE 5 — Admin management panel — M
- 5.1 🔨 Teams: create/rename/delete + which channels a team can access (ties to 3.1 allowedTeamIds).
- 5.2 🔨 Members: change role/title/team (`PUT .../members/{userId}`), remove member (`DELETE /desks/{id}`), invitations list/revoke.
- 5.3 🔨 Channels: edit access + moderators.
- Surface as an **Admin** area (modal or `/workspace/admin`), gated by role ≥ ADMIN.

# PHASE 6 — Panels resize/close ✅ DONE

---

## Sequencing & estimate
`0 → 1 → 2 → 3 → 4a → 4b → 5`. Phase 0 unblocks chat immediately (small). 1–2 are light (foundation exists). 3 and 4 are the bulk (channel access + reactions/mentions/pins). Rough: P0 ~0.5d, P1 ~0.5d, P2 ~1d, P3 ~2d, P4a ~1.5d, P4b ~2d, P5 ~1d.

## Cross-cutting decisions (please confirm)
1. **One team per person** (`Desk.teamId`, already the model) — keep. ✔ recommended.
2. Names/pictures from **Desk** (fullName/personalImageUrl), not a new user-service batch endpoint. ✔ recommended.
3. Workspace URL: `/workspace?work_name=<slug>` (as you asked). ✔
4. Onboarding **choice screen** (create/join) instead of silent auto-create. ✔ recommended (matches Slack).
5. Channel access model: visibility + allowedTeams + allowedPersons + moderators on the **Channel** doc. ✔


---

# Extended Features Roadmap — Phases 7–11

This roadmap continues the existing plan (Phases 0–6: onboarding/desks, chat core, People & Teams, channel access control, mentions/reactions/threads, workspace-admin panel) with 16 verified feature designs, sequenced into five new phases. Every feature below is grounded in load-bearing code that has already been read; the phasing is driven by real cross-dependencies (notification backbone, unwired SkyOffice layout, new microservices) and shared infrastructure (object storage, a search index, schedulers, RabbitMQ producers). The guiding principle throughout: services already own their truth (positions in SkyOffice, zones/desks in workspace-service, messages in chat-service, fan-out in notifications-service), so most work is *extending existing patterns and wiring the gaps*, not rearchitecting.

---

## Sequencing overview (Phases 7–11)

Three cross-cutting prerequisites recur across many features and are pulled forward:

- **Notifications reachability** — the gateway has **no `/api/notifications/**` route** and the website has **no notifications WS client**. Required by: Unified Inbox, Custom status/DND, Saved/reminders, Spatial notifications, Calendar. Built once in **Phase 7**.
- **Unwired SkyOffice layout** — `Game.ts` drops `layout.zones`, `SkyOffice.onCreate` uses hard-coded object loops instead of `config.mapObjects`, and `Player` lacks `userId`/`presence`/`status` schema fields. Shared by every spatial feature; consolidated as **Phase 9 foundations**.
- **New per-service RabbitMQ producers** into the existing type-agnostic `notifications.exchange` — hand-copied enum + publish-after-commit pattern, added incrementally by tasks-service, calendar-service, chat-service, and room-service as those come online.

| Phase | Theme | Features | Key infra introduced | Depends on |
|---|---|---|---|---|
| **7** | Notifications backbone & inbox | 7.1 Unified Inbox · 7.2 Custom status + DND + schedules | Gateway `/api/notifications/**` route + WS carve-out; website notifications STOMP client; generalized NotificationListener (EMAIL_TYPES default-to-in-app) + per-type renderer; `NotificationPreference` model | Phase 2 (names/photos), Phase 5 (mentions accuracy) |
| **8** | Chat message enrichment | 8.1 Attachments · 8.2 Rich text/snippets · 8.3 Sections/favorites/drafts · 8.4 Saved/scheduling/reminders | GridFS (or MinIO) object store; shared `website/src/api/chat.js`; chat-service `@EnableScheduling` + claim-poller | Phase 4 (`isMember`/`canAccess`); 8.4 reminders need Phase 7 |
| **9** | Spatial presence, rooms & interactions | 9.1 Presence · 9.2 Meeting rooms/knock · 9.3 Screen share + whiteboard · 9.4 Find/follow/ping · 9.5 Spatial notifications | SkyOffice `Player` schema fields, `Game.ts` zone consumption, `config.mapObjects` wiring; `whiteboard_snapshot` table; Redis knock state; STOMP `/topic/workspace/{id}/presence` | Phase 2 (member rows); 9.5 needs Phase 7 |
| **10** | New product services | 10.1 Tasks service · 10.2 Calendar & meetings | `tasks-service` (:8085, Postgres) + `calendar-service` (:8083, Postgres) scaffolded from workspace-service; calendar scheduler | Phase 0/2; calendar reuses Phase 9 rooms/`goToZone` + Phase 7 notifications |
| **11** | Platform: search, security, integrations | 11.1 Global search · 11.2 SSO/OAuth + audit + analytics · 11.3 Public API + integrations | Meilisearch + `search-service` (:8090); `audit-service` (:8092) + Prometheus/Grafana; `integrations-service` (:8088) + gateway API-key auth & rate limiting; **platform-role fix** (User.role→JWT claim) | Phase 3 (channel ACL); 11.3 two-way calendar needs Phase 10 |

**Cross-phase notes:** Unified Inbox (7.1) builds the *spine*; its six sources light up as producers land (tasks 10.1, calendar 10.2, spatial-ping 9.4/9.5, mentions/DMs/threads from chat-service). The platform-role gap (real `X-User-Role`) is **owned by 11.2** and is a prerequisite for any platform-admin gating (search admin, integrations admin, analytics). Files/search (11.1 `files` index) is gated on Attachments (8.1). Calendar's "join → spawn into voice zone" (10.2) reuses Phase 9's `Game.ts` zone consumption and room-service voice grouping unchanged.

---

# PHASE 7 — Notifications backbone & unified inbox

## 7.1 Unified Inbox (mentions/DMs/threads/tasks/calendar/spatial)

*Grounding:* notifications-service already has the full inbox spine (`model/Notification.java` Mongo `notifications` with `inbox_idx`/`unread_idx` + unique `eventId`; `InboxController` GET/`unread-count`/PATCH read/read-all/DELETE scoped by `X-User-Id`; generic `NotificationEvent{eventId,type,occurredAt,payload}` off `notifications.exchange`/`routing.key`; WS push `convertAndSendToUser(...,"/queue/notifications", WebSocketEvent("NEW_NOTIFICATION",...))` with ws-ticket). But it hard-codes `TASK_ASSIGNED` in two chokepoints (`NotificationListener.java:47-50` switch, `InAppNotificationService.createFromEvent()`), is **not routed in the gateway**, and no website WS client exists.

### Data model
- **`NotificationType`** — add `MENTION`, `DIRECT_MESSAGE`, `THREAD_REPLY`, `CALENDAR_INVITE`, `SPATIAL_PING` (keep `TASK_ASSIGNED`). Producers keep hand-copied enums (repo convention).
- **`Notification`** — add `category` (enum `MENTIONS|DMS|THREADS|TASKS|CALENDAR|SPATIAL`, derived from `type` at write) and indexed `workspaceId: Long`. Change `inbox_idx` → `{userId:1, category:1, createdAt:-1}`; add `{userId:1, workspaceId:1, createdAt:-1}`.
- **`userId` typing** — `Notification.userId` is `Long`, chat ids are `Integer`; reuse existing `readLong` coercion for all producers.
- **`data` payload per type** (free-form Map for deep-links): MENTION/THREAD_REPLY `{workspaceId,channelId,messageId,threadId,senderId,senderName,preview}`; DIRECT_MESSAGE `{workspaceId,channelId,senderId,senderName,preview}`; TASK_ASSIGNED `{taskId,assignedBy,workspaceId,dueAt}`; CALENDAR_INVITE `{eventId,workspaceId,startAt,roomId?,organizerName}`; SPATIAL_PING `{workspaceId,fromUserId,fromName,deskId?,x,y}`.
- **`NotificationRepository`** — add `findByUserIdAndCategoryInOrderByCreatedAtDesc(...)`; keep `countByUserIdAndReadFalse`; optional `countByUserIdAndCategoryAndReadFalse`.
- **`NotificationRenderer`** strategy keyed by type, replacing the inline task-only title/body in `createFromEvent()`.

### Endpoints / events
- **REST:** `GET /api/notifications?page&size&category=mentions,dms` (add `category` filter; absent → all). Existing `GET /unread-count`, `PATCH /{id}/read`, `PATCH /read-all`, `DELETE /{id}` unchanged.
- **Gateway (prerequisite):** add `Path=/api/notifications/**` → `${NOTIFICATIONS_SERVICE_URL:http://localhost:8082}`; register STOMP `/api/notifications/connect` with a public carve-out for the ws-ticket handshake (mirrors `/api/chat/connect`).
- **WS (reuse):** ws-ticket → connect → subscribe `/user/queue/notifications`; server pushes `WebSocketEvent{action:"NEW_NOTIFICATION", payload:NotificationResponse}` on each insert. Optional `UNREAD_COUNT` broadcast after read-all for multi-tab sync.
- **RabbitMQ producers (one `NotificationEvent` shape per source):**
  - **chat-service** (new `NotificationEventPublisher`, copy `WorkspaceChannelEventPublisher`) from `MessageServiceImpl.sendMessage()` after save: fan one `MENTION` per `mentions[]` id (minus self); if `Channel.type==DIRECT` → `DIRECT_MESSAGE`; if `threadId!=null` → `THREAD_REPLY`. Stable per-recipient `eventId = msg-{messageId}-{type}-{recipientId}`.
  - **tasks-service** → `TASK_ASSIGNED` (already consumed; producer built in 10.1).
  - **calendar-service** → `CALENDAR_INVITE`, `eventId = cal-{eventId}-invite-{userId}` (10.2).
  - **room-service / SkyOffice** → `SPATIAL_PING`, `eventId = ping-{fromUserId}-{toUserId}-{epochSecond}` (9.4).
- **Listener change:** invert `NotificationListener.handle()` to an explicit `EMAIL_TYPES` set, default everything else to `handleInApp` (so future types never silently no-op).

### Frontend (website)
- New `api/notifications.js` (`axiosInstance`): `getInbox({page,size,category})`, `getUnreadCount()`, `markRead(id)`, `markAllRead()`, `remove(id)`.
- New STOMP hook (reuse `ChatPage.js` connect flow) → `/api/notifications/connect`, subscribe `/user/queue/notifications`; on `NEW_NOTIFICATION` prepend + bump badge.
- New `pages/Inbox/InboxPage.js` (`<Route path="inbox">` under `PrivateRoute`): filter rail (All/Mentions/DMs/Threads/Tasks/Calendar/Spatial → `category`), list (unread dot, relative time, title/body), row-click deep-link via `data`, per-row read/delete, "Mark all read".
- Inbox entry + unread badge in `WorkspaceSidebar.js` rail (or `Sidebar.js` search/drafts row), badge from `/unread-count`, live via WS. Theme via `themes.css` vars.

### Dependencies
- **Hard prerequisite (not in Phases 0–6):** gateway route + WS carve-out. Reuses existing `notifications.exchange` topology — no new infra.
- Chat producer needs only chat-service (exists); mention accuracy improves with Phase 5 UI. TASK_ASSIGNED/CALENDAR_INVITE light up when tasks/calendar services scaffold (10.1/10.2). SPATIAL_PING needs 9.4. Independent of Phase 6 admin.

### Effort & DoD
**Effort: L** (generalization S–M, chat producer + gateway/WS wiring M, inbox page + badge M; incremental S per additional producer).
- Sending a message that @-mentions/DMs/thread-replies to B creates exactly one unread `Notification` per event (dedup on per-recipient `eventId`), delivered live over `/user/queue/notifications`.
- `GET /api/notifications?category=mentions` returns only mention-category items; badge stays consistent after read/read-all.
- No cross-user leakage (read/mark/delete another user's id → 404 via `findByIdAndUserId`).
- A new `NotificationType` with no email template routes to in-app by default (covered by test).

---

## 7.2 Custom status + DND + notification schedules

*Grounding:* `Desk` already has `status` (`DeskStatus{ACTIVE,AWAY,DO_NOT_DISTURB,FOCUS_MODE,CUSTOM}`), `statusEmoji`, `statusCustomText` and a working owner-only `PATCH /api/workspace/{id}/desks/{deskId}/status`. **No expiry** anywhere; **no `NotificationPreference`/DND/quiet-hours** model; no `@EnableScheduling`; `Sidebar.js:179` has a commented-out "Set Status" placeholder. SkyOffice `UPDATE_PLAYER_STATUS` is half-wired (server handler forwards `{status,statusEmoji}`, but no client sender, no `statusCustomText`, no `Player` schema field).

### Data model
- **workspace-service (Flyway `V…__status_expiry.sql`):** add `Desk.statusExpiresAt TIMESTAMPTZ NULL` (expose in `DeskResponse`); extend `UpdateStatusRequest` with optional `clearAt`/`clearAfterMinutes`. **Lazy expiry (no sweeper):** in the member/`/me` read path, if `now > statusExpiresAt` return `ACTIVE` + null emoji/text (optionally persist reset on write).
- **notifications-service — new Mongo `NotificationPreference`** (`notification_prefs`, unique `userId`): `{dndEnabled, dndUntil(Instant), quietHoursEnabled, quietStart/quietEnd(LocalTime), timezone, quietDays(Set<DayOfWeek>), mutedTypes(Set<NotificationType>), emailInQuietHours}` + repository.
- **Two-signal model:** the *visible badge* = `Desk.status=DO_NOT_DISTURB`; the *delivery suppression* = `NotificationPreference`. Client keeps them in sync.

### Endpoints / events
- **Set status w/ expiry (extend existing):** `PATCH …/desks/{deskId}/status` accepts `clearAt`/`clearAfterMinutes`; response carries `statusExpiresAt`.
- **Preferences (new, notifications-service, gateway-routed via 7.1):** `GET`/`PUT /api/notifications/preferences` (scoped by `UserContext.currentUserId()`); `POST /api/notifications/preferences/dnd {durationMinutes}` one-shot snooze.
- **Suppression gate (RabbitMQ consumer):** in `NotificationListener.handleInApp`, after `createFromEvent` (**always persist to inbox**) and **before** `push`, call `SuppressionService.shouldSuppressPush(userId,type,now)` (DND / `dndUntil` / timezone+day-aware quiet-hours / `mutedTypes`). Suppressed ⇒ skip WS push only. For `handleEmail`, apply the check *after* the idempotency claim; treat "suppressed" as terminal success (retain claim, no requeue).
- **SkyOffice wire:** add `Network.updateStatus({status,statusEmoji,statusCustomText})`; extend server handler + `PresenceSyncRequest` (+`SessionController`) to carry `statusCustomText`; add `status`/`statusEmoji`/`statusCustomText` to `Player`/`IPlayer` schema for the avatar bubble.
- **No new RabbitMQ topology** — delivery-side logic only.

### Frontend
- **Status picker (website):** new `pages/Chat/Components/StatusPicker/` from the `Sidebar.js` profile footer (replace the commented placeholder + `.user-status`). Emoji via existing `emoji-picker-react`, free-text, preset chips, expiry dropdown (30m/1h/today/custom) → new `api/workspace.js#setStatus`. Render emoji/text in `MembersList.js` + footer.
- **DND + quiet-hours settings:** 4th "Notifications" tab in `SettingsModal.js` (DND toggle + snooze, quiet-hours enable + time pickers + day chips + timezone, per-type mutes) → `GET/PUT /api/notifications/preferences` via new `api/notifications.js`. The DND toggle performs **two writes** (`PATCH status:DND` + preferences).
- **Live receipt:** reuse the Phase 7.1 website notifications STOMP client; DND simply means suppressed frames don't arrive while the inbox still fills.
- **SkyOffice UI:** status Fab in `HelperButtonGroup.tsx` → `network.updateStatus(...)`; render remote bubbles in `OtherPlayer` from new schema fields.

### Dependencies
- Ships after/alongside Phase 2 (`MembersList` real rows). Requires the Phase 7.1 gateway `/api/notifications` route + website WS client. Producers largely stubbed today, so DND is testable via the manual email trigger / seeded events. SkyOffice status live-render shares the `Player` schema additions with 9.1/9.4. No dependency on voice; DND does **not** gate proximity voice in v1 (out of scope).

### Effort & DoD
**Effort: L** (workspace-service S, SkyOffice S, notifications-service M, website M; no scheduler if expiry is lazy).
- Emoji + custom text + "clear after 1h" shows on member row and avatar bubble in both clients, auto-reverts to `ACTIVE` after expiry (lazy read path).
- DND on / inside quiet-hours ⇒ event **persisted to inbox** but **no** WS push; turning off resumes pushes with no lost items.
- `GET/PUT /preferences` round-trips scoped to `X-User-Id`; another user can't read/modify; toggle sets both `Desk.status` and preference.
- DND-suppressed email doesn't send and doesn't consume retry budget; a genuine SMTP failure still releases and retries.

---

# PHASE 8 — Chat message enrichment

*Shared:* all four features introduce/consolidate `website/src/api/chat.js` (the first proper chat axios module) — build it once. 8.1–8.3 are largely independent and can parallelize; 8.4's reminders depend on Phase 7.

## 8.1 File & image uploads in messages (attachments)

*Grounding:* inert UI stubs exist — `MessageInput.js` `Plus` button (no `onClick`), `Message.js:169-185` hard-coded PDF `message.attachment` branch (never populated). The only working upload precedent is `user-service` `uploadPhoto` (multipart, mime+size validation, auth'd binary GET via blob). chat-service `Message.java` has no attachment field, `SendMessageRequest` has `@NotBlank content` (blocks attachment-only). chat-service already has `spring-boot-starter-data-mongodb` ⇒ **GridFS available, no new dependency**; `compose.yml` has no MinIO/S3.

### Data model (chat-service, Mongo)
- **New embedded `model/Attachment.java`** (sub-doc array on `Message`, not a collection): `id` (GridFS key), `name` (sanitized), `mimeType`, `size`, `url` (`/api/chat/attachments/{id}`), `thumbnailUrl?`, `width?`, `height?`.
- **`Message.java`:** add `List<Attachment> attachments` (default empty); on delete, tombstone + enqueue blob cleanup.
- **`MessageResponse` + `DtoMapper`:** map `attachments`.
- **`SendMessageRequest`/`StompSendMessage`:** add `List<String> attachmentIds`; **replace field-level `@NotBlank content` with class-level `@AssertTrue` "content OR attachmentIds non-empty."**
- **GridFS metadata:** `channelId, uploaderUserId, workspaceId, mimeType, width/height, linked` flag. `channelId` is the access-control anchor.
- Keep `MessageType`; attachment presence drives rendering. No Postgres/`Channel` change.

### Endpoints / events
- **`POST /api/chat/channels/{id}/attachments`** (multipart, repeated parts): 403 if `!isMember`; validate size cap (`chat.attachments.max-size`, default 25MB) + mime allowlist; thumbnail + `width/height` for images; persist to GridFS `linked=false`; return `AttachmentResponse`.
- **Send path carries `attachmentIds`** (both REST + `/app/chat/send`): `MessageServiceImpl.sendMessage` resolves ids, verifies blob `channelId` matches (blocks cross-channel reuse), flips `linked=true`, embeds snapshot.
- **`GET /api/chat/attachments/{id}`** + `…/thumbnail` (member-gated via blob-metadata `channelId` → `isMember`): stream bytes with stored `Content-Type` + `Content-Disposition`.
- **WS:** reuse `NEW_MESSAGE` (now with `attachments[]`); no new STOMP type.
- **Storage** behind a `StorageService` interface (GridFS impl now; `MinioStorageService` swap for prod). Thumbnailing via `thumbnailator`/`javax.imageio` (max ~400px). Config: multipart limits, mime allowlist, thumbnail px. **Orphan GC:** scheduled sweep deletes `linked=false` blobs older than N minutes + on message delete.

### Frontend (website)
- New `api/chat.js`: `uploadAttachment(channelId,file,onProgress)`, `fetchAttachmentBlob(url)` (blob → `createObjectURL`, since downloads need the `Authorization` header).
- `MessageInput.js`: wire `Plus` → hidden `<input type=file multiple>`, upload each with progress chips, include `attachmentIds`, allow empty-text send.
- `Message.js`: map over `message.attachments` — `image/*` → bounded thumbnail `<img>` (click → lightbox); else → file-card with mime icon, real name, human size, working blob download.
- `MessagesList.js`: pass `attachments` through on history + `NEW_MESSAGE`.

### Dependencies
- **Phase 4 access control:** upload/download must call the *same* membership predicate (`isMember`/new `canAccess`). Threads already carry `threadId`. Edit preserves attachments; delete GCs blobs. Independent of spatial/onboarding/People. Net-new vs Phases 0–6.

### Effort & DoD
**Effort: L** (≈M backend + M frontend; XL only with MinIO+CDN).
- Member attaches ≥1 file (± text); non-members get 403 on **both** upload and download (same gate as `getMessages`).
- Images render as bounded server thumbnails (click → full); non-images as download cards; all stream via member-gated endpoint (no public URL).
- `MessageResponse` in REST history + `NEW_MESSAGE` includes `attachments[]`; attachment-only messages work.
- Over-cap/disallowed-mime rejected clearly; orphaned + deleted-message blobs GC'd.

---

## 8.2 Rich text formatting (markdown, code, snippets)

*Grounding:* `MessageInput.js` plain `<textarea>`; `Message.js:166` renders `{currentContent}` as a React text node (plain, XSS-safe, no formatting, **no `dangerouslySetInnerHTML`**). `Message.content` is a raw `String`; `MessageType` = `TEXT,SYSTEM`; `MessageServiceImpl.sendMessage:98` stores content **verbatim, no length cap**; send DTOs are `@NotBlank` only (STOMP bypasses bean validation) — the one real backend gap. No markdown library present.

### Data model
- **Keep raw markdown as source of truth** in `Message.content` (no rendered HTML stored).
- Add `ContentFormat format` (`PLAIN|MARKDOWN`, new sends default `MARKDOWN`; **null/legacy → PLAIN**) to `Message`, `MessageResponse`, `SendMessageRequest`, `StompSendMessage`, `EditMessageRequest` + `DtoMapper`.
- **Snippets** without touching delete-rule logic: `type=TEXT`, `format=MARKDOWN`, content = fenced block + optional `snippetTitle`, `snippetLanguage` metadata driving a collapsible card.
- **Size cap:** `@Size(max=12000)` on REST content **and** an explicit length guard in `ChatStompController.handleSendMessage` beside the blank check.

### Endpoints / events
- **No new endpoints/WS/RabbitMQ.** Existing send/edit + `NEW_MESSAGE`/`EDIT_MESSAGE` carry `format`/`snippet*` once DTOs add them. Over-cap ⇒ `400` (REST) / `INVALID_PAYLOAD` on `/user/queue/errors` (STOMP). Server stays a dumb store (no markdown parse/sanitize).

### Frontend (website)
- New `Markdown/MarkdownMessage.jsx`: `react-markdown` + `remark-gfm`; **`rehype-raw` OFF**; `rehype-sanitize` allowlist + protocol restriction (`http/https/mailto`, drop `javascript:`); links forced `target=_blank rel=noopener noreferrer`; fenced code via `rehype-highlight` in an `overflow-x:auto` container with language label + copy button. `format!=='MARKDOWN'` → plain fallback.
- Wire into `Message.js` (replace line 166); render snippet card when metadata present.
- Composer toolbar in `MessageInput.js` (keep `<textarea>`): Bold/Italic/Strike/Link/lists/blockquote/inline+block code that wrap the selection + shortcuts (`Cmd/Ctrl+B/I`, `Cmd+Shift+C`, `Cmd+Shift+7/8`); **Preview toggle** reusing `MarkdownMessage`; `Enter` inserts newline (not send) inside an unclosed ``` fence.
- Wire inert `Plus` → snippet modal (title, language select, code area). Apply toolbar+preview to edit mode too. Theme via `themes.css` vars.

### Dependencies
- **Composes with Phase 5 mentions:** `@user` linkify runs as a remark/rehype AST step (order: sanitize → highlight → mention-decorate), not regex over HTML; `mentions[]` unchanged. Independent of Phases 0–4, pins/reactions, attachments. New npm deps (web only): `react-markdown`, `remark-gfm`, `rehype-sanitize`, `rehype-highlight`. **Out of scope:** SkyOffice in-scene bubble chat stays plain.

### Effort & DoD
**Effort: M** (frontend-heavy; backend = one enum field + two optional strings + one size cap).
- `**bold**`/`_italic_`/`~~strike~~`/lists/quotes/links/inline+fenced code render correctly and round-trip unchanged after reload.
- `<img src=x onerror=…>` / `[x](javascript:…)` render inert (no script, no raw HTML, link neutralized).
- Fenced blocks show highlighting in a scrollable container with working copy; snippet renders as a titled collapsible card; over-cap rejected `400`/`INVALID_PAYLOAD`.
- Toolbar + `Cmd/Ctrl+B/I` wrap selection; Preview matches final; `Enter` in unclosed fence inserts newline; legacy (null `format`) renders plain.

---

## 8.3 Channel sections/folders + favorites + working Drafts

*Grounding:* `Sidebar.js` `.search-drafts` block is pure markup (no handlers); channels/dms are flat `useState` arrays with **hard-coded `workspaceId=100` and member id `1`** despite a real `workspaceId` prop being passed. `MessageInput.js` draft is volatile local state, lost on switch/reload. `usePersistentState(key,initial)` localStorage helper already exists in `ChatPage.js`. Per-`(channel,user)` server state precedent = `ReadReceiptServiceImpl` (Redis) via `ReadReceiptController` scoped by `X-User-Id`.

### Data model (chat-service, Mongo)
- **New `sidebar_layouts`** (one doc per `(userId,workspaceId)`): `sections: List<Section{id,name,collapsed,order,itemIds[]}>`, `favorites: List<String>` (channel/DM ObjectId hex strings, uniform). Unique compound `(userId,workspaceId)` via `MongoConfig.ensureIndexes()`.
- **New `drafts`** (one doc per `(userId,channelId,threadId)`): `{userId,channelId,workspaceId,content,threadId?,updatedAt}`. Unique `(userId,channelId,threadId)` + secondary `(userId,updatedAt desc)`.
- **No change to `Channel`/`Message`** — per-user state stays external (like read cursors). New DTOs + mapper entries.

### Endpoints / events
- New `SidebarLayoutController` + `DraftController` under `/api/chat/**`, scoped by `X-User-Id`:
  - `GET /api/chat/sidebar?workspaceId=` (empty default 200), `PUT /api/chat/sidebar?workspaceId=` (whole-doc replace); optional `POST`/`DELETE /api/chat/sidebar/favorites/{channelId}`.
  - `GET /api/chat/drafts[?workspaceId]`, `PUT /api/chat/channels/{id}/draft {content,threadId?}` (blank content deletes), `DELETE /api/chat/channels/{id}/draft`, optional `GET …/draft`.
- **No RabbitMQ.** **Optional cross-device sync (not MVP):** push `SIDEBAR_UPDATED`/`DRAFT_UPDATED` to `/user/queue/prefs` via `convertAndSendToUser`.

### Frontend
- Extend `api/chat.js` (shared): `getSidebarLayout/putSidebarLayout`, `getDrafts`, `putDraft`, `deleteDraft`.
- **`Sidebar.js` refactor:** pinned Favorites group → collapsible user sections (reuse `ChevronDown`) → uncategorized fallback. Star toggle on hover; create/rename/delete section via `useDialogs().prompt/confirm`; MVP reorder = per-item context menu (no new dep; drag-drop upgrade adds `@dnd-kit/core`). Debounced `putSidebarLayout` mirrored to localStorage. **Fix load-bearing bug:** use the real `workspaceId` prop + `getCurrentUserId()` instead of `100`/`1`.
- **Drafts view:** wire inert `.drafts` row → panel listing channels with drafts (`GET /drafts`), row sets `activeChannel` + restores text; draft dot on sidebar items.
- **Composer (`MessageInput.js`):** hydrate from draft on channel change; debounced `putDraft` on change; `deleteDraft`+clear on send; localStorage mirror. Add a `DraftsContext`/`SidebarLayoutContext` (mirror `DialogProvider.jsx`) rather than deep prop-drilling.

### Dependencies
- **Phase 0 satisfied** but the hard-coded `100`/`1` must be removed first (load-bearing). Orthogonal to Phase 3 (state stays in new collections). Synergy with Phase 4b unread counts (badges in sections). Uses existing `GET /api/chat/dm`. Optional WS sync uses existing `/user/**`; optional drag-drop adds one dep.

### Effort & DoD
**Effort: M–L** (backend M, sidebar M with menu-move / L with drag-drop, drafts S–M, WS sync S).
- Create/rename/delete/collapse sections, move channels **and** DMs, star to Favorites; persisted per `(userId,workspaceId)`, survives reload, never affects other users.
- Composer text preserved per channel across switch/reload; send clears; blank deletes.
- Drafts row lists every channel with a pending draft; click restores text; indicator on sidebar items.
- Deleting a section returns items to uncategorized (never deletes channel/DM); all state scoped by `X-User-Id`.

---

## 8.4 Saved items / bookmarks + message scheduling + reminders

*Grounding:* `Message.java` has no saved/scheduled fields; send flow = STOMP `/chat/send` → `MessageServiceImpl.sendMessage` (`isMember` gate, `clientMessageId` dedupe) → broadcast `NEW_MESSAGE`. **No scheduler anywhere** (no `@EnableScheduling`, no Quartz); chat-service has `RabbitTemplate` + Redis but no producer yet. User pushes today are **sessionId-keyed** (no userId-principal push in chat-service). notifications-service is the reminder-delivery target. `Sidebar.js` `.search-drafts` is the natural "Saved"/"Later" slot.

### Data model (chat-service, Mongo; no `Message` change)
- **`saved_items`**: `{userId:Integer, messageId, channelId, workspaceId, note?, createdAt}`; unique `(userId,messageId)`; list `(userId,createdAt desc)`. Denormalize channel/workspace.
- **`scheduled_messages`**: mirrors `SendMessageRequest` + `{senderId,senderRole(captured), channelId,workspaceId,content,threadId?,replyToId?,mentions[],clientMessageId, sendAt, status(PENDING|SENDING|SENT|FAILED|CANCELLED), sentMessageId?, failureReason?}`. Index `(status,sendAt)` + `(senderId,sendAt)`.
- **`reminders`**: `{userId, messageId?, channelId?, workspaceId, noteText?, remindAt, status(PENDING|FIRED|CANCELLED|DISMISSED)}`. Index `(status,remindAt)` + `(userId,remindAt)`. `Desk.timezone` read client-side; server stores UTC.

### Endpoints / events
- **Saved:** `POST /api/chat/saved {messageId,note?}` (member-gated), `DELETE /api/chat/saved/{messageId}`, `GET /api/chat/saved`, `PATCH …/{messageId} {note}`.
- **Scheduled:** `POST /api/chat/scheduled {channelId,content,sendAt,…}` (rejects past), `GET …?status=PENDING`, `PATCH …/{id}` (while PENDING), `DELETE …/{id}` → CANCELLED.
- **Reminders:** `POST /api/chat/reminders {messageId?,channelId?,remindAt,noteText?}`, `GET …?status=PENDING`, `DELETE …/{id}`.
- **Scheduler** (`@EnableScheduling` on `ChatServiceApplication`; `@Scheduled(PT15S)` DB-poll delayed queue):
  - *Scheduled messages:* atomic `findAndModify(PENDING,sendAt<=now→SENDING)` claim → reuse `MessageServiceImpl.sendMessage` (re-runs `isMember`; FORBIDDEN → FAILED) → **broadcast `NEW_MESSAGE`** identically → SENT + `sentMessageId`.
  - *Reminders:* claim `PENDING,remindAt<=now→FIRED` → publish `NotificationEvent` to `notifications.exchange` with `eventId="reminder-{id}"`, `type=REMINDER`, `payload={assigneeUserId,messageId,channelId,workspaceId,remindAt,noteText}`. New `ReminderEventPublisher` + duplicated wire enum.
- **notifications-service:** add `REMINDER` to `NotificationType` + `handleInApp` branch + a `REMINDER` formatter (deep-link `data`). Delivery = existing inbox + `/user/queue/notifications`.

### Frontend (website)
- Extend `api/chat.js`: `saveMessage/unsaveMessage/listSaved`, `scheduleMessage/listScheduled/cancelScheduled`, `createReminder/listReminders`.
- `Message.js` hover row: bookmark toggle (any message) + "…" overflow "Remind me" (20m/1h/3h/tomorrow/custom via `useDialogs()`).
- `MessageInput.js`: split-Send / clock icon → date-time picker (defaults from `Desk.timezone`) → `scheduleMessage`.
- Replace `.search-drafts` with functional "Saved" + "Later" (scheduled + pending reminders, edit/cancel) as a right drawer in `ChatArea`; click deep-links to `channelId+messageId`.
- Reminder toast/inbox via the Phase 7 notifications WS client; MVP fallback = "Later" panel polls `GET /reminders`.

### Dependencies
- **Reminders delivery depends on Phase 7** (gateway `/api/notifications` route + website WS client) — build once; without it, poll-only fallback. Permalinks/scroll-to-message (Phase 5) needed for jump; minimal scroll-into-view first. Names nicer with Phase 2. Independent of SkyOffice.

### Effort & DoD
**Effort: L** (Saved S/M, Scheduled M, Reminders M/L + the Phase 7 prerequisite).
- Save idempotent (unique `(userId,messageId)`), instant in Saved list, unsave removes, click deep-links; membership enforced.
- Scheduled message delivered within one poll (~≤15s), via normal `NEW_MESSAGE` (correct `senderId/senderRole`), editable/cancellable while PENDING; left-channel → FAILED not crash.
- Reminder fires once (atomic claim + stable `eventId` dedup) with working deep link.
- Multi-instance-safe (atomic `findAndModify`); restart mid-window recovers on next sweep.

---

# PHASE 9 — Spatial presence, rooms & interactions

**Phase 9 foundations (shared, build first):** (a) `Game.ts` consumes `layout.zones` (already fetched in `Bootstrap.launchWorkspace`, dropped in `Game.create()`) for zone render + entry/exit detection + "You are in {zone}" HUD — shared by 9.1/9.2/10.2; (b) `SkyOffice.onCreate` iterates `config.mapObjects` instead of the hard-coded `for(i<5)`/`for(i<3)` loops, keying `Computer`/`Whiteboard` by `MapObject.id` with persisted `roomId` — required by 9.3; (c) `Player` Colyseus schema gains `userId`, `presence`, `statusEmoji`, `status`/`statusCustomText` (used by 9.1/9.4/7.2). These are the "unwired layout" gaps every spatial feature otherwise re-declares.

## 9.1 Spatial presence unified with chat status

*Grounding:* backend presence plumbing is half-built — `UPDATE_PLAYER_STATUS` enum + server handler forwarding `{status,statusEmoji}` to `syncPresence`; `onJoin/onLeave` send online/offline; 30s batch flush; `PresenceUpdate` DTO carries `userId/isOnline/status/statusEmoji/positionX/Y`. workspace-service is the presence store (`Desk` has `isOnline/lastSeenAt/status/statusEmoji/statusCustomText/positionX/Y`; internal `POST …/presence`+`/batch`). `GET /desks` already returns presence but there's **no live push** (`writePresence` emits no event). Zone geometry is in SkyOffice `config.layout.zones`. chat-service already consumes `workspace.exchange` + runs STOMP. Presence CSS tokens exist; `MembersList.js` `.status-dot` is hardcoded. **Gaps:** no client `updateStatus` sender; `Player` schema has no status field; handler forwards raw string not `DeskStatus`.

### Data model
- **Derived `PresenceSignal{OFFLINE,AWAY,AT_DESK,IN_ROOM}` with DND as override** (computed in workspace-service, single source): `!isOnline`→OFFLINE; `DO_NOT_DISTURB`→DND (red, wins); `AWAY`/`FOCUS_MODE`/idle→AWAY; online + in `MEETING_ROOM`/`voiceRoomId` zone→IN_ROOM; else AT_DESK.
- **workspace-service `Desk`:** add `currentZoneId(Long)` + `currentZoneName(String)` (Flyway `Vn__desk_presence.sql`) so IN_ROOM survives a `GET /desks` seed.
- **`PresenceSyncRequest`:** add optional `statusCustomText`, `zoneId`, `zoneName`; `writePresence` persists + computes signal, publishes an event **only when signal/room changes** (dedupe against 30s batch churn).
- **`DeskResponse`:** add derived `presence` + `currentZoneName` (computed in `DeskMapper`).
- **SkyOffice `Player` schema:** `statusEmoji`, `presence` (Phase 9 foundation) for avatar dot/bubble parity.
- **Handler fix:** map client status → valid `DeskStatus` before `syncPresence`, forward `statusCustomText`.

### Endpoints / events
- **No new REST.** Reuse `PATCH …/desks/{deskId}/status`, internal `POST …/presence`+`/batch`, `GET /desks` (now carrying `presence`).
- **SkyOffice server additions (no HTTP):** on each `UPDATE_PLAYER`, compute zone from in-memory `config.layout.zones`; on zone-boundary crossing fire immediate `syncPresence({zoneId,zoneName})` (snappy vs 30s batch); idle detection → `syncPresence({status:'AWAY'})`, clear on movement.
- **New RabbitMQ `PRESENCE_CHANGED`** on `workspace.exchange`, payload `{workspaceId,userId,deskId,presence,statusEmoji,statusCustomText,currentZoneName,lastSeenAt}`, published post-commit from `writePresence`.
- **New STOMP fan-out:** `WorkspaceChannelListener` consumes `PRESENCE_CHANGED` → `/topic/workspace/{id}/presence`. Add carve-out in chat-service `WebSocketSubscriptionInterceptor` authorizing member-of-workspace subscribe (mirror `/topic/channel/{id}`).
- **2D map:** unchanged Colyseus diff — new `Player.presence`/`statusEmoji` auto-replicate.

### Frontend
- **Website:** `api/presence.js` (or extend `GET /desks`) seeds `Map<userId,PresenceSignal>`; `ChatPage.js` subscribes `/topic/workspace/{id}/presence` into a `PresenceContext`; replace hardcoded `MembersList.js` rows with data-driven dots (add `--dnd` red token); show `currentZoneName` sub-label + `lastSeenAt`; same dot in Sidebar DM list + footer; DND setter → `PATCH …/status`.
- **SkyOffice:** `Network.updateStatus(...)` + status Fab in `HelperButtonGroup.tsx`; render dot/emoji over avatars in `OtherPlayer`/`Player` from schema fields; route via `Game.handlePlayerUpdated`.

### Dependencies
- **Phase 2 People** (real member rows to attach dots). Reuses Phase 0 invariants (one room per workspace, desk-per-membership). Zone-derived IN_ROOM reuses the same `Zone` data as 9.2 but derives client-side from `config.layout.zones`, so degrades independently. Optional downstream: DND → notifications gate (7.2). Shares `Player` schema + `updateStatus` with 7.2.

### Effort & DoD
**Effort: L** (M if in-scene dots deferred/chat-only; XL with notifications DND gate).
- Walking into a meeting-room zone flips every member's chat dot to green "In {room}" within ~2s and back on exit — same signal on 2D dot and chat dot.
- DND forces a red dot in sidebar/members/avatar, overrides at-desk/in-room, survives reconnect.
- Closing the tab → grey/offline "Active {lastSeenAt} ago"; idle → AWAY (yellow) after threshold, clears on movement.
- Members panel seeds correct presence on first paint from `GET /desks`, stays live via topic; unauthorized cross-workspace subscribe rejected.

---

## 9.2 Meeting rooms / voice zones (auto-join + knock-to-enter)

*Grounding:* zone model end-to-end (`Zone{type,voiceRoomId,proximityRadius,...}`, internal `GET …/zones`). **Public zone auto-join already works** — `VoiceGrouping.assign()` maps an avatar in a `voiceRoomId` zone to that Agora channel, `ProximityServiceImpl.updatePositions` diffs → `VOICE_GROUP_CHANGED` on `/topic/workspace/{id}/voice`; SkyOffice `VoiceService.ts` reconciles via `AgoraVoice.setChannel` but **passes null token**. Explicit rooms are a parallel system (`Room{agoraChannelName='room-{id}',members[],maxParticipants}`, `/join` Lua-capacity-checked, **mints real Agora token**, `PARTICIPANT_JOINED`, bound chat channel). **Gaps:** zone-voice vs explicit-rooms disjoint; zone joins null-token; **no private/knock/lock**; `Game.ts` never reads `layout.zones`.

### Data model
- **room-service `Room`** (Mongo additive): `visibility(PUBLIC|PRIVATE default PUBLIC)`, `locked(default false)`; `@Indexed` on `agoraChannelName`.
- **Zone↔Room binding:** convention `zone.voiceRoomId == room.agoraChannelName` for MEETING_ROOM; add `roomId` to `ZoneResponse`/`LayoutZone` for REST paths.
- **workspace-service `Zone`** (optional): `private` boolean.
- **Knock state (Redis):** `room:{roomId}:knocks` hash (field=userId, val=requestedAt) + `room:{roomId}:knock:{userId}` ~60s TTL "ringing" window. Approval = existing `Room.members` add (durable). No migration.
- **DTO:** add nullable `token` to `VoiceGroupChange`.

### Endpoints / events
- **Knock REST (new `KnockController`):** `POST /api/rooms/{id}/knock` (active desk; 409 if member, 400 if PUBLIC, 423 if locked) → `KNOCK_REQUESTED`; `POST …/knock/{userId}/approve` (member; calls `addMember` → `ROOM_CHANNEL_ADD_MEMBER`) → `KNOCK_APPROVED`; `POST …/knock/{userId}/deny`; `GET …/knocks`.
- **Lock/capacity:** `PATCH /api/rooms/{id}` gains `locked`; `/join` adds locked→423 before Lua capacity→409.
- **Auto-join enforcement (in `ProximityServiceImpl.updatePositions`, post-`assign`, without changing `VoiceGrouping`'s pure contract):** PUBLIC+unlocked+≤max → keep channel + **mint token** → `VOICE_GROUP_CHANGED`; over max → null overflow + `ROOM_FULL`; PRIVATE/locked non-member → null + `KNOCK_REQUIRED`; member/approved → channel+token.
- **WS events:** `KNOCK_REQUESTED/APPROVED/DENIED` on `/topic/room/{id}`; `KNOCK_REQUIRED`/`ROOM_FULL`/`KNOCK_APPROVED/DENIED` to knocker via `/user/queue/room-knock`.
- **RabbitMQ:** no new topology (approval reuses `ROOM_CHANNEL_ADD_MEMBER`); optional `KNOCK_REQUIRED` notification event for out-of-app alerts.

### Frontend (SkyOffice)
- `AgoraVoice.setChannel(appId,channel,token,uid)` — pass token (closes null-token gap for zone + proximity).
- `VoiceService.ts`: read `mine.token`; subscribe `/user/queue/room-knock`; handle `KNOCK_REQUIRED`/`ROOM_FULL`/`KNOCK_APPROVED`/`KNOCK_DENIED`.
- **`Game.ts` (Phase 9 foundation):** consume `layout.zones`, render zone rects + labels, detect local entry/exit, drive "You are in {zone}" HUD.
- New React surface (gated by `RoomStore`, mounted like `ComputerDialog`): `RoomHud` (banner + participant chips + mute/leave), `KnockOverlay` (on `KNOCK_REQUIRED` → `POST /knock` via `zone.roomId`), `KnockRequestToast` (Approve/Deny).
- **website (admin):** `api/rooms.js` + room/zone admin panel (create MEETING_ROOM zones, bind Room, set visibility/max/locked) as a Phase 6 admin tab.

### Dependencies
- Phase 0 desk gate (enforced). Phase 3 names in knock toasts. **Phase 4 moderator concept** should own "who may approve/lock" rather than "any member". Zone rendering shares the Phase 9 `Game.ts` foundation with 9.1/10.2. Optional notifications-service for out-of-app alerts.

### Effort & DoD
**Effort: L** (backend extends existing patterns; greenfield zone-render + knock UI pushes toward XL if fully polished).
- Public MEETING_ROOM zone auto-joins Agora **with server-minted token**, leaving auto-leaves — two avatars hear each other.
- Private/locked zone does **not** join; entrant gets `KNOCK_REQUIRED`; `POST /knock` broadcasts to occupants; Approve adds to `Room.members` + chat channel + auto-joins on next push; Deny leaves out.
- Capacity holds both paths (409 on `/join`, `ROOM_FULL` on zone auto-join); locked rejects joins/knocks (423) while existing participants stay.
- No regression to `prox-*` voice or explicit-room join/leave; ad-hoc proximity channels now carry tokens.

---

## 9.3 Screen share in rooms + shared whiteboard object

*Grounding:* screen share works but is **PeerJS not Agora** (`Computer{connectedUser}`, no presenter/authorization; `ShareScreenManager.ts`). Whiteboard is an **external iframe to wbo.ophir.dev** (no stroke model, no first-party persistence; `roomId` is random not persisted). Backend primitives in place: `AgoraTokenBuilder` (grants VIDEO), screen-share state reflection round-trips (`STATE_CHANGED`, free-form boolean, no lock), Agora adapter + STOMP signaling, desk role via `JoinValidation.role`, `MapObject{type,roomId,capacity,isActive}` persistence anchor. **Prereq:** the hard-coded `for(i<5)`/`for(i<3)` object loops (Phase 9 foundation).

### Data model
- **Prereq (both halves):** iterate `config.mapObjects`, key `Computer`/`Whiteboard` by `MapObject.id`, set `Whiteboard.roomId = mapObject.roomId`, copy `capacity`.
- **Colyseus schema:** `Computer` add `sharerId(''=free)` + `capacity`; new `Stroke{id,author,color,width,tool(PEN|ERASER|RECT|LINE),points[],seq}`; `Whiteboard` add `strokes: ArraySchema<Stroke>` + `capacity` (ArraySchema diff = sync channel, no iframe).
- **New workspace-service table (Flyway `V__whiteboard_snapshot.sql`):** `whiteboard_snapshot{id,workspace_id,map_object_id FK,room_id,strokes_json JSONB,version,updated_at}`, unique `map_object_id` (durable store; Colyseus is live store). *(CRDT alt: `doc_state BYTEA` for a Yjs route.)*
- **Screen share:** no persisted rows (`sharerId` ephemeral; optional Redis mirror).

### Endpoints / events
- **Colyseus messages:** `REQUEST_SCREEN_SHARE{computerId}` → `ComputerClaimPresenterCommand` (reject if `sharerId` set or role < MEMBER; else set `sharerId`) → `SCREEN_SHARE_GRANTED/DENIED`; `STOP_SCREEN_SHARE` also clears `sharerId`; `WHITEBOARD_DRAW{whiteboardId,stroke}` (server assigns `seq`, auto-broadcast); `WHITEBOARD_CLEAR/UNDO` (CLEAR gated MEMBER+/presenter).
- **room-service:** `POST /api/rooms/screen-token{workspaceId,objectId}` — active-desk + role check, mint token for channel `computer-{wid}-{objId}` with a screen uid; viewers call same for subscribe token.  Optional hardened lock via Redis SETNX + `/app/room/screenshare-request`.
- **workspace-service (internal, `X-Internal-Token`):** `GET /api/internal/workspace/{wid}/map-objects/{id}/whiteboard` (hydrate on `onCreate`, fold into `session-config`); `PUT …/whiteboard{strokes,version}` (optimistic version, debounced flush timer + `onDispose`); `DELETE …/whiteboard`.
- **RabbitMQ:** none required.

### Frontend (SkyOffice)
- Replace `ShareScreenManager.ts` (PeerJS) with `ScreenShareManager.ts` (AgoraRTC screen track, join `computer-{wid}-{objId}` with token, publish; viewers auto-subscribe). Keep `ComputerStore` shape so `ComputerDialog`/`Video.tsx` largely unchanged.
- `ComputerDialog.tsx`: gate Share button (dispatch `REQUEST_SCREEN_SHARE`, enable on GRANTED, hide for GUEST, "X is sharing" when held). Wire senders/listeners in `Network.ts` + `Game.ts` (subscribe `computers` `sharerId` onChange).
- Replace whiteboard iframe with `WhiteboardCanvas.tsx` (`<canvas>` rendering `state.whiteboard` strokes + pointer capture → throttled `WHITEBOARD_DRAW`; toolbar color/width/tool/Undo/Clear; `disableKeys()` already called). Extend `WhiteboardStore.ts` + wire `whiteboards[key].strokes.onAdd/onRemove`.

### Dependencies
- **Hard dependency on `session-config` map-object wiring** (Phase 9 foundation) — do first. Reuses desk role model (GUEST<MEMBER<ADMIN<OWNER, same primitive as Phase 3). room-service token minting exists; only `screen-token` (non-Room channel) is additive. Independent of chat Phases 0–6. Config prereq: `room.agora.app-certificate` for real tokens.

### Effort & DoD
**Effort: L** (Agora migration + lock + token ≈M; first-party whiteboard ≈M–L; XL only for Yjs/`y-websocket`).
- MEMBER+ shares via Agora, appears in the other's dialog; GUEST cannot claim; second Share blocked while `sharerId` held; releases on Stop/leave/disconnect.
- Two users draw simultaneously, strokes appear within one tick; Clear (MEMBER+) wipes both; objects created from `session-config` (no hard-coded loops, persisted `roomId`).
- Whiteboard survives dispose/rejoin (persisted + rehydrated, optimistic `version` prevents lost overwrites).
- No PeerJS path required; backend outage degrades gracefully (live continues, persistence deferred).

---

## 9.4 Find / follow / locate a person + "come to my desk" ping

*Grounding:* live roster `playerNameMap` (Map<sessionId,name>) + sprite registry `Game.otherPlayerMap` (Map<sessionId,OtherPlayer>); `GET /desks` is the full directory (userId/fullName/title/photo/team/positions/isOnline); `MyDesk.positionX/Y` for "come to my desk"; direct-to-one-client relay precedent (`STOP_SCREEN_SHARE` loops `this.clients`); in-world bubble/toast primitives; durable-notification pipeline for offline recipients. **Nothing exists** for search/follow/auto-walk/ping — the key blocker is that clients can't correlate a searched desk (userId) to a live sprite (sessionId).

### Data model
- **`Player` schema — add `userId`** (Phase 9 foundation; set from `auth.userId` in `onJoin`), optional `deskId`. **The key enabler.**
- **New Colyseus message** `COME_TO_DESK_PING` (locate/follow are client-side camera only).
- **Client state:** extend `UserStore` with `userIdToSessionId: Map<number,string>` + `followTargetSessionId`.
- **Durable path (optional):** add `DESK_PING` to `NotificationType`; reuse `Notification.data{fromUserId,fromName,workspaceId,deskX,deskY}`. No new tables.

### Endpoints / events
- **Colyseus (primary):** `client.send(COME_TO_DESK_PING,{targetUserId,deskX,deskY})` → server reverse-scans `sessionToUser`, relays `{fromSessionId,fromUserId,fromName,deskX,deskY}` (identity stamped server-side).
- **Search (reuse):** `GET /api/workspace/{id}/desks?page&size` + optional `?q=`/`?online=true`; small workspaces filter client-side. New `Api.ts getDesks(...)`.
- **Durable ping (optional):** `backend.ts pingDesk(...)` → internal `POST /api/internal/workspace/{id}/desk-ping` → publish `NotificationEvent{type=DESK_PING}` → notifications-service routes to `handleInApp` (deduped by `eventId`). (This is the `SPATIAL_PING` source for 7.1.)

### Frontend (SkyOffice)
- New `PeoplePanel.tsx` (Fab in `HelperButtonGroup.tsx`): merge `getDesks()` with `userIdToSessionId`/`playerNameMap`; search by name/title/team; per-row presence dot + **Locate** (`cameras.main.pan` to sprite, toast if not in office), **Follow** (`startFollow(otherPlayer)`; Stop/ESC → follow self), **Come to my desk** (`network.sendDeskPing(targetUserId)`).
- Wiring: `Network.ts` register `COME_TO_DESK_PING` → React toast + phaser event; expose `Game.locatePlayer/followPlayer/goToDesk`; `goToDesk(x,y)` = teleport (reuse sit-teleport mechanics) + `network.updatePlayer`. Incoming `DeskPingToast.tsx` (Snackbar): "{fromName} wants you at their desk — [Go] [Dismiss]"; Go teleports (consent-based), Dismiss no-ops.
- **website (secondary):** durable ping lands in the Phase 7 notifications inbox.

### Dependencies
- Phase 0 desks (substrate). Richer search benefits from Phase 2. Online/away rides existing presence sync (9.1). Durable cross-surface ping depends on the Phase 7 inbox; live in-office path ships standalone. `Player.userId` is a Phase 9 foundation shared with 9.1.

### Effort & DoD
**Effort: L** (core M; durable path +M gated on inbox; true auto-walk XL — avoided via consent-teleport).
- People panel lists all members with online/offline indicator, name/title filter, distinguishes in-office (live sprite) from not.
- Locate pans within ~1s; Follow tracks; Stop/ESC restores self-follow.
- Come to my desk delivers a toast within ~1s (Colyseus relay); Go teleports, Dismiss no-op; away/offline ping surfaced via notifications (deduped).
- `Player.userId` populated on join; searched userId maps to live sprite with no mismatches across joins/leaves.

---

## 9.5 Spatial notifications

*Grounding:* full notifications consumer pipeline exists (single `switch` chokepoint, Mongo persist + `eventId` dedup, WS push). room-service already **diffs zone transitions** (`ProximityServiceImpl` + `VoiceGrouping.zoneAt`) — a ready-made "who entered which zone" detector; and has a RabbitMQ producer template (`RoomChannelEventPublisher`). SkyOffice owns live desk truth (`latestPosition`, `sessionToUser`, `config.desks` unused server-side; `backend.ts` is HTTP-only, no AMQP). **Gaps:** no preference/DND/throttle/spatial types in notifications-service; gateway doesn't route `/api/notifications/**`; no client consumer.

### Data model
- **`NotificationType`** — add `DESK_VISITOR`, `ROOM_ENTERED`, `MENTION_NEARBY` (consumer-side first, then room-service copy).
- **`NotificationPreference`** (shared with 7.2's model): `{spatialEnabled, muteDeskVisitor/muteRoomEntered/muteMentionNearby, dndUntil, persistSpatialToInbox}` + repo.
- **`Notification.data`** carries `{visitorUserId,visitorName,targetUserId,workspaceId,deskId|zoneId|roomId,locationName,x,y}` (no schema change). Add optional `ephemeral` flag (or push a synthetic non-persisted response) so high-frequency pings don't clutter inbox when `persistSpatialToInbox=false`.
- **SkyOffice in-memory:** per-room `deskOccupants: Map<deskId,Set<userId>>` (rising-edge; no Colyseus schema change).
- **Redis cooldown keys** `spatial:cooldown:{target}:{visitor}:{type}:{loc}` TTL ~300s.

### Endpoints / events
- **Detection → publish:** *desk-visitor/mention-nearby (SkyOffice):* detector on the 2s `startBackendFlush` tick over `config.desks`, radius R, rising edges vs `deskOccupants` → HTTP `POST /api/internal/workspace/{wid}/spatial-events` (new room-service endpoint, `X-Internal-Token`). *room-entered (room-service):* extend `ProximityServiceImpl.diff()` — transition into MEETING_ROOM/TEAM zone → enqueue `ROOM_ENTERED` targeted at other current occupants. Both flow into new **`SpatialNotificationPublisher`** (Redis cooldown SETNX, deterministic `eventId=sha1(type:target:visitor:loc:timeBucket)`) → `notifications.exchange`.
- **notifications-service:** route the 3 types to `handleInApp` (via the EMAIL_TYPES-default-to-in-app inversion from 7.1); before persist/push load `NotificationPreference` and drop if muted/DND/`!spatialEnabled`; ephemeral → skip persist, `push()` directly. Per-type title/body renderer. New `GET/PUT /api/notifications/preferences`.
- **Client WS event:** unchanged `NEW_NOTIFICATION`; discriminate by `type`. **Gateway:** `/api/notifications/**` route (Phase 7 prerequisite).

### Frontend
- **SkyOffice (primary):** `NotificationService.ts` (STOMP `/ws/notifications` + ws-ticket), started in `Bootstrap.ts`; `NotificationStore.ts` + `NotificationToast.tsx`; optional in-scene bubble via `updateDialogBubble`; opt-out toggle in `HelperButtonGroup.tsx` → `PUT /preferences`.
- **website (durable):** `api/notifications.js` + bell/unread badge in `WorkspaceSidebar.js` + inbox dropdown + STOMP live; preferences UI = "Notifications" tab in `SettingsModal.js` (shared with 7.2).

### Dependencies
- **Hard prerequisite: Phase 7** gateway route + WS. Phase 2 for names/photos + TEAM-zone routing. **Extension-point A (unified inbox generalization from 7.1) should land first** — spatial types are the first non-task in-app types and force the cleanup. Phase 5 for `MENTION_NEARBY` (chat-service currently only stores mentions) — scope it last/optional. `ROOM_ENTERED` reuses existing Zone/VoiceGrouping.

### Effort & DoD
**Effort: L** (M for desk-visitor MVP; grows with room-entered/DND/both frontends/gateway/inbox; XL with `MENTION_NEARBY` + full refactor).
- Entering another user's desk radius produces exactly **one** `DESK_VISITOR` per entry (rising-edge + Redis cooldown; loitering/boundary-bounce doesn't re-fire within TTL), as SkyOffice toast when in-office and inbox entry when not.
- Per-type mute / DND suppresses **both** persist and push; non-muted still deliver.
- Duplicate/redelivered events collapse via deterministic `eventId`; offline users get inbox entry on next `GET`.
- `ROOM_ENTERED` notifies current zone occupants (not the entrant) from the existing diff.

---

# PHASE 10 — New product services

*Shared:* both scaffold a new JPA/Postgres/Flyway module from the workspace-service template (package layout, `BIGINT IDENTITY`, enums as `VARCHAR CHECK`, `TIMESTAMPTZ DEFAULT now()`, JaCoCo 90% gate), authorize via a copied `WorkspaceClient.requireRole(...)` against workspace-service's internal role endpoint, and add a gateway route + `dev/compose.yml`/`run.sh` entries + a shared-Postgres DB. Both **produce only** into the existing `notifications.exchange` (no consumer).

## 10.1 Tasks / issues service (ClickUp-basics)

*Grounding:* `backend/tasks-service/` is a bare Maven skeleton (:8085, registered module, no `src/main/java`). workspace-service is the template. Role check = internal `GET /api/internal/workspace/{id}/members/{userId}/role` via the room-service `WorkspaceClientImpl` pattern. **`TASK_ASSIGNED` is already wired end-to-end** in notifications-service (payload `assigneeUserId/assignedByName/taskTitle`) — tasks-service only publishes. Not yet in gateway/`compose.yml`/`run.sh`.

### Data model (new Postgres `tasks`, Flyway `V1__init_schema.sql`)
- **`task`**: `id, workspace_id, team_id?, title, description, status CHECK(TODO|DOING|DONE) DEFAULT TODO, priority CHECK(LOW|MEDIUM|HIGH|URGENT) DEFAULT MEDIUM, assignee_id?, due_date, position INT DEFAULT 0, created_by, created_at/updated_at`. Indexes `(workspace_id,status,position)`, `(workspace_id,assignee_id)`.
- **`task_label`** (child, `ON DELETE CASCADE`, unique `(task_id,label)`); **`task_comment`** (optional).
- Enums `@Enumerated(STRING)`; `ddl-auto=validate`. Fixed 3-value status for MVP (custom columns = later `board_column` table, out of scope).

### Endpoints / events
- **REST (gateway `/api/tasks/**` → `${TASKS_SERVICE_URL:http://localhost:8085}`, `X-User-Id` + role check):** `POST /api/tasks` (MEMBER+, publishes `TASK_ASSIGNED` if `assigneeId`); `GET /api/tasks?workspaceId&status&assigneeId&teamId&page&size`; `GET/PATCH/DELETE /api/tasks/{id}` (PATCH powers card edits **and** drag-drop `{status,position}`; republish `TASK_ASSIGNED` only on new assignee); optional comments endpoints; `GET /api/tasks/health`.
- **RabbitMQ (produce only):** on create-with-assignee/reassignment publish `NotificationEvent{eventId=UUID,type=TASK_ASSIGNED,payload={assigneeUserId,assignedByName,taskTitle}}` after-commit best-effort. Duplicate `NotificationType`/`NotificationEvent` locally.
- **WS (deferred):** live board sync would add STOMP `/topic/workspace/{id}/tasks`; MVP = optimistic UI + refetch-on-focus.

### Frontend (website)
- Route `<Route path="tasks">` under `PrivateRoute`; new `pages/Tasks/`. `api/tasks.js` (`axiosInstance`). Components: `TasksPage` (Board|List tabs), `BoardView` (3 columns, drag-drop → `updateTask{status,position}` optimistic), `ListView`, `TaskCard`, `TaskDrawer`, `CreateTaskDialog`. Assignee/label pickers from `GET /desks`. Tasks Fab in `WorkspaceSidebar.js`.

### Dependencies
- **Hard: Phase 0** (active Desk for role → 403 otherwise). **Soft: Phase 3** (`teamId` nullable, ships without). **Reuses notifications-service unchanged** (feeds the 7.1 TASK_ASSIGNED tab). Independent of chat Phases 1–6. Infra: gateway route, `compose.yml`/`run.sh`, `tasks` DB, `InternalAuthFilter` if any internal endpoints.

### Effort & DoD
**Effort: L** (service-from-template M + Kanban/list UI M; M if comments+drag cut; XL with live STOMP + custom columns).
- MEMBER creates a task → persists + renders in Board and List scoped to workspace; non-member 403 via internal role check.
- Drag between columns → `PATCH{status,position}`; survives refresh in target column/order.
- Assign/reassign publishes exactly one `TASK_ASSIGNED`; assignee gets the existing in-app + WS notification.
- `/api/tasks/**` reachable only with valid JWT; boots under `run.sh` with Flyway-migrated `tasks` DB + passes health.

---

## 10.2 Calendar & meetings (activate calendar-service)

*Grounding:* `backend/calendar-service/` is an empty stub (:8083, registered module, no `src/main/java`). Templates: workspace-service (JPA), room-service `WorkspaceClientImpl` (internal REST client). The voice room to spawn into = `POST /api/rooms` (mints Agora channel + bound chat channel) / `POST /api/rooms/{id}/join` (per-user token). **Zone-voice auto-join already works** (be in zone ⇒ be in zone voice). notifications fan-out reuses `notifications.exchange`. Not routed/harnessed.

### Data model (new Postgres `calendar`, Flyway `V1__init_schema.sql`)
- **`event`**: `id, workspace_id, title, description, start_at, end_at, location, room_zone_id? (workspace Zone id, not FK'd), voice_room_id? (room-service Room id, filled at spawn), organizer_user_id, status CHECK(SCHEDULED|CANCELLED), spawned_at? (start-sweep idempotency), created/updated_at`. Index `(workspace_id,start_at)`.
- **`event_attendee`**: `id, event_id CASCADE, user_id, rsvp CHECK(NEEDS_ACTION|ACCEPTED|DECLINED|TENTATIVE), is_organizer, responded_at`; unique `(event_id,user_id)`.
- **`event_reminder`**: `id, event_id CASCADE, minutes_before, fired_at? (fire-once)`; default 10-min row on create.
- **Cross-service enum add (notifications-service):** `MEETING_INVITE, MEETING_REMINDER, MEETING_STARTING, MEETING_UPDATED, MEETING_CANCELLED, RSVP_UPDATED` routed to `handleInApp` (via the 7.1 EMAIL_TYPES inversion). *(Gotcha: workspace `Long` ids vs room-service `Integer` — cast at the RoomClient boundary.)*

### Endpoints / events
- **Gateway:** `Path=/api/calendar/**` → `${CALENDAR_SERVICE_URL:http://localhost:8083}`. Membership via copied `WorkspaceClient.requireRole(...,MEMBER)`.
- `POST /api/calendar/events{...,attendeeUserIds[],roomZoneId?,reminders?}` (organizer auto-ACCEPTED; publishes `MEETING_INVITE` per attendee); `GET /events?workspaceId&from&to`; `GET /events/{id}`; `PATCH` (organizer only, clears reminder `fired_at`, `MEETING_UPDATED`); `DELETE` (organizer, CANCELLED + `MEETING_CANCELLED` + best-effort room delete); `POST /events/{id}/rsvp{response}` (`RSVP_UPDATED` to organizer); **`POST /events/{id}/join`** (returns `{voiceRoomId,agoraChannelName,zoneId,spawnX,spawnY,deepLink}`, lazily spawns if live, 409/425 if early, 404 if cancelled).
- **Internal calls out:** room-service `POST /api/rooms`; workspace-service member role + zones (validate `roomZoneId`, read `voiceRoomId` + spawn coords).
- **RabbitMQ (produce only):** `MeetingNotificationPublisher` → `notifications.exchange` (copy user-service pattern). **No STOMP** — in-app via notifications `/ws/notifications`; voice via existing `/topic/workspace/{id}/voice` or `POST /rooms/{id}/join`.
- **Scheduler (calendar-service owns):** `@EnableScheduling` + two `@Scheduled(~30s)` sweeps. *Start sweep:* `SCHEDULED AND start_at<=now AND spawned_at IS NULL` → zone with `voiceRoomId` → target that channel (optionally still create a bound Room for participant list/chat); else create ad-hoc Room; set `spawned_at`; publish `MEETING_STARTING` per ACCEPTED/TENTATIVE. *Reminder sweep:* `start_at - minutes_before <= now AND fired_at IS NULL` → `MEETING_REMINDER`, set `fired_at`.

### Frontend
- `api/calendar.js`; `/calendar` route + `pages/Calendar/CalendarPage.js` (month/week grid, RSVP buttons); nav icon in `WorkspaceSidebar.js`. Create-event "Meet in Room" picker filters `layout.zones` to MEETING_ROOM w/ `voiceRoomId`; attendees from `GET /desks`.
- **Meeting-start toast:** reuse the Phase 7 website notifications WS client → `MEETING_STARTING`/`REMINDER`/`INVITE` via `DialogProvider.notify()`; "Join Room A" opens SkyOffice deep link `?token=…&workspaceId=…&goToZone={zoneId}`.
- **SkyOffice `goToZone` hook (Phase 9 foundation):** `Bootstrap.launchWorkspace` reads `goToZone`, passes into `Game.create`; `Game.ts` looks up the zone, `cameras.main.pan` + set position + `network.updatePlayer` → existing `VoiceService`/`VoiceGrouping` auto-connects audio (no new voice code).

### Dependencies
- Phase 0 + Phase 2 (active desks, attendee picker). Zones seeded with `voiceRoomId` for the zone path (ad-hoc path works without). **room-service unchanged** (hard dependency, already built). notifications-service needs the `MEETING_*` enum additions + the Phase 7 website WS client. **SkyOffice `goToZone` shares the Phase 9 `Game.ts` foundation** with 9.2. Orthogonal to chat Phases 0–6.

### Effort & DoD
**Effort: L** (M for events CRUD/RSVP/reminders + M for the room-spawn/teleport killer feature).
- Create persists event+attendees, returns 201, every non-organizer gets `MEETING_INVITE`; RSVP flips status + notifies organizer.
- At start (±one sweep) a zone-linked event resolves to that zone's `voiceRoomId` (ad-hoc auto-creates a Room), every ACCEPTED gets `MEETING_STARTING` + working Join link; Join lands them in the SkyOffice zone with Agora audio auto-connected.
- Reminders fire once per offset (idempotent `fired_at` + downstream `eventId`), surviving overlap/restart; start-sweep idempotent via `spawned_at`.
- Gateway routes `/api/calendar/**` and blocks `/api/internal/**`; non-members 403 on create, non-organizers 403 on update/cancel.

---

# PHASE 11 — Platform: search, security, integrations

## 11.1 Global search (messages, files, people, channels)

*Grounding:* nothing search-specific exists — `messages` has no text index, `MessageRepository` is exact-match only; `Channel` has flat `members[]`; People=Desk has all searchable fields but no search param; **files don't exist**; gateway has no `/api/search` route. Two dead frontend stubs mark the plug points (`Sidebar.js:198` `.search` row, `ChatHeader.js:187` `.header-search`).

**Backend recommendation — Meilisearch** (single ~100MB Go binary, prefix + typo-tolerant instant search, `_formatted` highlighting, filterable attributes + tenant tokens for ACL) over Mongo `$text` (one text index/collection, no prefix, weak ranking, can't unify three DBs) or Elastic (JVM ~1–2GB, disproportionate). **New `search-service`** (:8090, workspace-service template) owning a Meilisearch client + AMQP consumers. Fallback MVP if infra frozen: Mongo `$text` + Postgres `pg_trgm ILIKE`.

### Data model
- **No SQL/Mongo schema change.** Three Meilisearch indexes (fourth when files land):
  - **`messages`** `{id,workspaceId,channelId,channelType,content,senderId,senderName,threadId,createdAt,deleted}`; filterable `[workspaceId,channelId,deleted]`, sortable `[createdAt]`, searchable `[content,senderName]`. ACL via `channelId IN <accessible>` — membership changes re-index only the **channel** doc, never the backlog.
  - **`channels`** `{id,workspaceId,name,type,memberIds[],visibility,allowedTeamIds[],canonical}` (visibility/teams populated once Phase 3 exists).
  - **`people`** `{id(deskId),workspaceId,userId,fullName,nickName,title,teamId,workEmail,personalImageUrl,isActive}`.
  - **`files`** (deferred, blocked on 8.1) `{id,workspaceId,channelId,fileName,contentType,uploaderId,messageId,createdAt}`.
- One persisted checkpoint/cursor in search-service for idempotent resumable backfill.

### Endpoints / events
- **Gateway:** `Path=/api/search/**` → `${SEARCH_SERVICE_URL:http://localhost:8090}` (JWT-protected).
- `GET /api/search?q&workspaceId&types&limit&page` (Meilisearch multi-search → `{messages,channels,people,counts}` with `_formatted`); `GET /api/search/suggest?q&workspaceId&limit=8` (debounced palette).
- **Access control (core):** per request resolve caller's Desk + `teamId` (internal `GET /api/internal/workspace/{id}/members/{userId}` — Phase 3.2 extension; 403/no-desk → empty), compute accessible channelId set (query `channels` index), inject server-side Meilisearch filters: messages `workspaceId=W AND deleted=false AND channelId IN [...]`; people `workspaceId=W AND isActive=true`; channels `workspaceId=W AND (memberIds=userId OR visibility='PUBLIC')`. Never trust client-supplied scope.
- **RabbitMQ indexing (new `search.exchange` topic, `search.index.queue`):** chat-service (new producer, same paths that broadcast `NEW/EDIT/DELETE_MESSAGE`) publishes `MESSAGE_UPSERT/DELETE`, `CHANNEL_UPSERT`; workspace-service (mirror `WorkspaceChannelEventPublisher`) publishes `DESK_UPSERT/DELETE`. **Backfill:** `POST /api/internal/search/reindex` (`InternalAuthFilter`, idempotent via checkpoint).
- No new client WS.

### Frontend (website)
- `api/search.js` (`axiosInstance`): `search(...)`, `suggest(...)`.
- New `CommandPalette.jsx` — ⌘K/Ctrl+K overlay (debounced → `/suggest`, grouped Messages/Channels/People/Files, arrow-nav + Enter, `themes.css` vars). Global trigger in `ChatPage.js` toggling open state (passes `workspaceId`). Wire the two dead stubs to open the palette. Result activation: channel → `setActiveChannel`; person → profile/DM (`POST /api/chat/dm`); message → open channel + scroll (permalink `msg=<id>` from Phase 4.2 for exact jump); file → download (deferred).

### Dependencies
- **Phase 0** (workspace resolution). **Files search blocked on 8.1** — keep behind a flag. Channel ACL richness depends on **Phase 3** (`visibility`/`allowedTeamIds`); until then use flat `members[]` (index attrs pre-provisioned so Phase 3 is data-population, not re-architecture). People works today, reads best with Phase 2; needs the Phase 3.2 internal member endpoint returning `teamId`. Best message-jump depends on Phase 4.2 permalinks (degrades to "open channel"). New infra: Meilisearch + search-service in `pom.xml`/`compose.yml`/`run.sh` + gateway route.

### Effort & DoD
**Effort: XL** (new service + Meilisearch + indexing pipeline + AMQP producers in two services + per-user ACL + palette UI). Split: scaffold+wiring M, producers+backfill M, ACL layer M, palette FE M.
- ⌘K opens palette; as-you-type returns highlighted grouped results within one workspace; Enter navigates.
- A message in a non-member channel never appears (ACL filter, not client-side hide); membership changes reflected without backlog re-index.
- Send/edit/delete/rename/desk-update propagate within a few seconds; `POST /api/internal/search/reindex` rebuilds idempotently from cold Meilisearch.
- `GET /api/search` returns 200 empty (not 500) for no-active-desk callers; unreachable without JWT.

---

## 11.2 SSO/OAuth + audit logs + admin analytics

*Grounding:* JWT auth is end-to-end reusable (`generateToken(email,userId)` HS256; gateway verifies + injects `X-User-Id`). Spring Security already a user-service dependency (single filter chain, `/api/auth/**` permitAll) — the place to add `.oauth2Login(...)`; `CustomUserDetailsService` keys on email (find-or-link works). RabbitMQ producer pattern = `NotificationPublisher`. **Actuator on only 4/7 services; no `micrometer-registry-prometheus` anywhere; no `prometheus.yml`.** **Platform-role gap:** `UserRole{USER,ADMIN}` exists but `User` has no role column, JWT carries no role, gateway hardcodes `X-User-Role:"USER"` — this feature **owns the fix**.

### Data model
- **`User` (MySQL):** add `auth_provider(LOCAL|GOOGLE|GITHUB default LOCAL)`, `provider_subject?`, `role(USER|ADMIN default USER)`; relax `password_hash` to nullable (guard `CustomUserDetailsService` against null-password auth). ddl-auto `update`.
- **JWT claim:** `generateToken` adds `role`; gateway `JwtService` extracts + `AuthGatewayFilter` forwards the real value (kills the hardcoded constant).
- **New `audit-service`** (:8092, Postgres/Flyway, workspace-service template). Table `audit_log` (append-only): `id, event_id UUID UNIQUE, ts, actor_user_id?, actor_email?, action CHECK(...), outcome(SUCCESS|FAILURE), target_type?, target_id?, workspace_id?, ip?, metadata JSONB?`. Indexes `(actor_user_id,ts)`, `(workspace_id,ts)`, `(action,ts)`, `(ts)` (feed filters + `COUNT(DISTINCT actor_user_id)` DAU/WAU).
- **`AuditAction` enum** (hand-copied per producer + consumer): `USER_LOGIN, USER_LOGIN_FAILED, USER_REGISTER, OAUTH_LOGIN, ROLE_CHANGED, INVITATION_SENT/ACCEPTED, MEMBER_REMOVED, CHANNEL_CREATED/DELETED, MESSAGE_DELETED, USER_ACTIVITY`. **`AuditEvent` DTO** (clone of `NotificationEvent`).

### Endpoints / events
- **OAuth (user-service, public via gateway):** `GET /oauth2/authorization/{google|github}`; `GET /login/oauth2/code/{provider}` → `OAuth2LoginSuccessHandler` find-or-link by email → mint JWT → 302 to `${WEB_ORIGIN}/oauth/callback#token=<jwt>` (fragment, not query). Gateway `public-path-prefixes` gains `/oauth2/`, `/login/oauth2/`.
- **audit-service:** `@RabbitListener` on new `audit.exchange`/`audit.queue` (idempotent on `event_id`); `GET /api/audit?actorUserId&action&workspaceId&outcome&from&to&page&size` (**ADMIN-gated on `X-User-Role`**); `GET /api/audit/analytics/summary?from&to` (DAU/WAU SQL + messagesPerDay from Prometheus/rows); `POST /api/internal/audit` (`X-Internal-Token` HTTP fallback).
- **Audit producers (fire-and-forget, never block):** user-service login/register/OAuth; workspace-service role/member mutations + invitations; chat-service channel/message admin actions; gateway `AuthGatewayFilter` post-verify → throttled `USER_ACTIVITY` (one per user per ~10min via in-gateway Caffeine, offloaded to `boundedElastic`).
- **Prometheus (net-new):** add actuator + `micrometer-registry-prometheus` to gateway/user-service, `micrometer` to the other four; expose `prometheus`. Custom meters: chat `vo_messages_total{workspaceId,type}` in `sendMessage`; user `vo_logins_total{method,outcome}`; gateway `vo_active_users` gauge. New `infra/prometheus/prometheus.yml` + `prometheus`+`grafana` in root `docker-compose.yml`.
- No new WS.

### Frontend (website)
- Social buttons on `Login.js`/`Signup.js` (plain anchors → gateway authorize). New `pages/OAuthCallback/` (`/oauth/callback`: read `#token`, store, navigate `/chat`). `getCurrentUserRole()` in `utils/auth.js` + new `AdminRoute` (token && role===ADMIN). **`/admin`** route wrapped in `AdminRoute`, new `pages/Admin/` (KPI cards from analytics summary, audit table from `GET /api/audit`, optional Grafana iframe). `api/audit.js` + `api/admin.js` (`axiosInstance`). Admin icon in `WorkspaceSidebar.js` shown only for ADMIN.

### Dependencies
- **Owns the platform-role gap fix** (prerequisite for any platform-admin gating — search admin, integrations admin, analytics). OAuth + Prometheus independent of Phases 0–6. Reuses (not duplicates) workspace-scoped `WorkspaceAccessGuard.requireRole(...ADMIN)` — platform `ADMIN` is orthogonal to `Desk.role`. Distinct from the Phase 6 *workspace-admin* panel (separate route/data, shared theme). New infra: `audit-service` DB + gateway route + `compose.yml`/`run.sh` + `audit.exchange`; Prometheus/Grafana.

### Effort & DoD
**Effort: XL** — OAuth M, platform-role+JWT/gateway S–M, audit-service+producers L, Prometheus wiring M, admin dashboard+OAuth UI M.
- Sign in with Google **and** GitHub, find-or-linked by email (LOCAL + federated same-email resolve to one row), land in `/chat` with a working JWT; downstream services need **no** code change.
- Every login (success+failure), OAuth, role change, invitation, member removal, channel/message admin action → exactly one durable `audit_log` row (idempotent on `event_id`); no audit publish blocks/fails the request.
- `/actuator/prometheus` scrapeable on all 7; `vo_messages_total`/`vo_logins_total`/`vo_active_users` populated; analytics summary returns non-zero DAU/WAU/messages-per-day.
- `/admin` renders for ADMIN, hard-redirects USER; `GET /api/audit*` returns 403 to non-admin (server-side on `X-User-Role`).

---

## 11.3 Public API + integrations (GitHub/Jira/Calendar)

*Grounding:* gateway is JWT-only today (`AuthGatewayFilter` strips `X-User-*`, blocks `/api/internal/**`, no API-key branch, no rate limiting). Internal shared-secret filter pattern = room-service `InternalAuthFilter` (chat-service has none inbound). RabbitMQ "producer → chat-service consumes & broadcasts" fabric exists but consumers **manage membership, don't post messages** — the gap this fills. `MessageType.SYSTEM` exists; `Message` has `clientMessageId` dedupe. No API-key/scope/rate-limit/webhook model anywhere. **New `integrations-service`** (:8088, Postgres/JPA/Flyway).

### Data model (new Postgres `integrations`, provider tokens AES-GCM encrypted)
- **`api_key`** `{id,workspace_id,owner_user_id,name,key_prefix(vok_live_),key_hash(SHA-256),scopes(chat:read/write,members:read,events:write),rate_limit_tier(FREE|STANDARD|PARTNER),last_used_at,expires_at,revoked}` (full key returned once).
- **`oauth_connection`** `{provider(GITHUB|JIRA|GOOGLE),account_login,external_account_id,access_token_enc,refresh_token_enc,scopes,expires_at,status}`.
- **`integration_binding`** `{provider,external_resource(repo/project/calendar),channel_id,event_filters,active}`.
- **`inbound_webhook`** `{provider,slug,signing_secret,active}`; **`webhook_delivery`** `{provider,external_delivery_id,payload_hash,status(RECEIVED|PROCESSED|SKIPPED|FAILED)}` unique `(provider,external_delivery_id)`.
- **`outgoing_webhook`** `{target_url,secret,event_types,active}`; **`outgoing_delivery`** `{event_id,attempt,status,response_code,next_retry_at,last_error}`.
- **`calendar_sync`** `{oauth_connection_id,google_calendar_id,channel_id,sync_token,watch_*,last_synced_at}`.
- **chat-service changes:** add inbound `InternalAuthFilter` + `IntegrationChatListener` (creates `SYSTEM` message + broadcasts `NEW_MESSAGE`); reserve bot sentinels (`-101` GitHub, `-102` Jira, `-103` Calendar, `senderRole="INTEGRATION"`); add additive `Message.sourceType`; new queue/binding in `RabbitConfig`.
- **Redis:** API-key validation cache + gateway rate-limit buckets.

### Endpoints / events
- **Gateway:** routes `/api/public/**`, `/api/integrations/**` (JWT), `/api/webhooks/**` (public prefix, HMAC-verified downstream — **not** under `/api/internal/`). **New API-key branch in `AuthGatewayFilter`** for `/api/public/`: read `X-Api-Key`/`Bearer vok_…`, validate via cached `POST /api/internal/apikeys/validate`, inject `X-Workspace-Id`/`X-Api-Scopes`/`X-Api-Key-Id`/`X-User-Id`, 401 on miss. **Rate limiting:** Spring Cloud Gateway `RequestRateLimiter` (Redis, `KeyResolver=X-Api-Key-Id`, tiered → 429). Adds `spring-boot-starter-data-redis-reactive` to gateway.
- **Management API (JWT, ADMIN via copied `WorkspaceClient.requireRole`):** `POST/GET/DELETE /api/integrations/{ws}/api-keys` (create returns full key once); `bindings`; `oauth/{provider}/authorize` + `oauth/{provider}/callback`; `outgoing-webhooks` + `deliveries`; `connections`.
- **Inbound webhooks (public, HMAC in-service):** `POST /api/webhooks/github/{slug}` (verify `X-Hub-Signature-256`, `X-GitHub-Event`, dedup on `X-GitHub-Delivery`, resolve repo→binding→channel, emit `IntegrationChatEvent`); `…/jira/{slug}`; `…/google/{slug}` (push → incremental sync).
- **Public REST (`/api/public/v1/**`, API-key scoped):** `GET /channels`, `GET/POST /channels/{id}/messages`, `GET /workspace/members`, `POST /events`, `GET /me`.
- **RabbitMQ/WS:** new `integrations.exchange` (direct, `integration.chat.event`), payload `IntegrationChatEvent{...,senderSentinelId,clientMessageId=externalDeliveryId}` → chat `IntegrationChatListener` persists `SYSTEM` message (idempotent) + broadcasts `NEW_MESSAGE` (already-subscribed clients render live). **Outgoing webhooks:** integrations-service consumer queues bound to existing producers (workspace member add/remove for MVP) → match `event_types` → delivery worker POSTs with `X-VO-Signature` HMAC, exponential backoff via `next_retry_at`, max attempts → FAILED.

### Frontend (website)
- `api/integrations.js` (`axiosInstance`). "Integrations" tab in `SettingsModal.js` (ADMIN-gated): Connections (Connect GitHub/Jira/Google → gateway authorize popup, disconnect), Channel bindings, API keys (one-time reveal + revoke + scopes), Outgoing webhooks (URL + types + secret + delivery log). Message rendering: extend the SYSTEM branch in `Message.js` to show `sourceType` icon + clickable `link`. Calendar MVP = "Connect Google Calendar" + synced-events digest as SYSTEM messages (full view deferred to Phase 10 `pages/Calendar/`).

### Dependencies
- **Phase 4** channel access (bot sender permitted on bind or bypass in internal post; respect visibility once Phase 4 lands). **Phase 2/3 role** for ADMIN gating (reuse internal role endpoint). chat-service must add inbound `InternalAuthFilter` + `IntegrationChatListener` + `Message.sourceType`. gateway must add redis-reactive + API-key branch + 3 routes + `/api/webhooks/` carve-out + `RequestRateLimiter`. **Google two-way sync depends on Phase 10 calendar-service**; one-way pull → digest is independent. New infra: `integrations` DB + queues + `compose.yml`/`run.sh` + secrets (AES key, provider client-id+secret).

### Effort & DoD
**Effort: XL.** Phasing: M — scaffold + `api_key` + gateway API-key auth + rate limiting + public read; M — GitHub inbound → channel SYSTEM message (the demoable core); M — Jira inbound; L — outgoing webhooks + delivery worker + Google OAuth/calendar pull; S/M — settings tab.
- Creating an API key returns the secret once; `GET /api/public/v1/channels` → 200 with valid key, 401 revoked/absent, 429 on tier limit.
- Opening a PR / creating a GitHub issue on a bound repo posts a formatted `SYSTEM` message with a working link, visible live; replaying the same `X-GitHub-Delivery` doesn't double-post (idempotent on `webhook_delivery` + `clientMessageId`).
- Jira `issue_created/updated` on a bound project posts to its channel; invalid HMAC → 401 + recorded FAILED/SKIPPED.
- Registering an outgoing webhook + triggering member-added delivers a signed POST (verifiable `X-VO-Signature`), retries with backoff on 5xx, records each attempt; a Google account connects and upcoming events appear as a channel digest.

---

# New infrastructure / services introduced

**New backend microservices** (all scaffolded from the workspace-service JPA template, added to `backend/pom.xml`, `dev/compose.yml`, `dev/run.sh`, and gateway routes):
- **tasks-service** (:8085, Postgres `tasks`) — Phase 10.1
- **calendar-service** (:8083, Postgres `calendar`) + owns a `@Scheduled` sweep — Phase 10.2
- **search-service** (:8090, Meilisearch client + AMQP consumers) — Phase 11.1
- **audit-service** (:8092, Postgres `audit`, append-only) — Phase 11.2
- **integrations-service** (:8088, Postgres `integrations`, AES-GCM token encryption) — Phase 11.3

**New data stores / infra containers:**
- **Meilisearch** (search index) — Phase 11.1
- **Prometheus + Grafana** (metrics/observability) + `micrometer-registry-prometheus` across all 7 services — Phase 11.2
- **Object storage** — GridFS reuses existing Mongo (no new container); `StorageService` interface leaves a **MinIO/S3** swap path for prod — Phase 8.1
- New Postgres databases: `tasks`, `calendar`, `audit`, `integrations` (shared dev Postgres)

**New cross-cutting platform capabilities:**
- **Gateway `/api/notifications/**` route + WS carve-out** (Phase 7) — unblocks inbox/DND/reminders/spatial/calendar notifications; plus `/api/tasks`, `/api/calendar`, `/api/search`, `/api/audit`, `/api/public`, `/api/integrations`, `/api/webhooks` routes and the `/oauth2//login/oauth2` public prefixes as their phases land.
- **Gateway API-key auth branch + Redis-backed `RequestRateLimiter`** (`spring-boot-starter-data-redis-reactive`) — Phase 11.3
- **Platform-role fix** (`User.role` → JWT `role` claim → gateway forwards real `X-User-Role`) — Phase 11.2; prerequisite for all platform-admin gating.
- **OAuth2 (Google + GitHub)** in user-service via existing Spring Security chain — Phase 11.2
- **Schedulers:** chat-service `@EnableScheduling` (scheduled messages/reminders/orphan GC, Phase 8), calendar-service scheduler (start/reminder sweeps, Phase 10). Status expiry is **lazy** (no scheduler, Phase 7.2).
- **New RabbitMQ topology:** `audit.exchange`/`audit.queue` (11.2), `search.exchange`/`search.index.queue` (11.1), `integrations.exchange` (11.3), and new `PRESENCE_CHANGED` on the existing `workspace.exchange` (9.1). The `notifications.exchange` is reused unchanged for all new notification types (inbox, DND, reminders, tasks, calendar, spatial).
- **New/generalized producers:** chat-service (notifications, search, integrations listener), workspace-service (presence, search desk events), room-service (spatial + knock), tasks-service, calendar-service, user-service/gateway (audit).
- **New shared frontend module:** `website/src/api/chat.js` (consolidates attachments/rich-text/saved/sections/search chat REST); `website/src/api/notifications.js`; website's **first notifications STOMP client** (Phase 7).
- **New Colyseus/SkyOffice foundations:** `Player` schema fields (`userId`, `presence`, `status*`), `Game.ts` `layout.zones` consumption, `config.mapObjects` object wiring, `goToZone` deep-link hook — shared across Phase 9 + 10.2.
- **New persisted tables in existing services:** `whiteboard_snapshot` (workspace-service, 9.3); `Desk.currentZoneId/currentZoneName/statusExpiresAt` (9.1/7.2); chat-service Mongo collections `saved_items`, `scheduled_messages`, `reminders`, `sidebar_layouts`, `drafts` (8.3/8.4); notifications-service `NotificationPreference` (7.2/9.5).

---

# Rough total effort summary

| Phase | Features | Aggregate effort |
|---|---|---|
| 7 — Notifications backbone | Unified Inbox (L), Status+DND (L) | **~L·2** — front-loads the gateway/WS/generalization that 6 later features reuse |
| 8 — Chat enrichment | Attachments (L), Rich text (M), Sections/drafts (M–L), Saved/schedule/reminders (L) | **~L·3 + M** — largely parallelizable, shared `api/chat.js` |
| 9 — Spatial | Presence (L), Meeting rooms (L→XL), Screen+whiteboard (L), Find/follow (L), Spatial notifications (L) | **~L·5** — SkyOffice-heavy; Phase 9 foundations amortized across all five |
| 10 — New services | Tasks (L), Calendar (L) | **~L·2** — two new services from template |
| 11 — Platform | Search (XL), SSO/audit/analytics (XL), Public API/integrations (XL) | **~XL·3** — the heavy platform tier |

**Overall:** roughly **3 XL + ~11 L + 2 M** — a multi-quarter program for a small team. The critical path runs Phase 7 (notifications backbone) → then Phase 8 and Phase 9 can proceed in parallel (different surfaces: website-chat vs SkyOffice) → Phase 10 depends on Phase 9's spatial foundations + Phase 7 notifications → Phase 11 is the final platform tier (search/security/integrations), with 11.2's platform-role fix and 11.3's Google two-way sync being the only intra-phase-11 ordering constraints. The single highest-leverage early investment is the **Phase 7 notifications gateway route + website WS client + `NotificationListener` generalization**, which unblocks reminders, DND, spatial notifications, task/calendar/mention/DM inbox, and every later producer at once.

---

# Additional items (folded in per user)

# Plan additions (to merge into final roadmap after the workflow lands)

## ADD-1 — SkyOffice higher-quality character rendering
**What exists:** `SkyOffice/client/src/PhaserGame.ts` uses `Phaser.AUTO`, `pixelArt: true`
(nearest-neighbor, crisp pixel art), scale FIT, camera `zoom: 1.5` (`scenes/Game.ts`).
Characters are pixel-art **texture atlases**: `public/assets/character/{adam,ash,lucy,nancy}.png`+`.json`,
animated via `anims/CharacterAnims.ts` (`generateFrameNames`). Player render in `characters/{Player,MyPlayer,OtherPlayer}.ts`.
**Two paths:**
- **Low-cost (sharpness on HiDPI):** make the canvas devicePixelRatio-aware, add `roundPixels: true`,
  keep `pixelArt: true`; ensure no CSS blur on the canvas. Optionally raise `zoom`. Marginal but free.
- **High-fidelity (real upgrade):** replace low-res atlases with **2×–4× higher-resolution character art**
  (upscale existing sprites with a pixel-art upscaler, or source new art), update atlas frame dims in the
  `.json` + the frame refs in `CharacterAnims.ts`, and choose `pixelArt` vs linear filtering to match the new
  art style; adjust `setScale`/collision sizes accordingly.
**Frontend:** SkyOffice client only (config + assets + anims). No backend.
**Deps:** none (independent). **Effort:** S (config) / L (new/upscaled assets).
**DoD:** characters look crisp on retina/4K; if high-fidelity path chosen, visibly higher-detail avatars with animations intact.

## ADD-2 — Auto-updating user status from calendar/meetings
**Idea (Slack "based on your calendar"):** when a calendar event/meeting is active, auto-set the user's
status to "In a meeting" (emoji 📅) with an expiry = event end; revert to previous/none afterward.
**Backend:** calendar-service publishes `MEETING_STARTED`/`MEETING_ENDED` (RabbitMQ) -> a status resolver
(workspace-service Desk.status/statusEmoji/statusCustomText, which already exist) sets/clears an
**auto-status** layer that a manual status overrides. Store `statusExpiresAt` + `statusSource(MANUAL|AUTO)`.
Presence/DND (ADD in workflow) consumes this.
**Frontend:** status shows in sidebar/members + on the map; "Set a status" modal lists presets incl.
"In a meeting — based on your calendar".
**Deps:** builds on `custom-status-dnd` + `calendar` (both in the workflow), and `spatial-presence`.
**Effort:** M. **DoD:** joining a scheduled meeting flips status automatically and reverts on end; manual status wins.

## ADD-3 — Voice-channel (proximity/Agora) verification + fix
**Task (not just design):** end-to-end verify proximity voice works: room-service mints Agora tokens,
SkyOffice client `VoiceService` joins the Agora channel, audio is heard between nearby avatars / in a room zone.
Confirm `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE` are set (compose env), token endpoint returns 200,
client subscribes to remote audio, and mute/leave work. Fix whatever breaks.
**Deps:** ties into `meeting-rooms` (auto-join voice zones) from the workflow.
**Effort:** S–M (verify) + unknown (fixes). **DoD:** two browser sessions hear each other in proximity / same room.

## ADD-4 — Centralized logging: Loki + Promtail + Grafana
**Choice:** user said "DynamoDB or anything better" — DynamoDB is AWS-managed and awkward for this
self-hosted Docker stack. Since Grafana already runs, use **Grafana Loki** (log store) + **Promtail**
(ships container logs) — logs live next to the existing Prometheus/Grafana dashboards. (ELK/OpenSearch
is the alternative; DynamoDB only if the project later targets AWS.)
**Infra (docker-compose):** add `loki` + `promtail` services; Promtail tails Docker container logs
(json-file driver) and pushes to Loki; add Loki as a Grafana datasource; provision a "Logs" dashboard
+ Explore. Optionally have Spring services log JSON (logback) for structured fields (service, level, traceId).
**Backend:** structured JSON logging + correlation/trace id (MDC) across services and the gateway.
**Frontend:** none (Grafana Explore / dashboard).
**Deps:** none hard; complements existing Prometheus/Grafana observability.
**Effort:** M. **DoD:** every service's logs are searchable/filterable in Grafana by service+level+time; a
"Logs" dashboard shows error rates; correlation id ties a request across services.
