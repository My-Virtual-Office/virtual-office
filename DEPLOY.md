# Virtual Office — Deploy with Docker Compose

One command brings up the whole platform — datastores, the Spring Boot
microservices, the Colyseus realtime server, both web frontends, and the
logging stack — on a single Docker network.

## Prerequisites

- Docker Engine + the Docker Compose plugin (`docker compose version`)
- ~6 GB free disk for images (first build compiles all Java modules and installs
  the Node dependencies, so it takes a few minutes; later builds are cached)

## Quick start

```bash
cp .env.example .env      # then edit .env and replace every placeholder secret
docker compose up -d --build
```

`docker compose config` validates the file without starting anything.
`docker compose logs -f <service>` tails a service. `docker compose down`
stops the stack (`-v` also wipes the data volumes).

## Entry points

| What                  | URL                     | Notes                                     |
|-----------------------|-------------------------|-------------------------------------------|
| Web client (React)    | http://localhost:3001   | Workspace / chat UI                       |
| SkyOffice (2D office) | http://localhost:5000   | Phaser office + proximity voice           |
| API gateway           | http://localhost:8080   | Single edge for all `/api/**` REST + WS   |
| RabbitMQ console      | http://localhost:15672  | `RABBITMQ_USER` / `RABBITMQ_PASSWORD`     |
| Grafana (logs)        | http://localhost:3005   | `GRAFANA_USER` / `GRAFANA_PASSWORD`       |

Backend services are also published individually for debugging: user `8091`,
workspace `8087`, calendar `8083`, chat `8084`, tasks `8085`, room `8086`,
notifications `8082`. Postgres is on host `5433` (container `5432`).

## How the builds are wired

| Service            | Build context | Dockerfile               |
|--------------------|---------------|--------------------------|
| all backend svcs   | `./backend`   | `Dockerfile` (`SERVICE` build arg selects the Maven module) |
| skyoffice-server   | `./SkyOffice` | `server/Dockerfile`      |
| skyoffice-client   | `./SkyOffice` | `client/Dockerfile` (+ `client/nginx.conf`) |
| web-client         | `./website`   | `Dockerfile` (+ `nginx.conf`) |

- **web-client** talks to the backend with same-origin relative paths, so its
  nginx reverse-proxies `/api/*` (REST + STOMP-over-WebSocket) to the gateway.
  The nginx config is baked into the image from `website/nginx.conf` and keeps
  long-lived STOMP sockets alive (`proxy_read_timeout 3600s`, long resolver TTL).
- **skyoffice-client** uses absolute URLs baked at build time (`PUBLIC_*` in
  `.env`). Change them and rebuild that image: `docker compose build skyoffice-client`.

## LAN / multi-device note

The frontends are reachable from any device on the same WiFi. Because the
SkyOffice client bakes absolute host URLs at build time, point the `PUBLIC_*`
values in `.env` at the host machine's LAN IP (e.g. `http://192.168.1.20:8080`)
instead of `localhost`, then rebuild the frontends. `GATEWAY_CORS_ORIGINS=*`
reflects the request origin so cross-origin LAN calls work without hardcoding an
IP. Lock CORS and the `PUBLIC_*` URLs down to real origins for production.
