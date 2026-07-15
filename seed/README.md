# Northstar Software — demo data seeder

Populates a fresh Virtual Office stack with a realistic demo company so you can
log in and immediately see users, channels, projects, tasks, rooms and messages.

## What gets created

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 15 | all share one password — see [credentials.md](credentials.md) |
| Workspace | 1 | **Northstar Software** (owner: Maya Hassan) |
| Teams | 6 | Leadership, Product & Design, Backend & Platform, Frontend, Quality & Data, Revenue & Ops |
| Text channels | 25 | 15 public + 10 private/team, each with the right members |
| Projects (task spaces) | 7 | one per initiative + Internal |
| Tasks | 48 | July 1–15 history, real assignees / statuses / priorities |
| Voice rooms | 11 | Daily Standup, pairing rooms, Coffee Lounge, … |
| Calendar events | 15 | a full day of meetings, stamped onto **today** → shows on every desk's "Today's Agenda" |
| **Chat history** | **1,804 messages · 88 threads · 590 reactions** | **3 months** of in-character conversation (2026-04-15 → today) across all 25 channels |
| **Profile pictures** | 15 | generated avatars, shown in chat / members / contacts / sidebar |

Everything is data-driven from [`seed-data.json`](seed-data.json) — edit that file
to change the company, then re-run.

## Run it

### With Docker (recommended)

The seeder is a one-shot service behind the `seed` compose profile, so a normal
`docker compose up` never runs it. Bring the stack up, then:

```bash
docker compose up -d                                  # start the platform
docker compose --profile seed up seed seed-history    # seed, then load 3-month chat history
```

`seed` waits for the gateway + user/workspace/chat/room/tasks to be **healthy**,
does all the API work, and stages the chat-history script. `seed-history` then
runs only after `seed` exits successfully (`service_completed_successfully`) and
loads the message history into MongoDB. Both exit when done.

### From the host (no seed container)

Requires `bash`, `curl`, `jq`:

```bash
cd seed
GATEWAY_URL=http://localhost:8080 ./seed.sh
```

## Log in

Open the web client (http://localhost:3001), or the 2D office
(http://localhost:5000), and sign in with any address from
[credentials.md](credentials.md) — e.g. `maya.hassan@northstar.io` /
`Northstar@2026`. Maya owns the workspace, so log in as her to see everything.

## Re-running / options

The seeder is **idempotent**: users fall back to login, and the
workspace/teams/channels/projects/rooms are create-if-missing. Tasks and
messages are one-shot (they have no natural uniqueness) and are skipped once the
workspace has been seeded.

| Env var | Default | Purpose |
|---------|---------|---------|
| `GATEWAY_URL` | `http://gateway-api:8080` | gateway base URL (`http://localhost:8080` from the host) |
| `SEED_PASSWORD` | `Northstar@2026` | password for every seeded account |
| `SEED_FORCE` / `FORCE` | `0` | `1` re-creates tasks + messages even if already seeded (will duplicate) |
| `WAIT_TIMEOUT` | `300` | seconds to wait for the gateway |

```bash
# force a re-seed of tasks + messages
docker compose --profile seed run -e SEED_FORCE=1 seed
```

## How it maps to the platform

A few things worth knowing (discovered from the service APIs):

- **No email verification** is required — registration returns a working token.
- **Job title / team** live on the workspace *desk* (not the user account), set
  via the admin membership endpoint. **Presence status** is set per-user on their
  own desk.
- **Members** are added through the real 2-step invite → accept flow (each accept
  is performed with that member's own token).
- **Projects** are task "spaces"; every user is added as a member so everyone sees
  every board.
- Task **status** is one of `TODO` / `IN_PROGRESS` / `COMPLETE` and **priority**
  one of `LOW` / `NORMAL` / `HIGH` — the doc's richer states (In review, Blocked,
  Reopened, Draft…) are mapped onto these and preserved in the task description.
- The **calendar is a shared team calendar** (the list endpoint returns every
  workspace event in the window), so the seeded events show on *everyone's*
  "Today's Agenda" on My Desk. They're stamped onto the current **local** day
  (the seed container shares the host timezone), so the agenda is always
  populated for the day you view it.
- **Chat history goes straight into MongoDB, not through the API.** The REST API
  cannot backdate a message (`createdAt` is server-set), and the channel view
  paginates by `_id` — so `load-history.js` builds each message's ObjectId from
  its historical timestamp, keeping `createdAt` order and `_id` cursor order in
  sync (scroll-up paging works across the whole 3 months).
- **Profile pictures live in two places.** The sidebar's own avatar comes from
  the user-service photo (`POST /api/users/me/photo`), while chat/members/contacts
  read `desk.personalImageUrl`. That field has **no write API** (nothing in
  workspace-service ever sets it), so the seeder writes it directly in Postgres,
  pointing at `/avatars/<ref>.png` — served by the web-client from
  `website/public/avatars/`. Regenerate the images with `python3 make-avatars.py`
  (requires Pillow); the web-client must be rebuilt to pick up new files.

> ⚠️ These are demo accounts with a shared, well-known password. Never seed them
> into a public/production deployment.
