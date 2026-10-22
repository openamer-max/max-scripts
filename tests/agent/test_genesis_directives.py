"""The Genesis Directives must reach the system prompt -- and stay optional.

The directives live in the tracked tree so every installation gets them on
update. That only works if they are actually injected, so this module
pins the whole path:

  * the block renders with every directive id,
  * it lands in the system prompt's STABLE tier (a constitution that
    changed mid-conversation would invalidate the cached prefix),
  * the operator can switch it off via config.yaml
    (``agent.genesis_directives: false``) and then it is absent,
  * a broken renderer degrades to "no block" instead of breaking agent
    init.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent.genesis_directives import (  # noqa: E402
    GENESIS_DIRECTIVES,
    render_genesis_block,
)


def _make_agent(*, genesis: bool = True):
    """A MagicMock agent with just enough surface for the prompt builder.

    MagicMock invents an attribute for anything not set explicitly, and
    the prompt builder branches on several of them -- an invented
    MagicMock in the tool-guidance list breaks the join. So every
    attribute the builder reads is set explicitly here.
    """
    agent = MagicMock()
    agent.api_mode = "chat_completions"
    agent.platform = "linux"
    agent.model = "test-model"
    agent.provider = "test"
    agent.valid_tool_names = []
    agent.tools = []
    agent.session_id = "sess-genesis"
    agent.pass_session_id = False
    agent.load_soul_identity = False
    agent.skip_context_files = True
    agent.context_compressor = None
    agent._genesis_directives = genesis
    agent._task_completion_guidance = True
    agent._parallel_tool_call_guidance = True
    agent._tool_use_enforcement = False
    agent._memory_enabled = False
    agent._user_profile_enabled = False
    agent._memory_manager = None
    agent._memory_store = None
    agent._platform_hint_overrides = {}
    # MagicMock invents a truthy attribute here, which would append a
    # mock object to the tool-guidance list and break the string join.
    agent._kanban_worker_guidance = None
    agent.environment_probe = False
    agent.coding_context = ""
    agent.goal_engine = None
    agent.runtime_cwd = None
    agent.file_safety = None
    agent.get_toolset_for_tool = None
    agent._emit_status = lambda *a, **k: None
    agent._cached_system_prompt = None
    agent._cached_system_prompt_static = None
    return agent


def test_every_directive_has_an_id_title_rule_and_scope():
    """Every directive must be complete enough to render."""
    seen = set()
    for d in GENESIS_DIRECTIVES:
        assert d.id.startswith("DIR-"), f"bad id: {d.id!r}"
        assert d.id not in seen, f"duplicate id: {d.id}"
        seen.add(d.id)
        assert d.title.strip(), f"{d.id} has no title"
        assert d.rule.strip(), f"{d.id} has no rule"
        assert d.scope.strip(), f"{d.id} has no scope"


def test_ids_are_contiguous_from_dir_01():
    """The owner's numbering must stay stable across revisions."""
    ids = [d.id for d in GENESIS_DIRECTIVES]
    assert ids[0] == "DIR-01"
    numbers = [int(i.split("-")[1]) for i in ids]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"directive numbering has gaps: {numbers}"
    )


def test_there_are_exactly_twenty_four_directives():
    """The constitution has 24 directives.

    A count is a change-detector smell in general, but here the number IS
    the contract: the owner's numbering runs DIR-01..DIR-24 and a
    directive that silently disappears is a lost directive, not a
    refactor. Paired with the contiguity test above, this pins the set.
    """
    assert len(GENESIS_DIRECTIVES) == 24
    assert GENESIS_DIRECTIVES[-1].id == "DIR-24"


def test_the_load_bearing_numbers_survive():
    """The concrete figures of the constitution must not be lost.

    These are the numbers the owner pinned: the creator allocation, the
    emission schedule, the treasury share, the burn rate, the supply
    cap. A paraphrase that drops "exactly 9,000,000,000 OAC" or "32
    years" turns a precise directive into a vague one -- and no reviewer
    would notice, because the text still reads fine.
    """
    blob = " ".join(
        f"{d.id} {d.title} {d.rule}" for d in GENESIS_DIRECTIVES
    )
    required = [
        # DIR-03 -- creator allocation and its vesting schedule
        "10% of the maximum supply (900,000,000 OAC)",
        "12-month cliff",
        "linear monthly vesting over 36 months",
        "lifelong, final veto right",
        # DIR-20 -- emission
        "maximum supply of exactly 9,000,000,000 OAC",
        "spans 32 years",
        "eight degressive cycles of four years each",
        "Proof-of-Useful-Work, PoUW",
        "written in Rust",
        # DIR-22 -- treasury
        "exactly 15% of the maximum supply (1,350,000,000 OAC)",
        "OAC -> stablecoin swaps",
        "cryptographically excluded",
        # DIR-23 -- burn, verification, off-ramps
        "at least 30% of all OAC taken in for cloud use",
        "irreversibly destroyed",
        "crypto-to-fiat interfaces (off-ramps)",
        # DIR-24 -- client
        "OpenAmer-Node",
        "Rust/Tauri architecture",
        "CUDA/ROCm/Metal support",
        "9-billion OAC limit",
    ]
    missing = [r for r in required if r not in blob]
    assert not missing, f"lost from the constitution: {missing}"


def test_everything_is_english():
    """The constitution is written in English.

    A German word in the rendered prompt is a bug, not a style choice:
    the block is a standing document that every installation reads, and
    the project's own code and docs are English.
    """
    german_chars = set("äöüßÄÖÜ")
    german_words = (
        " und ", " der ", " die ", " das ", " für ", " nicht ", " eine ",
        " wird ", " durch ", " sich ", " mit ", " über ", " müssen ",
        " können ", " diese ", " seine ",
    )
    for d in GENESIS_DIRECTIVES:
        blob = f"{d.id} {d.title} {d.rule}"
        bad_chars = sorted(german_chars & set(blob))
        assert not bad_chars, f"{d.id} contains German characters: {bad_chars}"
        padded = f" {blob.lower()} "
        bad_words = [w for w in german_words if w in padded]
        assert not bad_words, f"{d.id} contains German words: {bad_words}"


def test_block_contains_every_directive():
    """All directives must be visible in the rendered block."""
    block = render_genesis_block()
    assert block, "the genesis block must not be empty"
    for d in GENESIS_DIRECTIVES:
        assert d.id in block, f"{d.id} missing from the rendered block"
        assert d.title in block, f"title of {d.id} missing"


def test_block_can_be_switched_off():
    """The operator can decline the constitution.

    A constitution the user cannot refuse is a takeover, so the off switch
    has to work -- and it has to be a plain config flag, not a code edit.
    """
    assert render_genesis_block(enabled=False) == ""


def test_block_is_bounded():
    """The block must not be able to blow up the prompt."""
    block = render_genesis_block(max_chars=500)
    assert len(block) <= 500 + 10, "the block ignored its character budget"
    assert block.startswith("## Genesis Directives")


def test_system_prompt_injects_the_block():
    """End-to-end: the block reaches the built system prompt."""
    from agent.system_prompt import build_system_prompt

    on = build_system_prompt(_make_agent(genesis=True))
    assert "Genesis Directives" in on, (
        "the genesis block did not reach the system prompt"
    )
    for d in GENESIS_DIRECTIVES:
        assert d.id in on, f"{d.id} missing from the system prompt"


def test_system_prompt_omits_the_block_when_disabled():
    """With the flag off, nothing about the constitution reaches the prompt."""
    from agent.system_prompt import build_system_prompt

    off = build_system_prompt(_make_agent(genesis=False))
    assert "Genesis Directives" not in off, (
        "the genesis block was injected even though the operator disabled it"
    )


def test_injection_site_survives_a_broken_renderer(monkeypatch):
    """The real call site must not propagate a renderer failure.

    A renderer that explodes means "no constitution injected", not "the
    agent cannot start".
    """
    import agent.genesis_directives as mod

    def _boom(*args, **kwargs):
        raise RuntimeError("renderer exploded")

    monkeypatch.setattr(mod, "render_genesis_block", _boom)

    from agent.system_prompt import build_system_prompt

    prompt = build_system_prompt(_make_agent(genesis=True))
    assert prompt, "the prompt build failed instead of degrading"
    assert "Genesis Directives" not in prompt


def test_block_is_stable_across_calls():
    """The block must not change between two builds.

    The stable prompt tier is cache-critical: a block that varies between
    turns would invalidate the cached prefix on every single request.
    """
    first = render_genesis_block()
    second = render_genesis_block()
    assert first == second
