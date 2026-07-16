# Repo organization plan — Virtual Office

Turn the loose root folder into a clean **`virtual-office`** umbrella repo that
pins the 6 product repos as git submodules, and move the non-product material
(deck, notes, thesis) out of it.

## Target: 7 (or 8) repos under `My-Virtual-Office`

| Repo | Contents | Status |
|---|---|---|
| `backend` | 9 microservices | exists ✓ |
| `website` | React web app | exists ✓ |
| `SkyOffice` | 2D office | exists ✓ |
| `Mobile_application` | Flutter app | exists ✓ |
| `Docs` | markdown source docs | exists ✓ |
| `My-Virtual-Office.github.io` | docs **site** (live) | exists ✓ |
| **`virtual-office`** | compose + ai-service + seed + observability + submodules | **NEW** |
| `graduation-book` *(optional)* | the thesis | optional |

Result: `git clone --recurse-submodules …/virtual-office && docker compose up`
brings up the whole system.

---

## Step 0 — Put each product repo on its canonical branch (IMPORTANT)

A submodule pins the **commit currently checked out**. Right now three repos are
on feature branches, so pin `main`/`master` instead — and commit the one dirty
file in backend first.

```bash
cd "…/Graduation Project"

# backend has 1 uncommitted change — inspect, then commit or discard it
git -C backend status
# git -C backend add -A && git -C backend commit -m "…"   # or: git -C backend stash

# Move each to its canonical branch (these are all already pushed there)
git -C backend            checkout main
git -C website            checkout main     # currently on fix/chat-names-and-ui
git -C SkyOffice          checkout master   # currently on feat/voice-and-observability
git -C Mobile_application checkout main
git -C doc                checkout main
git -C Docs               checkout main

# Make sure each local branch == its remote (submodule pins a pushed commit)
for d in backend website SkyOffice Mobile_application doc Docs; do
  git -C "$d" pull --ff-only
done
```

> If `website`/`SkyOffice` main/master is *behind* your feature-branch work,
> merge that work up first (`git -C website checkout main && git -C website merge fix/chat-names-and-ui && git -C website push`), so the submodule doesn't pin a stale commit.

---

## Step 1 — Clean the root working tree

```bash
# Third-party reference clone you don't own — remove it (4.8 MB, untracked)
rm -rf docs-examples

# Group the non-product material so the umbrella stays deployment-only
mkdir -p presentation notes

git mv build-deck.py build-shots.py build-diagrams.sh \
       deck-template.html deck-logos.json shot-ratios.json \
       Presentation-17-Slides.md Presentation.html \
       Virtual-Office-Deck.html Virtual-Office-Slides.md \
       Virtual-Office-Features.md Virtual-Office-Team-Split.md \
       diagrams shots screenshots presentation/

git mv OVERNIGHT_SUMMARY.md PRODUCTION_READINESS_PLAN.md FOCUS_MODE.md \
       CHAT_TEAMS_PLAN.md flow.md ENCRYPTION.md notes/
```

> `Presentation.pdf` is untracked; move it too if you want it kept
> (`git add presentation/Presentation.pdf` after moving), or leave it out.

**What stays at the umbrella root (the deployment surface):**
`docker-compose.yml`, `.env.example`, `make-release.sh`, `run.sh`,
`RUN.md`, `DEPLOY.md`, `DOCKER.md`, `ai-service/`, `seed/`, `observability/`.

---

## Step 2 — Convert the product folders to submodules

They're currently in `.gitignore` (as sibling clones). Un-ignore them, then add
each as a submodule. `--force` is needed because they were ignored, and the
directories already exist as clones at the right remote/commit.

```bash
# 1. Remove the "Sub-project repos" block from .gitignore
#    (the /website/ /SkyOffice/ /backend/ /Mobile_application/ lines)

# 2. Register each existing clone as a submodule (pins current commit)
git submodule add --force https://github.com/My-Virtual-Office/backend.git             backend
git submodule add --force https://github.com/My-Virtual-Office/website.git             website
git submodule add --force https://github.com/My-Virtual-Office/SkyOffice.git           SkyOffice
git submodule add --force https://github.com/My-Virtual-Office/Mobile_application.git   Mobile_application
git submodule add --force https://github.com/My-Virtual-Office/Docs.git                 Docs
git submodule add --force https://github.com/My-Virtual-Office/My-Virtual-Office.github.io.git  doc

git submodule status   # verify 6 entries, each at a pushed commit
```

This creates `.gitmodules`. The docs **site** repo stays deployed on its own
(its Pages workflow is unaffected by being a submodule here).

---

## Step 3 — Umbrella README + commit

Give the umbrella a short README (clone + run), then commit everything:

```bash
git add -A
git commit -m "chore: reorganize as the virtual-office platform umbrella

- product repos pinned as submodules (backend, website, SkyOffice, mobile,
  Docs, docs-site) — clone --recurse-submodules + docker compose up
- deck/slides/shots moved to presentation/, working notes to notes/
- dropped the third-party docs-examples clone"
```

---

## Step 4 — Create the remote and push

```bash
gh repo create My-Virtual-Office/virtual-office --private \
  --source=. --remote=origin --push
```

> Private is the safe default for the umbrella (it references `.env.example`
> and ops docs; nothing secret, but it's the deployment control repo). Make it
> public later if you want it to be the front door.

Teammates then get the whole system with:

```bash
git clone --recurse-submodules https://github.com/My-Virtual-Office/virtual-office.git
cd virtual-office && cp .env.example .env   # fill in secrets
docker compose up -d --build
```

---

## Step 5 (optional) — GraduationBook as its own repo

The thesis is a separate concern from the platform:

```bash
git rm -r --cached GraduationBook          # if it was tracked by root
cd GraduationBook && git init -b main && git add -A && git commit -m "init: graduation book"
gh repo create My-Virtual-Office/graduation-book --private --source=. --remote=origin --push
cd .. && echo "/GraduationBook/" >> .gitignore   # umbrella ignores it
```

---

## Working with submodules afterwards (cheat-sheet)

```bash
# Pull the umbrella AND update every submodule to its pinned commit
git pull --recurse-submodules

# You changed code inside, say, backend/ — commit & push IN the submodule first
cd backend && git add -A && git commit -m "…" && git push && cd ..
# then bump the pointer in the umbrella
git add backend && git commit -m "bump backend" && git push

# Point a submodule at the latest of its own branch
git submodule update --remote website
```

## Gotchas (why the order above matters)

- A submodule pins a **commit**, not a branch. If that commit isn't pushed, no
  one else can clone it — that's why Step 0 pushes canonical branches first.
- `git submodule add` on an already-cloned, already-ignored dir needs `--force`.
- Never `git add website/` as a plain folder from the umbrella without the
  submodule — it records a bare gitlink with no `.gitmodules` entry that nobody
  can resolve. (Your current `.gitignore` deliberately prevents this.)
