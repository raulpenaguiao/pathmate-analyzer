"""Expand thin randomisation pools with an LLM.

Reads rgroups_table.csv (from build_table.py). For every *pool*
(randomisationGroup x microDialog) that has fewer than TARGET distinct variants,
it asks an LLM for the missing variants - same meaning, ~same length, natural
emoji, age-appropriate for 10-19 year olds, both en-GB and ro-RO - and writes
rgroups_table.expanded.csv (existing rows + new `generated` rows).

Providers (pick with --provider, or it auto-detects from the env var present):
  claude   -> ANTHROPIC_API_KEY   (model: $ANTHROPIC_MODEL or claude-sonnet-5)
  chatgpt  -> OPENAI_API_KEY      (model: $OPENAI_MODEL or gpt-4o)

  .venv/bin/python expand_rgroups.py --dry-run           # write prompts only
  ANTHROPIC_API_KEY=sk-... .venv/bin/python expand_rgroups.py
  OPENAI_API_KEY=sk-...    .venv/bin/python expand_rgroups.py --provider chatgpt
  TARGET=12 .venv/bin/python expand_rgroups.py

No third-party packages - the HTTP calls are plain urllib.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE = HERE / "rgroups_table.csv"
OUT = HERE / "rgroups_table.expanded.csv"
PROMPTS = HERE / "expand_prompts.txt"
TARGET = int(os.environ.get("TARGET", "10"))

SYSTEM = (
    "You write message variants for a mobile asthma-coaching app used by "
    "adolescents aged 10-19. The app shows one variant picked at random from a "
    "pool, so every variant in a pool must be interchangeable in meaning. "
    "Romanian text MUST use the informal/colloquial second person ('tu': e.g. "
    "esti, ai, te simti, al tau / a ta) - NEVER the formal 'dumneavoastra' / "
    "'dumneata' or formal verb forms."
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


def call_llm(provider: str, prompt: str) -> list[dict]:
    if provider == "claude":
        key = os.environ["ANTHROPIC_API_KEY"]
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": model, "max_tokens": 2000, "system": SYSTEM,
                             "messages": [{"role": "user", "content": prompt}]}).encode(),
            method="POST",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
    elif provider == "chatgpt":
        key = os.environ["OPENAI_API_KEY"]
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({"model": model, "temperature": 0.9,
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
    return json.loads(text)


def main() -> None:
    dry = "--dry-run" in sys.argv
    provider = "dry-run" if dry else detect_provider()
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if not TABLE.is_file():
        sys.exit(f"{TABLE.name} not found - run build_table.py first")

    src_rows = list(csv.DictReader(TABLE.open()))
    fields = list(src_rows[0].keys()) + ["kind"]

    # group by pool, preserving first-seen order
    pools: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in src_rows:
        pools.setdefault(r["pool"], []).append(r)

    out_rows, prompt_log = [], []
    n_generated = 0
    n_generated_pools = 0
    for pool, rws in pools.items():
        for r in rws:
            out_rows.append({**r, "kind": "existing"})
        seen, variants = set(), []
        for r in rws:
            en = (r["en-GB"] or "").strip()
            if not en or en == "[not set]" or en.lower() in seen:
                continue
            seen.add(en.lower())
            variants.append({"en-GB": en, "ro-RO": (r["ro-RO"] or "").strip()})
        have = len(variants)
        if have >= TARGET:
            continue
        need = TARGET - have
        head = rws[0]
        ctx = ""
        if head.get("folderPath"):
            ctx += f"Folder: {head['folderPath']}\n"
        if head.get("comment") and head["comment"] not in ("---", ""):
            ctx += f"Comment: {head['comment']}\n"
        trg = {r["triggerExprs"] for r in rws if r.get("triggerExprs")}
        if trg:
            ctx += "Shown when: " + " | ".join(sorted(trg)) + "\n"
        existing = "\n".join(f'{i+1}. en-GB: {v["en-GB"]}\n   ro-RO: {v["ro-RO"]}'
                             for i, v in enumerate(variants)) or "(none yet)"
        prompt = PROMPT.format(md=head["microDialog"], group=head["randomisationGroup"],
                               ctx=ctx, have=have, need=need, existing=existing)
        prompt_log.append(f"### {pool}\n{prompt}\n")

        gen = []
        if not dry and (limit is None or n_generated_pools < limit):
            try:
                gen = call_llm(provider, prompt)
                n_generated += len(gen)
                n_generated_pools += 1
                print(f"  +{len(gen):2}/{need}  {pool[:70]}")
                time.sleep(1)
            except Exception as e:  # noqa: BLE001
                print(f"  !! {pool[:70]}  {e!r}")
        for j in range(need):
            g = gen[j] if j < len(gen) else {}
            out_rows.append({
                **{k: "" for k in fields},
                "randomisationGroup": head["randomisationGroup"], "pool": pool,
                "groupTotalMessages": head["groupTotalMessages"],
                "groupMicroDialogs": head["groupMicroDialogs"],
                "poolVariants": have + len([x for x in range(j + 1)]),
                "microDialog": head["microDialog"], "folderPath": head["folderPath"],
                "comment": head["comment"], "answerType": head["answerType"],
                "channel": head["channel"],
                "kind": "generated" if g else "TO_GENERATE",
                "en-GB": g.get("en-GB", ""), "ro-RO": g.get("ro-RO", ""),
            })

    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    PROMPTS.write_text("\n".join(prompt_log))
    print(f"\nprovider={provider}  pools<{TARGET}={len(prompt_log)}  "
          f"generated={n_generated}")
    print(f"wrote {OUT.name} ({len(out_rows)} rows) and {PROMPTS.name}")
    if dry:
        print("dry run - no API calls made; review expand_prompts.txt, then rerun "
              "without --dry-run and with an API key")


if __name__ == "__main__":
    main()
