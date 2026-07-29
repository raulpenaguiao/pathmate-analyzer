"""Extracts summary statistics from a raw PMCP coaching HTML export.

The export (see the accordion sections: Basic Settings / Surveys / Rules /
Message Groups and Messages / Micro Dialogs) has two different shapes that
matter here:

- The "Rules" section is a FLAT sequence of independent
  <table class="automatic"> blocks, one per rule, with nesting only implied
  visually via a border-left-width style (20px per level).
- "Message Groups and Messages" and "Micro Dialogs" genuinely nest tables
  (a message group contains per-message tables, a micro dialog contains
  per-node tables, which themselves contain further nested tables for
  multi-language text). Naive non-greedy regex across "</table>" cannot
  tell these apart, so a small balanced-tag scanner is used instead of
  pulling in an HTML parsing dependency for what is otherwise a very
  regular, machine-generated document.
"""
from __future__ import annotations

import html
import re
from collections import Counter

_TAG_PATTERN_CACHE: dict[str, re.Pattern] = {}


def _tag_pattern(tag: str) -> re.Pattern:
    if tag not in _TAG_PATTERN_CACHE:
        _TAG_PATTERN_CACHE[tag] = re.compile(rf"<{tag}\b[^>]*>|</{tag}>")
    return _TAG_PATTERN_CACHE[tag]


def _find_matching_close(text: str, pos: int, tag: str) -> int:
    """`pos` must sit right after an already-open <tag ...> (implied depth 1).
    Returns the start index of the </tag> that closes it, correctly skipping
    over any nested <tag>...</tag> occurrences in between."""
    depth = 1
    for m in _tag_pattern(tag).finditer(text, pos):
        if m.group(0)[1] == "/":
            depth -= 1
            if depth == 0:
                return m.start()
        else:
            depth += 1
    return len(text)


def _iter_blocks(text: str, tag: str, class_value: str | None = None):
    """Yield inner_html for each top-level <tag ...>...</tag> block in text
    (i.e. not nested inside another block of the same tag already returned),
    optionally filtered to a given class="..." attribute value."""
    open_re = re.compile(rf"<{tag}\b([^>]*)>")
    pos = 0
    while True:
        m = open_re.search(text, pos)
        if not m:
            return
        close_start = _find_matching_close(text, m.end(), tag)
        if class_value is None or f'class="{class_value}"' in m.group(1):
            yield text[m.end():close_start]
        pos = close_start + len(f"</{tag}>")


def _section_div(body: str, header_text: str) -> str:
    """Inner HTML of the <div> immediately following <h2>header_text</h2>."""
    marker = f"<h2>{header_text}</h2>"
    idx = body.find(marker)
    if idx == -1:
        return ""
    rest = body[idx + len(marker):]
    open_m = re.search(r"<div[^>]*>", rest)
    if not open_m:
        return ""
    start = idx + len(marker) + open_m.end()
    close_start = _find_matching_close(body, start, "div")
    return body[start:close_start]


_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _clean_text(raw: str | None) -> str:
    if not raw:
        return ""
    return html.unescape(_TAG_STRIP_RE.sub("", raw)).strip()


def _field(inner_html: str, label: str) -> str | None:
    m = re.search(rf"<th[^>]*>{re.escape(label)}</th><td\s*>(.*?)</td>", inner_html, re.DOTALL)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Rules section (flat table sequence, depth encoded via border-left-width)
# ---------------------------------------------------------------------------

_RULE_DEPTH_RE = re.compile(r'<th style="border-left-width:\s*(\d+)px;">Rule:</th>')


def _rules_stats(rules_div: str) -> dict:
    total = 0
    max_depth = 0
    stop_intervention_yes = 0
    send_message_yes = 0

    for block in _iter_blocks(rules_div, "table", "automatic"):
        total += 1

        depth_m = _RULE_DEPTH_RE.search(block)
        depth = int(depth_m.group(1)) // 20 if depth_m else 0
        max_depth = max(max_depth, depth)

        stop_field = _field(block, "Stop Intervention when TRUE:")
        if stop_field and 'class="yes"' in stop_field:
            stop_intervention_yes += 1

        send_field = _field(block, "Send message when TRUE:")
        if send_field and 'class="yes"' in send_field:
            send_message_yes += 1

    return {
        "total": total,
        "max_depth": max_depth,
        "stop_intervention_yes": stop_intervention_yes,
        "send_message_yes": send_message_yes,
    }


# ---------------------------------------------------------------------------
# Message Groups and Messages
# ---------------------------------------------------------------------------

def _message_group_stats(mg_div: str) -> dict:
    groups = list(_iter_blocks(mg_div, "table", "automatic"))
    messages_total = 0
    for group in groups:
        messages_total += sum(1 for _ in _iter_blocks(group, "table", "automatic"))
    return {"groups_total": len(groups), "messages_total": messages_total}


# ---------------------------------------------------------------------------
# Micro Dialogs
# ---------------------------------------------------------------------------

_NODE_TYPE_RE = re.compile(
    r"^\s*<tr\s*><th\s*>(Micro Dialog (?:Message|Command Message|Decision Point))</th></tr>"
)


def _classify_node(node_html: str) -> str:
    m = _NODE_TYPE_RE.match(node_html)
    return m.group(1) if m else "Unknown"


def _micro_dialog_stats(md_div: str) -> dict:
    node_type_counts: Counter = Counter()
    dialog_sizes = []
    largest = []

    for dialog in _iter_blocks(md_div, "table", "automatic"):
        name = _clean_text(_field(dialog, "Name:")) or "(unnamed)"
        nodes = list(_iter_blocks(dialog, "table", "automatic"))
        for node in nodes:
            node_type_counts[_classify_node(node)] += 1

        dialog_sizes.append(len(nodes))
        largest.append({"name": name, "node_count": len(nodes)})

    largest.sort(key=lambda d: d["node_count"], reverse=True)

    return {
        "dialogs_total": len(dialog_sizes),
        "nodes_total": sum(dialog_sizes),
        "messages": node_type_counts.get("Micro Dialog Message", 0),
        "command_messages": node_type_counts.get("Micro Dialog Command Message", 0),
        "decision_points": node_type_counts.get("Micro Dialog Decision Point", 0),
        "unknown_node_types": {
            k: v for k, v in node_type_counts.items() if k == "Unknown" and v
        },
        "size_distribution": {
            "min": min(dialog_sizes) if dialog_sizes else 0,
            "max": max(dialog_sizes) if dialog_sizes else 0,
            "avg": round(sum(dialog_sizes) / len(dialog_sizes), 1) if dialog_sizes else 0,
        },
        "largest_dialogs": largest[:5],
    }


# ---------------------------------------------------------------------------
# Document-wide (variables, channels, translation completeness)
# ---------------------------------------------------------------------------

_VARIABLE_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
_CHANNEL_RE = re.compile(r"Channel to send message:</th><td\s*>(.*?)</td>", re.DOTALL)
_LANGUAGE_LABEL_RE = re.compile(r"<th\s*>([a-z]{2}-[A-Z]{2}):</th>")


def _variable_count(body: str) -> int:
    return len(set(_VARIABLE_RE.findall(body)))


def _channel_mix(body: str) -> dict:
    counts = Counter(_clean_text(m) for m in _CHANNEL_RE.findall(body))
    return dict(counts.most_common())


def _translation_completeness(body: str) -> dict:
    languages = sorted(set(_LANGUAGE_LABEL_RE.findall(body)))
    result = {}
    for lang in languages:
        pattern = re.compile(rf"<th\s*>{lang}:</th><td\s*>(.*?)</td>", re.DOTALL)
        values = pattern.findall(body)
        not_set = sum(1 for v in values if _clean_text(v) == "[not set]")
        total = len(values)
        result[lang] = {
            "total": total,
            "set": total - not_set,
            "not_set": not_set,
            "pct_set": round(100 * (total - not_set) / total, 1) if total else 0,
        }
    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_stats(file_bytes: bytes) -> dict:
    body = file_bytes.decode("utf-8", errors="replace")

    return {
        "rules": _rules_stats(_section_div(body, "Rules")),
        "message_groups": _message_group_stats(_section_div(body, "Message Groups and Messages")),
        "micro_dialogs": _micro_dialog_stats(_section_div(body, "Micro Dialogs")),
        "unique_variables": _variable_count(body),
        "channels": _channel_mix(body),
        "languages": _translation_completeness(body),
    }
