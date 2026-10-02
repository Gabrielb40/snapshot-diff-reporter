"""Diff two snapshots and report added / removed / changed keys.

Flattening is intentionally only applied to keys that have been identified
as *changed*. If a whole subtree was added or removed we keep it as a
single value so the caller can decide how to present it; flattening it
again would lose the useful "this whole thing is new" signal.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, Mapping, Tuple


def _is_mapping(obj: Any) -> bool:
    """Mapping check that ignores str/bytes.

    Strings are technically sequences of characters and (in Python) not
    mappings, but they are iterable; the explicit isinstance check keeps
    us from descending into "hello"[0] territory.
    """
    return isinstance(obj, Mapping)


def flatten(obj: Mapping[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten a nested mapping into a dict with dot-separated keys.

    Only ``Mapping`` instances are traversed. Everything else (lists,
    strings, ints, None, custom objects) is treated as a leaf value — the
    library compares snapshots, not arbitrary data structures, so a list
    being replaced by another list is reported as a single change rather
    than an element-wise diff.
    """
    out: Dict[str, Any] = {}
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if _is_mapping(v):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def _walk(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else str(key)


def _shared_keys(a: Mapping[str, Any], b: Mapping[str, Any]) -> Iterator[str]:
    """Yield keys present in both mappings, in the iteration order of ``a``.

    Iterating ``a`` first keeps the diff order stable relative to the
    before-snapshot, which is what humans usually read from.
    """
    for k in a:
        if k in b:
            yield k


def _diff_recursive(
    a: Any,
    b: Any,
    prefix: str,
    added: Dict[str, Any],
    removed: Dict[str, Any],
    changed: Dict[str, Any],
) -> None:
    """Populate ``added``/``removed``/``changed`` for a single key path.

    This is where the one real decision lives: when both sides are mappings
    with the same key, we recurse *instead* of reporting a change at that
    level. That means ``a={"x": {"y": 1}}`` vs ``b={"x": {"y": 2}}`` is
    reported as ``changed={"x.y": (1, 2)}``, not
    ``changed={"x": ({"y": 1}, {"y": 2})}``.

    If either side stops being a mapping, we stop recursing and treat the
    whole thing as one changed leaf. So a dict turning into a string is a
    single change, not a forest of removals plus an add.
    """
    if _is_mapping(a) and _is_mapping(b):
        for k in b:
            if k not in a:
                added[_walk(prefix, k)] = b[k]
        for k in a:
            if k not in b:
                removed[_walk(prefix, k)] = a[k]
        for k in _shared_keys(a, b):
            _diff_recursive(a[k], b[k], _walk(prefix, k), added, removed, changed)
    else:
        # Comparable non-mapping values (int, str, list, None, custom objects).
        try:
            equal = bool(a == b)
        except Exception:
            # An __eq__ that raises is pathological but we promised
            # not to blow up; treat it as "changed".
            equal = False
        if not equal:
            changed[prefix] = (a, b)


def diff_snapshots(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Diff two snapshots.

    Returns ``(added, removed, changed)`` where ``added`` and ``removed``
    use dot-notation keys pointing at whole subtree values, and ``changed``
    maps dot-notation keys to ``(before_value, after_value)`` tuples for
    the *leaves* that differ.

    The three dicts are returned in a fixed order so callers can unpack
    positionally: ``added, removed, changed = diff_snapshots(old, new)``.
    """
    added: Dict[str, Any] = {}
    removed: Dict[str, Any] = {}
    changed: Dict[str, Any] = {}
    _diff_recursive(before, after, "", added, removed, changed)
    return added, removed, changed
