"""Extracts summary statistics from a raw PMCP coaching HTML export.

The "Rules" section is a FLAT sequence of independent <table class="automatic">
blocks with nesting implied only via a border-left-width style (20px per level),
while "Message Groups and Messages" and "Micro Dialogs" genuinely nest tables.
The balanced-tag scanner that tells these apart lives in :mod:`app.pmcp_html`;
:mod:`app.coaching_model` builds the browsable model on top of the same helpers.
"""
from __future__ import annotations

import re
from collections import Counter

from app.pmcp_html import clean_text as _clean_text
from app.pmcp_html import field as _field
from app.pmcp_html import find_matching_close as _find_matching_close
from app.pmcp_html import iter_blocks as _iter_blocks
from app.pmcp_html import section_div as _section_div


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


def build_rule_tree(rules_div: str) -> list[dict]:
    """Reconstruct the real parent/child nesting from the flat, depth-indented
    sequence of rule tables (see module docstring - nesting is only implied
    visually via border-left-width, not actual DOM nesting)."""
    roots: list[dict] = []
    stack: list[tuple[int, dict]] = []  # (depth, item), innermost last

    for block in _iter_blocks(rules_div, "table", "automatic"):
        depth_m = _RULE_DEPTH_RE.search(block)
        depth = int(depth_m.group(1)) // 20 if depth_m else 0

        comment = _clean_text(_field(block, "Comment:"))
        variable = _clean_text(_field(block, "Variable to store value to:"))
        stop_field = _field(block, "Stop Intervention when TRUE:")
        send_field = _field(block, "Send message when TRUE:")

        item = {
            "rule": _clean_text(_field(block, "Rule:")),
            "comment": comment if comment != "[not set]" else "",
            "variable": variable if variable != "[not set]" else "",
            "stop_intervention": bool(stop_field and 'class="yes"' in stop_field),
            "send_message": bool(send_field and 'class="yes"' in send_field),
            "children": [],
        }

        while stack and stack[-1][0] >= depth:
            stack.pop()

        (stack[-1][1]["children"] if stack else roots).append(item)
        stack.append((depth, item))

    return roots


def extract_rules_tree(file_bytes: bytes) -> list[dict]:
    body = file_bytes.decode("utf-8", errors="replace")
    return build_rule_tree(_section_div(body, "Rules"))


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

# A Micro Dialog is a sequence of items, each one of three types: a message
# (a plain message or a command message are both message variants), a
# decision point, or an event.
_ITEM_TYPE_RE = re.compile(
    r"^\s*<tr\s*><th\s*>(Micro Dialog (?:Message|Command Message|Decision Point|Event))</th></tr>"
)


def _classify_item(item_html: str) -> str:
    m = _ITEM_TYPE_RE.match(item_html)
    return m.group(1) if m else "Unknown"


def _micro_dialog_stats(md_div: str) -> dict:
    item_type_counts: Counter = Counter()
    dialog_sizes = []
    largest = []

    for dialog in _iter_blocks(md_div, "table", "automatic"):
        name = _clean_text(_field(dialog, "Name:")) or "(unnamed)"
        items = list(_iter_blocks(dialog, "table", "automatic"))
        for item in items:
            item_type_counts[_classify_item(item)] += 1

        dialog_sizes.append(len(items))
        largest.append({"name": name, "item_count": len(items)})

    largest.sort(key=lambda d: d["item_count"], reverse=True)

    return {
        "dialogs_total": len(dialog_sizes),
        "items_total": sum(dialog_sizes),
        "messages": item_type_counts.get("Micro Dialog Message", 0),
        "command_messages": item_type_counts.get("Micro Dialog Command Message", 0),
        "decision_points": item_type_counts.get("Micro Dialog Decision Point", 0),
        "events": item_type_counts.get("Micro Dialog Event", 0),
        "unknown_item_types": {
            k: v for k, v in item_type_counts.items() if k == "Unknown" and v
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
