/*
 * Virtual Office — AI assistant.
 *
 * Natural language in, real platform actions out. The model is given a small set
 * of tools that map 1:1 onto endpoints that already exist; this service just
 * executes them and feeds the results back.
 *
 * Identity: the gateway validates the JWT, strips any client-supplied X-User-*
 * and injects trusted ones, then forwards the original Authorization header. We
 * reuse *that user's* token for every downstream call, so the assistant can only
 * ever see or do what the signed-in user could do themselves — no privilege
 * escalation, no service account.
 *
 * The OpenAI key lives only here (server side); it is never sent to the browser.
 */
import express from "express";
import OpenAI from "openai";

const PORT = process.env.PORT || 8089;
const GATEWAY_URL = process.env.GATEWAY_URL || "http://gateway-api:8080";
const MODEL = process.env.OPENAI_MODEL || "gpt-4o-mini";
const MAX_STEPS = 6; // tool-call rounds before we force a text answer

// Any OpenAI-compatible endpoint works — the assistant only needs chat
// completions + function calling. Point OPENAI_BASE_URL at Groq, Google's
// OpenAI-compat layer, OpenRouter or a local Ollama to avoid paid OpenAI
// billing; leave it unset for OpenAI itself. See .env.example.
const BASE_URL = process.env.OPENAI_BASE_URL || undefined;

if (!process.env.OPENAI_API_KEY) {
  console.error("[ai-service] OPENAI_API_KEY is not set — /api/ai/chat will return 503");
}
const openai = process.env.OPENAI_API_KEY
  ? new OpenAI({ apiKey: process.env.OPENAI_API_KEY, baseURL: BASE_URL })
  : null;

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/actuator/health", (_req, res) => res.json({ status: openai ? "UP" : "DEGRADED" }));

// ── platform API helper ──────────────────────────────────────────────────────
async function api(token, method, path, body) {
  const res = await fetch(`${GATEWAY_URL}${path}`, {
    method,
    headers: {
      Authorization: token,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) throw new Error(`${method} ${path} -> ${res.status} ${typeof data === "string" ? data : JSON.stringify(data)}`);
  return data;
}

// Channels the user can see, as {id, name}.
async function channelsOf(token, workspaceId) {
  const page = await api(token, "GET", `/api/chat/channels?workspaceId=${workspaceId}&page=1&limit=100`);
  return (page?.content || []).map((c) => ({ id: c.id, name: c.name }));
}

// userId -> display name, so the model talks about people, not numbers.
async function membersOf(token, workspaceId) {
  const page = await api(token, "GET", `/api/workspace/${workspaceId}/desks?page=0&size=100`);
  return (page?.content || []).map((d) => ({
    userId: d.userId, name: d.fullName || d.workEmail || `User ${d.userId}`, title: d.title || "",
  }));
}

// ── tools exposed to the model ───────────────────────────────────────────────
const TOOLS = [
  {
    type: "function",
    function: {
      name: "list_channels",
      description: "List the chat channels the user can see in this workspace. Use this to resolve a #channel mention to an id before reading it.",
      parameters: { type: "object", properties: {}, additionalProperties: false },
    },
  },
  {
    type: "function",
    function: {
      name: "read_channel",
      description: "Read recent messages of one channel to summarise or answer questions about it. Returns newest-first with sender names and timestamps. Use `since` for time-bounded questions ('today', 'this week').",
      parameters: {
        type: "object",
        properties: {
          channel: { type: "string", description: "Channel name, without the leading # (e.g. 'engineering')." },
          limit: { type: "integer", description: "How many recent messages to read (default 60, max 100)." },
          since: { type: "string", description: "Optional ISO-8601 instant; only return messages at or after it. Use for 'today'/'this week' style questions." },
        },
        required: ["channel"],
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "catch_up",
      description: "Read ONLY the messages the user has not read yet in a channel, using their real read cursor. Use this for 'what did I miss', 'catch me up', 'anything I need to know'. Prefer this over read_channel when the user asks about what they missed. Reading does NOT mark anything as read.",
      parameters: {
        type: "object",
        properties: {
          channel: { type: "string", description: "Channel name without '#'. Omit to check every channel the user can see." },
        },
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_my_tasks",
      description: "List the tasks assigned to the signed-in user in this workspace.",
      parameters: {
        type: "object",
        properties: { status: { type: "string", enum: ["TODO", "IN_PROGRESS", "COMPLETE"], description: "Optional filter." } },
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_events",
      description: "List calendar events in a date range (this is a shared team calendar, so it returns the whole workspace's events). Defaults to today.",
      parameters: {
        type: "object",
        properties: {
          from: { type: "string", description: "ISO-8601 start instant, e.g. 2026-07-15T00:00:00Z. Defaults to start of today." },
          to: { type: "string", description: "ISO-8601 end instant. Defaults to end of today." },
        },
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "create_task",
      description: "Create a task. Only call this once the title is clear. Assign to someone by name if the user asked for that.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          priority: { type: "string", enum: ["LOW", "NORMAL", "HIGH"] },
          status: { type: "string", enum: ["TODO", "IN_PROGRESS", "COMPLETE"] },
          dueDate: { type: "string", description: "ISO-8601 instant, e.g. 2026-07-20T15:00:00Z." },
          assignee: { type: "string", description: "Person's name; omit to assign to the signed-in user." },
        },
        required: ["title"],
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "create_event",
      description: "Schedule a calendar event/meeting. startTime must be before endTime.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          startTime: { type: "string", description: "ISO-8601 instant." },
          endTime: { type: "string", description: "ISO-8601 instant." },
          attendees: { type: "array", items: { type: "string" }, description: "Person names to invite." },
        },
        required: ["title", "startTime", "endTime"],
        additionalProperties: false,
      },
    },
  },
];

// Resolve a channel name the user typed (with or without '#', possibly partial)
// to a real channel, or an error listing what they can actually see.
async function findChannel(token, workspaceId, nameish, ctx) {
  const wanted = String(nameish || "").replace(/^#/, "").trim().toLowerCase();
  const chans = ctx.channels || (ctx.channels = await channelsOf(token, workspaceId));
  const ch =
    chans.find((c) => c.name.toLowerCase() === wanted) ||
    chans.find((c) => c.name.toLowerCase().includes(wanted));
  if (!ch) return { error: `No channel named "${nameish}" that you can see. Available: ${chans.map((c) => c.name).join(", ")}` };
  return ch;
}

// Raw message DTOs -> { at, from, text } with senders resolved to real names.
async function renderMessages(token, workspaceId, raw, ctx) {
  const members = ctx.members || (ctx.members = await membersOf(token, workspaceId));
  const byId = new Map(members.map((m) => [Number(m.userId), m.name]));
  return raw.filter(Boolean).map((m) => ({
    at: m.createdAt,
    from: byId.get(Number(m.senderId)) || `User ${m.senderId}`,
    text: m.content,
  }));
}

// ── tool implementations ─────────────────────────────────────────────────────
async function runTool(name, args, ctx) {
  const { token, workspaceId, userId } = ctx;

  const findPerson = async (needle) => {
    const members = ctx.members || (ctx.members = await membersOf(token, workspaceId));
    const n = String(needle).trim().toLowerCase();
    return (
      members.find((m) => m.name.toLowerCase() === n) ||
      members.find((m) => m.name.toLowerCase().startsWith(n)) ||
      members.find((m) => m.name.toLowerCase().includes(n))
    );
  };

  switch (name) {
    case "list_channels":
      return (await channelsOf(token, workspaceId)).map((c) => c.name);

    case "read_channel": {
      const ch = await findChannel(token, workspaceId, args.channel, ctx);
      if (ch.error) return ch;
      const limit = Math.min(Math.max(Number(args.limit) || 60, 1), 100);
      const page = await api(token, "GET", `/api/chat/channels/${ch.id}/messages?page=1&limit=${limit}`);
      let msgs = await renderMessages(token, workspaceId, page?.content || [], ctx);
      if (args.since) {
        const cut = Date.parse(args.since);
        if (!Number.isNaN(cut)) msgs = msgs.filter((m) => Date.parse(m.at) >= cut);
      }
      return { channel: ch.name, count: msgs.length, messages: msgs };
    }

    case "catch_up": {
      // Uses the user's real read cursor, so "what did I miss" means exactly
      // that. Deliberately does NOT mark anything read — the assistant reading
      // on your behalf shouldn't clear your unread badges.
      const chans = await channelsOf(token, workspaceId);
      let targets = chans;
      if (args.channel) {
        const ch = await findChannel(token, workspaceId, args.channel, ctx);
        if (ch.error) return ch;
        targets = [ch];
      }
      const out = [];
      for (const ch of targets) {
        let u;
        try { u = await api(token, "GET", `/api/chat/channels/${ch.id}/unread`); } catch { continue; }
        if (!u || !u.unreadCount) continue;
        let raw = [];
        try {
          raw = u.lastReadMessageId
            ? await api(token, "GET", `/api/chat/channels/${ch.id}/messages?after=${u.lastReadMessageId}&limit=100`)
            : (await api(token, "GET", `/api/chat/channels/${ch.id}/messages?page=1&limit=50`))?.content || [];
        } catch { continue; }
        const msgs = await renderMessages(token, workspaceId, Array.isArray(raw) ? raw : [], ctx);
        if (msgs.length) out.push({ channel: ch.name, unreadCount: u.unreadCount, mentionsYou: !!u.mentioned, messages: msgs });
      }
      if (out.length === 0) {
        return { caughtUp: true, note: args.channel
          ? `Nothing unread in #${args.channel}.`
          : "Nothing unread anywhere — the user is fully caught up." };
      }
      return { caughtUp: false, channels: out };
    }

    case "get_my_tasks": {
      const list = await api(token, "GET", `/api/tasks/mine?workspaceId=${workspaceId}`);
      const tasks = (Array.isArray(list) ? list : [])
        .filter(Boolean)
        .filter((t) => !args.status || t.status === args.status)
        .map((t) => ({ number: t.taskNumber, title: t.title, status: t.status, priority: t.priority, due: t.dueDate }));
      return { count: tasks.length, tasks };
    }

    case "get_events": {
      const now = new Date();
      const start = new Date(now); start.setUTCHours(0, 0, 0, 0);
      const end = new Date(start.getTime() + 86400000 - 1);
      const from = args.from || start.toISOString();
      const to = args.to || end.toISOString();
      const list = await api(token, "GET", `/api/calendar/events?workspaceId=${workspaceId}&from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`);
      const events = (Array.isArray(list) ? list : []).filter(Boolean).map((e) => ({
        title: e.title, start: e.startTime, end: e.endTime, description: e.description || undefined,
      }));
      return { count: events.length, from, to, events };
    }

    case "create_task": {
      let assigneeUserId = userId;
      if (args.assignee) {
        const p = await findPerson(args.assignee);
        if (!p) return { error: `No workspace member matching "${args.assignee}".` };
        assigneeUserId = p.userId;
      }
      const created = await api(token, "POST", "/api/tasks", {
        workspaceId: Number(workspaceId),
        title: args.title,
        description: args.description || null,
        status: args.status || "TODO",
        priority: args.priority || "NORMAL",
        dueDate: args.dueDate || null,
        assigneeUserId,
      });
      return { ok: true, taskNumber: created.taskNumber, title: created.title, status: created.status, due: created.dueDate };
    }

    case "create_event": {
      const attendees = [];
      for (const a of args.attendees || []) {
        const p = await findPerson(a);
        if (p) attendees.push({ userId: p.userId, email: null });
      }
      const created = await api(token, "POST", "/api/calendar/events", {
        workspaceId: Number(workspaceId),
        title: args.title,
        description: args.description || null,
        startTime: args.startTime,
        endTime: args.endTime,
        busy: true,
        attendees,
      });
      return { ok: true, id: created.id, title: created.title, start: created.startTime, end: created.endTime, attendees: attendees.length };
    }

    default:
      return { error: `unknown tool ${name}` };
  }
}

// ── chat endpoint ────────────────────────────────────────────────────────────
app.post("/api/ai/chat", async (req, res) => {
  if (!openai) return res.status(503).json({ error: "AI assistant is not configured (missing OPENAI_API_KEY)." });

  const token = req.headers.authorization;
  const userId = Number(req.headers["x-user-id"]);
  const { workspaceId, messages } = req.body || {};
  if (!token) return res.status(401).json({ error: "missing Authorization" });
  if (!workspaceId) return res.status(400).json({ error: "workspaceId is required" });
  if (!Array.isArray(messages) || messages.length === 0) return res.status(400).json({ error: "messages[] is required" });

  const ctx = { token, workspaceId, userId, members: null };
  const now = new Date();

  const convo = [
    {
      role: "system",
      content: [
        "You are the assistant inside Virtual Office, a team workspace app. You help the signed-in user with their chat, tasks and calendar.",
        `The current date and time is ${now.toISOString()} (UTC). The user's workspace id is ${workspaceId}.`,
        "",
        "Use the tools to get real data — never invent messages, tasks, events or people. If a tool returns an error, tell the user plainly what went wrong.",
        "When the user mentions a channel like #engineering, use that name.",
        "'What did I miss', 'catch me up', 'anything I need to know' -> catch_up (it uses their real unread cursor). Only fall back to read_channel if they want a general summary rather than what's new. If catch_up reports caughtUp, say so plainly instead of summarising old messages.",
        "For time-bounded questions ('today', 'this week') pass `since` to read_channel rather than reading everything.",
        "When summarising: lead with what actually matters — decisions made, blockers, and anything addressed to the user or needing their action. Group by topic, not by person. Skip pleasantries and don't pad. If someone asked the user a direct question, surface that first.",
        "Resolve relative dates ('tomorrow at 3', 'next Sunday') against the current time above and pass full ISO-8601 instants to the tools.",
        "Before creating a task or event, make sure you have a clear title and (for events) a start and end. If something essential is genuinely ambiguous, ask one short question instead of guessing. Otherwise just do it and confirm what you created.",
        "",
        "Style: concise and plain. Short paragraphs or tight bullets. No preamble, no restating the question. Markdown is fine.",
      ].join("\n"),
    },
    ...messages.filter((m) => m && typeof m.content === "string" && ["user", "assistant"].includes(m.role))
      .slice(-12)
      .map((m) => ({ role: m.role, content: m.content })),
  ];

  const used = [];
  try {
    for (let step = 0; step < MAX_STEPS; step++) {
      const completion = await openai.chat.completions.create({
        model: MODEL,
        messages: convo,
        tools: TOOLS,
        // On the last step force a prose answer rather than another tool call.
        tool_choice: step === MAX_STEPS - 1 ? "none" : "auto",
        temperature: 0.2,
      });
      const msg = completion.choices[0].message;
      convo.push(msg);

      if (!msg.tool_calls?.length) {
        return res.json({ reply: msg.content || "", toolsUsed: used });
      }

      for (const call of msg.tool_calls) {
        // Models are not consistent here: some send "{}", some send "null", some
        // send malformed JSON. JSON.parse("null") returns null, which then blows
        // up on the first args.foo read — so normalise to a plain object.
        let args = {};
        try {
          const parsed = JSON.parse(call.function.arguments || "{}");
          if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) args = parsed;
        } catch { /* model sent bad JSON — treat as no arguments */ }
        let result;
        try {
          result = await runTool(call.function.name, args, ctx);
        } catch (e) {
          result = { error: String(e.message || e) };
        }
        used.push(call.function.name);
        convo.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(result).slice(0, 24000) });
      }
    }
    return res.json({ reply: "I wasn't able to finish that — too many steps. Try narrowing the request.", toolsUsed: used });
  } catch (e) {
    // Surface the *actionable* cause rather than a generic failure — the two we
    // actually hit are a key with no billing attached and a bad/rotated key.
    const code = e?.code || e?.error?.code;
    const status = e?.status;
    console.error("[ai-service]", code || status || "", e?.message || e);
    if (code === "insufficient_quota")
      return res.status(402).json({ error: "The OpenAI account attached to this key has no remaining quota. Add billing/credits at platform.openai.com, then try again.", code });
    if (status === 401 || code === "invalid_api_key")
      return res.status(401).json({ error: "The OpenAI key is invalid or has been revoked. Update OPENAI_API_KEY in .env and restart ai-service.", code: code || "invalid_api_key" });
    if (status === 429)
      return res.status(429).json({ error: "OpenAI is rate-limiting this key. Wait a moment and try again.", code: code || "rate_limit" });
    return res.status(502).json({ error: "The assistant failed to answer.", detail: String(e?.message || e) });
  }
});

app.listen(PORT, () =>
  console.log(`[ai-service] listening on ${PORT}, model=${MODEL}, provider=${BASE_URL || "api.openai.com"}, gateway=${GATEWAY_URL}`));
