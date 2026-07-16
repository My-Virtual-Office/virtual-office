<h1 align="center">Virtual Office — platform</h1>

<p align="center">
  <b>One workspace. Not five disconnected tools.</b><br>
  Chat, tasks, meetings, an AI assistant, and a real-time 2D office —
  on web, mobile, and a place your team can walk into.
</p>

<p align="center">
  <a href="https://my-virtual-office.github.io"><b>Docs & feature tour →</b></a>
</p>

---

This is the **umbrella repo**: it wires the whole system together and pins each
component as a git submodule. Clone it with submodules and one command runs
everything.

```bash
git clone --recurse-submodules https://github.com/My-Virtual-Office/virtual-office.git
cd virtual-office
cp .env.example .env          # fill in the secrets
docker compose up -d --build  # ~12 images on first boot; then it's live
```

Then open **http://localhost:3001**. See [RUN.md](RUN.md) for logins and the
seeded demo, [DEPLOY.md](DEPLOY.md) / [DOCKER.md](DOCKER.md) for the details.

## What's in here

| Path | Repo | What |
|---|---|---|
| `backend/` | [backend](https://github.com/My-Virtual-Office/backend) | 9 Spring Boot microservices + gateway |
| `website/` | [website](https://github.com/My-Virtual-Office/website) | React web app |
| `SkyOffice/` | [SkyOffice](https://github.com/My-Virtual-Office/SkyOffice) | Phaser + Colyseus 2D office |
| `Mobile_application/` | [Mobile_application](https://github.com/My-Virtual-Office/Mobile_application) | Flutter app |
| `Docs/` | [Docs](https://github.com/My-Virtual-Office/Docs) | markdown source docs |
| `doc/` | [docs site](https://github.com/My-Virtual-Office/My-Virtual-Office.github.io) | the live documentation site |
| `ai-service/` | *(here)* | the function-calling AI assistant (Node) |
| `seed/` | *(here)* | the Northstar demo dataset seeder |
| `observability/` | *(here)* | Loki · Promtail · Grafana · Prometheus configs |
| `presentation/` | *(here)* | deck, slides, screenshots |
| `notes/` | *(here)* | internal working notes |

The six component folders are **submodules** — develop each in its own repo; this
repo pins the commit the stack is known to run at.

## Working with the submodules

```bash
git pull --recurse-submodules              # update umbrella + all pinned components
git submodule update --remote website      # move one to the latest of its branch

# changed code inside a component:
cd backend && git commit -am "…" && git push && cd ..
git add backend && git commit -m "bump backend" && git push   # move the pin
```

## The stack

Spring Boot · Spring Cloud Gateway · React · Flutter · Phaser + Colyseus ·
PostgreSQL · MongoDB · MySQL · Redis · RabbitMQ · Agora · Docker Compose ·
Grafana + Loki + Prometheus. End-to-end encrypted DMs (ECDH + AES-GCM, in the
browser). One `docker compose up`.
