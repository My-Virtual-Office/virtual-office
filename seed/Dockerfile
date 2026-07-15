# One-shot seeder: bash + curl + jq (API work), psql (desk.personalImageUrl has
# no write API, so it is set directly in Postgres) and redis-cli (chat read
# cursors live in Redis and must be dropped when the history is replaced).
# Runs seed.sh and exits.
# Launch with `docker compose --profile seed up seed`.
FROM alpine:3.20

RUN apk add --no-cache bash curl jq coreutils postgresql-client redis

WORKDIR /seed
COPY seed.sh load-history.js ./
COPY seed-data.json conversations.json ./
COPY avatars ./avatars
RUN chmod +x seed.sh

# GATEWAY_URL / PG* / SEED_OUT are injected by compose.
ENTRYPOINT ["bash", "/seed/seed.sh"]
