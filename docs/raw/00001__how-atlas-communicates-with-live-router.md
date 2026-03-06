# How the Patchboard Atlas Communicates with a Live Patchboard Router

Date: 2026-03-05

---

## Overview

Patchboard Atlas and the Patchboard Router are separate processes that never talk
directly. They communicate entirely through the filesystem, using the FileTalk file
transport protocol. Atlas is an **observer-and-requestor**: it reads published router
state and writes request messages into the router's inbox. It never mutates router
state directly.

The router is always authoritative. Atlas only asks; the router decides.

---

## The Communication Medium

All messages are JSON files written to and read from filesystem directories. This is
the **FileTalk File Transport Profile**: each message is a `.json` file containing a
single JSON object with three fields:

```json
{
  "channel": "<routing identifier>",
  "signal": { ... },
  "timestamp": "<unix time>"
}
```

The `channel` field determines how the router dispatches the message. The `signal`
carries the payload. The `timestamp` is informational.

There are no sockets, no HTTP, no inter-process signals. If both processes can reach
the same filesystem path, they can communicate.

---

## The Router's Filesystem Layout

The router stores everything under a project directory at `.patchboard-router/`
beneath the execution root (a path managed by lionscliapp). The relevant paths for
Atlas are:

```
.patchboard-router/
    INBOX/          ← Atlas writes request messages here
    OUTBOX/         ← Atlas reads notification messages from here
    routes.json     ← Atlas reads current routing topology from here
    status.json     ← Atlas reads router liveness and metadata from here
    events.jsonl    ← Append-only event log (Atlas does not need to read this)
```

---

## Messages Atlas Sends to the Router

Atlas writes FileTalk message files into the router's `INBOX/`. The router reads
them on its next polling pass (roughly every `router.delay_seconds`, default 0.5s).

### `link` — Request a routing connection

```json
{
  "channel": "link",
  "signal": {
    "source-folder": "/absolute/path/to/component/OUTBOX",
    "source-channel": "data",
    "destination-folder": "/absolute/path/to/other/INBOX",
    "destination-channel": "received"
  },
  "timestamp": "1741234567.0"
}
```

The router adds the route to its routing table, records a `route_added` event,
rewrites `routes.json`, and emits a `notice` change-notification.

### `unlink` — Request removal of a routing connection

Same shape as `link`, with `"channel": "unlink"`. The router removes the matching
route (matched by all four path/channel fields), records `route_removed`, rewrites
`routes.json`, and emits a `notice`.

### `quit` — Request a clean shutdown

```json
{
  "channel": "quit",
  "signal": {},
  "timestamp": "1741234567.0"
}
```

The router finishes its current delivery pass, enters draining mode, emits a
`shutdown` message, and exits.

### Optional: Acknowledgement

Any `link` or `unlink` message may include an `"ack-path"` field in its signal.
If present, the router writes an acknowledgement artifact to that path after handling
the command. Atlas may use this to confirm that a request was processed rather than
relying solely on polling `routes.json`.

---

## Messages Atlas Receives from the Router

The router writes FileTalk message files into its own `OUTBOX/`. Atlas polls this
directory (or watches it) and processes whatever it finds.

### `notice` — Something has changed

```json
{
  "channel": "notice",
  "signal": {},
  "timestamp": "1741234567.0"
}
```

This is a coarse-grained "something changed" signal. The signal is always an empty
object — it carries no detail about what changed. Upon receiving a `notice`, Atlas
must re-read `routes.json` to learn the new topology and reconcile its visual model.

This is a deliberate design choice: keeping observers loosely coupled to router
internals, and keeping notification traffic small.

### `startup` — Router came online

```json
{
  "channel": "startup",
  "signal": {},
  "timestamp": "1741234567.0"
}
```

Indicates the router process has started. Atlas should re-read `routes.json` and
`status.json` to initialize its view of the world.

### `shutdown` — Router is going offline

```json
{
  "channel": "shutdown",
  "signal": {},
  "timestamp": "1741234567.0"
}
```

Indicates the router is shutting down cleanly. Atlas should mark the router as
unavailable and stop sending requests.

---

## Reading Published Router State

The router continuously rewrites two JSON files as derived projections of its
authoritative event log.

### `routes.json` — Current routing topology

```json
{
  "schema-version": "1",
  "updated-at-utc": "1741234567.0",
  "routes": [
    {
      "source-folder": "/path/to/OUTBOX",
      "source-channel": "data",
      "destination-channel": "received",
      "destination-folder": "/path/to/INBOX"
    }
  ]
}
```

This is Atlas's authoritative view of what wires currently exist. Atlas reads this
file after every `notice` message and on startup. All folder paths are in canonical
absolute form.

### `status.json` — Router liveness and metadata

Contains `router_id`, `started_at_utc`, tick counter, delivery statistics, and an
`alive` boolean. `alive: false` means the router is draining and will not process
new requests. Atlas uses this to show router liveness in the UI.

---

## The Observation Loop

The full cycle for Atlas observing a topology change:

1. User draws a wire in Atlas (or a wire is created externally).
2. Atlas writes a `link` message to the router `INBOX/`.
3. The router's poll loop reads the message, adds the route, rewrites `routes.json`,
   and writes a `notice` to its `OUTBOX/`.
4. Atlas's poll loop reads the `notice` from the router `OUTBOX/`.
5. Atlas re-reads `routes.json`.
6. Atlas reconciles its visual model against the new topology.
7. The wire appears (or is confirmed) in the canvas.

If Atlas sent a request and the router rejected it (e.g., duplicate route), no
`route_added` event is recorded and `routes.json` does not change. Atlas will
converge to the correct view on its next sync regardless.

---

## Design Principles

- **Atlas never assumes its request succeeded.** It waits for the router to confirm
  via `routes.json`.
- **Temporary visual divergence is acceptable.** A wire may appear as "pending" in
  Atlas before the router confirms it.
- **The router is the sole source of truth.** Atlas does not maintain a shadow
  routing table; it reads `routes.json` directly.
- **All paths in messages must be absolute and canonical.** The router matches routes
  by exact string equality after canonicalization.
- **Message files are consumed after processing.** The router deletes INBOX files
  after reading them. Atlas deletes OUTBOX files after reading them.
