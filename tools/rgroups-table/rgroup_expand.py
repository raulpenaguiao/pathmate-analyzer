"""Step 3 of the r_ pipeline — rgroups_requests.csv + an API key -> rgroups_generated.csv

For the first `--limit N` request rows (thin pools), build the prompt, call
the LLM, and write one row per generated variant. `--limit` is REQUIRED so
the number of API calls is always an explicit, bounded choice.

  ANTHROPIC_API_KEY=sk-... .venv/bin/python rgroup_expand.py --limit 10
  OPENAI_API_KEY=sk-...    .venv/bin/python rgroup_expand.py --limit 10 --provider chatgpt
  .venv/bin/python rgroup_expand.py --limit 10 --dry-run   # prompts only, no calls

Provider auto-detects from whichever key env var is set (ANTHROPIC_API_KEY ->
claude, OPENAI_API_KEY -> chatgpt); --provider forces it. No third-party
packages — plain urllib.
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
REQUESTS = HERE / "rgroups_requests.csv"
OUT = HERE / "rgroups_generated.csv"
PROMPTS = HERE / "expand_prompts.txt"

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


def call_llm(provider: str, prompt: str, api_key: str | None = None) -> list[dict]:
    if provider == "claude":
        key = api_key or os.environ["ANTHROPIC_API_KEY"]
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
        key = api_key or os.environ["OPENAI_API_KEY"]
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
            try:
                variants = call_llm(provider, prompt, api_key=api_key)
                status = "ok"
                time.sleep(1)
            except Exception as e:  # noqa: BLE001
                status = f"failed: {e!r}"
        for j in range(need):
            v = variants[j] if j < len(variants) else {}
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
    if not REQUESTS.is_file():
        sys.exit(f"{REQUESTS.name} not found — run rgroup_prepare.py first")

    reqs = list(csv.DictReader(REQUESTS.open(encoding="utf-8")))

    def _p(i, n, pool, status):
        if status == "start":
            print(f"  [{i}/{n}] {pool[:66]} ...", end="", flush=True)
        else:
            print(f" {status}")

    gen_rows, prompt_log = expand(reqs, provider, limit, dry=dry, progress=_p)

    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GEN_COLS)
        w.writeheader()
        w.writerows(gen_rows)
    PROMPTS.write_text("\n".join(prompt_log))
    ok = sum(1 for r in gen_rows if r["status"] == "ok")
    print(f"\nprovider={provider}  pools processed={min(limit, len(reqs))}/{len(reqs)}  "
          f"variants ok={ok}/{len(gen_rows)}")
    print(f"wrote {OUT.name} and {PROMPTS.name}")
    if dry:
        print("dry run — no API calls; review expand_prompts.txt, then rerun with a key")


if __name__ == "__main__":
    main()
