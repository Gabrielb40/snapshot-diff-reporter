import unittest

from snapshot_diff_reporter import diff_snapshots, flatten
from snapshot_diff_reporter.core import _is_mapping


class TestFlatten(unittest.TestCase):
    def test_flat(self):
        self.assertEqual(flatten({"a": 1, "b": 2}), {"a": 1, "b": 2})

    def test_nested(self):
        self.assertEqual(
            flatten({"a": {"b": {"c": 1}}}),
            {"a.b.c": 1},
        )

    def test_mixed(self):
        self.assertEqual(
            flatten({"a": 1, "b": {"c": 2}, "d": {"e": {"f": 3}}}),
            {"a": 1, "b.c": 2, "d.e.f": 3},
        )

    def test_empty(self):
        self.assertEqual(flatten({}), {})

    def test_list_is_leaf(self):
        self.assertEqual(flatten({"a": [1, 2, 3]}), {"a": [1, 2, 3]})


class TestIsMapping(unittest.TestCase):
    def test_str_is_not_mapping(self):
        self.assertFalse(_is_mapping("hello"))

    def test_dict_is_mapping(self):
        self.assertTrue(_is_mapping({}))


class TestDiffSnapshots(unittest.TestCase):
    def test_identical(self):
        a = {"x": 1, "y": "z"}
        added, removed, changed = diff_snapshots(a, a)
        self.assertEqual(added, {})
        self.assertEqual(removed, {})
        self.assertEqual(changed, {})

    def test_added_top_level(self):
        before = {"a": 1}
        after = {"a": 1, "b": 2}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {"b": 2})
        self.assertEqual(removed, {})
        self.assertEqual(changed, {})

    def test_removed_top_level(self):
        before = {"a": 1, "b": 2}
        after = {"a": 1}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {})
        self.assertEqual(removed, {"b": 2})
        self.assertEqual(changed, {})

    def test_changed_scalar(self):
        before = {"a": 1}
        after = {"a": 2}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {})
        self.assertEqual(removed, {})
        self.assertEqual(changed, {"a": (1, 2)})

    def test_changed_nested_becomes_dot_key(self):
        before = {"x": {"y": 1}}
        after = {"x": {"y": 2}}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(changed, {"x.y": (1, 2)})
        self.assertEqual(added, {})
        self.assertEqual(removed, {})

    def test_added_subtree_kept_whole(self):
        before = {"a": 1}
        after = {"a": 1, "b": {"c": 2, "d": 3}}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {"b": {"c": 2, "d": 3}})
        self.assertEqual(removed, {})
        self.assertEqual(changed, {})

    def test_removed_subtree_kept_whole(self):
        before = {"a": 1, "b": {"c": 2, "d": 3}}
        after = {"a": 1}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {})
        self.assertEqual(removed, {"b": {"c": 2, "d": 3}})
        self.assertEqual(changed, {})

    def test_dict_to_scalar_is_one_change(self):
        before = {"a": {"b": 1}}
        after = {"a": 5}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(changed, {"a": ({"b": 1}, 5)})
        self.assertEqual(added, {})
        self.assertEqual(removed, {})

    def test_scalar_to_dict_is_one_change(self):
        before = {"a": 5}
        after = {"a": {"b": 1}}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(changed, {"a": (5, {"b": 1})})
        self.assertEqual(added, {})
        self.assertEqual(removed, {})

    def test_list_change_is_single_change(self):
        before = {"a": [1, 2, 3]}
        after = {"a": [1, 2, 4]}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(changed, {"a": ([1, 2, 3], [1, 2, 4])})

    def test_mixed_changes(self):
        before = {"keep": 1, "gone": 2, "swap": {"x": 1}, "deep": {"k": {"v": 9}}}
        after = {"keep": 1, "new": 3, "swap": {"x": 2}, "deep": {"k": {"v": 10}}}
        added, removed, changed = diff_snapshots(before, after)
        self.assertEqual(added, {"new": 3})
        self.assertEqual(removed, {"gone": 2})
        self.assertEqual(changed, {"swap.x": (1, 2), "deep.k.v": (9, 10)})

    def test_empty_inputs(self):
        added, removed, changed = diff_snapshots({}, {})
        self.assertEqual(added, {})
        self.assertEqual(removed, {})
        self.assertEqual(changed, {})

    def test_returns_three_dicts_in_order(self):
        result = diff_snapshots({}, {})
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ({}, {}, {}))


if __name__ == "__main__":
    unittest.main()
