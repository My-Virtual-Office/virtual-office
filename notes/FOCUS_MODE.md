# Focus Mode ("Working Mode") — research, requirements, design

Research notes behind `website/src/pages/Chat/Components/FocusMode/`. Sources at the bottom.

## 1. Why it is worth building (the evidence)

| Finding | Source |
| --- | --- |
| **23 min 15 s** to fully regain focus after an interruption | Gloria Mark, UC Irvine |
| Each interruption costs a **15–25 min** cognitive reset — you lose far more than the interruption itself | Network Perspective |
| **~4 h/week** spent reorienting after app switching ≈ **9% of annual work time** | Context-switching statistics 2026 |
| Cutting interruptions moved developers' daily progress from **7% → 82%** | GitHub |
| **90 min** is the practical ceiling for one sustained block | Deep-work literature |

The number that matters: a single mistimed notification costs ~23 minutes, not ~5 seconds. That
is the whole justification for a mode whose only job is to not interrupt.

## 2. What the incumbents actually do

**Slack — focus mode**
- Theme drops to **grayscale**; badges lose colour.
- New activity becomes a **subtle dot**, not a numbered badge; names stop bolding.
- Notifications pause; **VIPs still break through**.
- **Duration is user-set**; hovering still reveals real counts.

**Microsoft Teams — quiet hours**
- Blocks alerts for a window, **without logging you out**.
- Colleagues **see DND**, so they don't expect a reply.
- Messages still **queue** — nothing is lost.

**The shared pattern:** suppress *delivery*, never *capture*; tell other people; keep one
escape hatch open.

## 3. The counter-evidence (this is the important one)

Nielsen Norman Group, *Why Zen Mode Isn't the Answer to Everything*:

> Zen mode "can ultimately increase cognitive strain by taking away users' attention from their
> task and asking them to focus on finding hidden tools, paradoxically requiring users to focus
> on the interface rather than the task."

So hiding everything is **not** automatically good. A focus mode that hides the tools you need
makes you hunt for them — you end up thinking about the UI instead of the work. This is the
single biggest design risk here, and it is why the controls below stay on screen.

## 4. Requirements

### Functional
1. **One control in, one control out.** No menus, no settings trip.
2. **One surface**: My Desk full-screen — the tasks you chose to work on, nothing else.
3. **Broadcast the state**: desk status → `FOCUS_MODE`, so teammates see 🎯 Focused and don't
   expect a reply (Teams' rule).
4. **Gate notifications, don't drop them**: only `MENTION` reaches the screen. Everything else
   is held silently and **counted**.
5. **Deliver the backlog on exit**: the held count is reported when you leave. Nothing is lost.
6. **Keep the needed tools visible** (NN/g): Ask AI, Virtual Office, Exit — always on screen,
   never behind a hover or a gesture.
7. **Elapsed timer**, so a session is a decision rather than a drift.
8. **Survives reload** — a refresh must not silently drop you back into the noise.

### Non-functional
1. **Nothing is lost.** Suppression is presentation-only; capture and persistence are untouched.
2. **Legible to others.** The status is the contract; without it focus mode is just ghosting.
3. **Always an escape hatch.** Mentions break through — the analogue of Slack's VIPs. Someone
   must be able to reach you in a genuine emergency, or the mode is unusable and won't be used.
4. **No tool-hunting.** See NN/g above.
5. **Reversible instantly**, and the previous status is restored exactly.
6. **Cheap to render.** Focus mode must not be a second app: it reuses My Desk and the AI panel.

## 5. Design

```
┌──────────────────────────────────────────────────────────┐
│  🎯 Focus · 12:34        3 held   [Ask AI] [Office] [Exit]│  ← always visible (NN/g)
├──────────────────────────────────────────────────────────┤
│                                                          │
│                  My Desk — full screen                   │
│                  (your tasks, your day)                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
        ▲ a mention slides in here, and only a mention
```

- **Held ≠ hidden.** The count is on screen the whole time, like Slack's hover-to-reveal: you
  can see there is noise without being pulled into it.
- **Mentions surface as a banner**, not a toast — no sound, no auto-dismiss, dismissible.
  Someone asked for you by name; that is the one thing worth 23 minutes.
- **Exit restores** the previous status and reports what was held.

## Sources

- [Use focus mode in Slack](https://slack.com/help/articles/51416500176147-Use-focus-mode-in-Slack)
- [Add contacts as VIPs — Slack](https://slack.com/help/articles/34963579361683-Add-contacts-as-VIPs)
- [A redesigned Slack, built for focus](https://slack.com/blog/productivity/a-redesigned-slack-built-for-focus)
- [Slack Focus Hours and Teams Quiet Time](https://www.attendancebot.com/blog/slack-teams-set-focus-hours/)
- [Why Zen Mode Isn't the Answer to Everything — Nielsen Norman Group](https://www.nngroup.com/articles/zen-mode/)
- [Context Switching in Developer Experience — Network Perspective](https://www.networkperspective.io/devex-book/context-switching-protecting-focus)
- [Context Switching Statistics 2026](https://speakwiseapp.com/blog/context-switching-statistics)
- [Context switching is the main productivity killer for developers](https://newsletter.techworld-with-milan.com/p/context-switching-is-the-main-productivity)
