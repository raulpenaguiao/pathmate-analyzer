"""Low-level scanner for PMCP coaching HTML exports.

The export is a machine-generated, very regular document built out of nested
``<table class="automatic">`` blocks. "Rules" is a flat sequence of such blocks
(nesting only implied visually via ``border-left-width``), while "Message Groups"
and "Micro Dialogs" genuinely nest tables. A non-greedy regex across ``</table>``
cannot tell those apart, so this module provides a small balanced-tag scanner
instead of pulling in a full HTML parsing dependency.

These helpers are shared by :mod:`app.coaching_stats` (summary numbers) and
:mod:`app.coaching_model` (the structured model behind the coaching view).
"""
from __future__ import annotations

import html
import re

_TAG_PATTERN_CACHE: dict[str, re.Pattern] = {}


def tag_pattern(tag: str) -> re.Pattern:
    if tag not in _TAG_PATTERN_CACHE:
        _TAG_PATTERN_CACHE[tag] = re.compile(rf"<{tag}\b[^>]*>|</{tag}>")
    return _TAG_PATTERN_CACHE[tag]


def find_matching_close(text: str, pos: int, tag: str) -> int:
    """`pos` must sit right after an already-open <tag ...> (implied depth 1).
    Returns the start index of the </tag> that closes it, correctly skipping
    over any nested <tag>...</tag> occurrences in between."""
    depth = 1
    for m in tag_pattern(tag).finditer(text, pos):
        if m.group(0)[1] == "/":
            depth -= 1
            if depth == 0:
                return m.start()
        else:
            depth += 1
    return len(text)


def iter_blocks(text: str, tag: str, class_value: str | None = None):
    """Yield inner_html for each top-level <tag ...>...</tag> block in text
    (i.e. not nested inside another block of the same tag already returned),
    optionally filtered to a given class="..." attribute value."""
    open_re = re.compile(rf"<{tag}\b([^>]*)>")
    pos = 0
    while True:
        m = open_re.search(text, pos)
        if not m:
            return
        close_start = find_matching_close(text, m.end(), tag)
        if class_value is None or f'class="{class_value}"' in m.group(1):
            yield text[m.end():close_start]
        pos = close_start + len(f"</{tag}>")


def section_div(body: str, header_text: str) -> str:
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
    close_start = find_matching_close(body, start, "div")
    return body[start:close_start]


_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def clean_text(raw: str | None) -> str:
    if not raw:
        return ""
    return html.unescape(_TAG_STRIP_RE.sub("", raw)).strip()


def field(inner_html: str, label: str) -> str | None:
    """Raw ``<td>`` HTML for a ``<th>label</th><td>...</td>`` row, or None."""
    m = re.search(
        rf"<th[^>]*>{re.escape(label)}</th><td\s*>(.*?)</td>", inner_html, re.DOTALL
    )
    return m.group(1) if m else None
