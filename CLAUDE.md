# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

A Python tool that pulls a contest from the DOMjudge REST API (or replays a saved
CLICS event feed) and writes an `event-feed.json` for the ICPC `resolver`, with
award events (champion, top 3, medals, best women's team, first-to-solve, special
prizes) attached. It also writes a `<name>.csv` listing every awarded team for
building ceremony slides.

User-facing docs: `README.md` (English, default) and `README_zh.md` (Chinese).
Keep both in sync when config options change.

## Running

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python main.py --config demo/config.json   # offline smoke test
.venv/bin/python main.py --config config.json        # default config
```

The demo config replays `demo/event-feed.json` into `cdp-demo/event-feed.json`
without any network access. Use it to verify award changes: grep the output for
`"awards"` events. There is no test suite.

The resolver itself is a separate download (icpctools resolver 2.6.x) and is run
as `resolver.sh <cdp-dir>`. `demo/` is a ready-made CDP directory.

## Layout

- `main.py` - entry point, `--config` flag (default `config.json`).
- `classes/domjudge.py` - the whole pipeline: `load_*` methods fetch each API
  endpoint, `prep_data` computes ranks, `resolver_*_formatter` methods emit the
  event-feed objects, `resolver_award_*_formatter` methods produce awards.
- `classes/pta.py` - older variant for the PTA platform (CCPC school-ranked
  medals). Not exercised by `main.py`; left as is.
- `utils/event_feed.py` - converts a CLICS NDJSON event feed into the dict shape
  the REST API would return, including a recomputed `/scoreboard`.
- `utils/feed_to_api_cache.py` - dumps such a feed into `api-cache/`.
- `utils/utils.py` - time parsing, ordinals, `api_cache_path`.
- `config.json` - generic template committed to git. `demo/config.json` - demo.

## Data flow to remember

`API(method)` resolves in this order: local event feed (`"file"` set) →
`api-cache/` (`cache_requests: true`) → live HTTP. Logos are only downloaded on
the live path. Teams are filtered to known groups minus `exclude_teams`;
submissions, judgements, runs and scoreboard rows are then filtered to those
teams, so excluding a team removes every trace of it.

Awards are assembled in `resolver_award_formatter`. Conventions:
- `self.award(id, citation, team_ids)` also appends to the CSV award list;
  `self.award_as_list(...)` does not and renders as a list in the resolver.
- `team_award_occupy(team_id)` is False for star teams
  (`no_occupy_award_categories`). Star teams get medals shown but never take
  slots, first-to-solve, or rule-based special awards.
- `manual_medals` overrides ranking-based medals and the 1st-3rd Place awards.
- `special_awards` is a list; each entry has `rule` (`last_ac`,
  `most_submissions`) or `team_ids`. To add a rule, write a
  `special_<name>(self) -> [team_id]` method and register it in the `rules`
  dict in `resolver_award_special_formatter`. `last_ac_citation` alone is the
  backward-compatible fallback.
- Team `photo` fields from DOMjudge are stripped on export so the resolver uses
  `teams/<id>/photo.png` from the CDP directory.

## Local, contest-specific files (gitignored, do not commit)

`contest/`, `cdp/`, `cdp-demo/`, `real/`, `real-config.json`, `run.sh`,
`api-cache/`, `organizations/`, `logs/`, `.venv/`, and any top-level
`*.json`/`*.csv` other than `config.json` and `pta.json`. `run.sh` is a
machine-specific wrapper that builds the CDP directory and launches the
resolver; it is intentionally untracked. Never put real credentials or contest
names into the tracked `config.json`.

## Conventions

- Existing comments and docstrings mix Chinese and English; either is fine.
- Config keys are read with `self.config.get(key, default)` so old configs keep
  working. Preserve that when adding options, and document new keys in both
  READMEs (schema block plus a bullet).
- Commits: small, one logical change each, imperative subject line.
