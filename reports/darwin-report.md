# Darwin Engine Report
_2026-10-13T14:35:58.390597+00:00 — evolutionary skill ecosystem_

**Population:** 1145 Skills | **Offspring:** 5 | **Competitions:** 29

## Top 10 (fittest skills)

| Skill | Fitness | Usage | Age (days) | Mutationen W/L |
|---|---|---|---|---|
| autonomous-learning-architecture | 2130.0 | 1387 | 0 | 389/51 |
| asi-capability-summary | 2011.37 | 1999 | 19 | 0/0 |
| a2a-brain-meshlearn-verify | 1716.97 | 1704 | 1 | 0/0 |
| auto-env-checker | 1312.4 | 1358 | 18 | 15/88 |
| darwin-cron-guard | 1106.0 | 291 | 0 | 413/24 |
| darwin-harvested-training-internet-learn-log-jsonl | 1091.0 | 281 | 0 | 409/21 |
| cdp-social-posting | 994.0 | 978 | 0 | 0/0 |
| learning-loop | 755.27 | 744 | 52 | 0/0 |
| train-from-usage | 722.27 | 713 | 22 | 0/4 |
| plugin-api | 593.27 | 582 | 52 | 0/0 |

## Bottom 5 (selection candidates)

- **tao-setup-nvidia-gpu-host** (Fitness 7.9, 3 days old)
- **tao-train-optical-inspection** (Fitness 7.9, 3 days old)
- **web-artifacts-builder** (Fitness 7.9, 3 days old)
- **xlsx** (Fitness 7.9, 3 days old)
- **cron-autotest-run-cron-entry** (Fitness 7.23, 23 days old)

## New mutations

- autonomous-learning-architecture → `autonomous-learning-architecture__mutbroaden_trigger` (op=broaden_trigger, applied=True)
- asi-capability-summary → `asi-capability-summary__mutbroaden_trigger` (op=broaden_trigger, applied=True)
- a2a-brain-meshlearn-verify → `a2a-brain-meshlearn-verify__muttighten_trigger` (op=tighten_trigger, applied=True)
- auto-env-checker → `auto-env-checker__mutbroaden_trigger` (op=broaden_trigger, applied=True)
- darwin-cron-guard → `darwin-cron-guard__muttighten_trigger` (op=tighten_trigger, applied=True)

## Competitions

- ⏳ `a2a-brain-meshlearn-verify+asi-capability-summary` (0) vs `None` (0)
- ⏳ `a2a-brain-meshlearn-verify__mutbroaden_trigger` (1716.97) vs `a2a-brain-meshlearn-verify` (1716.97)
- ⏳ `a2a-brain-meshlearn-verify__muttighten_trigger` (1716.97) vs `a2a-brain-meshlearn-verify` (1716.97)
- ⏳ `asi-capability-summary+asi-identity` (0) vs `None` (0)
- ⏳ `asi-capability-summary__mutbroaden_trigger` (2011.37) vs `asi-capability-summary` (2011.37)
- ⏳ `asi-capability-summary__muttighten_trigger` (2011.37) vs `asi-capability-summary` (2011.37)
- ⏳ `asi-identity+auto-env-checker` (0) vs `None` (0)
- ⏳ `auto-env-checker+autonomous-learning-architecture` (0) vs `None` (0)
- ⏳ `auto-env-checker+cdp-social-posting` (0) vs `None` (0)
- ⏳ `auto-env-checker__mutbroaden_trigger` (1312.4) vs `auto-env-checker` (1312.4)
- ⏳ `autonomous-learning-architecture__mutbroaden_trigger` (2130.0) vs `autonomous-learning-architecture` (2130.0)
- ⏳ `autonomous-learning-architecture__muttighten_trigger` (2130.0) vs `autonomous-learning-architecture` (2130.0)
- ⏳ `cdp-social-posting__mutbroaden_trigger` (994.0) vs `cdp-social-posting` (994.0)
- ⏳ `cdp-social-posting__muttighten_trigger` (994.0) vs `cdp-social-posting` (994.0)
- ⏳ `darwin-cron-guard__muttighten_trigger` (1106.0) vs `darwin-cron-guard` (1106.0)
- ⏳ `discord-server-management__mutadd_verification_step` (45.13) vs `discord-server-management` (45.13)
- ⏳ `discord-server-management__mutbroaden_trigger` (45.13) vs `discord-server-management` (45.13)
- ⏳ `discord-server-management__muttighten_trigger` (45.13) vs `discord-server-management` (45.13)
- ⏳ `github-readme-summary__mutbroaden_trigger` (29.93) vs `github-readme-summary` (29.93)
- ⏳ `github-readme-summary__muttighten_trigger` (29.93) vs `github-readme-summary` (29.93)
- ⏳ `openamer-plugin-development__muttighten_trigger` (25.97) vs `openamer-plugin-development` (25.97)
- ⏳ `plugin-api__mutbroaden_trigger` (593.27) vs `plugin-api` (593.27)
- ⏳ `plugin-api__muttighten_trigger` (593.27) vs `plugin-api` (593.27)
- ⏳ `train-from-usage__mutadd_pitfall` (722.27) vs `train-from-usage` (722.27)
- ⏳ `train-from-usage__mutadd_verification_step` (722.27) vs `train-from-usage` (722.27)
- ⏳ `train-from-usage__mutbroaden_trigger` (722.27) vs `train-from-usage` (722.27)
- ⏳ `train-from-usage__muttighten_trigger` (722.27) vs `train-from-usage` (722.27)
- ⏳ `undetectable-browsing__muttighten_trigger` (30.33) vs `undetectable-browsing` (30.33)
- ⏳ `vscode-extension-scaffold__mutbroaden_trigger` (27.27) vs `vscode-extension-scaffold` (27.27)

## Evolution Tree

```mermaid
graph TD
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-architecture__mutbroaden_trigger["autonomous-learning-architecture__mutbroaden_trigger"]
    asi-capability-summary["asi-capability-summary"] --> asi-capability-summary__mutbroaden_trigger["asi-capability-summary__mutbroaden_trigger"]
    a2a-brain-meshlearn-verify["a2a-brain-meshlearn-verify"] --> a2a-brain-meshlearn-verify__muttighten_trigger["a2a-brain-meshlearn-verify__muttighten_trigger"]
    auto-env-checker["auto-env-checker"] --> auto-env-checker__mutbroaden_trigger["auto-env-checker__mutbroaden_trigger"]
    darwin-cron-guard["darwin-cron-guard"] --> darwin-cron-guard__muttighten_trigger["darwin-cron-guard__muttighten_trigger"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-loops["autonomous-learning-loops"]
    darwin-cron-guard["darwin-cron-guard"] --> guard["guard"]
    darwin-harvested-training-internet-learn-log-jsonl["darwin-harvested-training-internet-learn-log-jsonl"] --> learn["learn"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-architecture__mutbroaden_trigger["autonomous-learning-architecture__mutbroaden_trigger"]
    asi-capability-summary["asi-capability-summary"] --> asi-capability-summary__mutbroaden_trigger["asi-capability-summary__mutbroaden_trigger"]
    a2a-brain-meshlearn-verify["a2a-brain-meshlearn-verify"] --> a2a-brain-meshlearn-verify__muttighten_trigger["a2a-brain-meshlearn-verify__muttighten_trigger"]
    auto-env-checker["auto-env-checker"] --> auto-env-checker__mutbroaden_trigger["auto-env-checker__mutbroaden_trigger"]
    darwin-cron-guard["darwin-cron-guard"] --> darwin-cron-guard__muttighten_trigger["darwin-cron-guard__muttighten_trigger"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-loops["autonomous-learning-loops"]
    darwin-cron-guard["darwin-cron-guard"] --> guard["guard"]
    darwin-harvested-training-internet-learn-log-jsonl["darwin-harvested-training-internet-learn-log-jsonl"] --> learn["learn"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-architecture__mutbroaden_trigger["autonomous-learning-architecture__mutbroaden_trigger"]
    asi-capability-summary["asi-capability-summary"] --> asi-capability-summary__mutbroaden_trigger["asi-capability-summary__mutbroaden_trigger"]
    a2a-brain-meshlearn-verify["a2a-brain-meshlearn-verify"] --> a2a-brain-meshlearn-verify__muttighten_trigger["a2a-brain-meshlearn-verify__muttighten_trigger"]
    auto-env-checker["auto-env-checker"] --> auto-env-checker__mutbroaden_trigger["auto-env-checker__mutbroaden_trigger"]
    darwin-cron-guard["darwin-cron-guard"] --> darwin-cron-guard__muttighten_trigger["darwin-cron-guard__muttighten_trigger"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-loops["autonomous-learning-loops"]
    darwin-cron-guard["darwin-cron-guard"] --> guard["guard"]
    darwin-harvested-training-internet-learn-log-jsonl["darwin-harvested-training-internet-learn-log-jsonl"] --> learn["learn"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-architecture__mutbroaden_trigger["autonomous-learning-architecture__mutbroaden_trigger"]
    asi-capability-summary["asi-capability-summary"] --> asi-capability-summary__mutbroaden_trigger["asi-capability-summary__mutbroaden_trigger"]
    a2a-brain-meshlearn-verify["a2a-brain-meshlearn-verify"] --> a2a-brain-meshlearn-verify__muttighten_trigger["a2a-brain-meshlearn-verify__muttighten_trigger"]
    auto-env-checker["auto-env-checker"] --> auto-env-checker__mutbroaden_trigger["auto-env-checker__mutbroaden_trigger"]
    darwin-cron-guard["darwin-cron-guard"] --> darwin-cron-guard__muttighten_trigger["darwin-cron-guard__muttighten_trigger"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-loops["autonomous-learning-loops"]
    darwin-cron-guard["darwin-cron-guard"] --> guard["guard"]
    darwin-harvested-training-internet-learn-log-jsonl["darwin-harvested-training-internet-learn-log-jsonl"] --> learn["learn"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-architecture__mutbroaden_trigger["autonomous-learning-architecture__mutbroaden_trigger"]
    asi-capability-summary["asi-capability-summary"] --> asi-capability-summary__mutbroaden_trigger["asi-capability-summary__mutbroaden_trigger"]
    a2a-brain-meshlearn-verify["a2a-brain-meshlearn-verify"] --> a2a-brain-meshlearn-verify__muttighten_trigger["a2a-brain-meshlearn-verify__muttighten_trigger"]
    auto-env-checker["auto-env-checker"] --> auto-env-checker__mutbroaden_trigger["auto-env-checker__mutbroaden_trigger"]
    darwin-cron-guard["darwin-cron-guard"] --> darwin-cron-guard__muttighten_trigger["darwin-cron-guard__muttighten_trigger"]
    autonomous-learning-architecture["autonomous-learning-architecture"] --> autonomous-learning-loops["autonomous-learning-loops"]
    darwin-cron-guard["darwin-cron-guard"] --> guard["guard"]
    darwin-harvested-training-internet-learn-log-jsonl["darwin-harvested-training-internet-learn-log-jsonl"] --> learn["learn"]
```
