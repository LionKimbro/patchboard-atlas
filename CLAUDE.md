# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Patchboard Atlas is a graphical configuration and observation tool for FileTalk Patchboard Routers. It provides a canvas-based interface (Python/Tkinter) for placing components, wiring connections, and visualizing routing topology. The router is always authoritative — Atlas is an observer-and-requestor that communicates via FileTalk messages.

## Commands

```bash
# Run the app
patchboard-atlas

# Run with GUI tests (tkintertester harness)
patchboard-atlas --runtime.testing

# Run pure-logic tests
pytest test/

# Run a single test file
pytest test/test_coord_machine.py

# Install in development mode
pip install -e .
```

## Key Dependencies

- **lionscliapp**: CLI framework providing app lifecycle, exec root, context keys, and project directory management. API docs at `F:/lion/github/lionscliapp/doc/lionscliapp_api.json`.
- **tkintertester**: Event-loop-native test harness for Tkinter GUIs. The harness provides the Tk root; `create_gui` receives it. Spec at `F:/lion/github/tkintertester/docs/spec/tkintertester_spec.json`.

## Architecture

### Data Flow Pattern: Forth-Style Stack

Not universal — used for data flow operations. Functions may take 0, 1, or 2 parameters (3 if the third is flags). When an argument is repeatedly applied or passed down chains of function calls, it should go on the stack (`mem.push`/`mem.pop`/`mem.drop`) or into named memory (`mem.var`). Docstrings use Forth stack-effect notation: `( input -- output )`.

### Module State Convention

No `global` keyword. Scalar module state lives in `g` dicts (e.g., `g = {"next_entity_id": 1}`). Module-level dicts and lists live outside `g` (e.g., `cmp_entities = set()`, `loaded_component_id_cards = {}`) and are cleared with `D.clear()` or `del L[:]`. Every module with clearable state has a reset function wired into `reset.py`.

### ECS World (`ecs_world.py`)

Minimal entity-component system. Three tables:
- `cmp_entities`: set of live entity IDs
- `cmp_card_ref`: eid → Component ID Card dict
- `cmp_spatial`: eid → `{"x", "y"}` (optional — entities exist without spatial placement)

### Rendering Pipeline (`rendering.py`)

Three-layer declarative architecture: **World (ECS) → Render Intent (RENDER dict) → Canvas Substrate (Tk)**

1. `rebuild_render_intent()` — iterates spatially-placed entities, runs rules to populate RENDER dict
2. `flush_to_canvas()` — reconciles RENDER intent against actual Tk canvas items (create/update/delete)
3. `sync_all()` — orchestrates viewport update → rebuild → flush

Rules are functions that emit element descriptors keyed by element_key tuples. Canvas items are tracked via `ek|...` tags for reconciliation.

### Coordinate Machine (`coord_machine.py`)

Register-based coordinate transformer. Global dicts hold point/rect registers (`g_coord`), camera state (`g_cam`), viewport (`g_view`), and event coords (`g_event`). `project_to("c")` converts world→canvas; `project_to("w")` converts canvas→world. Integer arithmetic throughout (no floats).

### GUI Scaffold (`gui_scaffold.py`)

All widgets registered in the `widgets` dict for static visibility. Layout: three-pane horizontal split (tree | canvas | inspector) with status bar and button bar. `create_gui(root)` builds into a Toplevel; `destroy_gui()` tears down.

### Startup Sequence (`startup.py`)

Thin orchestrator: load persisted cards → cull invalid → rebuild tree → bind canvas events → sync rendering.

### Validation Strategy

Castle-gate validation at system boundaries (card ingestion). Interior code trusts data that passed the gate.

## Testing

Two test layers:
- **Pure-logic tests** (`test/`): pytest, no GUI. Cover coord_machine, ecs_world, component_registry, log.
- **GUI tests** (`guitest/`): tkintertester harness, run inside real Tk mainloop via `--runtime.testing`. Each test module has a `register_*` function called from `cliapp.register_tests()`.

## Key Project Files

- `inventory.json` — document inventory with paths to all specs and external references
- `TODO.json` — current work items and status
- `PROGRESS.json` — session-by-session development notes
- `cryogenic-capsule.json` — links to essential design conversations and salvaged material from marginalia-atlas
- `docs/spec/` — JSON specification documents (rendering system, wire model, component ingestion, etc.)
- `.patchboard-atlas/` — runtime project directory (persisted component ID cards)
