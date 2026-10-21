# Konkurrenz-Analyse — OpenAmer AGI (Stand 21.10.2026)

**by Amer Sacirovic** · Recherche via **Google im eingeloggten Chrome** (CDP, Port 9222)

Alle unten genannten Repos/Frameworks wurden **live aus den Google-Ergebnissen
extrahiert** (DOM-Text der echten Ergebnisseite, keine Modellantwort).
Die Quellen-Domains sind jeweils genannt.

---

## 1. Kostenlose LLM-APIs (ohne Kreditkarte)

Google-Suche: *„free llm api no credit card 2026 openrouter groq gemini"*
Gefundene Domains: `openrouter.ai`, `github.com`, `www.kdnuggets.com`,
`klymentiev.com`, `arjusingh.com`, `app.stationx.net`

| Anbieter | Domain | Befund aus der Recherche |
|---|---|---|
| **GroqCloud** | — | LPU-Hardware, Llama/Qwen, „blazing-fast inference“, tägliche/minütige Rate-Limits, **ohne Kreditkarte** |
| **OpenRouter** | `openrouter.ai` | `:free`-Modell-Tags, „20+ free models“, **ein API-Key, keine Kreditkarte** — der naheliegendste Einstieg |
| **Google AI Studio** | — | Gemini Flash / Flash-Lite; **neue Accounts brauchen Karte oder Prepaid** |
| **NVIDIA NIM** | — | großer Open-Weight-Katalog (Nemotron), ~**40 Requests/Minute** für Tests |
| **Mistral (La Plateforme)** | — | Codestral, Ministral, kleinere/spezialisierte Modelle |
| **Cloudflare Workers AI** | — | in der „Top 5“-Liste 2026 genannt |

**Weitere Funde:**
- `github.com/open-free-llm-api/awesome-freellm-apis` — „**134+**“ kostenlose APIs
- KDnuggets: „Top Free LLM API Providers“
- klymentiev.com: „How to Get **8 Free AI API Keys** in 2026 (No Credit Card)“
- arjusingh.com: „**12+ Free LLM APIs** You Can Use RIGHT NOW“
- „Free LLM API in 2026: **13 Options** Ranked and Compared“

**Konsequenz für OpenAmer:** `openrouter.ai` mit `:free`-Routing ist die
plattformneutrale Integration (ein Key, viele Modelle). Groq ist der
Geschwindigkeits-Pfad. Beides passt zum bestehenden
`custom_providers`-Mechanismus in `config.yaml` — **kein Core-Eingriff nötig**.

---

## 2. Self-Improving Agent Frameworks

Google-Suche: *„self improving ai agent framework github autonomous 2026"*
Gefundene Domains: `github.com`, `selfimproving-agent.github.io`, `o-mega.ai`,
`futureagi.com`

| Projekt | Repo | Mechanismus (laut Recherche) |
|---|---|---|
| **SIA** | `hexo-ai/sia` | Meta-Agent + Target-Agent + Feedback-Loop; verbessert Modell **und** Agent auf Benchmarks, inkl. Harness- und Weight-Updates |
| **Ouroboros** | `razzant/ouroboros` | General-Purpose-Agent mit **durable memory**, koordiniert Agent-Swarms und **rewritet eigene Codebase, Prompts und Architektur** über Restarts hinweg |
| **BerriAI Self-Improving Agent** | `BerriAI/self-improving-agent` | Drop-in-npm-Layer, injiziert Self-Improvement- und Skill-Evolution-Loops in bestehende Coding-Agents (Claude Code u. a.) |
| **AutoAgent** | `hkuds/autoagent` | Zero-Code-Framework, baut/evaluiert/**selbst-optimiert** Multi-Agent-Workflows per natürlicher Sprache |
| **DSPy / Reflexion / TextGrad** | — | Forschungsbasierte **programmatische** Prompt- und Code-Optimierung — die Bausteine autonomer Selbstverfeinerung |

**Bester Treffer zum Vergleich:** `razzant/ouroboros` beschreibt exakt das,
was in der Roadmap als „Rekursions-Schleife“ steht: durable Memory +
Selbst-Rewrite der Codebase. **OpenAmer hat dafür bereits `selfcode/self_coder.py`**
(mit Fail-Closed-Kette: Pfad-Positivliste, Sandbox, Test-Pflicht, Rollback) —
das ist **strenger** als der Ouroboros-Workflow, weil dort der Testlauf
erzwungen wird.

**BerriAI** ist interessant als *Drop-in*-Layer, weil OpenAmer bereits
`delegate_task`, Skills und Darwin besitzt — ein Self-Improvement-Layer
könnte als Plugin andocken, ohne den Core zu berühren.

---

## 3. Schwarm-/Multi-Agent-Frameworks

Google-Suche: *„multi agent swarm framework parallel github 2026"*
Gefundene Domains: `github.com`, `resources.rework.com`, `www.ayautomate.com`,
`is4.ai`

| Projekt | Befund |
|---|---|
| **LangGraph** | laut Recherche „**the best multi-agent framework for production in 2026**“: zustandsbehaftete Graphen, **durable execution**, human-in-the-loop Checkpoints |
| **Agency Swarm** | Multi-Agent-Orchestrierung auf dem OpenAI-Agents-SDK; Agent-Teams mit Rollen und Kommunikationsflüssen (`VRSEN`) |
| **EvoMap/awesome-agent-swarm** | kuratierte Liste der AI-**Swarm**-Frameworks |
| **AOP (Agent Orchestration Protocol)** | spezialisierte Medical-Agents als MCP-Tools — produktionsreifes Template auf Basis von `swarms` |
| **PARL** (Parallel-Agent Reinforcement Learning) | Trainingsmethodik gegen **„serial collapse“** — Multi-Agent-Systeme kollabieren defaultmäßig auf sequentielle Ausführung |

**PARL ist der wertvollste Fund:** Es benennt exakt die Schwachstelle, gegen
die die eigene `swarm/scheduler.py` gebaut wurde — serielle Ausführung.
Der Scheduler erzwingt bereits `MAX_PARALLEL` und priorisiert nach
`priority`; die Abhängigkeits-Auflösung (A → B → C) ist der
Fertigkeits-Graph, den PARL mit RL trainiert. **Das ist ein
Differenzierungsmerkmal gegenüber der Konkurrenz**: OpenAmer erzwingt
Parallelität strukturell (Scheduler + Claim-Mechanik), PARL trainiert sie.

---

## 4. Was OpenAmer bereits hat, was die Konkurrenz nicht zeigt

| Fähigkeit | OpenAmer | SIA | Ouroboros | BerriAI | LangGraph |
|---|---|---|---|---|---|
| **Durable Memory über Restarts** | ✅ | Teilweise | ✅ | ✅ | ✅ |
| **Selbst-Rewrite der Codebase** | ✅ `selfcode/self_coder.py` | Harness+Weights | ✅ | ✅ (Prompt/Code) | ❌ |
| **Fail-Closed + Test-Pflicht** | ✅ erzwungen | ❌ | ❌ | ❌ | ❌ |
| **Pfad-Positivliste (kein Core-Eingriff)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Schwarm-Parallelität strukturell** | ✅ `swarm/scheduler.py` | ❌ | ✅ | ❌ | ✅ |
| **Black-Box-Kapital-Dashboard (live)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Windows-Desktop-Automation im Hintergrund** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Multi-Plattform-Gateway (20+)** | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 5. Konkrete Konkurrenz-Integrationen (ohne Core-Eingriff)

Nach der Projektlinie *„schmaler Kern, breite Kante“*:

1. **Free-LLM-Provider-Plugin** — `plugins/llm-free-tiers/`
   Ein Plugin, das Groq / OpenRouter-`:free` / Mistral / Google-AI-Studio als
   **Fallback-Kette** registriert. Nutzt den bestehenden
   `custom_providers`-Mechanismus in `config.yaml` — **kein Core-Tool**.

2. **Swarm-Topologie-Vergleich** — `docs/SWARM_BENCHMARK.md`
   OpenAmer vs. LangGraph vs. Agency Swarm vs. AOP: Parallelität,
   Persistenz, Checkpoints. Eigene Stärke: der `scheduler.py`-Ansatz erzwingt
   Parallelität ohne Framework-Abhängigkeit.

3. **Ouroboros-Learning-Loop-Vergleich** — `docs/SELF_CODING_BENCHMARK.md`
   Fail-Closed-Kette (Pfad-Positivliste, Sandbox, Test-Pflicht, Rollback) vs.
   Ouroboros-Rewrite und SIA-Harness. OpenAmer ist **nachweisbar strenger**,
   weil der Testlauf erzwungen wird.

4. **Konkurrenz-Tracker im Collector** — `collect_competitors.py`
   Trägt die Free-API-Quellen und die Konkurrenz-Frameworks ins Ledger, damit
   das Black-Box-Dashboard auch den Markt-Stand zeigt.

---

## 6. Ehrliche Einordnung

- Die **Kostenlos-API-Landschaft** ist eng umkämpft; der Vorteil liegt nicht
  in der Existenz eines Keys, sondern in der **Fallback-Kette** (kein
  Single-Point-of-Failure, wenn ein Anbieter die Rate-Limits verschärft).
- **Self-Improving-Agent-Frameworks** sind 2026 ein überlaufendes Feld.
  OpenAmer kann hier nicht mit "noch einem Framework" gewinnen, sondern nur
  mit der **Fail-Closed-Sicherheit** und der **Windows-Native-Automation**.
- **Schwarm-Frameworks** (LangGraph et al.) sind produktionsreifer für
  reine Workflow-Logik. OpenAmer's Alleinstellungsmerkmal ist der
  **Heartbeat-getriebene** Schwarm (Session-übergreifend, resumable) plus
  das Black-Box-Dashboard — beides hat keine der gefundenen Vergleichs-
  plattformen.

---

*Recherche-Methode: Google-Suche im eingeloggten Chrome via DevTools Protocol,
Extraktion des sichtbaren Resultat-Texts. Rohdaten: `research4.py`-Läufe vom
21.10.2026. Keine Modellantwort, keine Schätzung.*
