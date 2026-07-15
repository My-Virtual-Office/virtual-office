// mongosh loader — inserts backdated chat history into the chat_service DB.
//
// Expects a global SEED object to be defined BEFORE this file (the runner
// prepends `const SEED = {...}`):
//   SEED = {
//     wsId: <workspaceId>,
//     base: "YYYY-MM-DD",              // day 0 (today); messages are stamped days-ago from here
//     users: { <ref>: <userId>, ... }, // person ref -> numeric user id
//     conversations: [ { channel:"<name>", messages:[{day,hm,author,text,reactions?}], threads:[{day,hm,name,root:{author,text},replies:[{author,text}]}] } ]
//   }
//
// Messages sort by createdAt then paginate by _id, so each _id is built from the
// message's historical timestamp (4-byte time prefix) to keep both orders in sync.
// Idempotent: clears existing messages/threads for the target channels first.
(function () {
  const cdb = db.getSiblingDB("chat_service");
  const U = SEED.users;
  const BASE = new Date(SEED.base + "T00:00:00Z").getTime();
  const MSG_CLASS = "com.virtualoffice.chat_service.model.Message";
  const THR_CLASS = "com.virtualoffice.chat_service.model.ChatThread";
  let SEQ = 1;

  function oid(tsSec, seq) {
    const tsHex = Math.floor(tsSec).toString(16).padStart(8, "0");
    const seqHex = seq.toString(16).padStart(16, "0");
    return new ObjectId(tsHex + seqHex);
  }
  // Nothing may be stamped in the future. Messages are written across a whole
  // working day, so if the seed runs at 05:00 a "17:00 today" message would land
  // hours ahead of now — which breaks unread (it counts `_id > lastReadId`, and
  // a future message pins the cursor above anything real you send afterwards)
  // and makes new messages sort *below* seeded ones.
  const MAX_TS = Math.floor(Date.now() / 1000) - 90;

  function tsOf(day, hm) {
    const p = String(hm).split(":");
    const h = parseInt(p[0], 10) || 0, m = parseInt(p[1], 10) || 0;
    const dayStart = Math.floor((BASE - day * 86400000) / 1000);
    let t = dayStart + h * 3600 + m * 60;
    if (t > MAX_TS) {
      // Compress the intended time-of-day into the part of the day that has
      // actually elapsed, so "today" still reads as a full day of chatter
      // instead of everything collapsing onto one timestamp.
      const elapsed = Math.max(MAX_TS - dayStart, 0);
      t = dayStart + Math.floor(((h * 3600 + m * 60) / 86400) * elapsed);
    }
    return t;
  }
  function reactMap(arr) {
    const out = {};
    (arr || []).forEach(function (r) {
      const ids = (r.by || []).map(function (x) { return U[x]; }).filter(function (v) { return v != null; });
      if (ids.length) out[r.emoji] = Array.from(new Set(ids));
    });
    return out;
  }

  // channel name -> _id  (in this dataset the channel ref == its name)
  const chan = {};
  cdb.channels.find({ workspaceId: SEED.wsId }).forEach(function (c) { chan[c.name] = c._id; });

  const channelIds = SEED.conversations
    .map(function (c) { return chan[c.channel]; })
    .filter(function (v) { return v != null; });

  const delM = cdb.messages.deleteMany({ channelId: { $in: channelIds } }).deletedCount;
  const delT = cdb.threads.deleteMany({ channelId: { $in: channelIds } }).deletedCount;
  print("cleared old  messages=" + delM + "  threads=" + delT);

  const MSG = [], THR = [];
  let skippedChannels = 0;

  SEED.conversations.forEach(function (conv) {
    const chId = chan[conv.channel];
    if (!chId) { skippedChannels++; print("  ! no channel for '" + conv.channel + "'"); return; }

    (conv.messages || []).forEach(function (m) {
      const uid = U[m.author]; if (uid == null) return;
      const ts = tsOf(m.day, m.hm), at = new Date(ts * 1000);
      MSG.push({ _id: oid(ts, SEQ++), channelId: chId, senderId: uid, senderRole: "USER",
        content: m.text, type: "TEXT", mentions: [], reactions: reactMap(m.reactions),
        pinned: false, deleted: false, createdAt: at, updatedAt: at, _class: MSG_CLASS });
    });

    (conv.threads || []).forEach(function (t) {
      const ruid = U[t.root.author]; if (ruid == null) return;
      const ts = tsOf(t.day, t.hm), at = new Date(ts * 1000);
      const rootId = oid(ts, SEQ++);
      MSG.push({ _id: rootId, channelId: chId, senderId: ruid, senderRole: "USER",
        content: t.root.text, type: "TEXT", mentions: [], reactions: reactMap(t.reactions),
        pinned: false, deleted: false, createdAt: at, updatedAt: at, _class: MSG_CLASS });
      const thId = oid(ts + 1, SEQ++);
      THR.push({ _id: thId, channelId: chId, rootMessageId: rootId, name: t.name,
        createdBy: ruid, creatorRole: "USER", deleted: false, createdAt: at, updatedAt: at, _class: THR_CLASS });
      (t.replies || []).forEach(function (rep, i) {
        const uid = U[rep.author]; if (uid == null) return;
        const rts = ts + (i + 1) * 200, rat = new Date(rts * 1000);
        MSG.push({ _id: oid(rts, SEQ++), channelId: chId, senderId: uid, senderRole: "USER",
          content: rep.text, type: "TEXT", threadId: thId, mentions: [], reactions: {},
          pinned: false, deleted: false, createdAt: rat, updatedAt: rat, _class: MSG_CLASS });
      });
    });
  });

  if (MSG.length) cdb.messages.insertMany(MSG, { ordered: false });
  if (THR.length) cdb.threads.insertMany(THR, { ordered: false });
  print("inserted messages=" + MSG.length + "  threads=" + THR.length +
        (skippedChannels ? "  (skipped " + skippedChannels + " channels)" : ""));
})();
