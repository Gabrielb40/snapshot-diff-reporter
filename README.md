# Snapshot Diff Reporter

Diffs two dicts and reports added, removed, and changed keys, flattening nested changes with dot notation.

```python
from snapshot_diff_reporter import diff_snapshots, flatten

before = {"user": {"name": "Alice", "age": 30}, "role": "admin"}
after  = {"user": {"name": "Alice", "age": 31}, "email": "a@x.io"}

added, removed, changed = diff_snapshots(before, after)
# added   == {"email": "a@x.io"}
# removed == {"role": "admin"}
# changed == {"user.age": (30, 31)}

flatten({"a": {"b": 1}})  # {"a.b": 1}
```

## Why

Snapshot tests tend to print huge blobs and leave the reader to spot the difference. This library gives you three small dicts you can render directly: things that appeared, things that vanished, and the exact before/after pair for every leaf that moved. The whole thing is standard-library-only so it drops into a containerised test runner with no install step.

The one trade-off worth stating: `added` and `removed` keep whole subtree values (a new `{"email": ...}` key shows up once, not flattened), while `changed` flattens to dot-notation leaves (`user.age`). The reasoning is that a wholly-new subtree is usually rendered as one block, but a changed leaf is easiest to read as a single dotted path next to its old and new values.

## Edge you will hit

When a key's value changes *type* — a dict turning into a string, or vice versa — the whole key is reported as one `changed` entry with `(before, after)` as the two raw values, rather than recursing into a dict that no longer exists. Lists are also treated as opaque leaves: `[1, 2, 3]` vs `[1, 2, 4]` is a single change, not an element-wise diff.

Run the tests with `PYTHONPATH=src python -m unittest discover -s tests`.
