/*
 * Tool-layer self-test — exercises every assistant tool against the real
 * platform APIs, with NO OpenAI call. Proves the plumbing (auth pass-through,
 * endpoint shapes, name resolution) independently of model availability/billing.
 *
 *   node selftest.js <gatewayUrl> <email> <password> <workspaceId>
 *
 * Read-only by default; pass --write to also create a task + event.
 */
const [, , GATEWAY = "http://localhost:8080", EMAIL = "maya.hassan@northstar.io", PASS = "Northstar@2026", WS = "49"] = process.argv;
const WRITE = process.argv.includes("--write");

const ok = (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`);
const bad = (m) => { console.log(`  \x1b[31m✗\x1b[0m ${m}`); process.exitCode = 1; };

async function api(token, method, path, body) {
  const r = await fetch(`${GATEWAY}${path}`, {
    method,
    headers: { Authorization: token, ...(body ? { "Content-Type": "application/json" } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const t = await r.text();
  let d; try { d = t ? JSON.parse(t) : null; } catch { d = t; }
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status} ${typeof d === "string" ? d : JSON.stringify(d)}`);
  return d;
}

(async () => {
  console.log(`AI tool self-test -> ${GATEWAY} (workspace ${WS})\n`);

  const auth = await fetch(`${GATEWAY}/api/auth/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASS }),
  }).then((r) => r.json());
  if (!auth.token) return bad(`login failed for ${EMAIL}`);
  const token = `Bearer ${auth.token}`;
  ok(`login as ${auth.firstName} ${auth.lastName} (id=${auth.id})`);

  // list_channels
  const chans = (await api(token, "GET", `/api/chat/channels?workspaceId=${WS}&page=1&limit=100`))?.content || [];
  chans.length ? ok(`list_channels -> ${chans.length} channels`) : bad("list_channels -> none");

  // members (name resolution)
  const members = (await api(token, "GET", `/api/workspace/${WS}/desks?page=0&size=100`))?.content || [];
  const named = members.filter((m) => m.fullName);
  named.length === members.length && members.length
    ? ok(`members -> ${members.length} all with real names (e.g. ${named[0].fullName})`)
    : bad(`members -> ${named.length}/${members.length} have fullName`);

  // read_channel
  const target = chans.find((c) => c.name === "calendar-sync") || chans[0];
  const byId = new Map(members.map((m) => [Number(m.userId), m.fullName]));
  const msgs = (await api(token, "GET", `/api/chat/channels/${target.id}/messages?page=1&limit=60`))?.content || [];
  if (!msgs.length) bad(`read_channel(#${target.name}) -> no messages`);
  else {
    const unresolved = msgs.filter((m) => !byId.get(Number(m.senderId))).length;
    ok(`read_channel(#${target.name}) -> ${msgs.length} msgs, senders resolved (${unresolved} unknown)`);
    console.log(`      e.g. ${byId.get(Number(msgs[0].senderId))}: "${String(msgs[0].content).slice(0, 60)}…"`);
  }

  // get_my_tasks
  const mine = await api(token, "GET", `/api/tasks/mine?workspaceId=${WS}`);
  Array.isArray(mine) ? ok(`get_my_tasks -> ${mine.length} assigned`) : bad("get_my_tasks -> bad shape");

  // get_events (today)
  const s = new Date(); s.setUTCHours(0, 0, 0, 0);
  const e = new Date(s.getTime() + 86400000 - 1);
  const evs = await api(token, "GET", `/api/calendar/events?workspaceId=${WS}&from=${encodeURIComponent(s.toISOString())}&to=${encodeURIComponent(e.toISOString())}`);
  Array.isArray(evs) ? ok(`get_events(today) -> ${evs.length} events`) : bad("get_events -> bad shape");

  if (!WRITE) return console.log("\n(read-only; pass --write to test create_task/create_event)");

  // create_task
  const t = await api(token, "POST", "/api/tasks", {
    workspaceId: Number(WS), title: "[selftest] AI assistant smoke task",
    description: "Created by ai-service selftest", status: "TODO", priority: "NORMAL",
    dueDate: new Date(Date.now() + 86400000).toISOString(), assigneeUserId: auth.id,
  });
  t?.id ? ok(`create_task -> #${t.taskNumber} "${t.title}"`) : bad("create_task failed");

  // create_event
  const st = new Date(Date.now() + 3600000), en = new Date(Date.now() + 7200000);
  const ev = await api(token, "POST", "/api/calendar/events", {
    workspaceId: Number(WS), title: "[selftest] AI assistant smoke event",
    startTime: st.toISOString(), endTime: en.toISOString(), busy: true, attendees: [],
  });
  ev?.id ? ok(`create_event -> id=${ev.id} "${ev.title}"`) : bad("create_event failed");

  // clean up so the demo data stays pristine
  if (t?.id) { await api(token, "DELETE", `/api/tasks/${t.id}`); ok("cleaned up test task"); }
  if (ev?.id) { await api(token, "DELETE", `/api/calendar/events/${ev.id}`); ok("cleaned up test event"); }
})().catch((e) => bad(String(e.message || e)));
