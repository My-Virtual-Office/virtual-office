# Virtual Office — Production Readiness Plan

**A deep-analysis roadmap from graduation prototype → production system.**

> Scope: `backend/` (Spring Boot microservices), `website/` (React web client),
> `SkyOffice/` (Colyseus + Phaser 2D office), the Flutter **mobile** client, and the
> cross-cutting platform (infra, CI/CD, security, observability, ops).
>
> Basis: this plan is grounded in **(a)** the graduation book's own honest
> self-assessment — its *Limitations* (Ch. 9), *Non-functional Evaluation* (Ch. 9),
> and *Future Work* (Ch. 10) — and **(b)** a fresh four-part code audit of the actual
> repositories. The book already flags that "the principal non-functional gaps are
> **operational hardening** rather than design flaws." This document turns that
> sentence into an executable plan.

---

## 0. How to read this

Every item carries a **priority** and a rough **effort**:

- Priority: 🔴 **P0** (stop-ship / security) · 🟠 **P1** (blocks any real deploy) · 🟡 **P2** (hardening) · 🟢 **P3** (polish/feature)
- Effort: **S** ≈ ≤1 day · **M** ≈ 2–5 days · **L** ≈ 1–3 weeks · **XL** ≈ 1 month+

File references (`path:line`) point at the exact place to change. Secret *values*
are deliberately **not** reprinted here — only their locations.

---

## 1. Executive summary

The system is a genuinely integrated, multi-client, real-time platform and an
excellent graduation result. It is **not production-ready**. The gap is almost
entirely **operational and security hardening plus deployability**, not core design.

**Headline verdict by area:**

| Area | State | Production readiness |
|---|---|---|
| Backend core services (user, workspace, chat, room, notifications) | Functionally strong | 🟠 ~55% |
| Backend platform (secrets, CI, containers, TLS, scaling, observability) | Missing | 🔴 ~15% |
| Web client (`website`) | Chat works; much unwired/prototype | 🟠 ~40% |
| SkyOffice (server) | Auth solid; single-process, deploy missing | 🟠 ~45% |
| SkyOffice (client) | Runs, but map/spawn not DB-driven | 🟠 ~40% |
| Mobile (Flutter) | Chat-only; **source not in this repo** | 🔴 unknown |
| Stubs: calendar, tasks, shared-library | Empty scaffolds | 🔴 0% |
| CI/CD, IaC, TLS, secret management, backups, runbook | Absent | 🔴 ~5% |

**The single most urgent action:** live secrets are committed to the repositories
(a working Gmail app password, an Agora app-certificate, and a weak shared JWT
signing key used as a fallback). These must be **rotated and purged today** —
before anything else. See §2.

---

## 2. 🔴 P0 — STOP-SHIP: secret exposure (do this first, today)

Real, working credentials are committed to git. Anyone with repo access (or anyone
who ever cloned it) has them. **Rotate every value, remove it from the code, and
purge it from git history.**

| # | Secret | Location | Action |
|---|---|---|---|
| 1 | **Live Gmail app password** (SMTP) | `backend/notifications-service/src/main/resources/application.properties:36-37` | Revoke the Google app password now; move to `${MAIL_USERNAME}/${MAIL_PASSWORD}`. |
| 2 | **Agora app-certificate** (+ app-id) — mints voice tokens | `backend/room-service/src/main/resources/application.yml:30-31` | Rotate the certificate in the Agora console; externalize `${AGORA_APP_ID}/${AGORA_APP_CERTIFICATE}`. |
| 3 | **JWT signing secret** (weak, shared, committed default) | `backend/user-service/.../application.properties:26`, `backend/gateway-api/.../application.yml:29` | Generate a high-entropy secret; **require** the env var (fail-fast if unset); never commit a usable default. HS256 + guessable key = full auth bypass. |
| 4 | **`INTERNAL_API_TOKEN` = `dev-internal-token`** (server-to-server auth) | `backend/{room,workspace,chat}-service` yml; `SkyOffice/server/services/backend.ts:22`; `backend/dev/run.sh` | Require env, no default; rotate. |
| 5 | **DB passwords / `root` users** hardcoded | `backend/user-service/...properties:7` (MySQL root), `room`/`chat` Mongo URIs, `notifications` | Externalize all; stop using DB `root`. |
| 6 | **Agora App ID** default in client | `SkyOffice/client/src/services/VoiceService.ts:19` | Require `VITE_AGORA_APP_ID` at build, no fallback. |

**Also:**
- After rotating, **purge history** (`git filter-repo` / BFG) on all three repos and force-push, or accept the values as permanently compromised and rely on rotation.
- Add a **secret scanner** (gitleaks / trufflehog) as a pre-commit hook and CI gate so this cannot recur.
- Adopt a real **secret store** (Phase 4): Vault, SOPS-encrypted files, or the cloud provider's KMS/Secrets Manager. Standardize on `${VAR}` with **no committed defaults**.

Effort: **M** (rotation + externalization is fast; history purge + coordinating the team is the slow part).

---

## 3. Backend plan (`backend/`)

Spring Boot 3.4.1 / Spring Cloud 2024.0.0 / Java 21. Five real services + gateway;
calendar/tasks/shared-library are empty. **What's good:** the gateway trust boundary
is solid (strips client identity headers, blocks `/api/internal/**`, fails JWT
closed), idempotency/dedup is properly implemented (Redis `SETNX`, Mongo unique
indexes), and workspace-service is rigorously tested (JaCoCo 90% + Testcontainers).

### 3.1 Secrets & config — 🔴 P0 / 🟠 P1
Covered in §2. Additionally standardize config: every service on `${VAR}` (no
default) with a documented `.env.example`. Today externalization is inconsistent —
workspace/gateway use `${VAR:default}`, but user/room/chat/notifications hardcode.

### 3.2 Containerization & deployment — 🔴 P1
- **No Dockerfiles exist for any service** — the system only runs as host `java -jar` via `backend/dev/run.sh`. **Not deployable to any container platform.**
  - Add a **multi-stage Dockerfile per service** (build with Maven, run on a slim JRE 21). **[M]**
- **No production orchestration.** Only per-service *infra* compose files exist. Author a **single top-level `docker-compose.prod.yml`** (all 5 services + gateway + infra) and then **Kubernetes/Helm** for real deploys. **[L]**
- Add **liveness/readiness probes** (wire the existing Actuator `health` endpoint) and **CPU/memory limits** per container. **[S]**
- The `dev/run.sh` demo builds with `-DskipTests` and skips user-service/MySQL — keep it as a *dev* tool only; it is not a deployment path.

### 3.3 CI/CD — 🟠 P1
- The only workflow is `deploy-docs.yml` (publishes `docs/` to Pages). **No build, test, lint, or deploy pipeline.**
  - Add a **monorepo CI**: `./mvnw verify` per module (enforcing workspace's JaCoCo gate + Testcontainers), then **build & push images**, then deploy. Gate PRs on it. **[M]**
  - Add the **gitleaks** secret scan (§2) to CI.

### 3.4 Security hardening — 🟠 P1 / 🟡 P2
- **No TLS/HTTPS anywhere** — gateway serves plain HTTP; JWTs travel cleartext. Terminate **TLS at the gateway/ingress**. 🟠 **[M]**
- **No rate limiting** — public `/api/auth/**` and `/api/otp/**` are unthrottled (brute-force / OTP-spam). Add gateway **`RequestRateLimiter`** (Redis) + per-endpoint limits. 🟠 **[M]**
- **No platform-level RBAC** — `AuthGatewayFilter` hardcodes `DEFAULT_ROLE = "USER"` for everyone (`:52-54`). Model platform roles and emit a real `X-User-Role` from JWT claims; add admin authz at the edge. 🟡 **[M]** *(Book Future Work item.)*
- **Internal-token compare is not constant-time** (`InternalAuthFilter` uses `.equals`, `room:52`/`workspace:54`) — use `MessageDigest.isEqual`. 🟡 **[S]**
- **CORS** defaults to `localhost:*` with `allowCredentials(true)` — lock to real origins in prod (overridable via `GATEWAY_CORS_ORIGINS`). 🟡 **[S]**
- **Inconsistent input validation** — chat uses `@Valid`; room/workspace/notifications/user largely don't. Add bean validation on all request DTOs. 🟡 **[M]**
- `user-service` ships `jpa.show-sql=true` + `ddl-auto=update` — remove for prod. 🟡 **[S]**

### 3.5 Reliability & messaging — 🟠 P1 / 🟡 P2
- **No dead-letter queues** — retries (5×, backoff) exist but exhausted messages are **dropped** (`requeue-rejected: false`). Declare **DLX/DLQ** and route failures there. 🟠 **[M]** *(Book Future Work.)*
- **Presence reaper is passive TTL only** (30s Redis TTL, no active sweep) — a crashed client's presence lingers until the next heartbeat window with no leave-event. Add a **keyspace-expiry listener or `@Scheduled` reaper** to emit leave events. 🟡 **[M]** *(Book Future Work.)*
- **No graceful shutdown** — enable `server.shutdown=graceful` + `spring.lifecycle.timeout-per-shutdown-phase` so in-flight WS/HTTP/AMQP work drains on deploy. 🟡 **[S]**
- **Migrations only in workspace-service** (Flyway). **user-service (MySQL) uses `ddl-auto=update`** — add **Flyway**. Version Mongo indexes/migrations for chat/room/notifications. 🟠 **[M]**

### 3.6 Observability — 🟡 P2
The book documents a Prometheus/Grafana setup (Ch. 9 §Observability), but the audit
found **no `micrometer-registry-prometheus` dependency in any pom** and services
only expose `health,info,metrics` (no `/actuator/prometheus`). Reconcile book ↔ code:
- Add the **Prometheus registry** to every service (incl. gateway) and expose the endpoint. 🟡 **[S]**
- **No distributed tracing** — add **Micrometer Tracing + OTLP** (trace gateway→workspace→room and RabbitMQ hops). 🟡 **[M]** *(Book Future Work.)*
- **Plain, per-service logging** — add **JSON logging** + centralized aggregation (Loki/ELK); drop `DEBUG` (e.g. room's `web.socket: DEBUG`). 🟡 **[M]**
- **No alerting** — define alerts on the metrics (error rate, latency, pool saturation, DLQ depth). 🟡 **[M]**

### 3.7 Testing — 🟡 P2
- Enforce **JaCoCo** on chat & room (they have Testcontainers but no coverage gate). **[S]**
- **user-service & notifications-service** have **no Testcontainers, no JaCoCo** — add real-infra integration tests (MySQL, mail, Rabbit). **[M]**
- Add **contract tests** (Spring Cloud Contract / Pact) for the header contract between gateway↔services and the Colyseus client. **[M]**

### 3.8 The stubs — 🔴 P3 (feature) 
`calendar-service` (:8083) and `tasks-service` (:8085) are **empty** (2-line
`application.properties` only — no main class, won't even start). `shared-library`
is empty. See §7 for the completion plan.

### 3.9 Scaling — 🟠 P1 / 🟡 P2
- **WebSocket services can't scale horizontally** — room/chat/notifications use the **in-memory simple STOMP broker**, which does not fan out across instances. Switch to the **RabbitMQ STOMP relay** + **sticky sessions** at the LB. 🟠 **[L]**
- **All infra is single-node** (one Postgres/MySQL/Mongo/Redis/RabbitMQ) — add **replication/HA** in prod. 🟡 **[L]**
- **No HikariCP pool tuning** — set `maximum-pool-size` etc. per service. 🟡 **[S]**
- REST paths are otherwise stateless and scale fine once containerized. ✅

### Top 10 backend blockers
1. 🔴 Live Gmail password committed → rotate.
2. 🔴 Agora certificate committed → rotate.
3. 🔴 Weak shared JWT secret default → auth bypass.
4. 🔴 No Dockerfiles / orchestration → not deployable.
5. 🟠 No CI pipeline.
6. 🟠 No TLS.
7. 🟠 No rate limiting on auth/OTP.
8. 🟠 No dead-letter queues.
9. 🟠 WebSocket can't scale (in-memory broker) + single-node infra.
10. 🟡 No RBAC, no tracing, inconsistent secret/DB-cred externalization; calendar/tasks non-functional.

---

## 4. Frontend plan (`website/` — React / CRA, plain JS)

**What's good:** the chat domain (channels, DMs, threads, STOMP send/receive) is
implemented. **What's not:** production networking is fundamentally broken, several
advertised features are unwired, and there is no deploy story.

### 4.1 Networking & config — 🔴 P1
- **Production networking is broken.** All API calls use relative paths that only reach the backend via `src/setupProxy.js`, which runs **only under `react-scripts start` (dev)** and hardcodes `localhost:8081/8084`. A production `build/` has **no proxy** → every API/WS call hits the static host and fails.
  - Introduce `REACT_APP_API_BASE_URL` / `REACT_APP_WS_URL`, set `axios.baseURL`, and put a **real reverse proxy (nginx)** in front in prod. 🔴 **[M]**
- **No `.env` / no dev-prod separation** — add `.env.development` / `.env.production`. 🟠 **[S]**

### 4.2 Deploy — 🔴 P1
- **No deploy artifacts at all** — no Dockerfile, nginx config, CI, or SPA fallback. Deep links (`/chat`) **404 on refresh**. Add a container/host config with **SPA rewrite → `index.html`** + caching headers. 🔴 **[M]**
- **Committed git merge-conflict markers in `README.md`** (`<<<<<<< HEAD` …) — the repo is in a half-merged state. Resolve. 🔴 **[S]**

### 4.3 Auth & security — 🟠 P1
- **Spoofable client-asserted identity** — chat/WS requests send `X-User-Id` (decoded client-side from the JWT `sub`) and `X-User-Role: "USER"` as plain headers (`ChatPage.js:21`, `MessagesList.js:20-21`). The backend must derive identity from the **verified JWT only**, never trust client headers (the gateway already strips them — ensure chat is *behind* the gateway). 🟠 **[M]**
- **JWT in `localStorage`** (XSS-exposed), **no token refresh**, **no logout flow**; `PrivateRoute` only checks token *presence*, not validity. Centralize auth, add refresh + logout, consider HttpOnly cookie. 🟠 **[M]**
- WS ticket passed in **URL query string** (leaks to logs/history) — prefer CONNECT-frame auth. 🟡 **[S]**

### 4.4 Realtime robustness — 🟠 P1
- **No STOMP reconnection** (`new Client({...})` sets no `reconnectDelay`/heartbeats) — socket dies silently on network drop. 🟠 **[S]**
- **Subscribe race** (`MessagesList.js:44` only subscribes `if connected` at effect time, never re-subscribes on connect) — live messages can silently never arrive. 🟠 **[S]**
- **Two inconsistent HTTP clients** — axios (with interceptors) for auth/user, raw `fetch` for all chat (bypasses the 401/auth interceptor). Route everything through one axios instance. 🟡 **[M]**

### 4.5 Incomplete / unwired features — 🟠 P1 (verified in code)
- **Presence roster is fake** — `MembersList.js` renders hardcoded `User-1..7`; no fetch/WS. 🟠 **[M]**
- **Typing indicator is send-only** — publishes to `/app/chat/typing`, nothing renders incoming typing. 🟠 **[S]**
- **Attachment upload is dead** — the "add attachment" button has **no `onClick`**; message attachment UI exists but no upload path. 🟠 **[M]**
- **Agora room-calls do not exist in the web client at all** (0 hits for "agora"/WebRTC) — the book's "room calls via Agora (web)" is unimplemented on the frontend. 🟠 **[L]**
- `Dashboard.js` = the literal word "Dashboard"; `Home.js` renders only a header; `/forgot-password` link is a dead route. 🟡 **[M]**

*(These are exactly the book's "partially wired" web features — presence roster, typing display, attachment upload — plus more the audit surfaced.)*

### 4.6 Quality & perf — 🟡 P2
- **Zero tests**, **no error boundaries** (any render throw blanks the app), **no code splitting** (one heavy bundle; MUI + emoji-picker + stompjs eager). Add smoke tests, an error boundary, and `React.lazy` on routes. **[M]**
- Plain JS, no PropTypes/TS; only default CRA ESLint, no `lint` script/CI gate. **[M]**
- No list virtualization (long channels degrade); `getUserPhoto` leaks `createObjectURL` blobs (no `revokeObjectURL`); 25 `console.*` left in shipping code; source maps on in prod. **[S–M]**
- CRA (`react-scripts`) is deprecated — plan a **Vite** migration. 🟢 **[L]**

### Top frontend blockers
1. 🔴 Dev-only API proxy → no prod backend connectivity.
2. 🔴 No deploy/host config; deep links 404.
3. 🔴 Committed merge-conflict markers in `README.md`.
4. 🟠 Presence/typing/attachments non-functional; Agora video absent.
5. 🟠 Spoofable identity headers.
6. 🟠 JWT in localStorage; no refresh/logout.
7. 🟠 No STOMP reconnection; subscribe race drops live updates.
8. 🟡 No tests / error boundaries / code splitting; empty Dashboard & Home.

---

## 5. SkyOffice plan (`SkyOffice/` — Colyseus server + Phaser client)

**What's good & genuinely done:** real HS256 JWT verification (`server/services/backend.ts:43-69`, pins alg, checks exp, timing-safe), auth error handling, URL-token auto-join, chat persistence, and Agora proximity signaling. **What's not:** the client map isn't DB-driven, the server can't scale, and there's no deploy path.

### 5.1 Client — make the DB the source of truth — 🔴 P1
- **Client map is still built from bundled Tiled assets, not the DB.** `Game.ts:86-140` uses `assets/map/map.json`; the fetched backend `layout`/`mapObjects` are **discarded**; `client/src/services/mapBuilder.ts` is **dead code**. Build the tilemap from `layout` and place computers/whiteboards from `mapObjects`. 🔴 **[L]** *(This is the book's #2 Future Work: "drive the 2D office live from the backend.")*
- **Spawn hardcoded `705,500`** (`Game.ts:94`, `OfficeState.ts:11-12`) — desk `positionX/Y` ignored; client & server disagree. Spawn `MyPlayer` from the desk. 🔴 **[S]**
- **Computer/whiteboard ids are index-matched across 3 independent sources** (server hardcoded, client Tiled-index, DB ids) — reconcile to a single `mapObjects` id source. 🟠 **[M]**
- **No Colyseus reconnection** on the client (no `room.onLeave/onError/reconnect`) — a dropped socket strands the user. Add reconnect/rejoin UI + server `allowReconnection`. 🟠 **[M]**

### 5.2 Server — session-config & lifecycle — 🟠 P1
- **`onCreate` ignores `session-config.mapObjects`** and hardcodes 5 computers / 3 whiteboards (`SkyOffice.ts:48-65`); build them from config. 🟠 **[M]**
- **Whiteboard `roomId` is random** (`getRoomId()`), not the persisted `MapObject.roomId` — shared boards aren't persistent/shared. Use the DB id; delete `getRoomId()`. 🟠 **[S]**
- **No graceful shutdown** — add `SIGTERM → gameServer.gracefulShutdown()`; every deploy currently hard-drops all users. 🟡 **[S]**
- Position batching fires every 2s per room even when idle — skip when unchanged; add timeout/backpressure. 🟡 **[S]**

### 5.3 Scaling — 🔴 P1
- **Single-process Colyseus, no Redis presence/driver** (`index.ts:17`). With 2+ instances, `filterBy(['workspaceId'])` only matches *local* rooms → the same workspace **splits into isolated rooms per node** (users can't see/hear each other). Add `@colyseus/redis-presence` + Redis driver **and** sticky sessions **before** scaling out. 🔴 **[M]**

### 5.4 Media plane — 🔴 P1 (decision required)
- **Two parallel media stacks.** Proximity **voice** = Agora (good), but **webcam video/screenshare = PeerJS P2P** (`web/WebRTC.ts`) with **no `iceServers`/TURN** and the public `0.peerjs.com` broker → **fails behind real NATs/firewalls**. **Decide one plane:** either self-host the PeerJS broker + TURN/STUN, or move video to Agora too. 🔴 **[L]**
- **Agora joins are token-less** (`AgoraVoice.ts:31`, `client.join(appId, channel, null, uid)`) — anyone with the App ID joins any channel. **Mint Agora RTC tokens server-side** (room-service already holds the certificate). 🟠 **[M]**

### 5.5 Deploy & secrets — 🔴 P1
- **No Dockerfiles / compose / CI**; deploy still wired to upstream **Heroku `Procfile` + Netlify + `ts-node-dev`** (dev runner). Add server + client Dockerfiles, a manifest, and CI; remove the abandoned Heroku/Netlify config. 🔴 **[M]**
- Committed default `JWT_SECRET` / `INTERNAL_API_TOKEN` / Agora App ID (§2) — require env, fail-fast, rotate. 🔴 **[S]**
- Add `.env.example` for all `VITE_*` and server envs; pin Node ≥18 (`engines`). 🟡 **[S]**

### 5.6 Fork hygiene — 🟡 P2
Delete dead upstream code: LOBBY/PUBLIC/CUSTOM room-picker methods + available-rooms
Redux (`Network.ts:52-116`), `types/Rooms.ts` enum/`IRoomData`, `getRoomId()`
machinery, the `bcrypt` room-password dep, and the stale `SEND_ROOM_DATA` handler. **[M]**

### Top SkyOffice blockers
1. 🔴 Client map bundled, not DB-driven (`mapBuilder.ts` dead).
2. 🔴 Hardcoded spawn `705,500`; desk position ignored.
3. 🔴 Single-process Colyseus (no Redis presence/driver) — can't scale.
4. 🔴 No Dockerfiles/CI; deploy wired to Heroku/Netlify/dev-runner.
5. 🔴 PeerJS video with no TURN → fails behind NAT; redundant second media plane.
6. 🟠 Server ignores `mapObjects`; random whiteboard roomIds.
7. 🔴 Committed default secrets; token-less Agora joins.
8. 🟠 No client reconnection; no server graceful shutdown.

---

## 6. Mobile plan (Flutter — chat only)

- **The mobile source is not in this workspace** — it cannot be audited. **Bring it into version control** (submodule or directory) alongside the other repos so it's buildable/auditable/CI-covered. 🔴 **[S]**
- **Identity is spoofable by design** — the app sends raw `X-User-Id`/`X-User-Role` via a connection screen, no JWT login (book Ch. 8). Implement the **real JWT login** the backend already supports; never let a client set identity headers. 🟠 **[M]** *(Book Future Work.)*
- **Broaden beyond chat** — workspace membership, room presence, eventually a mobile office view. 🟢 **[XL]** *(Book Future Work.)*
- Add **Flutter CI** (build + test), release signing, and store metadata once in VCS. 🟡 **[M]**

---

## 7. Cross-cutting platform ("everything")

| Concern | Gap | Action | Priority |
|---|---|---|---|
| **Secret management** | No vault; secrets are committed defaults (§2) | Vault / SOPS / cloud KMS; `${VAR}` only, no defaults; gitleaks in CI | 🔴 P0/P1 |
| **CI/CD** | Only `deploy-docs.yml`; nothing builds/tests/ships | Per-repo pipelines: build → test (JaCoCo/Testcontainers, RTL, Flutter) → image build/push → deploy; PR gates | 🟠 P1 |
| **Containers / IaC** | No Dockerfiles anywhere; no root compose/k8s/terraform | Dockerfile per service+client; `docker-compose.prod.yml`; then k8s/Helm | 🔴 P1 |
| **Ingress / TLS / env separation** | Plain HTTP; every URL defaults to `localhost`; no domains | Gateway/ingress with TLS termination; per-env base URLs injected at build/deploy | 🟠 P1 |
| **Observability stack** | Metrics endpoints only; no registry in code, no tracing/alerting/central logs | Prometheus + Grafana (all services incl. gateway), OTel tracing, Loki/ELK logs, alert rules | 🟡 P2 |
| **Data: backups & retention** | No backup strategy; retention only implicit (Redis TTLs) | Automated DB backups + restore drills; document retention (receipt TTL, presence reaper) | 🟠 P1 |
| **HA infra** | Single node for every datastore + broker | Replicated Postgres/MySQL/Mongo/Redis/RabbitMQ | 🟡 P2 |
| **Runbook / docs** | Rich per-service markdown, but no deployment/on-call runbook | One top-level runbook: prod deploy, secrets, scaling, incident response, rollback | 🟡 P2 |
| **Load & security testing** | None | k6/Gatling load tests on chat + proximity; a security review / dependency scan (OWASP, `mvn dependency-check`, `npm audit`) | 🟡 P2 |

---

## 8. Feature-completion backlog (from the book's evaluation)

These are **product** gaps (the book marks them *Partial* / *Not implemented*):

1. **Tasks service** (:8085) — build it: task CRUD, assignment, progress, deadlines. It immediately lights up the **existing** `TASK_ASSIGNED` notification consumer end-to-end. 🟢 **[L]**
2. **Calendar service** (:8083) — scheduling, meeting invites, bind meetings to rooms; emit events consumed by notifications. 🟢 **[L]**
3. **Shared library** — extract the duplicated `X-Internal-Token` filter, header constants, and event DTOs each service re-implements. 🟡 **[M]**
4. **Live 2D-office integration** — §5.1/§5.2 (book Future Work #2).
5. **Web feature polish** — presence roster, typing display, attachment upload, Agora video, Dashboard/Home (§4.5).
6. **Mobile broadening** — §6 (book Future Work #3).

---

## 9. Phased roadmap

Ordered so each phase unblocks the next. Rough calendar assumes a small team.

### Phase 0 — Security lockdown (days) 🔴
Rotate & externalize all secrets (§2); add gitleaks; resolve the `website/README.md`
merge conflict. **Exit:** no secret in any repo; secret scan green.

### Phase 1 — Make it deployable (2–4 weeks) 🟠
Dockerfiles for every service + both SkyOffice halves + web; one
`docker-compose.prod.yml`; env-based config everywhere (kill `localhost` defaults and
the CRA dev proxy); gateway/ingress with **TLS**; CI that builds, tests, and pushes
images. **Exit:** the whole system boots from one command in a container environment,
over HTTPS, with no code changes between dev and prod.

### Phase 2 — Security & reliability hardening (2–4 weeks) 🟠/🟡
Rate limiting; platform RBAC; DLQs + presence reaper + graceful shutdown; Flyway on
user-service; STOMP reconnection (web) + Colyseus reconnection (SkyOffice);
constant-time internal-token compare; input validation everywhere. **Exit:** no
silent message loss; brute-force protected; deploys drain cleanly; clients recover
from drops.

### Phase 3 — Scale (2–4 weeks) 🟡
RabbitMQ STOMP relay + sticky LB for WS services; Colyseus Redis presence/driver +
sticky routing; HA datastores; HikariCP tuning; media-plane decision (Agora tokens /
TURN). **Exit:** two instances of every service (and Colyseus) serve one workspace
correctly; a datastore node can fail without outage.

### Phase 4 — Observability & ops (1–2 weeks) 🟡
Prometheus registry in every service; Grafana dashboards; OTel tracing; JSON +
central logs; alert rules; automated backups + restore drill; the production runbook.
**Exit:** every service is scraped and traced; alerts fire; a documented, tested
restore exists.

### Phase 5 — Feature completion & polish (ongoing) 🟢
Tasks & calendar services; live 2D-office integration; web feature polish; mobile
into VCS + JWT login + broadening; shared library. **Exit:** the book's *Partial* /
*Not implemented* rows become *Complete*.

---

## 10. Definition of Done — production exit criteria

- [ ] **No secrets in any repo**; all injected at deploy; secret scan green in CI.
- [ ] **Every component containerized**; one-command reproducible prod deploy (compose or k8s).
- [ ] **All traffic over TLS**; no `localhost` in any shipped config; clean dev/prod env separation.
- [ ] **CI gates every PR**: build + tests (backend coverage gates, web smoke, Flutter) + secret scan; images built on green.
- [ ] **Auth is server-trusted only** (no client-asserted identity honored); platform RBAC in place; rate limiting on auth/OTP.
- [ ] **No silent failure**: DLQs for AMQP; STOMP + Colyseus reconnection; graceful shutdown; presence reaper.
- [ ] **Horizontally scalable**: WS broker relay + sticky LB; Colyseus Redis presence/driver; HA datastores.
- [ ] **Observable**: metrics + tracing + centralized logs + alerts across all services incl. gateway.
- [ ] **Recoverable**: automated backups with a tested restore; a written runbook.
- [ ] **Media works behind NAT** (TURN or Agora-only) with server-minted Agora tokens.
- [ ] Book's *Partial*/*Not implemented* items closed or explicitly descoped.

---

## 11. Risk register (top risks)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Committed secrets already scraped/abused (mail, Agora, JWT) | High | Critical | Rotate **today**; monitor Agora/Gmail usage; treat as compromised |
| Forgeable JWTs via default signing key in a real deploy | Med | Critical | Require strong `JWT_SECRET`, fail-fast if unset (§2/§3.4) |
| Web/SkyOffice ship pointing at `localhost` → total outage | High | High | Env-based config + reverse proxy (Phase 1) before any deploy |
| Colyseus split-brain when scaled | High (on scale) | High | Redis presence/driver + sticky routing before adding a 2nd node |
| Poison AMQP message dropped → lost notification/channel op | Med | High | DLQs + monitoring (Phase 2) |
| P2P video fails for most real users (no TURN) | High | Med | TURN or Agora-only video (Phase 3) |
| No backups → unrecoverable data loss | Low | Critical | Automated backups + restore drill (Phase 4) |

---

## 12. Documentation — missing/thin book sections

The graduation book (`GraduationBook/`) is broad and honest, but a coverage audit
of its chapters found technical topics that are present in the *system* yet missing
or thin in the *book* — the same kind of gap the **Observability** section (Ch. 9)
just filled. Documentation completeness is part of production readiness (a runbook
and accurate design docs are operational assets), so these are tracked here.

> Priority below is **documentation** priority (📕 High / Med), distinct from the
> code P0–P3 used elsewhere. Effort uses the same S/M/L scale.

| # | Missing section | Why it's a gap | Where it goes | Priority | Effort |
|---|---|---|---|---|---|
| A1 | **Data / Database Design** | Book has only a *conceptual* Domain Model (Ch. 3) + a short *Polyglot Persistence* section (Ch. 4). The real schemas are undocumented — yet `workspace-service/DATABASE.md` holds a **full BCNF PostgreSQL schema**, plus MongoDB collections, Redis key schemes, and index designs. | New **"Data Design"** chapter (after Architecture) or a large Ch. 4 section | 📕 High | M |
| A2 | **Security (consolidated)** | Security is scattered (gateway, JWT, WS tickets across Ch. 4). No single treatment of the **threat model, two-token trust model (JWT + `X-Internal-Token`), zero-trust boundary, per-workspace RBAC**, and the known gaps (no platform RBAC, committed secrets). | New Security section in Ch. 4, or a short Security chapter | 📕 High | M |
| A3 | **CI/CD & DevOps / Deployment topology** | Ch. 9 covers the *demo* stack and a deployment *view* only — no containerization, environments, or pipelines (the code audit confirms these are absent). | Section in Ch. 9 | Med | S–M |
| A4 | **Performance & benchmarks** | The Non-functional Evaluation (Ch. 9) is **qualitative** ("addressed structurally") — no measured latency/throughput or load-test numbers. | Section in Ch. 9 | Med | M |
| A5 | **Development methodology & team contribution** | No coverage of process (Git/GitHub workflow, branching, agile), timeline, or a **who-did-what** matrix — usually expected by the committee. | New short chapter or appendix | 📕 High | S–M |
| A6 | **Visual walkthrough / screenshots** | All figures are TikZ; there are **no UI screenshots** of the web app, 2D office, or mobile. The "Feature Tour" (Ch. 7) is prose-only. | Screenshot set in `figures/`, referenced in Ch. 6–8 | Med | S (needs images) |

**Suggested order:** A1 (Data Design — source material already exists in
`DATABASE.md`), A2 (Security — writeable from the gateway/auth code), A5 (Methodology
+ team contribution), then A3/A4/A6. A1, A2, A3, A4 can be written from the codebase
now; A5 needs the team's process details; A6 needs screenshots supplied.

> Not included here (tracked separately as academic front/back-matter, not technical
> sections): References/Bibliography, List of Abbreviations, Acknowledgements, Arabic
> abstract (ملخص), and Appendices.

---

*Generated from the graduation book's self-assessment plus a four-part code audit
(backend, web, SkyOffice, mobile/cross-cutting). Secret values are referenced by
location only and must be rotated, not reused.*
