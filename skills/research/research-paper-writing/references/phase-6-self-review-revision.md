# research-paper-writing -- moved sections

Split out of `SKILL.md` because the file exceeded the 100,000-character
SKILL.md limit; content is unchanged.

## Phase 6: Self-Review & Revision

**Goal**: Simulate the review process before submission. Catch weaknesses early.

### Step 6.1: Simulate Reviews (Ensemble Pattern)

Generate reviews from multiple perspectives. The key insight from automated research pipelines (notably SakanaAI's AI-Scientist): **ensemble reviewing with a meta-reviewer produces far more calibrated feedback than a single review pass.**

**Step 1: Generate N independent reviews** (N=3-5)

Use different models or temperature settings. Each reviewer sees only the paper, not other reviews. **Default to negative bias** — LLMs have well-documented positivity bias in evaluation.

```
You are an expert reviewer for [VENUE]. You are critical and thorough.
If a paper has weaknesses or you are unsure about a claim, flag it clearly
and reflect that in your scores. Do not give the benefit of the doubt.

Review this paper according to the official reviewer guidelines. Evaluate:

1. Soundness (are claims well-supported? are baselines fair and strong?)
2. Clarity (is the paper well-written? could an expert reproduce it?)
3. Significance (does this matter to the community?)
4. Originality (new insights, not just incremental combination?)

Provide your review as structured JSON:
{
  "summary": "2-3 sentence summary",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1 (most critical)", "weakness 2", ...],
  "questions": ["question for authors 1", ...],
  "missing_references": ["paper that should be cited", ...],
  "soundness": 1-4,
  "presentation": 1-4,
  "contribution": 1-4,
  "overall": 1-10,
  "confidence": 1-5
}
```

**Step 2: Meta-review (Area Chair aggregation)**

Feed all N reviews to a meta-reviewer:

```
You are an Area Chair at [VENUE]. You have received [N] independent reviews
of a paper. Your job is to:

1. Identify consensus strengths and weaknesses across reviewers
2. Resolve disagreements by examining the paper directly
3. Produce a meta-review that represents the aggregate judgment
4. Use AVERAGED numerical scores across all reviews

Be conservative: if reviewers disagree on whether a weakness is serious,
treat it as serious until the authors address it.

Reviews:
[review_1]
[review_2]
...
```

**Step 3: Reflection loop** (optional, 2-3 rounds)

Each reviewer can refine their review after seeing the meta-review. Use an early termination sentinel: if the reviewer responds "I am done" (no changes), stop iterating.

**Model selection for reviewing**: Reviewing is best done with the strongest available model, even if you wrote the paper with a cheaper one. The reviewer model should be chosen independently from the writing model.

**Few-shot calibration**: If available, include 1-2 real published reviews from the target venue as examples. This dramatically improves score calibration. See [references/reviewer-guidelines.md](references/reviewer-guidelines.md) for example reviews.

### Step 6.1b: Visual Review Pass (VLM)

Text-only review misses an entire class of problems: figure quality, layout issues, visual consistency. If you have access to a vision-capable model, run a separate **visual review** on the compiled PDF:

```
You are reviewing the visual presentation of this research paper PDF.
Check for:
1. Figure quality: Are plots readable? Labels legible? Colors distinguishable?
2. Figure-caption alignment: Does each caption accurately describe its figure?
3. Layout issues: Orphaned section headers, awkward page breaks, figures far from their references
4. Table formatting: Aligned columns, consistent decimal precision, bold for best results
5. Visual consistency: Same color scheme across all figures, consistent font sizes
6. Grayscale readability: Would the figures be understandable if printed in B&W?

For each issue, specify the page number and exact location.
```

This catches problems that text-based review cannot: a plot with illegible axis labels, a figure placed 3 pages from its first reference, inconsistent color palettes between Figure 2 and Figure 5, or a table that's clearly wider than the column width.

### Step 6.1c: Claim Verification Pass

After simulated reviews, run a separate verification pass. This catches factual errors that reviewers might miss:

```
Claim Verification Protocol:
1. Extract every factual claim from the paper (numbers, comparisons, trends)
2. For each claim, trace it to the specific experiment/result that supports it
3. Verify the number in the paper matches the actual result file
4. Flag any claim without a traceable source as [VERIFY]
```

For agent-based workflows: delegate verification to a **fresh sub-agent** that receives only the paper text and the raw result files. The fresh context prevents confirmation bias — the verifier doesn't "remember" what the results were supposed to be.

### Step 6.2: Prioritize Feedback

After collecting reviews, categorize:

| Priority | Action |
|----------|--------|
| **Critical** (technical flaw, missing baseline) | Must fix. May require new experiments → back to Phase 2 |
| **High** (clarity issue, missing ablation) | Should fix in this revision |
| **Medium** (minor writing issues, extra experiments) | Fix if time allows |
| **Low** (style preferences, tangential suggestions) | Note for future work |

### Step 6.3: Revision Cycle

For each critical/high issue:
1. Identify the specific section(s) affected
2. Draft the fix
3. Verify the fix doesn't break other claims
4. Update the paper
5. Re-check against the reviewer's concern

### Step 6.4: Rebuttal Writing

When responding to actual reviews (post-submission), rebuttals are a distinct skill from revision:

**Format**: Point-by-point. For each reviewer concern:
```
> R1-W1: "The paper lacks comparison with Method X."

We thank the reviewer for this suggestion. We have added a comparison with 
Method X in Table 3 (revised). Our method outperforms X by 3.2pp on [metric] 
(p<0.05). We note that X requires 2x our compute budget.
```

**Rules**:
- Address every concern — reviewers notice if you skip one
- Lead with the strongest responses
- Be concise and direct — reviewers read dozens of rebuttals
- Include new results if you ran experiments during the rebuttal period
- Never be defensive or dismissive, even of weak criticisms
- Use `latexdiff` to generate a marked-up PDF showing changes (see Professional LaTeX Tooling section)
- Thank reviewers for specific, actionable feedback (not generic praise)

**What NOT to do**: "We respectfully disagree" without evidence. "This is out of scope" without explanation. Ignoring a weakness by only responding to strengths.

### Step 6.5: Paper Evolution Tracking

Save snapshots at key milestones:
```
paper/
  paper.tex                    # Current working version
  paper_v1_first_draft.tex     # First complete draft
  paper_v2_post_review.tex     # After simulated review
  paper_v3_pre_submission.tex  # Final before submission
  paper_v4_camera_ready.tex    # Post-acceptance final
```

---

## Phase 7: Submission Preparation

**Goal**: Final checks, formatting, and submission.

### Step 7.1: Conference Checklist

Every venue has mandatory checklists. Complete them carefully — incomplete checklists can result in desk rejection.

See [references/checklists.md](references/checklists.md) for:
- NeurIPS 16-item paper checklist
- ICML broader impact + reproducibility
- ICLR LLM disclosure policy
- ACL mandatory limitations section
- Universal pre-submission checklist

### Step 7.2: Anonymization Checklist

Double-blind review means reviewers cannot know who wrote the paper. Check ALL of these:

```
Anonymization Checklist:
- [ ] No author names or affiliations anywhere in the PDF
- [ ] No acknowledgments section (add after acceptance)
- [ ] Self-citations written in third person: "Smith et al. [1] showed..." not "We previously showed [1]..."
- [ ] No GitHub/GitLab URLs pointing to your personal repos
- [ ] Use Anonymous GitHub (https://anonymous.4open.science/) for code links
- [ ] No institutional logos or identifiers in figures
- [ ] No file metadata containing author names (check PDF properties)
- [ ] No "our previous work" or "in our earlier paper" phrasing
- [ ] Dataset names don't reveal institution (rename if needed)
- [ ] Supplementary materials don't contain identifying information
```

**Common mistakes**: Git commit messages visible in supplementary code, watermarked figures from institutional tools, acknowledgments left in from a previous draft, arXiv preprint posted before anonymity period.

### Step 7.3: Formatting Verification

```
Pre-Submission Format Check:
- [ ] Page limit respected (excluding references and appendix)
- [ ] All figures are vector (PDF) or high-res raster (600 DPI PNG)
- [ ] All figures readable in grayscale
- [ ] All tables use booktabs
- [ ] References compile correctly (no "?" in citations)
- [ ] No overfull hboxes in critical areas
- [ ] Appendix clearly labeled and separated
- [ ] Required sections present (limitations, broader impact, etc.)
```

### Step 7.4: Pre-Compilation Validation

Run these automated checks **before** attempting `pdflatex`. Catching errors here is faster than debugging compiler output.

```bash
# 1. Lint with chktex (catches common LaTeX mistakes)
# Suppress noisy warnings: -n2 (sentence end), -n24 (parens), -n13 (intersentence), -n1 (command terminated)
chktex main.tex -q -n2 -n24 -n13 -n1

# 2. Verify all citations exist in .bib
# Extract \cite{...} from .tex, check each against .bib
python3 -c "
import re
tex = open('main.tex').read()
bib = open('references.bib').read()
cites = set(re.findall(r'\\\\cite[tp]?{([^}]+)}', tex))
for cite_group in cites:
    for cite in cite_group.split(','):
        cite = cite.strip()
        if cite and cite not in bib:
            print(f'WARNING: \\\\cite{{{cite}}} not found in references.bib')
"

# 3. Verify all referenced figures exist on disk
python3 -c "
import re, os
tex = open('main.tex').read()
figs = re.findall(r'\\\\includegraphics(?:\[.*?\])?{([^}]+)}', tex)
for fig in figs:
    if not os.path.exists(fig):
        print(f'WARNING: Figure file not found: {fig}')
"

# 4. Check for duplicate \label definitions
python3 -c "
import re
from collections import Counter
tex = open('main.tex').read()
labels = re.findall(r'\\\\label{([^}]+)}', tex)
dupes = {k: v for k, v in Counter(labels).items() if v > 1}
for label, count in dupes.items():
    print(f'WARNING: Duplicate label: {label} (appears {count} times)')
"
```

Fix any warnings before proceeding. For agent-based workflows: feed chktex output back to the agent with instructions to make minimal fixes.

### Step 7.5: Final Compilation

```bash
# Clean build
rm -f *.aux *.bbl *.blg *.log *.out *.pdf
latexmk -pdf main.tex

# Or manual (triple pdflatex + bibtex for cross-references)
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# Verify output exists and has content
ls -la main.pdf
```

**If compilation fails**: Parse the `.log` file for the first error. Common fixes:
- "Undefined control sequence" → missing package or typo in command name
- "Missing $ inserted" → math symbol outside math mode
- "File not found" → wrong figure path or missing .sty file
- "Citation undefined" → .bib entry missing or bibtex not run

### Step 7.6: Conference-Specific Requirements

| Venue | Special Requirements |
|-------|---------------------|
| **NeurIPS** | Paper checklist in appendix, lay summary if accepted |
| **ICML** | Broader Impact Statement (after conclusion, doesn't count toward limit) |
| **ICLR** | LLM disclosure required, reciprocal reviewing agreement |
| **ACL** | Mandatory Limitations section, Responsible NLP checklist |
| **AAAI** | Strict style file — no modifications whatsoever |
| **COLM** | Frame contribution for language model community |

### Step 7.7: Conference Resubmission & Format Conversion

When converting between venues, **never copy LaTeX preambles between templates**:

```bash
# 1. Start fresh with target template
cp -r templates/icml2026/ new_submission/

# 2. Copy ONLY content sections (not preamble)
#    - Abstract text, section content, figures, tables, bib entries

# 3. Adjust for page limits
# 4. Add venue-specific required sections
# 5. Update references
```

| From → To | Page Change | Key Adjustments |
|-----------|-------------|-----------------|
| NeurIPS → ICML | 9 → 8 | Cut 1 page, add Broader Impact |
| ICML → ICLR | 8 → 9 | Expand experiments, add LLM disclosure |
| NeurIPS → ACL | 9 → 8 | Restructure for NLP conventions, add Limitations |
| ICLR → AAAI | 9 → 7 | Significant cuts, strict style adherence |
| Any → COLM | varies → 9 | Reframe for language model focus |

When cutting pages: move proofs to appendix, condense related work, combine tables, use subfigures.
When expanding: add ablations, expand limitations, include additional baselines, add qualitative examples.

**After rejection**: Address reviewer concerns in the new version, but don't include a "changes" section or reference the previous submission (blind review).

### Step 7.8: Camera-Ready Preparation (Post-Acceptance)

After acceptance, prepare the camera-ready version:

```
Camera-Ready Checklist:
- [ ] De-anonymize: add author names, affiliations, email addresses
- [ ] Add Acknowledgments section (funding, compute grants, helpful reviewers)
- [ ] Add public code/data URL (real GitHub, not anonymous)
- [ ] Address any mandatory revisions from meta-reviewer
- [ ] Switch template to camera-ready mode (if applicable — e.g., AAAI \anon → \camera)
- [ ] Add copyright notice if required by venue
- [ ] Update any "anonymous" placeholders in text
- [ ] Verify final PDF compiles cleanly
- [ ] Check page limit for camera-ready (sometimes differs from submission)
- [ ] Upload supplementary materials (code, data, appendix) to venue portal
```

### Step 7.9: arXiv & Preprint Strategy

Posting to arXiv is standard practice in ML but has important timing and anonymity considerations.

**Timing decision tree:**

| Situation | Recommendation |
|-----------|---------------|
| Submitting to double-blind venue (NeurIPS, ICML, ACL) | Post to arXiv **after** submission deadline, not before. Posting before can technically violate anonymity policies, though enforcement varies. |
| Submitting to ICLR | ICLR explicitly allows arXiv posting before submission. But don't put author names in the submission itself. |
| Paper already on arXiv, submitting to new venue | Acceptable at most venues. Do NOT update arXiv version during review with changes that reference reviews. |
| Workshop paper | arXiv is fine at any time — workshops are typically not double-blind. |
| Want to establish priority | Post immediately if scooping is a concern — but accept the anonymity tradeoff. |

**arXiv category selection** (ML/AI papers):

| Category | Code | Best For |
|----------|------|----------|
| Machine Learning | `cs.LG` | General ML methods |
| Computation and Language | `cs.CL` | NLP, language models |
| Artificial Intelligence | `cs.AI` | Reasoning, planning, agents |
| Computer Vision | `cs.CV` | Vision models |
| Information Retrieval | `cs.IR` | Search, recommendation |

**List primary + 1-2 cross-listed categories.** More categories = more visibility, but only cross-list where genuinely relevant.

**Versioning strategy:**
- **v1**: Initial submission (matches conference submission)
- **v2**: Post-acceptance with camera-ready corrections (add "accepted at [Venue]" to abstract)
- Don't post v2 during the review period with changes that clearly respond to reviewer feedback

```bash
# Check if your paper's title is already taken on arXiv
# (before choosing a title)
pip install arxiv
python -c "
import arxiv
results = list(arxiv.Search(query='ti:\"Your Exact Title\"', max_results=5).results())
print(f'Found {len(results)} matches')
for r in results: print(f'  {r.title} ({r.published.year})')
"
```

### Step 7.10: Research Code Packaging

Releasing clean, runnable code significantly increases citations and reviewer trust. Package code alongside the camera-ready submission.

**Repository structure:**

```
your-method/
  README.md              # Setup, usage, reproduction instructions
  requirements.txt       # Or environment.yml for conda
  setup.py               # For pip-installable packages
  LICENSE                # MIT or Apache 2.0 recommended for research
  configs/               # Experiment configurations
  src/                   # Core method implementation
  scripts/               # Training, evaluation, analysis scripts
    train.py
    evaluate.py
    reproduce_table1.sh  # One script per main result
  data/                  # Small data or download scripts
    download_data.sh
  results/               # Expected outputs for verification
```

**README template for research code:**

```markdown
# [Paper Title]

Official implementation of "[Paper Title]" (Venue Year).

## Setup
[Exact commands to set up environment]

## Reproduction
To reproduce Table 1: `bash scripts/reproduce_table1.sh`
To reproduce Figure 2: `python scripts/make_figure2.py`

## Citation
[BibTeX entry]
```

**Pre-release checklist:**
```
- [ ] Code runs from a clean clone (test on fresh machine or Docker)
- [ ] All dependencies pinned to specific versions
- [ ] No hardcoded absolute paths
- [ ] No API keys, credentials, or personal data in repo
- [ ] README covers setup, reproduction, and citation
- [ ] LICENSE file present (MIT or Apache 2.0 for max reuse)
- [ ] Results are reproducible within expected variance
- [ ] .gitignore excludes data files, checkpoints, logs
```

**Anonymous code for submission** (before acceptance):
```bash
# Use Anonymous GitHub for double-blind review
# https://anonymous.4open.science/
# Upload your repo → get an anonymous URL → put in paper
```

---

## Phase 8: Post-Acceptance Deliverables

**Goal**: Maximize the impact of your accepted paper through presentation materials and community engagement.

### Step 8.1: Conference Poster

Most conferences require a poster session. Poster design principles:

| Element | Guideline |
|---------|-----------|
| **Size** | Check venue requirements (typically 24"x36" or A0 portrait/landscape) |
| **Content** | Title, authors, 1-sentence contribution, method figure, 2-3 key results, conclusion |
| **Flow** | Top-left to bottom-right (Z-pattern) or columnar |
| **Text** | Title readable at 3m, body at 1m. No full paragraphs — bullet points only. |
| **Figures** | Reuse paper figures at higher resolution. Enlarge key result. |

**Tools**: LaTeX (`beamerposter` package), PowerPoint/Keynote, Figma, Canva.

**Production**: Order 2+ weeks before the conference. Fabric posters are lighter for travel. Many conferences now support virtual/digital posters too.

### Step 8.2: Conference Talk / Spotlight

If awarded an oral or spotlight presentation:

| Talk Type | Duration | Content |
|-----------|----------|---------|
| **Spotlight** | 5 min | Problem, approach, one key result. Rehearse to exactly 5 minutes. |
| **Oral** | 15-20 min | Full story: problem, approach, key results, ablations, limitations. |
| **Workshop talk** | 10-15 min | Adapt based on workshop audience — may need more background. |

**Slide design rules:**
- One idea per slide
- Minimize text — speak the details, don't project them
- Animate key figures to build understanding step-by-step
- Include a "takeaway" slide at the end (single sentence contribution)
- Prepare backup slides for anticipated questions

### Step 8.3: Blog Post / Social Media

An accessible summary significantly increases impact:

- **Twitter/X thread**: 5-8 tweets. Lead with the result, not the method. Include Figure 1 and key result figure.
- **Blog post**: 800-1500 words. Written for ML practitioners, not reviewers. Skip formalism, emphasize intuition and practical implications.
- **Project page**: HTML page with abstract, figures, demo, code link, BibTeX. Use GitHub Pages.

**Timing**: Post within 1-2 days of paper appearing on proceedings or arXiv camera-ready.

---

## Workshop & Short Papers

Workshop papers and short papers (e.g., ACL short papers, Findings papers) follow the same pipeline but with different constraints and expectations.

### Workshop Papers

| Property | Workshop | Main Conference |
|----------|----------|-----------------|
| **Page limit** | 4-6 pages (typically) | 7-9 pages |
| **Review standard** | Lower bar for completeness | Must be complete, thorough |
| **Review process** | Usually single-blind or light review | Double-blind, rigorous |
| **What's valued** | Interesting ideas, preliminary results, position pieces | Complete empirical story with strong baselines |
| **arXiv** | Post anytime | Timing matters (see arXiv strategy) |
| **Contribution bar** | Novel direction, interesting negative result, work-in-progress | Significant advance with strong evidence |

**When to target a workshop:**
- Early-stage idea you want feedback on before a full paper
- Negative result that doesn't justify 8+ pages
- Position piece or opinion on a timely topic
- Replication study or reproducibility report

### ACL Short Papers & Findings

ACL venues have distinct submission types:

| Type | Pages | What's Expected |
|------|-------|-----------------|
| **Long paper** | 8 | Complete study, strong baselines, ablations |
| **Short paper** | 4 | Focused contribution: one clear point with evidence |
| **Findings** | 8 | Solid work that narrowly missed main conference |

**Short paper strategy**: Pick ONE claim and support it thoroughly. Don't try to compress a long paper into 4 pages — write a different, more focused paper.

---

## Paper Types Beyond Empirical ML

The main pipeline above targets empirical ML papers. Other paper types require different structures and evidence standards. See [references/paper-types.md](references/paper-types.md) for detailed guidance on each type.

### Theory Papers

**Structure**: Introduction → Preliminaries (definitions, notation) → Main Results (theorems) → Proof Sketches → Discussion → Full Proofs (appendix)

**Key differences from empirical papers:**
- Contribution is a theorem, bound, or impossibility result — not experimental numbers
- Methods section replaced by "Preliminaries" and "Main Results"
- Proofs are the evidence, not experiments (though empirical validation of theory is welcome)
- Proof sketches in main text, full proofs in appendix is standard practice
- Experimental section is optional but strengthens the paper if it validates theoretical predictions

**Proof writing principles:**
- State theorems formally with all assumptions explicit
- Provide intuition before formal proof ("The key insight is...")
- Proof sketches should convey the main idea in 0.5-1 page
- Use `\begin{proof}...\end{proof}` environments
- Number assumptions and reference them in theorems: "Under Assumptions 1-3, ..."

### Survey / Tutorial Papers

**Structure**: Introduction → Taxonomy / Organization → Detailed Coverage → Open Problems → Conclusion

**Key differences:**
- Contribution is the organization, synthesis, and identification of open problems — not new methods
- Must be comprehensive within scope (reviewers will check for missing references)
- Requires a clear taxonomy or organizational framework
- Value comes from connections between works that individual papers don't make
- Best venues: TMLR (survey track), JMLR, Foundations and Trends in ML, ACM Computing Surveys

### Benchmark Papers

**Structure**: Introduction → Task Definition → Dataset Construction → Baseline Evaluation → Analysis → Intended Use & Limitations

**Key differences:**
- Contribution is the benchmark itself — it must fill a genuine evaluation gap
- Dataset documentation is mandatory, not optional (see Datasheets, Step 5.11)
- Must demonstrate the benchmark is challenging (baselines don't saturate it)
- Must demonstrate the benchmark measures what you claim it measures (construct validity)
- Best venues: NeurIPS Datasets & Benchmarks track, ACL (resource papers), LREC-COLING

### Position Papers

**Structure**: Introduction → Background → Thesis / Argument → Supporting Evidence → Counterarguments → Implications

**Key differences:**
- Contribution is an argument, not a result
- Must engage seriously with counterarguments
- Evidence can be empirical, theoretical, or logical analysis
- Best venues: ICML (position track), workshops, TMLR

---

## OpenAmer Agent Integration

This skill is designed for the OpenAmer agent. It uses OpenAmer tools, delegation, scheduling, and memory for the full research lifecycle.

### Related Skills

Compose this skill with other OpenAmer skills for specific phases:

| Skill | When to Use | How to Load |
|-------|-------------|-------------|
| **arxiv** | Phase 1 (Literature Review): searching arXiv, generating BibTeX, finding related papers via Semantic Scholar | `skill_view("arxiv")` |
| **subagent-driven-development** | Phase 5 (Drafting): parallel section writing with 2-stage review (spec compliance then quality) | `skill_view("subagent-driven-development")` |
| **plan** | Phase 0 (Setup): creating structured plans before execution. Writes to `.openamer/plans/` | `skill_view("plan")` |
| **qmd** | Phase 1 (Literature): searching local knowledge bases (notes, transcripts, docs) via hybrid BM25+vector search | Install: `skill_manage("install", "qmd")` |
| **diagramming** | Phase 4-5: creating Excalidraw-based figures and architecture diagrams | `skill_view("diagramming")` |
| **data-science** | Phase 4 (Analysis): Jupyter live kernel for interactive analysis and visualization | `skill_view("data-science")` |

**This skill supersedes `ml-paper-writing`** — it contains all of ml-paper-writing's content plus the full experiment/analysis pipeline and autoreason methodology.

### OpenAmer Tools Reference

| Tool | Usage in This Pipeline |
|------|----------------------|
| **`terminal`** | LaTeX compilation (`latexmk -pdf`), git operations, launching experiments (`nohup python run.py &`), process checks |
| **`process`** | Background experiment management: `process("start", ...)`, `process("poll", pid)`, `process("log", pid)`, `process("kill", pid)` |
| **`execute_code`** | Run Python for citation verification, statistical analysis, data aggregation. Has tool access via RPC. |
| **`read_file`** / **`write_file`** / **`patch`** | Paper editing, experiment scripts, result files. Use `patch` for targeted edits to large .tex files. |
| **`web_search`** | Literature discovery: `web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | Fetch paper content, verify citations: `web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | **Parallel section drafting** — spawn isolated subagents for each section. Also for concurrent citation verification. |
| **`todo`** | Primary state tracker across sessions. Update after every phase transition. |
| **`memory`** | Persist key decisions across sessions: contribution framing, venue choice, reviewer feedback. |
| **`cronjob`** | Schedule experiment monitoring, deadline countdowns, automated arXiv checks. |
| **`clarify`** | Ask the user targeted questions when blocked (venue choice, contribution framing). |
| **cron `deliver:`** | Notify the user when experiments complete or drafts are ready even if they're not in chat — schedule the check as a cron job with a messaging `deliver:` target (the agent no longer has a `send_message` tool; outbound delivery is handled by cron/`openamer send`). |

### Tool Usage Patterns

**Experiment monitoring** (most common):
```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<descriptive message>' && git push")
→ (final response auto-delivers "Experiment complete: <summary>"; for unattended runs, schedule via cron with a deliver: target)
```

**Parallel section drafting** (using delegation):
```
delegate_task("Draft the Methods section based on these experiment scripts and configs. 
  Include: pseudocode, all hyperparameters, architectural details sufficient for 
  reproduction. Write in LaTeX using the neurips2025 template conventions.")

delegate_task("Draft the Related Work section. Use web_search and web_extract to 
  find papers. Verify every citation via Semantic Scholar. Group by methodology.")

delegate_task("Draft the Experiments section. Read all result files in results/. 
  State which claim each experiment supports. Include error bars and significance.")
```

Each delegate runs as a **fresh subagent** with no shared context — provide all necessary information in the prompt. Collect outputs and integrate.

**Citation verification** (using execute_code):
```python
# In execute_code:
from semanticscholar import SemanticScholar
import requests

sch = SemanticScholar()
results = sch.search_paper("attention mechanism transformers", limit=5)
for paper in results:
    doi = paper.externalIds.get('DOI', 'N/A')
    if doi != 'N/A':
        bibtex = requests.get(f"https://doi.org/{doi}", 
                              headers={"Accept": "application/x-bibtex"}).text
        print(bibtex)
```

### State Management with `memory` and `todo`

**`memory` tool** — persist key decisions (bounded: ~2200 chars for MEMORY.md):

```
memory("add", "Paper: autoreason. Venue: NeurIPS 2025 (9 pages). 
  Contribution: structured refinement works when generation-evaluation gap is wide.
  Key results: Haiku 42/42, Sonnet 3/5, S4.6 constrained 2/3.
  Status: Phase 5 — drafting Methods section.")
```

Update memory after major decisions or phase transitions. This persists across sessions.

**`todo` tool** — track granular progress:

```
todo("add", "Design constrained task experiments for Sonnet 4.6")
todo("add", "Run Haiku baseline comparison")
todo("add", "Draft Methods section")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

**Session startup protocol:**
```
1. todo("list")                           # Check current task list
2. memory("read")                         # Recall key decisions
3. terminal("git log --oneline -10")      # Check recent commits
4. terminal("ps aux | grep python")       # Check running experiments
5. terminal("ls results/ | tail -20")     # Check for new results
6. Report status to user, ask for direction
```

### Cron Monitoring with `cronjob`

Use the `cronjob` tool to schedule periodic experiment checks:

```
cronjob("create", {
  "schedule": "*/30 * * * *",  # Every 30 minutes
  "prompt": "Check experiment status:
    1. ps aux | grep run_experiment
    2. tail -30 logs/experiment_haiku.log
    3. ls results/haiku_baselines/
    4. If complete: read results, compute Borda scores, 
       git add -A && git commit -m 'Add Haiku results' && git push
    5. Report: table of results, key finding, next step
    6. If nothing changed: respond with [SILENT]"
})
```

**[SILENT] protocol**: When nothing has changed since the last check, respond with exactly `[SILENT]`. This suppresses notification delivery to the user. Only report when there are genuine changes worth knowing about.

**Deadline tracking**:
```
cronjob("create", {
  "schedule": "0 9 * * *",  # Daily at 9am
  "prompt": "NeurIPS 2025 deadline: May 22. Today is {date}. 
    Days remaining: {compute}. 
    Check todo list — are we on track? 
    If <7 days: warn user about remaining tasks."
})
```

### Communication Patterns

**When to notify the user** (via your direct/final response, or a cron `deliver:` target for unattended runs):
- Experiment batch completed (with results table)
- Unexpected finding or failure requiring decision
- Draft section ready for review
- Deadline approaching with incomplete tasks

**When NOT to notify:**
- Experiment still running, no new results → `[SILENT]`
- Routine monitoring with no changes → `[SILENT]`
- Intermediate steps that don't need attention

**Report format** — always include structured data:
```

## Experiment: <name>
Status: Complete / Running / Failed

| Task | Method A | Method B | Method C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

Key finding: <one sentence>
Next step: <what happens next>
```

### Decision Points Requiring Human Input

Use `clarify` for targeted questions when genuinely blocked:

| Decision | When to Ask |
|----------|-------------|
| Target venue | Before starting paper (affects page limits, framing) |
| Contribution framing | When multiple valid framings exist |
| Experiment priority | When TODO list has more experiments than time allows |
| Submission readiness | Before final submission |

**Do NOT ask about** (be proactive, make a choice, flag it):
- Word choice, section ordering
- Which specific results to highlight
- Citation completeness (draft with what you find, note gaps)

---

## Reviewer Evaluation Criteria

Understanding what reviewers look for helps focus effort:

| Criterion | What They Check |
|-----------|----------------|
| **Quality** | Technical soundness, well-supported claims, fair baselines |
| **Clarity** | Clear writing, reproducible by experts, consistent notation |
| **Significance** | Community impact, advances understanding |
| **Originality** | New insights (doesn't require new method) |

**Scoring (NeurIPS 6-point scale):**
- 6: Strong Accept — groundbreaking, flawless
- 5: Accept — technically solid, high impact
- 4: Borderline Accept — solid, limited evaluation
- 3: Borderline Reject — weaknesses outweigh
- 2: Reject — technical flaws
- 1: Strong Reject — known results or ethics issues

See [references/reviewer-guidelines.md](references/reviewer-guidelines.md) for detailed guidelines, common concerns, and rebuttal strategies.

---

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Abstract too generic | Delete first sentence if it could prepend any ML paper. Start with your specific contribution. |
| Introduction exceeds 1.5 pages | Split background into Related Work. Front-load contribution bullets. |
| Experiments lack explicit claims | Add: "This experiment tests whether [specific claim]..." before each one. |
| Reviewers find paper hard to follow | Add signposting, use consistent terminology, make figure captions self-contained. |
| Missing statistical significance | Add error bars, number of runs, statistical tests, confidence intervals. |
| Scope creep in experiments | Every experiment must map to a specific claim. Cut experiments that don't. |
| Paper rejected, need to resubmit | See Conference Resubmission in Phase 7. Address reviewer concerns without referencing reviews. |
| Missing broader impact statement | See Step 5.10. Most venues require it. "No negative impacts" is almost never credible. |
| Human eval criticized as weak | See Step 2.5 and [references/human-evaluation.md](references/human-evaluation.md). Report agreement metrics, annotator details, compensation. |
| Reviewers question reproducibility | Release code (Step 7.9), document all hyperparameters, include seeds and compute details. |
| Theory paper lacks intuition | Add proof sketches with plain-language explanations before formal proofs. See [references/paper-types.md](references/paper-types.md). |
| Results are negative/null | See Phase 4.3 on handling negative results. Consider workshops, TMLR, or reframing as analysis. |

---

## Reference Documents

| Document | Contents |
|----------|----------|
| [references/writing-guide.md](references/writing-guide.md) | Gopen & Swan 7 principles, Perez micro-tips, Lipton word choice, Steinhardt precision, figure design |
| [references/citation-workflow.md](references/citation-workflow.md) | Citation APIs, Python code, CitationManager class, BibTeX management |
| [references/checklists.md](references/checklists.md) | NeurIPS 16-item, ICML, ICLR, ACL requirements, universal pre-submission checklist |
| [references/reviewer-guidelines.md](references/reviewer-guidelines.md) | Evaluation criteria, scoring, common concerns, rebuttal template |
| [references/sources.md](references/sources.md) | Complete bibliography of all writing guides, conference guidelines, APIs |
| [references/experiment-patterns.md](references/experiment-patterns.md) | Experiment design patterns, evaluation protocols, monitoring, error recovery |
| [references/autoreason-methodology.md](references/autoreason-methodology.md) | Autoreason loop, strategy selection, model guide, prompts, scope constraints, Borda scoring |
| [references/human-evaluation.md](references/human-evaluation.md) | Human evaluation design, annotation guidelines, agreement metrics, crowdsourcing QC, IRB guidance |
| [references/paper-types.md](references/paper-types.md) | Theory papers (proof writing, theorem structure), survey papers, benchmark papers, position papers |

### LaTeX Templates

Templates in `templates/` for: **NeurIPS 2025**, **ICML 2026**, **ICLR 2026**, **ACL**, **AAAI 2026**, **COLM 2025**.

See [templates/README.md](templates/README.md) for compilation instructions.

### Key External Sources

**Writing Philosophy:**
- [Neel Nanda: How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/)

**APIs:** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**Venues:** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)
