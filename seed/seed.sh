#!/usr/bin/env bash
# =============================================================================
# Northstar Software — demo data seeder for the Virtual Office platform.
#
# Registers 15 users, creates the "Northstar Software" workspace, invites every
# member, assigns titles/teams/presence, then seeds teams, channels, projects,
# ~48 tasks, voice rooms and a handful of messages — all through the API gateway.
#
# Everything is driven by seed-data.json (same folder). Safe to re-run: users
# fall back to login, workspace/teams/channels/spaces/rooms are create-if-missing,
# and one-shot content (tasks/messages) is skipped once seeded (override FORCE=1).
#
# Usage:
#   GATEWAY_URL=http://localhost:8080 ./seed.sh      # from the host
#   docker compose --profile seed up seed            # inside the docker network
#
# Env:
#   GATEWAY_URL   base URL of the gateway   (default http://gateway-api:8080)
#   SEED_PASSWORD password for every user   (default Northstar@2026)
#   SEED_DATA     path to the JSON dataset  (default <script dir>/seed-data.json)
#   FORCE         =1 to re-create tasks/messages even if already seeded
#   WAIT_TIMEOUT  seconds to wait for the gateway (default 300)
# =============================================================================
set -uo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://gateway-api:8080}"
PASSWORD="${SEED_PASSWORD:-Northstar@2026}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${SEED_DATA:-$SCRIPT_DIR/seed-data.json}"
FORCE="${FORCE:-0}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"

# ── logging ──────────────────────────────────────────────────────────────────
c_reset=$'\033[0m'; c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_dim=$'\033[2m'
log()  { printf '%s»%s %s\n'  "$c_blue"   "$c_reset" "$*"; }
ok()   { printf '  %s✓%s %s\n' "$c_green"  "$c_reset" "$*"; }
warn() { printf '  %s!%s %s\n' "$c_yellow" "$c_reset" "$*"; }
err()  { printf '%sERROR%s %s\n' "$c_red"  "$c_reset" "$*" >&2; }
dim()  { printf '  %s%s%s\n'    "$c_dim"   "$*" "$c_reset"; }

command -v jq   >/dev/null || { err "jq is required";   exit 1; }
command -v curl >/dev/null || { err "curl is required"; exit 1; }
[ -f "$DATA" ] || { err "dataset not found: $DATA"; exit 1; }

# ── HTTP helper: sets RESP_CODE and RESP_BODY ────────────────────────────────
RESP_CODE=""; RESP_BODY=""
api() {
  local method="$1" path="$2" token="$3" body="${4:-}"
  local args=(-s -X "$method" -H 'Content-Type: application/json' "$GATEWAY_URL$path")
  [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
  [ -n "$body" ]  && args+=(--data "$body")
  local out; out=$(curl "${args[@]}" -w $'\n%{http_code}')
  RESP_CODE="${out##*$'\n'}"
  RESP_BODY="${out%$'\n'*}"
}
is2xx() { [[ "$RESP_CODE" =~ ^2 ]]; }
jqb()   { jq -r "$1" <<<"$RESP_BODY" 2>/dev/null; }

# ── associative maps: ref -> value ───────────────────────────────────────────
declare -A TOKEN UID_ EMAIL_ TEAM_ID SPACE_ID CHAN_ID DESK_BY_UID
declare -a USER_REFS
WS_ID=""
n_users=0 n_members=0 n_teams=0 n_channels=0 n_spaces=0 n_tasks=0 n_rooms=0 n_msgs=0 n_events=0 n_photos=0

# =============================================================================
# 0. Wait for the gateway to answer
# =============================================================================
log "Waiting for gateway at $GATEWAY_URL (timeout ${WAIT_TIMEOUT}s)…"
deadline=$(( $(date +%s) + WAIT_TIMEOUT ))
until code=$(curl -s -o /dev/null -w '%{http_code}' "$GATEWAY_URL/actuator/health" 2>/dev/null) \
      && [[ "$code" =~ ^(200|401|403|404)$ ]]; do
  [ "$(date +%s)" -ge "$deadline" ] && { err "gateway did not become ready in time"; exit 1; }
  sleep 3
done
ok "Gateway is up (HTTP $code)"

# =============================================================================
# 1. Users — register (or log in if they already exist)
# =============================================================================
log "Registering users…"
while IFS= read -r u; do
  ref=$(jq -r '.ref' <<<"$u")
  USER_REFS+=("$ref")
  body=$(jq -c --arg pw "$PASSWORD" \
    '{firstName:.firstName,lastName:.lastName,email:.email,password:$pw,phoneNumber:.phone}' <<<"$u")
  email=$(jq -r '.email' <<<"$u")
  api POST /api/auth/register "" "$body"
  if is2xx; then
    :
  elif [ "$RESP_CODE" = 409 ]; then
    api POST /api/auth/login "" "$(jq -nc --arg e "$email" --arg pw "$PASSWORD" '{email:$e,password:$pw}')"
  fi
  tok=$(jqb '.token'); id=$(jqb '.id')
  if [ -n "$tok" ] && [ "$tok" != null ] && [ -n "$id" ] && [ "$id" != null ] && [ "$id" != 0 ]; then
    TOKEN[$ref]="$tok"; UID_[$ref]="$id"; EMAIL_[$ref]="$email"; n_users=$((n_users+1))
    ok "$(printf '%-8s' "$ref") id=$id  $email"
  else
    warn "could not obtain token for $email (HTTP $RESP_CODE)"
  fi
done < <(jq -c '.users[]' "$DATA")
[ "$n_users" -gt 0 ] || { err "no users could be created — aborting"; exit 1; }

owner_ref=$(jq -r '.users[] | select(.wsRole=="OWNER") | .ref' "$DATA" | head -1)
OWNER_TOKEN="${TOKEN[$owner_ref]:-}"
[ -n "$OWNER_TOKEN" ] || { err "owner ($owner_ref) has no token — aborting"; exit 1; }

# =============================================================================
# 2. Workspace — create as the owner (auto-creates the owner's desk)
# =============================================================================
log "Creating workspace…"
WSLUG=$(jq -r '.workspace.slug' "$DATA")
ws_body=$(jq -c '{name:.workspace.name, slug:.workspace.slug, description:.workspace.description, defaultTimezone:.workspace.timezone}' "$DATA")
api POST /api/workspace "$OWNER_TOKEN" "$ws_body"
if is2xx; then
  WS_ID=$(jqb '.id'); ok "workspace '$(jq -r .workspace.name "$DATA")' created (id=$WS_ID)"
else
  api GET /api/workspace/mine "$OWNER_TOKEN"
  WS_ID=$(jq -r --arg s "$WSLUG" '.[]? | select(.slug==$s) | .id' <<<"$RESP_BODY" | head -1)
  [ -n "$WS_ID" ] && ok "workspace already existed (id=$WS_ID)" || { err "cannot create or find workspace (HTTP $RESP_CODE)"; exit 1; }
fi

# =============================================================================
# 3. Teams
# =============================================================================
log "Creating teams…"
api GET "/api/workspace/$WS_ID/teams" "$OWNER_TOKEN"
existing_teams="$RESP_BODY"
while IFS= read -r t; do
  ref=$(jq -r '.ref' <<<"$t"); name=$(jq -r '.name' <<<"$t")
  id=$(jq -r --arg n "$name" '.[]? | select(.name==$n) | .id' <<<"$existing_teams" | head -1)
  if [ -z "$id" ]; then
    api POST "/api/workspace/$WS_ID/teams" "$OWNER_TOKEN" "$(jq -c '{name:.name,description:.description}' <<<"$t")"
    is2xx && id=$(jqb '.id')
  fi
  if [ -n "$id" ] && [ "$id" != null ]; then TEAM_ID[$ref]="$id"; n_teams=$((n_teams+1)); ok "team $name (id=$id)"; else warn "team $name failed (HTTP $RESP_CODE)"; fi
done < <(jq -c '.teams[]' "$DATA")

# =============================================================================
# 4. Members — invite (as owner) then accept (as the invitee)
# =============================================================================
log "Adding members…"
api GET "/api/workspace/$WS_ID/desks?page=0&size=100" "$OWNER_TOKEN"
member_uids=" $(jq -r '.content[]?.userId' <<<"$RESP_BODY" | tr '\n' ' ') "
while IFS= read -r u; do
  ref=$(jq -r '.ref' <<<"$u"); role=$(jq -r '.wsRole' <<<"$u"); email=$(jq -r '.email' <<<"$u")
  [ "$role" = OWNER ] && continue
  [ -n "${TOKEN[$ref]:-}" ] || { warn "$ref has no token, skipping"; continue; }
  uid="${UID_[$ref]}"
  if [[ "$member_uids" == *" $uid "* ]]; then ok "$(printf '%-8s' "$ref") already a member"; n_members=$((n_members+1)); continue; fi
  # invite
  api POST "/api/workspace/$WS_ID/invitations" "$OWNER_TOKEN" "$(jq -nc --arg e "$email" --arg r "$role" '{email:$e,role:$r}')"
  tok=""
  if is2xx; then tok=$(jqb '.token'); fi
  if [ -z "$tok" ] || [ "$tok" = null ]; then
    api GET "/api/workspace/$WS_ID/invitations" "$OWNER_TOKEN"
    tok=$(jq -r --arg e "$email" '.[]? | select(.invitedEmail==$e and .status=="PENDING") | .token' <<<"$RESP_BODY" | head -1)
  fi
  [ -n "$tok" ] && [ "$tok" != null ] || { warn "no invite token for $email (HTTP $RESP_CODE)"; continue; }
  # accept as the invitee
  api POST "/api/invitations/accept?token=$tok" "${TOKEN[$ref]}" ""
  if is2xx || [ "$RESP_CODE" = 409 ]; then ok "$(printf '%-8s' "$ref") joined as $role"; n_members=$((n_members+1)); else warn "$ref accept failed (HTTP $RESP_CODE)"; fi
done < <(jq -c '.users[]' "$DATA")

# refresh desk directory: userId -> deskId
api GET "/api/workspace/$WS_ID/desks?page=0&size=100" "$OWNER_TOKEN"
while IFS=$'\t' read -r duid ddesk; do
  [ -n "$duid" ] && DESK_BY_UID[$duid]="$ddesk"
done < <(jq -r '.content[]? | "\(.userId)\t\(.id)"' <<<"$RESP_BODY")

# =============================================================================
# 5. Titles + team assignment (admin), then per-user presence status
# =============================================================================
log "Assigning titles, teams and presence…"
while IFS= read -r u; do
  ref=$(jq -r '.ref' <<<"$u")
  [ -n "${UID_[$ref]:-}" ] || continue
  deskId="${DESK_BY_UID[${UID_[$ref]}]:-}"
  [ -n "$deskId" ] || { warn "$ref has no desk yet, skipping profile"; continue; }
  title=$(jq -r '.title' <<<"$u"); teamRef=$(jq -r '.team' <<<"$u")
  teamId="${TEAM_ID[$teamRef]:-}"
  # title + team via admin membership patch
  if [ -n "$teamId" ]; then mbody=$(jq -nc --arg t "$title" --argjson tid "$teamId" '{title:$t,teamId:$tid}')
  else mbody=$(jq -nc --arg t "$title" '{title:$t}'); fi
  api PATCH "/api/workspace/$WS_ID/desks/$deskId/membership" "$OWNER_TOKEN" "$mbody"
  # fullName is what chat/member lists display — without it they fall back to
  # "User <id>". It is NOT settable via the admin membership PATCH; only the desk
  # owner can set it (PUT own desk). Sending just fullName leaves other fields alone.
  full="$(jq -r '.firstName + " " + .lastName' <<<"$u")"
  api PUT "/api/workspace/$WS_ID/desks/$deskId" "${TOKEN[$ref]}" "$(jq -nc --arg n "$full" '{fullName:$n}')"
  # presence status via the user's own token
  status=$(jq -r '.status' <<<"$u"); emoji=$(jq -r '.statusEmoji' <<<"$u"); text=$(jq -r '.statusText' <<<"$u")
  sbody=$(jq -nc --arg s "$status" --arg e "$emoji" --arg x "$text" \
    '{status:$s, statusEmoji:(if $e=="" then null else $e end), statusCustomText:(if $x=="" then null else $x end)}')
  api PATCH "/api/workspace/$WS_ID/desks/$deskId/status" "${TOKEN[$ref]}" "$sbody"
  ok "$(printf '%-8s' "$ref") $title  ·  $status"
done < <(jq -c '.users[]' "$DATA")

# helper: turn a JSON array of member refs into a JSON array of numeric ids ("ALL" -> everyone)
members_json() {
  local refs_json="$1"; local -a ids=()
  if [ "$(jq -r '.[0]' <<<"$refs_json")" = "ALL" ]; then
    for r in "${USER_REFS[@]}"; do [ -n "${UID_[$r]:-}" ] && ids+=("${UID_[$r]}"); done
  else
    while IFS= read -r r; do [ -n "${UID_[$r]:-}" ] && ids+=("${UID_[$r]}"); done < <(jq -r '.[]' <<<"$refs_json")
  fi
  printf '%s\n' "${ids[@]}" | jq -R 'tonumber' | jq -sc '.'
}

# =============================================================================
# 6. Channels — create as their owner, with resolved member ids
# =============================================================================
log "Creating channels…"
api GET "/api/chat/channels?workspaceId=$WS_ID&page=1&limit=100" "$OWNER_TOKEN"
declare -A CHAN_BY_NAME
while IFS=$'\t' read -r cn ci; do [ -n "$cn" ] && CHAN_BY_NAME[$cn]="$ci"; done \
  < <(jq -r '.content[]? | "\(.name)\t\(.id)"' <<<"$RESP_BODY")
while IFS= read -r c; do
  ref=$(jq -r '.ref' <<<"$c"); name=$(jq -r '.name' <<<"$c")
  if [ -n "${CHAN_BY_NAME[$name]:-}" ]; then CHAN_ID[$ref]="${CHAN_BY_NAME[$name]}"; ok "#$name already exists"; continue; fi
  ownerRef=$(jq -r '.owner' <<<"$c"); ownerTok="${TOKEN[$ownerRef]:-$OWNER_TOKEN}"
  vis=$(jq -r '.visibility' <<<"$c"); desc=$(jq -r '.description' <<<"$c")
  mids=$(members_json "$(jq -c '.members' <<<"$c")")
  body=$(jq -nc --arg n "$name" --argjson ws "$WS_ID" --arg d "$desc" --arg v "$vis" --argjson m "$mids" \
    '{name:$n, workspaceId:$ws, description:$d, visibility:$v, members:$m}')
  api POST /api/chat/channels "$ownerTok" "$body"
  if is2xx; then CHAN_ID[$ref]=$(jqb '.id'); n_channels=$((n_channels+1)); ok "#$name ($vis, $(jq -r '.members|length' <<<"$body") members)"
  else warn "#$name failed (HTTP $RESP_CODE)"; fi
done < <(jq -c '.channels[]' "$DATA")

# =============================================================================
# 7. Projects (task "spaces") — created by the owner, all users as members
# =============================================================================
log "Creating projects…"
api GET "/api/tasks/spaces?workspaceId=$WS_ID" "$OWNER_TOKEN"
existing_spaces="$RESP_BODY"
SEEDED=0
all_ids=$(members_json '["ALL"]')
while IFS= read -r s; do
  ref=$(jq -r '.ref' <<<"$s"); name=$(jq -r '.name' <<<"$s")
  id=$(jq -r --arg n "$name" '.[]? | select(.name==$n) | .id' <<<"$existing_spaces" | head -1)
  if [ -n "$id" ]; then SEEDED=1; else
    api POST /api/tasks/spaces "$OWNER_TOKEN" "$(jq -nc --arg n "$name" --argjson ws "$WS_ID" --argjson m "$all_ids" '{workspaceId:$ws,name:$n,memberUserIds:$m}')"
    is2xx && id=$(jqb '.id')
  fi
  if [ -n "$id" ] && [ "$id" != null ]; then SPACE_ID[$ref]="$id"; n_spaces=$((n_spaces+1)); ok "$name (id=$id)"; else warn "space $name failed (HTTP $RESP_CODE)"; fi
done < <(jq -c '.spaces[]' "$DATA")

# Local calendar day + UTC offset, used to turn every relative date in the
# dataset into an absolute instant. Computed once, here, because both the task
# and the event phases need them.
DAY_LOCAL=$(date +%F); TZOFF=$(date +%:z)

# =============================================================================
# 8. Tasks (one-shot: skipped if already seeded unless FORCE=1)
# =============================================================================
if [ "$SEEDED" = 1 ] && [ "$FORCE" != 1 ]; then
  warn "projects already existed — skipping task/message seeding (set FORCE=1 to re-create)"
else
  log "Creating tasks…"
  while IFS= read -r t; do
    spRef=$(jq -r '.space' <<<"$t"); asgRef=$(jq -r '.assignee' <<<"$t")
    spId="${SPACE_ID[$spRef]:-}"; asgId="${UID_[$asgRef]:-}"
    [ -n "$spId" ] || { warn "task '$(jq -r .title <<<"$t")' — unknown space $spRef"; continue; }
    # Due dates are stored relative to the seed run (dueDay: -14 = two weeks ago,
    # +7 = a week out) so the board always straddles "now" whenever it is seeded,
    # instead of being pinned to the day the dataset was written.
    dday=$(jq -r '.dueDay // empty' <<<"$t"); dtime=$(jq -r '.dueTime // "17:00"' <<<"$t")
    if [ -n "$dday" ]; then
      dueIso="$(date -d "$DAY_LOCAL ${dday} days" +%F)T${dtime}:00${TZOFF}"
    else
      dueIso=$(jq -r '.due // empty' <<<"$t")
    fi
    body=$(jq -c --argjson ws "$WS_ID" --argjson sp "$spId" --argjson as "${asgId:-null}" --arg due "${dueIso:-}" \
      '{workspaceId:$ws, spaceId:$sp, title:.title, description:.description, status:.status, priority:.priority,
        dueDate:(if $due=="" then null else $due end), assigneeUserId:$as}' <<<"$t")
    api POST /api/tasks "$OWNER_TOKEN" "$body"
    if is2xx; then n_tasks=$((n_tasks+1)); else warn "task '$(jq -r .title <<<"$t")' failed (HTTP $RESP_CODE)"; fi
  done < <(jq -c '.tasks[]' "$DATA")
  ok "$n_tasks tasks created"
fi

# =============================================================================
# 9. Voice rooms (idempotent: duplicate name -> 409, treated as ok)
# =============================================================================
log "Creating voice rooms…"
while IFS= read -r r; do
  name=$(jq -r '.name' <<<"$r")
  api POST /api/rooms "$OWNER_TOKEN" "$(jq -c --argjson ws "$WS_ID" '{name:.name, workspaceId:$ws, maxParticipants:.capacity}' <<<"$r")"
  if is2xx; then n_rooms=$((n_rooms+1)); ok "🔊 $name"; elif [ "$RESP_CODE" = 409 ]; then ok "🔊 $name (exists)"; else warn "room $name failed (HTTP $RESP_CODE)"; fi
done < <(jq -c '.rooms[]' "$DATA")

# =============================================================================
# 9b. Calendar — the last two weeks through the next two
#
# Everything is stamped relative to the seed run, so the calendar always
# straddles "now": `recurringEvents` are expanded across working days (Sun-Thu,
# Egypt) and `events` are one-offs at a `day` offset. Times are LOCAL wall-clock
# with the local UTC offset, so they land on the day the browser thinks they
# should (the desk agenda filters by the viewer's local day).
# =============================================================================
log "Creating calendar events…"
EV_FROM=${EVENTS_FROM:--15}   # days back
EV_TO=${EVENTS_TO:-14}        # days forward

# Query bounds in Z-form UTC: a literal '+' offset in a URL query decodes to a
# space and 500s, so convert the window's edges to UTC for the GET.
win_from=$(date -u -d "$(date -d "$DAY_LOCAL ${EV_FROM} days" +%F)T00:00:00${TZOFF}" +%Y-%m-%dT%H:%M:%SZ)
win_to=$(date -u -d "$(date -d "$DAY_LOCAL ${EV_TO} days" +%F)T23:59:59${TZOFF}" +%Y-%m-%dT%H:%M:%SZ)

# The calendar list endpoint is a SHARED team calendar (every workspace event in
# the window), so idempotency is one workspace-level check over the whole span.
api GET "/api/calendar/events?workspaceId=$WS_ID&from=$win_from&to=$win_to" "$OWNER_TOKEN"
if is2xx && [ "$(jqb 'type')" = array ]; then existing_ev=$(jqb 'length'); else existing_ev=0; fi
[[ "$existing_ev" =~ ^[0-9]+$ ]] || existing_ev=0

if [ "$existing_ev" -gt 0 ] && [ "$FORCE" != 1 ]; then
  warn "workspace already has $existing_ev event(s) in this window — skipping (FORCE=1 to add anyway)"
else
  # refs -> [{userId,email}] for the attendee list
  attendees_json() {
    local out='[]'
    while IFS= read -r ar; do
      [ -n "${UID_[$ar]:-}" ] || continue
      out=$(jq -c --argjson a "$out" --argjson id "${UID_[$ar]}" --arg em "${EMAIL_[$ar]:-}" '$a + [{userId:$id,email:$em}]' <<<'null')
    done < <(jq -r '.attendees[]?' <<<"$1")
    printf '%s' "$out"
  }
  # Create one event for `owner` on the date `DAY_LOCAL + off`.
  make_event() {
    local ev="$1" off="$2"
    local owner tok date_on att body
    owner=$(jq -r '.owner' <<<"$ev"); tok="${TOKEN[$owner]:-}"
    [ -n "$tok" ] || return 0
    date_on=$(date -d "$DAY_LOCAL ${off} days" +%F)
    att=$(attendees_json "$ev")
    body=$(jq -c --argjson ws "$WS_ID" \
      --arg st "${date_on}T$(jq -r '.start' <<<"$ev"):00${TZOFF}" \
      --arg en "${date_on}T$(jq -r '.end' <<<"$ev"):00${TZOFF}" \
      --argjson at "$att" \
      '{workspaceId:$ws, title:.title, description:(.description // ""), startTime:$st, endTime:$en, busy:true, attendees:$at}' <<<"$ev")
    api POST /api/calendar/events "$tok" "$body"
    if is2xx; then n_events=$((n_events+1)); else warn "event '$(jq -r '.title' <<<"$ev")' (day $off) failed (HTTP $RESP_CODE)"; fi
  }

  # Recurring ceremonies across working days only — a standup on the weekend
  # would give the whole thing away.
  while IFS= read -r r; do
    days=$(jq -r '[.days[]] | join(",")' <<<"$r")
    for ((off=EV_FROM; off<=EV_TO; off++)); do
      # date +%u: 1=Mon .. 7=Sun. Egypt works Sun-Thu; Fri/Sat are the weekend.
      case "$(date -d "$DAY_LOCAL ${off} days" +%u)" in
        7) dow=sun ;; 1) dow=mon ;; 2) dow=tue ;; 3) dow=wed ;; 4) dow=thu ;; 5) dow=fri ;; *) dow=sat ;;
      esac
      [[ ",$days," == *",$dow,"* ]] || continue
      make_event "$r" "$off"
    done
  done < <(jq -c '.recurringEvents[]?' "$DATA")

  # One-offs at their own day offset, snapped onto a working day — a raw offset
  # happily lands a board meeting on a Saturday, which gives the demo away in a
  # Sun-Thu country. Day 0 is never moved: today is today.
  snap_workday() {
    local off="$1"
    for _ in 1 2; do
      case "$(date -d "$DAY_LOCAL ${off} days" +%u)" in
        5) off=$((off + 2)) ;;   # Fri -> Sun
        6) off=$((off + 1)) ;;   # Sat -> Sun
        *) break ;;
      esac
    done
    printf '%s' "$off"
  }
  while IFS= read -r ev; do
    off=$(jq -r '.day // 0' <<<"$ev")
    [ "$off" -ge "$EV_FROM" ] && [ "$off" -le "$EV_TO" ] || continue
    [ "$off" -ne 0 ] && off=$(snap_workday "$off")
    make_event "$ev" "$off"
  done < <(jq -c '.events[]?' "$DATA")
  ok "$n_events calendar events created (day $EV_FROM .. +$EV_TO)"
fi

# =============================================================================
# 10. Profile pictures
#
# Two places show a picture, and they read from DIFFERENT stores:
#   * the sidebar's own-avatar  -> user-service photo (POST /api/users/me/photo)
#   * chat / members / contacts -> desk.personalImageUrl (workspace-service)
# personalImageUrl has NO write API (it is never set anywhere in the service), so
# it is written straight to Postgres and points at /avatars/<ref>.png, which the
# web-client serves from its own origin (website/public/avatars/).
# =============================================================================
log "Uploading profile pictures…"
while IFS= read -r u; do
  ref=$(jq -r '.ref' <<<"$u")
  tok="${TOKEN[$ref]:-}"; img="$SCRIPT_DIR/avatars/$ref.png"
  [ -n "$tok" ] && [ -f "$img" ] || { warn "no token/image for $ref"; continue; }
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$GATEWAY_URL/api/users/me/photo" \
    -H "Authorization: Bearer $tok" -F "file=@${img};type=image/png")
  if [ "$code" = 200 ]; then n_photos=$((n_photos+1)); else warn "photo $ref -> HTTP $code"; fi
done < <(jq -c '.users[]' "$DATA")
ok "$n_photos profile photos uploaded"

if command -v psql >/dev/null && [ -n "${PGHOST:-}" ]; then
  log "Linking desk avatars…"
  sql=""
  for ref in "${USER_REFS[@]}"; do
    [ -n "${UID_[$ref]:-}" ] || continue
    sql+="UPDATE desk SET personal_image_url='/avatars/${ref}.png' WHERE workspace_id=${WS_ID} AND user_id=${UID_[$ref]};"
  done
  if printf '%s' "$sql" | PGPASSWORD="${PGPASSWORD:-}" psql -q -h "$PGHOST" -U "${PGUSER:-workspace}" -d "${PGDATABASE:-workspace}" -f - 2>/dev/null; then
    ok "desk avatars linked to /avatars/<ref>.png"
  else
    warn "could not update desk.personal_image_url (avatars will fall back to initials)"
  fi
else
  warn "psql/PGHOST unavailable — skipping desk avatar link (chat avatars will fall back)"
fi

# =============================================================================
# 11. Chat history hand-off
#
# conversations.json holds ~1.8k messages spread over 3 months. The REST API
# cannot backdate a message (createdAt is server-set), and the channel list
# paginates by _id, so the history is inserted straight into MongoDB with
# ObjectIds built from each message's historical timestamp. This step only
# renders the runnable script; the `seed-history` service (mongo image, which
# has mongosh) executes it once this container exits successfully.
# =============================================================================
if [ -f "$SCRIPT_DIR/conversations.json" ] && [ -f "$SCRIPT_DIR/load-history.js" ]; then
  outdir="${SEED_OUT:-/seedout}"
  if mkdir -p "$outdir" 2>/dev/null; then
    umap="{}"
    for ref in "${USER_REFS[@]}"; do
      [ -n "${UID_[$ref]:-}" ] || continue
      umap=$(jq -c --argjson m "$umap" --arg k "$ref" --argjson v "${UID_[$ref]}" '$m + {($k): $v}' <<<'null')
    done
    {
      printf 'const SEED = '
      jq -n --argjson ws "$WS_ID" --arg base "$(date +%F)" --argjson users "$umap" \
        --slurpfile conv "$SCRIPT_DIR/conversations.json" \
        '{wsId:$ws, base:$base, users:$users, conversations:$conv[0]}'
      printf ';\n'
      cat "$SCRIPT_DIR/load-history.js"
    } > "$outdir/history-run.js"
    # seed-history wipes and reinserts each channel's messages, which invalidates
    # every read cursor pointing into them. A cursor left pointing at a deleted
    # message silently breaks unread for good: unread counts `_id > cursor`, and
    # the old ids can sort above everything reinserted. Drop them here.
    if command -v redis-cli >/dev/null && [ -n "${REDIS_HOST:-}" ]; then
      dropped=0
      for ref in "${!CHAN_ID[@]}"; do
        for k in $(redis-cli -h "$REDIS_HOST" --scan --pattern "read:${CHAN_ID[$ref]}:*" 2>/dev/null); do
          redis-cli -h "$REDIS_HOST" DEL "$k" >/dev/null 2>&1 && dropped=$((dropped+1))
        done
      done
      ok "dropped $dropped stale read cursor(s)"
    fi
    n_hist=$(jq '[.[].messages|length] as $m | [.[]|.threads[]|1+(.replies|length)] as $t | ($m|add) + ($t|add)' "$SCRIPT_DIR/conversations.json")
    ok "chat history script ready ($n_hist messages) -> $outdir/history-run.js"
  else
    warn "cannot write to ${SEED_OUT:-/seedout} — chat history not staged"
  fi
fi

# =============================================================================
# Summary
# =============================================================================
echo
log "Seed complete."
dim "workspace id : $WS_ID"
dim "users        : $n_users"
dim "members      : $n_members"
dim "teams        : $n_teams"
dim "channels     : $n_channels new"
dim "projects     : $n_spaces"
dim "tasks        : $n_tasks"
dim "rooms        : $n_rooms"
dim "events today : $n_events"
dim "photos       : $n_photos"
echo
ok  "Log in at the web client with any \"*@northstar.io\" email / password: $PASSWORD"
ok  "Workspace owner: $(jq -r '.users[] | select(.wsRole=="OWNER") | .email' "$DATA")"
