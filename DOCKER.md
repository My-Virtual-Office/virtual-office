# Running Virtual Office with Docker Compose

One command brings up the **entire platform** — datastores, six backend
microservices, the Colyseus realtime server, and both web frontends — on a
single Docker network.

```bash
cp .env.example .env      # then edit secrets for anything beyond local dev
docker compose up --build -d
```

First run compiles all Java modules and installs the Node dependencies, so it
takes a few minutes. Afterwards, images are cached and startup is fast.

## Entry points

| What | URL | Notes |
|------|-----|-------|
| Web client (React) | http://localhost:3001 | Slack-style workspace/chat UI |
| SkyOffice (2D office) | http://localhost:5000 | Phaser office + proximity voice |
| API gateway | http://localhost:8080 | Single edge for all `/api/**` REST + WS |
| RabbitMQ console | http://localhost:15672 | `guest` / `guest` |

Backend services are also published individually for debugging: user `8091`,
workspace `8087`, chat `8084`, room `8086`, notifications `8082`.

## Architecture

```
Browser ──► web-client (nginx :3001) ──/api/*──► gateway-api :8080 ─┬─► user-service    :8091 ─► MySQL
                                                                    ├─► workspace-service:8087 ─► Postgres
        ──► skyoffice-client (nginx :5000)                          ├─► chat-service     :8084 ─► Mongo · Redis
              │  (absolute URLs, host ports)                        └─► room-service     :8086 ─► Mongo · Redis
              ├──ws :2567──► skyoffice-server (Colyseus)
              └──ws :8086──► room-service (voice tickets)     notifications-service :8082 ─► Mongo · Redis
                                                              ( all services ◄──► RabbitMQ event bus )
```

### How the pieces are wired

- **web-client** talks to the backend with **same-origin relative paths**
  (`/api/...`, STOMP over `window.location.host`). Its nginx therefore
  **reverse-proxies `/api/*` to the gateway** (REST *and* WebSocket upgrade).
- **skyoffice-client** uses **absolute URLs baked at build time**
  (`VITE_API_URL`, `VITE_SERVER_URL`, `VITE_ROOM_WS_URL`) — the browser reaches
  the host-published ports directly. Change them in `.env`
  (`PUBLIC_*`) and rebuild that image.
- **gateway-api** validates every JWT at the edge and routes to services by
  their Compose DNS names.
- **JWT_SECRET** and **INTERNAL_API_TOKEN** are shared by the services that must
  agree on them (gateway, user, workspace, room, chat, and the SkyOffice server)
  — set once in `.env`.

## Design choices

- **One inline build recipe for all six Spring services.** A single
  parameterized multi-stage build (`SERVICE` arg → `mvn -pl $SERVICE -am`)
  produces every backend image, with a shared BuildKit `~/.m2` cache mount so
  dependencies download only once.
- **Nothing added to the source repos.** All Docker build logic lives inline in
  `docker-compose.yml`; the only per-repo files are `.dockerignore`s.
- **Health-gated startup.** Every datastore has a real healthcheck; services
  wait on `service_healthy`, and the gateway waits until all four routed
  services are healthy — so `up` converges without connection-refused races.
- **Persistent data.** MySQL, Postgres, Mongo, and RabbitMQ use named volumes.

The two stub modules (`calendar-service`, `tasks-service`) are intentionally
excluded — they carry no datastore config and the gateway routes nothing to them.

## Common commands

```bash
docker compose ps                     # status + health of every service
docker compose logs -f gateway-api    # tail one service
docker compose up --build -d web-client   # rebuild one image after a code change
docker compose down                   # stop (keep data volumes)
docker compose down -v                # stop and wipe all data
```

## Security note

`.env` ships with **dev-only defaults** (weak JWT secret, default DB passwords,
and the committed Agora credentials). Before any non-local deployment, rotate
every secret and keep the real `.env` out of version control.
