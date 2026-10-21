"""Contract tests for GitHubSource.search() limit semantics.

``limit <= 0`` means "no cap". The offline index builder relies on this:
``scripts/build_skills_index.py`` calls ``search("", limit=0)`` to pull the
whole tap catalog. Slicing with ``[:0]`` returned an empty list *after* every
tap had already been walked, so the build burned 201s of GitHub traffic and
still contributed zero skills to the index.

These tests pin the contract (a non-positive limit must not truncate the
result), not the current tap count, so they stay valid as taps change.
"""

from unittest.mock import MagicMock, patch

import pytest

from tools.skills_hub import GitHubAuth, GitHubSource, SkillMeta


def _make_source(skills):
    """A GitHubSource whose taps all yield the same skill list."""
    src = GitHubSource(auth=MagicMock())
    src.taps = [{"repo": "acme/skills", "path": "skills"}]
    metas = [
        SkillMeta(
            name=f"skill-{i}",
            description="d",
            source="github",
            identifier=f"acme/skills/skills/skill-{i}",
            trust_level="community",
        )
        for i in range(skills)
    ]
    return src, metas


class TestSearchLimitContract:
    """limit <= 0 must mean 'return everything', not 'return nothing'."""

    @pytest.mark.parametrize("limit", [0, -1, -100])
    def test_non_positive_limit_returns_full_result_set(self, limit):
        src, metas = _make_source(5)
        with patch.object(src, "_list_skills_in_repo", return_value=metas):
            results = src.search("", limit=limit)
        assert len(results) == 5, (
            f"limit={limit} must not truncate the result set; "
            f"got {len(results)} of {len(metas)}"
        )

    def test_positive_limit_still_truncates(self):
        src, metas = _make_source(10)
        with patch.object(src, "_list_skills_in_repo", return_value=metas):
            results = src.search("", limit=3)
        assert len(results) == 3

    def test_non_positive_limit_keeps_every_tap_contribution(self):
        """All taps must be walked and their skills merged, not just the first."""
        src, metas = _make_source(4)
        src.taps = [
            {"repo": "acme/one", "path": "skills"},
            {"repo": "acme/two", "path": "skills"},
        ]
        with patch.object(src, "_list_skills_in_repo", return_value=metas):
            results = src.search("", limit=0)
        identifiers = {r.identifier for r in results}
        assert identifiers == {m.identifier for m in metas}

    def test_empty_catalog_with_non_positive_limit_is_empty(self):
        """The unlimited path must not fabricate rows when a tap is empty."""
        src, _ = _make_source(0)
        with patch.object(src, "_list_skills_in_repo", return_value=[]):
            assert src.search("", limit=0) == []
