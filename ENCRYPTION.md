# End-to-End Encryption — how it works

Direct messages are encrypted **in the browser**. The server stores ciphertext it
has no key for.

## The mechanism

```
Maya's browser                     Server                    Omar's browser
──────────────                     ──────                    ──────────────
generate ECDH P-256 keypair                                  generate keypair
  ├─ private key ──► localStorage    (never sent)              private ─► localStorage
  └─ public key  ─────────────────►  users.e2e_public_key  ◄───── public key

send a DM:
  ECDH(my private, Omar's public)
        │
        ▼  shared secret
   AES-GCM-256 encrypt
        │
        ▼
  "vo1:<iv>:<ciphertext>"  ─────►  stored as-is  ─────►  ECDH(my private, Maya's public)
                                   (unreadable)               │  same shared secret
                                                              ▼  AES-GCM decrypt
                                                          plaintext
```

**Why the server can't read it:** ECDH lets two people derive the *same* secret
from their own private key + the other's public key. That secret is never
transmitted, and the server only ever holds public keys — so it cannot derive it.

| Where | What it holds |
|---|---|
| Browser `localStorage` | your **private** key (never leaves the device) |
| MySQL `users.e2e_public_key` | **public** keys only |
| MongoDB `messages.content` | `vo1:<iv>:<ciphertext>` |

## Scope: DMs only — deliberately

Channels stay readable by the server. That is a **trade-off, not an oversight**:
search, the 3-month history, and the AI assistant summarising a channel all
need plaintext. Encrypting channels would silently break them.

This is the same split real products make — Signal is end-to-end encrypted and
has no server-side search or AI; Slack is server-readable and has both.

## Honest limitations

- **One device.** The key lives in one browser. Clear site data or sign in
  elsewhere → old DMs are unreadable. There is no key backup or multi-device
  sync (adding one means the server holds keys, which defeats the point).
- **No forward secrecy.** Static ECDH, no ratchet. If a private key leaks, past
  DMs can be decrypted. Signal solves this with the Double Ratchet.
- **Trust on first use.** The server serves public keys, so a malicious server
  could substitute its own and man-in-the-middle a conversation. Real defence
  needs out-of-band verification (safety numbers / QR).
- **Needs a secure context.** WebCrypto requires https or localhost. Over plain
  http to a LAN IP the client falls back to plaintext rather than pretending.
- **Metadata is not encrypted.** Who talked to whom, and when, is still visible.

## Verifying it

```bash
node website/e2e-dm-test.mjs http://localhost:8080
```

Checks, against the live stack: the directory exposes no private component; the
stored message does not contain the plaintext; the recipient round-trips it; an
unrelated keypair **cannot** decrypt it; tampered ciphertext is rejected.

Or look at the database directly:

```bash
docker compose exec -T mongo mongosh -u root -p rootpassword \
  --authenticationDatabase admin --quiet --eval '
  const d = db.getSiblingDB("chat_service");
  const dms = d.channels.find({type:"DIRECT"},{_id:1}).toArray().map(c=>c._id);
  d.messages.find({channelId:{$in:dms}, content:/^vo1:/}).limit(3).forEach(m => print(m.content));'
```

## Code

| File | Role |
|---|---|
| `website/src/utils/e2e.js` | keygen, ECDH→AES-GCM, encrypt/decrypt |
| `website/src/pages/Chat/Components/ChatArea/MessageInput/MessageInput.js` | encrypts before send |
| `website/src/pages/Chat/Components/ChatArea/MessagesList/MessagesList.js` | decrypts for display |
| `backend/user-service/.../UserController.java` | `PUT /api/users/me/e2e-key` (public half only) |
| `website/e2e-dm-test.mjs` | the proof |
