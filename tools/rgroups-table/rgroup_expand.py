"""Step 3 of the r_ pipeline — rgroups_requests.csv + an API key -> rgroups_generated.csv

For the first `--limit N` request rows (thin pools), build the prompt, call
the LLM, and write one row per generated variant. `--limit` is REQUIRED so
the number of API calls is always an explicit, bounded choice.

  ANTHROPIC_API_KEY=sk-... .venv/bin/python rgroup_expand.py --limit 10
  OPENAI_API_KEY=sk-...    .venv/bin/python rgroup_expand.py --limit 10 --provider chatgpt
  .venv/bin/python rgroup_expand.py --limit 10 --dry-run   # prompts only, no calls

Provider auto-detects from whichever key env var is set (ANTHROPIC_API_KEY ->
claude, OPENAI_API_KEY -> chatgpt, also read from <repo>/.env if not already
set); --provider forces it. No third-party packages for the API calls
themselves — plain urllib.

All input/output files (rgroups_requests_*.csv, rgroups_generated_*.csv,
expand_prompts_*.txt, expand_raw_failures.txt) live in <repo>/data/rgroups/,
not next to this script - the directory is created if missing, and the path
is computed from this file's own location, not the current working
directory, so this runs the same regardless of where it's invoked from.

The input defaults to the most RECENTLY-RUN rgroups_requests_*.csv (by its
embedded YYMMDDHHMMSS timestamp, not file mtime); the output CSV and its
matching prompt log share one fresh timestamp for this run, so a
rgroups_generated_<ts>.csv and expand_prompts_<ts>.txt pair always
correspond to the exact same run. expand_raw_failures.txt stays a single
running append-only log across every run (not per-run timestamped) - it's
a diagnostic history, not a per-run artifact.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path

from dotenv import load_dotenv

from _rgroups_files import latest, now_ts

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
# Explicit path (not a cwd-relative search) so this works the same regardless
# of where this script is invoked from - matches app/config.py's load_dotenv()
# use, just pointed at the repo root by construction instead of relying on
# python-dotenv's own upward-search default. Never overrides a key already
# set in the real shell environment (load_dotenv's own default behavior).
load_dotenv(REPO / ".env")

# All generated/intermediate files live in data/rgroups/, not next to this
# script - keeps a `--dry-run` test (or any test run) from ever clobbering
# real output sitting in the same directory as the source, and matches how
# tools/coaching-bundle-export writes into data/exports/. Path is computed
# from this file's own location, not the cwd - run this from anywhere.
DATA_DIR = REPO / "data" / "rgroups"
RAW_FAILURES = DATA_DIR / "expand_raw_failures.txt"

GEN_COLS = ["pool", "randomisationGroup", "microDialog", "folderPath",
            "variantIndex", "en-GB", "ro-RO", "status"]

SYSTEM = (
    "You write message variants for a mobile asthma-coaching app used by "
    "adolescents aged 10-19. The app shows one variant picked at random from a "
    "pool, so every variant in a pool must be interchangeable in meaning. "
    "Romanian text MUST use the informal/colloquial second person ('tu': e.g. "
    "esti, ai, te simti, al tau / a ta) - NEVER the formal 'dumneavoastra' / "
    "'dumneata' or formal verb forms. For any adjective or participle that "
    "agrees with the reader's gender, follow the existing ro-RO house style: "
    "use the unmarked generic masculine (e.g. 'esti pregatit', 'te simti "
    "odihnit') or, better, rephrase to avoid a gendered form (e.g. 'esti gata', "
    "an invariable adjective, verb-only phrasing). NEVER write spelled-out "
    "slash pairs like 'singur/singura' or 'pregatit/pregatita'. The ro-RO must "
    "read like something a Romanian teenager would actually say or text, NOT a "
    "word-for-word rendering of the English. When the English uses an idiom or "
    "figure of speech (e.g. 'hope your day is treating you well', \"you're on a "
    "roll\", 'I'm a message away', 'stay awesome', 'sending you support', 'your "
    "lungs will thank you', 'take a moment for yourself'), replace it with "
    "natural Romanian phrasing - never translate it literally. Do NOT use "
    "English loanwords (write 'memento' or 'reamintire', not 'reminder'). Use "
    "Romanian comma-below diacritics (s-comma, t-comma), never cedilla forms."
)

PROMPT = """Micro dialog: "{md}"   (randomisation group `{group}`)
{ctx}This pool has {have} existing variant(s):

{existing}

Write {need} ADDITIONAL variant(s). Every new variant must:
- carry the same meaning / intent as the existing ones (fully interchangeable)
- be about the same length as the existing ones
- use emoji naturally and sparingly, in the same spirit as the existing ones
- sound warm and encouraging, right for ages 10-19 (not childish, not clinical)
- keep $placeholder tokens usable (e.g. $participantName); match the existing
  mix of "with name" vs "without name"
- give BOTH en-GB and ro-RO. The ro-RO must be a natural (not literal)
  translation and MUST address the user with the informal/colloquial "tu"
  (e.g. "ai dormit", "cum te simti", "programul tau") - never "dumneavoastra"
  or any formal form, matching the existing ro-RO variants.
- for ro-RO words that agree with the reader's gender, match the existing
  variants: unmarked generic masculine ("esti pregatit") or a gender-neutral
  rephrase ("esti gata"); never a spelled-out slash pair ("singur/singura")
- write ro-RO that sounds native, not translated: swap English idioms for real
  Romanian phrasing, use no English loanwords ("reminder"), and never render a
  figure of speech word-for-word

Return ONLY a JSON array of exactly {need} objects: {{"en-GB": "...", "ro-RO": "..."}}
"""


def detect_provider() -> str:
    if "--provider" in sys.argv:
        return sys.argv[sys.argv.index("--provider") + 1]
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("OPENAI_API_KEY"):
        return "chatgpt"
    sys.exit("set ANTHROPIC_API_KEY or OPENAI_API_KEY (or pass --dry-run)")


class LLMParseError(Exception):
    """The LLM's response wasn't valid JSON (truncated mid-string, an
    unescaped quote inside a message, extra commentary, etc). Carries
    whatever _salvage_variants() could still recover, so a caller can use
    partial results instead of throwing away an entire pool over one bad
    character - and the raw text, so the failure is actually diagnosable
    instead of just a JSONDecodeError with a line/column number."""

    def __init__(self, original: Exception, raw_text: str, salvaged: list[dict]):
        super().__init__(str(original))
        self.original = original
        self.raw_text = raw_text
        self.salvaged = salvaged


def _salvage_variants(text: str) -> list[dict]:
    """Best-effort recovery from a malformed/truncated JSON array: pull out
    every top-level {...} object individually (each variant object is flat -
    no nested braces - so a simple non-greedy brace match is safe) and keep
    whichever ones parse on their own. One truncated object at the end (the
    common case when the response got cut off) or one bad escape in the
    middle no longer costs the whole batch."""
    out = []
    for m in re.finditer(r"\{[^{}]*\}", text, re.DOTALL):
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _log_raw_failure(pool: str, text: str, error: Exception) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with RAW_FAILURES.open("a", encoding="utf-8") as fh:
        fh.write(f"\n{'='*80}\npool: {pool}\nerror: {error!r}\n{'-'*80}\n{text}\n")


def call_llm(provider: str, prompt: str, api_key: str | None = None,
             max_tokens: int = 2000, pool: str = "?") -> list[dict]:
    if provider == "claude":
        key = api_key or os.environ["ANTHROPIC_API_KEY"]
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": model, "max_tokens": max_tokens, "system": SYSTEM,
                             "messages": [{"role": "user", "content": prompt}]}).encode(),
            method="POST",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
    elif provider == "chatgpt":
        key = api_key or os.environ["OPENAI_API_KEY"]
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({"model": model, "temperature": 0.9, "max_tokens": max_tokens,
                             "messages": [{"role": "system", "content": SYSTEM},
                                          {"role": "user", "content": prompt}]}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        text = data["choices"][0]["message"]["content"]
    else:
        sys.exit(f"unknown provider {provider!r} (use claude or chatgpt)")

    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:].strip() if text.lower().startswith("json") else text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        salvaged = _salvage_variants(text)
        _log_raw_failure(pool, text, e)
        raise LLMParseError(e, text, salvaged) from e


def build_prompt(req: dict) -> str:
    """Build the LLM prompt for one request row (from rgroups_requests.csv)."""
    en = [x for x in (req.get("existing_enGB") or "").split("\n") if x.strip()]
    ro = (req.get("existing_roRO") or "").split("\n")
    existing = "\n".join(
        f'{i+1}. en-GB: {e}\n   ro-RO: {ro[i] if i < len(ro) else ""}'
        for i, e in enumerate(en)) or "(none yet)"
    ctx = ""
    if req.get("folderPath"):
        ctx += f"Folder: {req['folderPath']}\n"
    if req.get("comment") and req["comment"] not in ("---", ""):
        ctx += f"Comment: {req['comment']}\n"
    if req.get("triggerExprs"):
        ctx += f"Shown when: {req['triggerExprs']}\n"
    return PROMPT.format(md=req["microDialog"], group=req["randomisationGroup"],
                         ctx=ctx, have=req["haveVariants"],
                         need=req["needVariants"], existing=existing)


def expand(requests, provider, limit, dry=False, progress=None, api_key=None):
    """Process the first `limit` request rows. `progress(i, n, pool, status)`
    is called before and after each pool. Returns (generated_rows, prompt_log).
    `api_key` overrides the provider's env var (used by the portal, which
    never writes the key to disk or the environment).
    """
    reqs = list(requests)[:limit]
    n = len(reqs)
    gen_rows, prompt_log = [], []
    for i, req in enumerate(reqs, 1):
        pool = req["pool"]
        prompt = build_prompt(req)
        prompt_log.append(f"### {pool}\n{prompt}\n")
        if progress:
            progress(i, n, pool, "start")
        need = int(req["needVariants"])
        variants, status = [], "dry-run"
        if not dry:
            # Scale the token budget with how much was actually asked for -
            # a fixed 2000 is plenty for a couple of variants but can run
            # close to the edge for a pool needing many, making truncation
            # (an unterminated string at the cutoff) more likely.
            max_tokens = max(2000, 400 * need + 500)
            try:
                variants = call_llm(provider, prompt, api_key=api_key,
                                     max_tokens=max_tokens, pool=pool)
                if not isinstance(variants, list):
                    raise ValueError(
                        f"expected a JSON array, got {type(variants).__name__}")
                status = "ok"
                time.sleep(1)
            except LLMParseError as e:
                if e.salvaged:
                    variants = e.salvaged
                    status = (f"partial: recovered {len(e.salvaged)}/{need} after "
                              f"a JSON parse error ({e.original!r}) - raw response "
                              f"in {RAW_FAILURES.name}")
                else:
                    variants = []
                    status = f"failed: {e.original!r} - raw response in {RAW_FAILURES.name}"
            except Exception as e:  # noqa: BLE001 -- one bad pool must not abort the run
                variants = []
                status = f"failed: {e!r}"
        for j in range(need):
            v = variants[j] if j < len(variants) else {}
            if not isinstance(v, dict):
                v = {}
            gen_rows.append({
                "pool": pool, "randomisationGroup": req["randomisationGroup"],
                "microDialog": req["microDialog"], "folderPath": req["folderPath"],
                "variantIndex": j + 1,
                "en-GB": v.get("en-GB", ""), "ro-RO": v.get("ro-RO", ""),
                "status": "ok" if v else status,
            })
        if progress:
            progress(i, n, pool, status)
    return gen_rows, prompt_log


def main() -> None:
    dry = "--dry-run" in sys.argv
    provider = "dry-run" if dry else detect_provider()
    if "--limit" not in sys.argv:
        sys.exit("--limit N is required (it caps the number of API calls). "
                 "See rgroups_requests.csv for how many thin pools there are.")
    limit = int(sys.argv[sys.argv.index("--limit") + 1])
    requests_csv = latest(DATA_DIR, "rgroups_requests", ".csv")
    if requests_csv is None:
        sys.exit(f"no rgroups_requests_*.csv in {DATA_DIR} — run rgroup_prepare.py first")
    print(f"using {requests_csv.name}")

    reqs = list(csv.DictReader(requests_csv.open(encoding="utf-8")))

    def _p(i, n, pool, status):
        if status == "start":
            print(f"  [{i}/{n}] {pool[:66]} ...", end="", flush=True)
        else:
            print(f" {status}")

    gen_rows, prompt_log = expand(reqs, provider, limit, dry=dry, progress=_p)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = now_ts()
    out = DATA_DIR / f"rgroups_generated_{ts}.csv"
    prompts = DATA_DIR / f"expand_prompts_{ts}.txt"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GEN_COLS)
        w.writeheader()
        w.writerows(gen_rows)
    prompts.write_text("\n".join(prompt_log))
    ok = sum(1 for r in gen_rows if r["status"] == "ok")
    print(f"\nprovider={provider}  pools processed={min(limit, len(reqs))}/{len(reqs)}  "
          f"variants ok={ok}/{len(gen_rows)}")
    print(f"wrote {out} and {prompts}")
    if dry:
        print(f"dry run — no API calls; review {prompts.name}, then rerun with a key")


if __name__ == "__main__":
    main()
