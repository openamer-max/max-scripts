"""Contract tests for the GitHub tap listing path.

Two properties matter here:

1. ``GitHubSource.search()`` with a non-positive limit must not truncate the
   result set. The offline index builder calls ``search("", limit=0)`` to pull
   the whole tap catalog; slicing with ``[:0]`` returned an empty list *after*
   every tap had already been walked, so the build burned 201s of GitHub
   traffic and still contributed zero skills.

2. The tap listing fetches its per-skill SKILL.md metadata concurrently. The
   result must be identical to the sequential walk -- same skills, same
   order, same category stamps -- because the index file is sorted by
   (source, name) downstream and a reordering would change the shipped
   artifact.

These tests pin behaviour, not the current tap or skill count, so they stay
valid as the upstream catalogs change.
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


class TestTapListingContract:
    """The concurrent tap walk must produce exactly the sequential result."""

    def _entries(self, names):
        return [{"type": "dir", "name": n} for n in names]

    @pytest.fixture
    def isolated_source(self):
        """A GitHubSource with the on-disk index cache neutralised.

        ``_list_skills_in_repo`` reads and writes a real cache file under
        OPENAMER_HOME, keyed by repo and path. Without this, a tap listing
        test inherits whatever a previous test wrote for the same key and
        asserts against foreign data.
        """
        src = GitHubSource(auth=MagicMock())
        with patch.object(src, "_read_cache", return_value=None), \
             patch.object(src, "_write_cache"):
            yield src

    def test_concurrent_listing_matches_sequential_order(self, isolated_source):
        src = isolated_source
        names = [f"skill-{i}" for i in range(12)]
        entries = self._entries(names)

        def fake_inspect(identifier):
            return SkillMeta(
                name=identifier.rsplit("/", 1)[-1],
                description="d",
                source="github",
                identifier=identifier,
                trust_level="community",
            )

        with patch.object(src, "_github_get") as gh:
            gh.return_value.status_code = 200
            gh.return_value.json.return_value = entries
            with patch.object(src, "_get_skillsh_groupings", return_value=None):
                with patch.object(src, "inspect", side_effect=fake_inspect):
                    results = src._list_skills_in_repo("acme/skills", "skills")

        assert [r.identifier for r in results] == [
            f"acme/skills/skills/{n}" for n in names
        ]

    def test_grouping_stamps_are_applied_in_the_concurrent_path(self, isolated_source):
        src = isolated_source
        entries = self._entries(["alpha", "beta"])

        def fake_inspect(identifier):
            return SkillMeta(
                name=identifier.rsplit("/", 1)[-1],
                description="d",
                source="github",
                identifier=identifier,
                trust_level="community",
            )

        with patch.object(src, "_github_get") as gh:
            gh.return_value.status_code = 200
            gh.return_value.json.return_value = entries
            with patch.object(
                src, "_get_skillsh_groupings", return_value={"alpha": "Category A"}
            ):
                with patch.object(src, "inspect", side_effect=fake_inspect):
                    results = src._list_skills_in_repo("acme/skills", "skills")

        by_name = {r.name: r for r in results}
        assert by_name["alpha"].extra.get("category") == "Category A"
        assert "category" not in by_name["beta"].extra

    def test_hidden_directories_are_skipped(self, isolated_source):
        src = isolated_source
        entries = self._entries(["visible", ".hidden", "_private"])

        with patch.object(src, "_github_get") as gh:
            gh.return_value.status_code = 200
            gh.return_value.json.return_value = entries
            with patch.object(src, "_get_skillsh_groupings", return_value=None):
                with patch.object(src, "inspect", return_value=None):
                    results = src._list_skills_in_repo("acme/skills", "skills")

        assert results == []
