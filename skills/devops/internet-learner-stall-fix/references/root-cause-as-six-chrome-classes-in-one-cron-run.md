# internet-learner-stall-fix -- moved sections

Split out of `SKILL.md` because the file exceeded the 100,000-character
SKILL.md limit; content is unchanged.

## Root cause AS — SIX chrome classes in ONE cron run (58–63), and the "post-fix cycles create the next leak" loop (live 18.09.26)

Cron run began on the documented `cycle_a_technews: rejected` line. Per-day rate
**54.5 %** vs the documented 50–80 % band → **no gate change was warranted for
the rejection itself**; `buffer_junk` last 20 = `duplicate` at the 296–300 cap +
documented `junk` shapes = rotation noise. All six finds came from the prescribed
cheapest method: run `--once`, read the BUFFER TAIL `u`/`a`, repeat after each
fix. **Every single leak was created by a POST-FIX live cycle** — i.e. the buffer
was clean at entry every time and the next two-or-three cycles produced the next
class. Budget accordingly: six classes needed ~20 `--once` runs in one session.

| class | helper | measured |
|---|---|---|
| 58 | `_is_pagination_newsletter_widget` — `Previous Page N of M Next` within 200 chars of `New articles by email` | 1 hit, IS the leak / 0 FP / 0 le |
| 59 | `_is_fullscreen_toggle_chrome` — `Enter fullscreen mode` + `Exit fullscreen mode` space-glued | 1 hit, IS the leak / 0 FP / 0 le |
| 60 | `_is_hashtag_run_after_headline` — >=3 whitespace-adjacent hashtags AND a TitleCase headline (>=4 caps words) before them | 1 hit, IS the leak / 0 FP / 0 le |
| 61 | `_is_dated_tag_strip_chrome` — `\u00b7 #` AND a strip of >=5 tokens with >=3 mixed-case/digit tokens | 2 hits, BOTH the leak / 0 FP / 0 le |
| 62 | `_is_model_listing_run_chrome` — >=2 `Updated <Mon DD, YYYY>` AND a `size \u00b7 Updated` separator | 1 hit, IS the leak / 0 FP / 0 le |
| 63 | `_is_trending_repo_row_chrome` — star counter `\u2605 <N>k +<M>` AND owner/slug AND a language-% stat | 2 hits, BOTH the family / 0 FP / 0 le |

### The single most useful rule from this run: measure the CONJUNCTION, not the phrase
Every class above first failed as a single-literal or single-count candidate.
The repeated shape of the failure:

| class | single-part candidate | why REJECTED |
|---|---|---|
| 58 | `Previous Page N of M Next` OR `New articles by email` alone | bounded AND flagged my own control at whole-text scope; 200-char window fixed it |
| 59 | `Enter fullscreen mode` / `Enter…Exit…mode` generic | 1–3 control FPs |
| 60 | bare hashtag count >=3 / >=4 | **71 then 42 episodes**, 2 then 1 control FPs |
| 61 | `\u00b7 #` separator; then token-count 5/6/7 | 2–3 control FPs at EVERY threshold |
| 62 | repeated `Updated <date>` alone | 2 control FPs |
| 63 | `\u2605 <N>k +<M>` star counter alone | 2 control FPs; `>=2` occurrences still 1 FP |

**So: when a count threshold is 2-FP-clean but you cannot lower it without FPs,
the PATTERN is wrong, not the number.** Add a second structural co-occurrence
(window, adjacency, density, three-way pair) and re-measure. Classes 61 and 63
both went 0-FP only after the *density* / *three-way* form.

### Also — "the buffer is clean" does NOT survive the next cycle
The AP lesson repeats: after every cleanup the census read **0**, and the next
two cycles produced the next class. Re-census after every fix; never conclude the
run is done from an entry-time census.

### Cleanup guards — widen deliberately, and re-derive the drop set
`assert len(drop) == 4` fired correctly on the class-58 pass (1 leak + 2 stubs +
1 root-cause-AG off-topic row). Class 60 needed its own separate pass because I
had applied the gate but not yet deleted the row it caught — **after applying a
gate, immediately delete the matching rows in the same step**, or the next
census reads non-zero and looks like a regression. Class 58/59/60/61/62/63
censuses: 300→296, 298→297, 300→296, 300→296, 297→296, 298→295; every time
`0 unparsable`, lone LF 0, **55** structural-connection rows (the historical 53
has drifted to 55 — re-count, never quote the old number).

### Tests — the pure-byte append again, now the standing routine
Six appends, each `git diff --cached --numstat` showing **0 removed** and the
repo file's lone-LF census **58 → 58** (the laptop copy 0 → 0). Gate-file suite
**76 → 82 passed**; `tests/scripts` **233 → 238 passed**. The test file imports
`buffer_store` lazily inside each test — an appended test MUST `import
buffer_store` itself (root cause AN pitfall, recurred). One class (63) asserts a
list of TWO leaks in a loop plus 8 prose counter-cases, because the leak family
had two shapes.

### Push — six commits, all landed on the same foreign branch
Branch was `fix/28-respawn-test-psutil-hermetic` every time;
`merge-base --is-ancestor origin/main HEAD` → `NO_DIVERGED` each round, so
`git push origin HEAD:main` fast-forwarded cleanly six times
(`e5a6479a9..995fa727e`, `..1c3907827`, `..1f1466297`, `..36709d638`,
`..f44a1c568`). Verify with `git branch -r --contains <sha>` AND
`git cat-file blob origin/main:<file> | grep -c <marker>` — the push exit code
alone is not proof.

### One leak deliberately left un-gated — the model-hallucination repetition
Row 297 (`zero-copy, zero-copy-free, and zero-copy-free`) is a 2B-model
degradation artifact. A repetition detector was measured and **REJECTED**:
`immediate repetition of a long token` flagged 8 buffer rows and **1 real
episode**, and the matches included `announcement Announcement` and
`Communications , Communications` — ordinary editorial prose. **No clean
discriminator exists for "the model broke down mid-generation", so do not gate
it**: remove by signature only. Same call as root cause AG.

## Root cause AT — THREE chrome classes in ONE cron run (64–66), and "the rejection was NOT the regression" again (live 18.09.26)

Cron run began on the documented `cycle_b_papers: rejected` line. Per-day rate
**56.0 %** (28 ok / 22 rej) vs the documented 50–80 % band → **no gate change was
warranted for the rejection itself**; `buffer_junk` last 12 = `duplicate` at the
296–300 cap + documented `junk` shapes (`Self-critique:` echo, SERP `… — <date>`,
`Nuxt HN | News …`) = rotation noise. All three finds came from the prescribed
cheapest method: run `--once`, read the BUFFER TAIL `u`/`a` pairs, repeat after
each fix. All three rows passed BOTH gates and NONE was ever in
`buffer_junk.jsonl`. Buffer was clean at entry in the sense that only 4 stale
pre-gate SERP rows were flagged — re-census after every fix anyway (the AP/AS
lesson: "clean at entry" does not survive the next cycle).

| class | helper | measured |
|---|---|---|
| 64 | `_is_de_portal_fact_box_chrome` — a German portal's own byline label + summary label pair (`\bAutor(?:in)?\s*:\s*[A-Z][A-Za-z]+\b[\s\S]{0,140}?K[üu]rze\s*:`) | 1 hit, IS the leak / 0 FP / 0 le / 0 lit |
| 65 | `_is_prompt_echo_fragment` — the learner's own task template stored as the answer, whole-segment anchored | 1 hit, IS the leak / 0 FP / 0 le / 0 lit |
| 66 | `_is_generated_plan_echo_fragment` — own-artifact title + `+`-list + DANGLING list marker | 5 hits, ALL the leak family / 0 FP / 0 le / 0 lit |

**Class 64 — "check whether the existing helper covers the vocabulary but not the
LANGUAGE".** Three byline helpers already exist (29 `_strip_byline_prefix`, 40
`_is_byline_published_article_header`, 51 `_is_news_byline_share_header`) and all
three are English-keyed (`By <First> <Last>`, `Published`, `Share`). A German
portal's `Autor: <Name> … in Kürze:` pair matches none of them. The discriminator
is the welded PAIR of the portal's OWN two labels; `in Kürze:` alone AND
`Autor: <Name>` alone are both ordinary German prose. Sweep note: the
order-reversed form (`in Kürze: … Autor:`) measured **0 buffer hits** — keep the
orientation that the live page ships, and prefer the tighter variant
(`Autor` + name + `Kürze:` = 0/11 controls) over the looser one
(`in Kürze:` + any of `[Autor|Banff|Alberta]` = 1 control FP, because the control
`Banff Nationalpark in Kurze: ein Park in Alberta.` contains two of the three
alternatives).

**Class 65 — a 41-char fragment: the length trust is NOT the only way chrome gets
in (class-33 precedent, third occurrence).** `Shared underlying pattern one
sentence.` is the instruction the cycle was given, stored as its answer. Why every
existing marker missed it: `_INSTRUCTION_OPENER_RE` is **START-anchored on
imperative verbs** and this is a bare noun-phrase fragment;
`_is_prompt_echo_bullet_chain` (class 42) needs **>=2 bullets**. The surviving
form is the **whole-segment anchor** (`^…pattern…one sentence.?$` with `re.M`).
All non-anchored candidates were REJECTED after measuring: any-context
`shared underlying pattern` + `one sentence` → 1 control FP; bare
`shared underlying pattern one sentence` substring → 1 control FP; `Have you
ever …?` teaser → **2–3 control FPs** (`Have you ever wished you could predict
the future, especially when it comes to your investments?` IS the leak and IS the
shape, so no discriminator exists — removed by signature only, like root cause AG
and the model-hallucination row).

**Class 66 — the leak is the AGENT'S OWN prior output, and it had FIVE copies.**
The `Structural connection between energy efficiency and …` cycles stored their
own deliverable list `KI-Performance-Optimierung: Python-Skript für
RAM/Disk/Cron-Monitoring + Optimierungsvorschläge + Skill + Cron-Job alle 12h` +
newline + `2.` (four German variants, one English). Tell: title-with-colon +
`+`-joined feature list + a **DANGLING** list marker, ending abruptly — the model
enumerated a plan and the extractor kept item 1 plus the marker. **Always group
the flagged rows before designing the marker** (root-cause-AM class-38 rule):
here the group was 5 rows of 2 languages, so the title alternation had to include
both. Threshold/shape sweep that mattered: the bare title alone hit **1 real
`longterm_episodes` row**, the bare dangling marker alone flagged the control
`Our toolchain: script + docs + tests + CI.` + newline + `2.`, and a *generic*
`^<title>: … + …` + dangling-marker form also flagged that same control. Only
adding the own-artifact title **AND** the `+`-join kept it at 0. The leak being
the agent's own prior generation is what makes the site-identity anchor
legitimate here — unlike the "`about scribd` is itself prose" rejection from
class 50.

### Also — the class-66 family was NOT the rejection's cause, and one variant slipped the first cleanup
The German signature removed 4 of the 5 copies; the **English** variant
(`Python script for RAM/Disk/Cron-Monitoring + optimization suggestions …`) had
to be deleted in a second pass. A signature-based cleanup that only lists the
language you just looked at is incomplete — after any cleanup, re-run the writer
census AND look for the same family in the other language.

### Also — always sweep the buffer for stale PRE-GATE leftovers in the same pass
The entry census read 4 flagged rows (idx 4/6/10/19) that were
`GitHub - <owner>/<repo>: …` and `<Title> | <Site> — <desc>` SERP shapes. Those
are gated by `_is_serp_snippet` (class 15, landed **15.09.26**) — the rows
**predate the rule**, which is exactly the AS precedent ("a stale buffer row is
not a new class: grep for a rule added that day; if it exists, delete by
signature, no code change"). The same pass removed them.

Cleanup + verify (standard shape): 297 → 290 → 285 records, every step
`0 unparsable`, lone LF 0, **structural-connection rows 55 → 49** (the historical
count keeps drifting — re-count, never quote an old number), writer-gate census
**4 → 5 → 0** and learner-gate census **0**.
`pytest tests/scripts/test_internet_learner_gate.py -q` → **82 → 85 passed**
(3 new tests, each asserting the helper AND `_is_junk` AND `is_junk` on the leak
plus 5–7 prose counter-cases); `pytest tests/scripts -q` → **241 passed**.
Tests appended as **pure bytes** (75 added / **0 removed**, repo lone-LF census
58 → 58), and the repo test file mirrored to the laptop + openamer-agent test
copies.
Commit `dc18ae902` on the same foreign branch `fix/28-respawn-test-psutil-hermetic`
(`merge-base --is-ancestor origin/main HEAD` → FF_SAFE), pushed `HEAD:main`;
verified with `git branch -r --contains dc18ae902` → `origin/main` **and**
`git cat-file blob origin/main:<file> | grep -c <marker>` → 3/3/3 + 1 for the new
test (the push exit code alone is not proof).
Post-fix live: 3 × `--once` → **3 learned**, all new rows writer-gate clean,
census **0 of 288**.

### Pitfall — the `-c` options must precede the SUBCOMMAND
`git push -c credential.helper= -c credential.helper=store origin HEAD:main`
prints the push `--help` and pushes **nothing** (the `-c` after the subcommand is
parsed as a push option). Correct: `git -c credential.helper= -c
credential.helper=store push origin HEAD:main`. Same reason `git commit -F`
needs the **Windows** path (`C:/Users/.../msg.txt`) while `/c/Users/...` gives
`fatal: could not read log file`.

## Root cause AT — moved to references/
AT (three chrome classes 64-66 in ONE cron run, and "the rejection was NOT
the regression" again) plus the `-c` options-before-subcommand pitfall and
the always-sweep-for-stale-PRE-GATE-leftovers rule are in
`references/root-causes-archive.md`.

## Root cause AV — TWO classes (75, 76) + the "a previous cron left gate work UNCOMMITTED" trap (live 19.09.26)

Cron run began with the documented `cycle_c_github: rejected` line. Per-day rate
**50 % (12 ok / 12 rej)** vs the documented 50–80 % band → **no gate change was
warranted for the rejection itself**; `buffer_junk` last 12 = `duplicate` at the
288/300 cap + documented `junk` shapes = rotation noise.

**THE NEW TRAP — check the repo working tree FIRST.** `git status` showed
`M scripts/training/internet_learner.py`, `M buffer_store.py`,
`M tests/scripts/test_internet_learner_gate.py`, and `git diff` revealed a
**finished class-74 + class-75 fix** (`_is_decorative_alt_text_chrome`,
`_is_bio_page_furniture_pair`) that the PREVIOUS cron run had applied to all
three copies and tested, but **never committed** — the session died after
cleanup. Head said `1508f630b fix(training): gate welded decorative alt-text
chrome (class 74)` while the working tree already carried 75. Consequences:
- The 75 leak row (`Read Full Bio Mary Cunningham …`) was **already deleted from
  the buffer** by that run (it survives only in `online_buffer.jsonl.bak75b`,
  which is how it was recovered for the commit message).
- Only the **laptop** test copy had been synced; the `openamer-agent` test copy
  still carried the old md5 → sync it before pytest.
**So the first step of every run is now `git -C <repo> status --porcelain
scripts/training tests/scripts` + `git diff --stat`** — an unfinished previous
run looks exactly like "nothing to do" from the log, and re-designing a class
that is already in the tree wastes the whole session.

| class | helper | measured |
|---|---|---|
| 75 | `_is_bio_page_furniture_pair` — publisher byline card welded to the lede (`Read Full Bio <Name>` + `Updated on: <date> / <time>` dateline) | 1 hit, IS the leak / 0 FP / 0 le / 0 lit |
| 76 | `_is_tag_counter_run_chrome` — a tag-cloud counter strip, `>=8` `word (n)` pairs with **single-digit** counts, `len <= 400` | 1 hit, IS the leak / 0 FP / 0 le / 0 lit |

**Class 75 — the PAIR is the marker.** `Read Full Bio` alone flagged 2 hostile
controls, a bare `Mon DD, YYYY / H:MM AM` dateline 3. Only the welded pair of the
page's OWN furniture reached 0.

**Class 76 — single-digit counts are the discriminator against real prose.**
Real prose carries 4-digit counts (dates, scores) or `(12)/(8)`-style counts for
list items; the widget prints `tag (2)`, `tag (1)`. Sweep that mattered:
`>=6` pairs → **3 control FPs** (an ablation sentence naming 6 methods with
counts, a score series, a sidebar sentence), `>=8` → 0 of 7 hostile controls,
`>=10` → 0 too but the leak holds **15** so 8 keeps headroom. `len <= 400` and
`len <= 260` were equivalent here; keep the 400 cap.
Note a deliberate harness distinction: a control sentence that **is** the widget
shape (`Tag counts were AI (2), mcp (2), … across the sidebar.`) is asserted as a
**leak** (its own `assert IL._is_tag_counter_run_chrome(...) is True`), never
listed in the false-positive set — the AJ/AN/AQ/AU control-corpus rule again.

**Verify (standard shape, all met):** 3-copy `md5sum` identical for both modules
after the apply (`35c5ba0f…` learner, `a711e236…` store) and after the class-75
commit; every module `exec_module`-verified (the `re` vs `_re` alias trap —
`ast.parse` was already green); `pytest tests/scripts/test_internet_learner_gate.py
-q` → **94 → 95 passed**; `pytest tests/scripts -q` → **251 passed**; test file
appended as **pure bytes** (41 added / **0 removed**, lone-LF census 58 → 58);
buffer census **0 / 0** (learner / writer) at 290 records, **49** structural rows
preserved. Commits `929b4f919` (75) and `d50ec4231` (76) on the foreign branch
`fix/28-respawn-test-psutil-hermetic` (`merge-base --is-ancestor origin/main
HEAD` → FF_SAFE), pushed `HEAD:main`; verified with `git branch -r --contains`
→ `origin/main`, `git cat-file blob origin/main:<file> | grep -c <marker>` →
3/3/1, and the LF-normalized md5 (remote blob == local after `tr -d '\r'`).
Post-fix live: 3 × `--once` → 1 learned (real paper prose) / 2 rejected, both
rejections honest (`duplicate` at the cap + a documented SERP shape), new row
`writer=False extract=False`.

137 (22.09.26): a docs-site breadcrumb welded to a REPEATED title prefix, AND
`_FULL_DATE_RE` (class 35) accepting ABBREVIATED months -- it was wired but had
a blind spot for `Sep 24, 2025`. Also: the per-FILE merge resolution (HEAD vs
origin/main measured, not assumed), and `clean_buffer.py` has NO `--help`
(it just runs). refs/.
**140** (a paper/arXiv AUTHOR LIST with affiliation superscripts -- `cycle_g_security` stored an author block twice; discriminator is the affiliation segment repeated, with a STRUCT-word guard so "Section 3, Figure 2, Table 1, ..." stays learnable; the `_re`/`re` alias fired via `_recompile`, and the guard was red from pre-existing scratch litter) is archived there too.
**141** (a year-welded SERP TITLE restated by its own SNIPPET -- 4 rows of one family in the buffer tail, incl. `Grok Pricing 2026:` and `Claude Opus 5 Review 2026:`. Neither conjunct separates: the year-colon weld alone hits 6 prose controls, a bare repeat hits 201 real episodes + 35 asserted gate literals; the PAIR is 0 FP everywhere. The restatement is an identical price token, an identical `<verb> <n> %` pair, or an identical 4-token run of PLURAL-STEMMED tokens -- a backreference cannot see the NER row's `LLMs`->`LLM` drift. The China-chip row (real article, bare `417%` across different verbs) survives by construction and is the control that decides the rule. The `_re`/`re` alias returned a THIRD time on a new face: alias `re.IGNORECASE` too, not just `re.compile`; and `open(p,'wb',newline='')` is a TypeError that half-applies a patch BEFORE the census assert) is archived there too.
**142** (the SILENT-DROP family: `internet_learner._is_junk()` accepted what `buffer_store.is_junk()` refused -- 368 of 600 audited junk rows; missing detectors `_is_serp_snippet` 222 / `self-critique` marker 109 / `_is_nav_chrome` 88. Fix = `_writer_gate_refuses()` consulted at the write decision in `store()`, audited under the new reason `writer-gate`; plus `active_learn.store_if_trainable()` + `_strip_reasoning_trace()`. PITFALL: never fold the writer into `_is_junk` -- `_clean_insight` depends on the extractor's looser rule, 4 tests regress) is in refs/.
**143/144** (22.09.26: 143 = the silent drops were NOT the rejection rate -- fixing 142 moved the loss from invisible to visible without raising yield; 144 = class 142 shipped as a pure REJECT predicate and over-rejected, 24 of 60 refused rows carry real prose behind the header stack. Fix = `_strip_article_byline_header(region=100)`, applied where `store()` judges the RAW text -- a strip inside `_clean_insight` is UNREACHABLE because `_is_junk(raw)` fires first. `region=200` broke 36/6,128 episodes, `region=100` breaks 0. PITFALL: `write_file` TRUNCATES -- append to this archive with a BINARY `'ab'` write only) is in refs/.
**145** (22.09.26: the spelled-out read-time WELD (`Reading time 5 min`) and the
ORDINAL dateline (`March 6th, 2025`) -- the class-142 vocabulary had neither, so two
rows were STORED; the bare weld is a topic-word trap and was MEASURED-AND-REJECTED,
the ANCHORED form is +2 leaks / 0 FP) is in refs/.

**146** (22.09.26: a SINGLE aggregator feed row -- handle + relative time +
`| N comments` + points + a capitalized second handle + headline. class 37
wants the unit REPEATED, 49 the aggregator's name, 83 an arXiv year tail, so a
one-item row passed both gates; fix = the trailing points/handle pair. Also:
`(?-i:[A-Z])` scoped case-sensitivity -- under IGNORECASE a bare `[A-Z]` token
re-admits lowercase prose. Also: regex NEVER via shell heredoc, and a whole-file
`cp` across diverged trees pulls unrelated work in) is in refs/.
**147** (22.09.26: German consultation/contact chrome -- `Wir beraten Sie
persönlich unter 0681 5866-4466 (Mo-Do 9-18 Uhr)` welded to a nav lockup. The
conjunction of a consultation term and a contact marker within 90 chars on ONE
line; scan forward from EACH match and cut at the newline) is in refs/.
**148** = the learner's OWN bare `Need ...` generation PLAN, stored 12x -- class 142 MIRRORED (here the WRITER was looser than the learner). LESSON: a predicate on only ONE of the two gates is a hole, either direction. Archived in refs/.
**149/150/151** (23.09.26: 149 = the cycle was FINE -- the LIVE tree is a second stale copy, diff it against ~/openamer-repo before any gate fix; traces ONE rejection via a buffer_store._audit spy, 60/70 writer-gate hits are _is_serp_snippet, which the learner has no counterpart for. 150 = a 0-BYTE marker file proves an "install root" in 12 consumers -> _vaultfinal phantom swarm, 781 runs "ok" on 0 tasks; rule: file marker NON-EMPTY, dir marker >=1 NON-EMPTY file. 151 = git push HANGS while ls-remote is fast -> the GCM credential helper, NOT the network:  -> 124; fix , then ls-remote sha == HEAD) in refs/.
**152** (23.09.26: "the live tree is AHEAD of the repo" is NOT "work is unlanded" -- a pairwise diff against ONE checkout is BRANCH NOISE; measure the content UNION over ALL refs: 0 live-only lines, the 143/144 gaps already published on open PR #47, 0 refs shipping the class-143 gate without the `(?-i:)` scope, and the unscoped `[A-Z]` hazard measured at 0 corpus cost) in refs/.
**157** (23.09.26: a docs/SECTION-HEADING STACK welded to an interrogative heading -- TWO rows passed BOTH gates; fix = `is_docs_heading_qweld` (question-weld + len>=80 + cap-ratio>=0.50 + <=1 terminator) in both gates; REJECTED: bare question-weld (2 real episode hits), TitleCase-run rule (215 episodes), cap>=0.55; PLUS two live git traps -- a non-FF push on a strict-superset file content needs a fresh worktree off origin/main, never a rebase of the shared live tree, and `git worktree add` under MSYS mangles `/c/...` to `C:/c/...`, so pass the NATIVE path) in refs/.
**158** (23.09.26: a BibTeX CITATION RECORD welded to a license footer -- fix = the CONJUNCTION of a prose-valued `field = {value}` pair AND a license footer, in both gates; every part ALONE was measured-and-rejected, as was the BibTeX field VOCABULARY (5 hostile FPs); the `re` vs `_re` alias trap fired a THIRD time -- `ast.parse` stays green, only `exec_module` catches it) in refs/.
**159** (23.09.26: a SECURITY-ADVISORY LISTING CARD -- GHSA-id + the list's own BARE numeric pager `Previous 1 2 3 Next`, in both gates; the near-miss matters MORE than the class: the date-free form PASSES `_is_nav_list` and the advisory date's ONE COMMA disarms it, so measure `_is_nav_list` on a nav-shaped leak BEFORE designing a rule; every part ALONE measured-and-rejected, incl. GHSA+severity (2/3 citing prose) and pager+date (3/4 both-part controls); also: a REGEX scan of test literals under-counts by splitting implicit concatenation -- use `ast.Constant`) in refs/.
**161** (23.09.26: the `writer-gate` census ATTRIBUTED for the first time -- on the last 300 writer-gate rows, `_is_serp_snippet` refuses 140/152 (92 %) while `internet_learner._is_junk()` returns False on 152/152, so the 142 disagreement is quantified AND singly-sourced; still NON-FIX, because the reject streak is 8 vs a whole-log max of 14 and the last 60 `duplicate` rows carry 36 distinct `u` (not the 121/128 saturation signature). Folding the writer into `_is_junk` is the 142 MEASURED-AND-REJECTED fix -- attribute first, re-open only if the streak exceeds 14) in refs/.
**166** (23.09.26: a GitHub-trending listing row with the relative-age badge WELDED to `release` (`2yrs agorelease`); the MISSING SPACE is the discriminator, the loose spaced form measured-and-rejected on 2 real-prose controls; gate the PAIR in BOTH gates. Same run: the entry buffer still carried a class-165 row whose gate already existed -- applying a gate is NOT a cleanup, delete the rows in the same step; and the whole 166 fix was left UNCOMMITTED by the previous cron (class-AV trap, 2nd time) -- `git status --porcelain scripts/training tests/scripts` FIRST. New pitfall: `io.open(p,'wb').write(expr)` TRUNCATES p BEFORE evaluating expr, so a NameError leaves a 0-byte module -- write `<p>.tmp` then `os.replace`) in refs/.
