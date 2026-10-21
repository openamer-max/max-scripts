# OpenAmer – Wettbewerbsvergleich (Stand: 21.10.2026)

**Methode:** Alle Sternzahlen, Repo-URLs, Lizenzen und Push-Daten via `api.github.com`
verifiziert (Abruf 2026-10-21 00:37–00:50 UTC, un-authentifiziert → 60 Calls/Std.).
Feature-Angaben aus den offiziellen READMEs (`raw.githubusercontent.com`, jeweils auf
den Default-Branch geprüft). OpenAmer-Baseline wurde **aus dem lokal installierten
Quellcode** verifiziert (`C:\Users\amer7\AppData\Local\openamer\openamer-agent`,
Version `2026.10.20`, upstream `c316b88e`), **nicht** aus der Selbstdarstellung.

---

## 0. Baseline: Was OpenAmer bereits kann (verifiziert)

| Feature | Status | Beleg im Quellcode |
|---|---|---|
| MCP Client + Server | ✅ voll | `tools/mcp_tool*.py` (15 Module), `mcp_oauth_manager.py`, `openamer_cli/mcp` |
| Approval-Workflows | ✅ voll | `tools/approval.py` (`approvals.mode`, `hitl.enabled`, `approvals.cron_mode`), `tools/write_approval.py` |
| Checkpointing / Rollback | ✅ voll | `tools/checkpoint_manager.py` (Shared Shadow-Git-Store, Snapshot pro Turn) |
| Session-Fork | ⚠️ partiell | nur über `acp_adapter/server.py:fork_session` + `gateway/platforms/api_server.py` (`POST /api/sessions/{id}/fork`) – **kein Core-CLI-Befehl** |
| Cost-Tracking | ✅ voll | `agent/usage_pricing.py`, `agent/billing_usage.py`, `agent/credits_tracker.py`, `agent/account_usage.py` |
| Sandbox | ✅ voll | `cli-config.yaml.example` → `terminal.sandbox`, Remote-Server-Modus, Daytona-Cloud-Sandbox |
| Voice / TTS | ✅ voll | `tools/voice_mode.py`, `tts_tool.py`, `tts_streaming.py`, `neutts_synth.py` |
| Web-UI | ✅ voll | `openamer dashboard` (Admin-Panel + eingebetteter Chat) |
| Desktop-App | ✅ voll | `apps/desktop` (Electron, macOS/Linux/Windows-Builds) |
| Plugin-/Skill-Marktplatz | ✅ voll | `tools/skills_hub.py` (GitHub-Quell-Adapter, Quarantäne, Audit-Log), `openamer plugins search` |
| A2A / Multi-Agent | ✅ voll (eigenes Protokoll) | `openamer_cli/a2a/` (26 Module: relay, mesh_learning, beacon, trust, privacy), `scripts/a2a_{server,worker,delegate}.py` |
| Telemetrie | ✅ Privacy-by-default | cua-driver-PostHog wird standardmäßig deaktiviert (`tools/computer_use/cua_backend.py:227`) |
| VS Code / JetBrains | ✅ | `apps/vscode`, `apps/jetbrains` |
| Durable Execution | ✅ | README + `tools/checkpoint_manager.py` |

**Die echten Lücken (verifiziert im Quellcode):**

1. **Keine Mobile-App** – `apps/` enthält nur `desktop`, `jetbrains`, `shared`, `vscode`, `bootstrap-installer`.
2. **Keine granulare Multi-User-RBAC** – `grep rbac|user_group|tenant` in `gateway/platforms/api_server.py` → 0 Treffer; nur `shared_multi_user_session`-Flag.
3. **Kein OTEL-/OpenTelemetry-Export** – `grep -ri opentelemetry` über den gesamten Baum → 0 Treffer.
4. **Kein Eval-/Benchmark-Harness** – kein `tools/eval_*` oder `tools/bench_*`.
5. **Keine native LSP-Kontext-Anreicherung** – LSP nur beiläufig in `patch_parser.py`/`mcp_tool.py`, nicht Crush-artig.
6. **Kein Standard-A2A-Agent-Card-Endpoint** – eigener ARD-Catalog (`/.well-known/ai-catalog.json`), **nicht** die Google-A2A-Spec (`/.well-known/agent-card.json`).
7. **Keine visuelle Workflow-/Canvas-Oberfläche** für Nicht-Entwickler.
8. **Kein Enterprise-Control-Plane** (REST-API-Server als Produkt, Audit-Logs, Mandanten-Isolation).
9. **Keine Community-Größe**: `openamer/openamer` = **8 Stars**, Repo erst seit 2026-08-16, 4 Forks. Das ist der mit Abstand größte Abstand zu allen Wettbewerbern.

---

## A. Terminal-/Desktop-Coding-Agents (nächste Wettbewerber)

### 1. Claude Code
- **Repo:** https://github.com/anthropics/claude-code — **152.645 ★** — TypeScript, kein SPDX-Lizenzfile im Root (proprietär)
- **Kern-Feature:** Terminal-first Coding-Agent von Anthropic mit repo-weitem Verständnis und Git-Workflows.
- **Was OpenAmer fehlt:** (a) **Abo-Login statt API-Key** – Claude-Code nutzt die bestehende Claude-Subscription; OpenAmer braucht `ANTHROPIC_API_KEY`; (b) **GitHub-Integration mit `@claude`-Mention im PR/Issue** – OpenAmer hat keinen GitHub-Bot-Workflow; (c) **1-Klick-Installer für macOS/Linux/Windows/WinGet/Homebrew** – OpenAmer-Installer setzt uv+Python voraus; (d) **Anthropic-Provider-Deep-Integration** (Prompt-Caching-Optimierung, Beta-Features) – OpenAmer ist provider-agnostisch, also nie tief in Anthropic-Sonderfeatures; (e) **offizielle Produkt-Sicherheits- und Zertifizierungsstufe**.

### 2. OpenAI Codex CLI
- **Repo:** https://github.com/openai/codex — **130.164 ★** — Rust, Apache-2.0
- **Kern-Feature:** In Rust geschriebener, blitzschneller lokaler Coding-Agent mit nativer Sandbox-Ausführung.
- **Was OpenAmer fehlt:** (a) **Rust-Binary** – ~10× kürzerer Start als OpenAmers Python-Bootstrap (uv+venv+Dependencies); (b) **`codex app` Desktop-App** (OpenAI-eigene, verifiziert im README) neben `codex` CLI und IDE-Extension; (c) **Codex Web** – cloudbasierter Agent, OpenAmer ist strikt lokal; (d) **ChatGPT-Subscription-Auth** (Abo statt API-Key); (e) **IDE-Integration für Cursor/Windsurf** – OpenAmer hat nur VS Code/JetBrains.

### 3. OpenHands (jetzt "Agent Canvas")
- **Repo:** https://github.com/OpenHands/OpenHands — **91.411 ★** — TypeScript, MIT
- **Kern-Feature:** Self-hosted Control-Center, das OpenHands **und jeden ACP-kompatiblen Agenten** (Claude Code, Codex, Gemini CLI, OpenCode) über lokale, Docker-, VM- oder Cloud-Backends orchestriert.
- **Was OpenAmer fehlt:** (a) **Fremd-Agent-Orchestrierung** – OpenAmer kann ACP-Agenten nicht als Worker in sein Board hängen; (b) **Multi-Backend-Abstraktion** (lokal / Docker / VM / Enterprise-Cloud) – OpenAmer hat nur lokale Worker; (c) **vorgebaute Automationen, die nach Slack publizieren** und GitHub-Issues in Tasks zerlegen; (d) **komplett neues Produkt-Rebranding 2026** mit starker Doku/Story – OpenAmer wirkt dagegen unfertig (8 Stars); (e) **Enterprise-Self-Hosting-Doku** (SELF_HOSTING.md).

### 4. Cline
- **Repo:** https://github.com/cline/cline — **70.706 ★** — TypeScript, Apache-2.0
- **Kern-Feature:** Open-Source-Coding-Agent in IDE, Terminal und Desktop-App mit Human-in-the-Loop-Freigaben.
- **Was OpenAmer fehlt:** (a) **VS-Code-Marketplace-Präsenz** – Cline ist die bekannteste Coding-Agent-Erweiterung; OpenAmer hat keine VS-Code-Marketplace-Listing; (b) **Headless-Modus für CI/CD** (`cline` headless) als first-class Kommando – OpenAmer hat `chat -q`, aber kein CI-spezifisches Harness; (c) **„schedule routines" in der Desktop-App** – OpenAmer-Cron ist CLI/Tool-basiert, nicht in der GUI; (d) **komplettes SDK** (Cline als SDK, IDE, CLI) – OpenAmer hat keine öffentliche Agent-SDK für Fremd-Apps.

### 5. Roo Code
- **Repo:** https://github.com/RooCodeInc/Roo-Code — **24.273 ★** — TypeScript, Apache-2.0
- **Kern-Feature:** „Ganzes Dev-Team" im Editor mit anpassbaren Betriebs-Modi (Code, Architect, Ask, Debug, Custom).
- **Was OpenAmer fehlt:** (a) **Modus-System als UI-Metapher** – OpenAmer hat Werkzeuge, aber keine sichtbaren, umschaltbaren „Persona-Modi" im Desktop; (b) **VS-Code-Marketplace-Listing** + 20+ Übersetzungen (Community-Reichweite); (c) **Custom-Mode-Definition durch den Nutzer** (eigene Persona-Prompts ohne Code); (d) **Booster-Mode-Effizienz** (erhöhtes Context-Budget für große Tasks) – OpenAmer läuft in ein 429/Timeout bei „Capped at N".

### 6. Continue.dev
- **Repo:** https://github.com/continuedev/continue — **36.273 ★** — TypeScript, Apache-2.0
- **Kern-Feature:** Früher Open-Source-Coding-Agent für VS Code/JetBrains/CLI.
- **Status:** **KEIN Wettbewerber mehr.** README: *„The `continuedev/continue` repository is no longer actively maintained and is read-only for all users."* Letzter Release 2.0.0, Telemetrie entfernt, Auth entfernt. → **Kein Gap relevant.**

### 7. Goose (Block → AAIF/Linux Foundation)
- **Repo:** https://github.com/aaif-goose/goose — **55.462 ★** — Rust, Apache-2.0 (Linux-Foundation-AAIF)
- **Kern-Feature:** Allgemein-Zweck-Agent mit nativer Desktop-App, CLI und embedbarer API, der 70+ MCP-Extensions anbindet.
- **Was OpenAmer fehlt:** (a) **Native Desktop-App in Rust** – OpenAmers Electron-App ist schwergewichtig; (b) **ACP-Provider-Auth**: Nutzt bestehende Claude-/ChatGPT-/Gemini-Subscriptions ohne API-Key; (c) **eingebettete API (Goose API)** – OpenAmer hat nur Gateway-Protokolle, keine REST-API zum Einbetten; (d) **70+ kuratierte Extensions** vs. OpenAmers Skills-Hub ohne Marketplace-Ökosystem; (e) **Foundation-Governance + Firmen-Backend** (Block) = höheres Vertrauen.

### 8. OpenCode
- **Repo:** https://github.com/anomalyco/opencode — **218.852 ★** — TypeScript, MIT (`sst/opencode` → 301 Redirect dorthin)
- **Kern-Feature:** Der meistgesteuerte Open-Source-Coding-Agent (Klartext-Repo, keine Marketing-Sprache), inzwischen mit Desktop-App (BETA).
- **Was OpenAmer fehlt:** (a) **Community-Größe** (218k vs. 8 Stars) – das ist der wichtigste Wettbewerbsfaktor schlechthin; (b) **Desktop-App für macOS (dmg)**; (c) **YOLO-Installer** mit einem Einzeiler; (d) **Provider-freie Session-Persistenz mit Ordner-/Projekt-Sessions**; (e) **Leaderboard-Ökosystem** (OpenCode Zen), das Nutzer anzieht.
- *Hinweis:* Das ältere Go-Repo https://github.com/opencode-ai/opencode (13.801 ★) ist seit 2025-09 inaktiv → **nicht** der aktive Wettbewerber.

### 9. Crush (Charm)
- **Repo:** https://github.com/charmbracelet/crush — **28.721 ★** — Go, Lizenz NOASSERTION
- **Kern-Feature:** Charm-ecosystem-Coding-Agent mit LSP-gestützter Kontextanreicherung und MCP-Erweiterung.
- **Was OpenAmer fehlt:** (a) **Native LSP-Integration** – Crush nutzt LSPs *für Kontext*, OpenAmer nur beiläufig in `patch_parser.py`; (b) **Modellwechsel mit erhaltenem Kontext** (OpenAmer: Provider-Wechsel, aber kein LSP-Kontext); (c) **Android/BSD-Support** (Termux, FreeBSD, OpenBSD, NetBSD) – OpenAmer fokussiert Win/macOS/Linux; (d) **Charm-Ökosystem** (25k+ Apps) als Vertrauens-/Qualitätssignal; (e) **LSP-Diagnostik-Feedback-Loop** in den Agentenloop.

### 10. Aider
- **Repo:** https://github.com/Aider-AI/aider — **49.666 ★** — Python, Apache-2.0
- **Kern-Feature:** Git-natives AI-Pair-Programming im Terminal mit automatischem Commit.
- **Was OpenAmer fehlt:** (a) **Repo-Map** (Tree-Sitter-Index) für Token-sparsame Codebasis-Kontexte – OpenAmer liest Dateien ad hoc; (b) **Architect/Editor-2-Modell-Split** (Planungsmodell + Implementierungsmodell getrennt) – OpenAmer hat nur ein aktives Modell pro Session; (c) **Auto-Lint-und-Test nach jeder Änderung** mit Auto-Fix – OpenAmer hat keinen verpflichtenden Lint/Test-Gate im Code-Loop; (d) **git-native Undo** (jeder AI-Commit ist reversibel) – OpenAmer hat Checkpoint-Rollback, aber nicht git-basiert; (e) **Voice-Modus zum Coden** (Transkript → Umsetzung).

### 11. SWE-agent / mini-swe-agent
- **Repo:** https://github.com/SWE-agent/SWE-agent — **20.604 ★** — Python, MIT
- **Kern-Feature:** nimmt ein GitHub-Issue und behebt es automatisch – State-of-the-Art auf SWE-bench unter Open Source.
- **Was OpenAmer fehlt:** (a) **SWE-bench-verifizierte Performance-Messung** – OpenAmer hat keinen unabhängigen Benchmark; (b) **Issue→Patch-Pipeline mit reproduzierbarem Harness**; (c) **reine YAML-Konfigurierbarkeit** („simple & hackable by design") für Forschungs-Workflows; (d) **Agent-Trajektorien-Export** als Forschungsdatensatz.

### 12. Open Interpreter
- **Repo:** https://github.com/openinterpreter/openinterpreter — **68.623 ★** — Rust, Apache-2.0
- **Kern-Feature:** Codex-Fork, optimiert auf **Low-Cost-Modelle** – Agent-Harness, der billige Modelle maximal ausreizt.
- **Was OpenAmer fehlt:** (a) **Harness-Fokus auf Kosteneffizienz** – OpenAmer hat keinen „cheap-model-optimized"-Pfad; (b) **Codex-Exec-Protokoll-Kompatibilität** (SDK + `scripts/test-codex-sdk-compat.sh`) – ermöglicht Drop-in-Ersatz in fremden Tools; (c) **ACP-Client-Kompatibilität** (`interpreter acp`) – OpenAmer ist selbst ACP-Server, nicht -Client; (d) **Local-Streaming-Web-Chat** (eigene Web-UI) – OpenAmer-Dashboard ist Admin-Panel, kein Chat-First-UI.

---

## B. Agent-Frameworks (Bibliotheken – konkurrieren um Entwickler, nicht um Enduser)

### 13. smolagents (Hugging Face)
- **Repo:** https://github.com/huggingface/smolagents — **29.950 ★** — Python, Apache-2.0
- **Kern-Feature:** Minimalistische Bibliothek für Agenten, die in Code denken (`CodeAgent`).
- **Was OpenAmer fehlt:** (a) **CodeAgent-Paradigma** – Aktionen werden als Code geschrieben, nicht als Tool-Calls; (b) **verwaltete Sandbox-Backends** (E2B, Blaxel, Modal, Docker) als first-class Option – OpenAmer hat nur lokale/Daytona-Sandbox; (c) **Hub-Spaces als Tools** (`agent.from_hub(...)`); (d) **Tool-Interop** (MCP, LangChain, HF-Space) als Kernfunktion; (e) **Hugging-Face-Hub-Integration** (Modelle, Spaces, Datasets) als Distributionskanal.

### 14. Pydantic AI
- **Repo:** https://github.com/pydantic/pydantic-ai — **20.757 ★** — Python, MIT
- **Kern-Feature:** Typisiertes Python-AI-SDK – derselbe Agent läuft in Web, Terminal, Voice, GitHub Actions und auf dauerhaften Queues.
- **Was OpenAmer fehlt:** (a) **Durable Execution** (Temporal, DBOS, Prefect, Restate, Lambda, Airflow) – OpenAmer-Delegation ist prozesslokal und stirbt mit dem Parent; (b) **Pydantic Evals** inkl. **Online-Evaluation auf Live-Traffic** und Tool-Call-Trajektorien-Grading – OpenAmer hat keinen Eval-Harness; (c) **Pydantic AI Gateway** mit Echtzeit-Kostenmonitoring **und Budget-Kontrolle** – OpenAmer zeigt Kosten, hat aber kein Budget-Limit; (d) **Monty** – sandboxed Python-Interpreter für modellgeschriebenen Code; (e) **realtime Voice** als Framework-Feature; (f) **OpenTelemetry** (Logfire) – OpenAmer hat keinen OTEL-Export; (g) **Typisierte Graph-Steuerung** (Pydantic Graph).

### 15. LangGraph
- **Repo:** https://github.com/langchain-ai/langgraph — **43.595 ★** — Python, MIT
- **Kern-Feature:** Low-Level-Orchestrierungs-Framework für langlebige, zustandsbehaftete Agenten (Grafen, Checkpoints, Persistenz).
- **Was OpenAmer fehlt:** (a) **Explizite Graph-/Zustandsmaschine** mit Time-Travel und Checkpoint-Resume – OpenAmers Ablauf ist ein monolithischer Loop; (b) **Interrupte/Resume für Human-in-the-Loop** auf beliebigen Knoten; (c) **LangSmith-Observability** (kommerzielles Tracer-Panel) – OpenAmer hat nur internen Trace-Browser; (d) **Deep-Agents-Paket** (Plan, Subagents, Filesystem) als Framework; (e) **Enterprise-Deployment** (Kunden: Klarna, Replit, Elastic).

### 16. AutoGen (→ Microsoft Agent Framework)
- **Repo:** https://github.com/microsoft/autogen — **61.501 ★** — Python, CC-BY-4.0
- **Kern-Feature:** Programmier-Framework für agentische AI (Multi-Agent-Chat, GroupChat, Code-Ausführung).
- **Status-Hinweis:** Offizieller Nachfolger ist **Microsoft Agent Framework** (https://github.com/microsoft/agent-framework, **14.235 ★**, MIT), README: *„Microsoft Agent Framework (MAF) is the enterprise-ready successor to AutoGen."*
- **Was OpenAmer fehlt:** (a) **A2A-Standard-Interoperabilität** über Runtime-Grenzen hinweg („cross-runtime interoperability via A2A and MCP") – OpenAmer hat ein eigenes A2A-Protokoll ohne Standard-Agent-Card; (b) **.NET-Parität**; (c) **McpWorkbench** als typed Abstraktion (Playwright-MCP als einbürgerliches Muster); (d) **Microsoft-Enterprise-Ökosystem** (Azure, Entra, VS, Teams) = Vertrauensvorteil.

### 17. CrewAI
- **Repo:** https://github.com/crewAIInc/crewAI — **59.924 ★** — Python, MIT
- **Kern-Feature:** Rollenbasiertes Orchestrierungs-Framework (Roles, Goals, Backstories, Crews, Flows).
- **Was OpenAmer fehlt:** (a) **CrewAI AMP Suite** – kommerzielles Control-Plane mit Observability, Governance, Deployments, Security; (b) **A2A-Support** (explizit gelistet) – OpenAmer-A2A ist proprietär; (c) **Checkpointing** als Kern-API; (d) **Tracing & Observability** mit Metriken/Logs/Traces (Amplitude); (e) **Dify-Docs-MCP-Server** als offizieller Support-Kanal.

### 18. Agno
- **Repo:** https://github.com/agno-agi/agno — **42.839 ★** — Python, Apache-2.0
- **Kern-Feature:** Agent-Plattform mit eigenem Control-Plane (AgentOS), eigener DB für Sessions/Traces und JWT-RBAC.
- **Was OpenAmer fehlt:** (a) **AgentOS Control-Plane** – REST-API + Postgres für Sessions, Memory, Knowledge, Traces; (b) **JWT-basierte RBAC** – in OpenAmer komplett nicht vorhanden; (c) **Human-Approval als API-Feature** („Pause runs for user confirmation. Block tools that require admin approval.") mit Admin-Gate pro Tool – OpenAmer hat Approval-Modi, aber keine rollenbasierte Tool-Sperre; (d) **Learning-Loop durch Simulationen** und Usage-Daten; (e) **A2A-Interface** zur Agent-Interoperabilität; (d) **9 fertige Deploy-Templates** (Docker, Railway, AWS, GCP, Azure, Fly, Render, Modal, Helm).

### 19. Mastra
- **Repo:** https://github.com/mastra-ai/mastra — **28.957 ★** — TypeScript, NOASSERTION
- **Kern-Feature:** Modernes TypeScript-Framework für KI-Agenten mit Workflow-Engine, Observability und Evals.
- **Was OpenAmer fehlt:** (a) **Suspend-and-Resume-Workflows** mit persistiertem Zustand → unbegrenzt pausierbar bis User-Input; (b) **eingebaute Evals** (Mastra Evals) als Framework-Kern; (c) **Observability** als Kern-Modul; (d) **MCP-Server-Authoring** (Agent/Workflows als MCP-Ressourcen exponieren) – OpenAmer kann MCP nur konsumieren; (e) **Observational Memory** (menschenähnliches Langzeitgedächtnis); (f) **Next.js/React-First**-Zielgruppe (Web-Entwickler statt Shell-Entwickler).

### 20. Letta (MemGPT)
- **Repo:** https://github.com/letta-ai/letta — **25.207 ★** — Apache-2.0 (aktueller Quellcode: https://github.com/letta-ai/letta-code, **3.665 ★**)
- **Kern-Feature:** Plattform für zustandsbehaftete Agenten mit lernendem Gedächtnis, das sich über Zeit verbessert.
- **Was OpenAmer fehlt:** (a) **MemGPT-Kernidee**: Memory-Tiering (Core/Archival/Recall) als *Runtime-Mechanik* – OpenAmer-Memory ist ein Skill-/State-DB, kein Self-Editing-Memory-Heap; (b) **Identität & Persona-Kontinuität** über Sessions hinweg; (c) **Letta Cloud** für geräteübergreifende Memory (Cloud ist Abweichung vom rein lokalen Ansatz, aber ein echtes Alleinstellungsmerkmal); (d) **kanalübergreifende Memory-Teilung** (Slack/Telegram/Discord + Web + mobil).

---

## C. Memory- / Kontext-Infrastruktur (Komponenten, keine Enduser-Produkte)

### 21. mem0
- **Repo:** https://github.com/mem0ai/mem0 — **67.539 ★** — Python, Apache-2.0
- **Kern-Feature:** Drop-in-Memory-Schicht für Agenten mit token-effizientem Retrieval.
- **Was OpenAmer fehlt:** (a) **Entity-Linking** (Entitäten extrahiert, eingebettet, verknüpft) für Retrieval-Boost; (b) **Multi-Signal-Retrieval** (semantisch + BM25 + Entity-Matching, parallel gescort und gefusht) – OpenAmer nutzt TF-IDF-Vektoren; (c) **temporale Argumentation** (zeitbewusste Retrieval-Rangfolge); (d) **LongMemEval-Benchmark 94.4** – OpenAmer hat keinen extern validierten Memory-Benchmark; (e) **Multi-Signal-Fusion** ist OpenAmers Vector-Memory deutlich unterlegen.

### 22. Zep (+ Graphiti)
- **Repo:** https://github.com/getzep/zep — **4.966 ★** — Python, Apache-2.0
- **Kern-Feature:** Zep ist inzwischen ein *Beispiel-/Integrations-Repo*; der eigentliche Kern ist **Graphiti**.
- **Wichtiger:** https://github.com/getzep/graphiti — **32.085 ★** — Python, Apache-2.0 — *„Build Real-Time Knowledge Graphs for AI Agents"*
- **Was OpenAmer fehlt:** (a) **temporaler Wissensgraph** mit Bi-Temporal-Modell (Fakt vs. Valid_from/Valid_to) – OpenAmer hat flache Key-Value-/TF-IDF-Erinnerung; (b) **Graph-basiertes Retrieval** (Entitätsrelationen statt Textähnlichkeit); (c) **`zep-eval-harness`** (LoCoMo, LongMemEval) – bewertbare Memory-Qualität; (d) **Memory-Plugin für Claude Desktop/Cowork und ChatGPT Work** – Vermarktung über fremde Ökosysteme; (e) **Ingestion-Graph-Building in Echtzeit** (nicht nur Chat-Extraktion).

---

## D. Browser-Agenten

### 23. Browser Use
- **Repo:** https://github.com/browser-use/browser-use — **118.664 ★** — Python, MIT
- **Kern-Feature:** Open-Source-Browser-Agent (Python + TypeScript) plus gehostete Cloud-Browser ab $0.02/Stunde.
- **Was OpenAmer fehlt:** (a) **Stealth-Browser-Cloud** mit CAPTCHA-Lösung und Residential-Proxies (Stealth Bench V2: 90,5 %) – OpenAmer fährt den lokalen Browser ohne Camoufox/Proxy-Pool; (b) **hosted Agent API** mit Skalierung; (c) **vergleichsweise starker Benchmark-Fokus**; (d) **Cloud-Produkt als Geschäftsmodell** (OpenAmer ist bewusst kommerziell-api-los). *Nicht-Gap:* MCP-Support und lokale Python-Library hat OpenAmer nicht nötig.

### 24. Stagehand (Browserbase)
- **Repo:** https://github.com/browserbase/stagehand — **25.751 ★** — TypeScript, MIT
- **Kern-Feature:** SDK, das Webseiten per `observe/act/extract` strukturiert manipuliert und dabei echte Selektoren zurückgibt.
- **Was OpenAmer fehlt:** (a) **`observe()` gibt echte Selektoren zurück, damit Credentials nie das Modell erreichen** – OpenAmers Browser-Tool ist primär screenshot/vision-basiert; (b) **deterministische `act()`-Stabilität** über Re-Runs (Caching der Selektoren) statt freier Vision-Navigation; (c) **Zod-typisierte Extraktion**; (d) **`extract()`-API** für strukturierte Daten; (e) **First-class-Integration in Claude Code, Codex, Mastra** – OpenAmer ist dort nicht als Workbench angebunden.

---

## E. Persönliche Agenten / „Second Brain" (Produktniveau, nicht nur Code)

### 25. OpenClaw  ⚠️ **wichtigster direkter Wettbewerber**
- **Repo:** https://github.com/openclaw/openclaw — **392.676 ★** — TypeScript, MIT
- **Kern-Feature:** Open-Source-Assistent auf dem eigenen Rechner, der in 20+ Chat-Channels und in nativen Apps für macOS, **iOS, Android**, Windows und Linux läuft; eine Gateway-Instanz dient Personal- **oder** geteilter Team-Deployment.
- **Was OpenAmer fehlt:** (a) **Native iOS-/Android-Apps** – OpenAmer hat **keine** mobile App; (b) **„Companion Apps and Nodes"** mit Voice, Canvas, Kamera, Bildschirm und device-lokalen Aktionen; (c) **Team-/Shared-Deployment** als Konfigurationsunterschied desselben Gateways; (d) **Control UI** (Web-UI mit echtem Chat-Fokus) + TUI; (e) **Pairing-Approval-Flow** für unbekannte Absender (`openclaw pairing approve <channel> <code>`) – in OpenAmer existiert das Konzept, aber nicht als Channel-Pairing-Protokoll; (f) **Gründungsorganisation (OpenClaw Foundation, 501(c)(3))** mit OpenAI als Donor – massiver Vertrauensvorsprung; (g) **ClawHub** als öffentlicher Skill-/Plugin-Marktplatz mit offenem Plugin-SDK; (h) **dokumentierte Telemetrie-Politik** (`update.checkOnStart: false`); (i) **Canvas**-UI-Konzept; (j) **40× höhere Star-Zahl** (392k vs. 8).

### 26. Agent Zero
- **Repo:** https://github.com/agent0ai/agent-zero — **19.525 ★** — Python, NOASSERTION
- **Kern-Feature:** Agent-Framework mit **dockerisiertem Linux-Desktop** (XFCE), Browser mit DOM-Annotation, Live-Dokument-Co-Work und Host-Bridge.
- **Was OpenAmer fehlt:** (a) **Vollständiger Linux-Desktop im Container**, in dem der Agent echte GUI-Software (Blender, Office) bedient – OpenAmer steuert den *Host*-Desktop, nicht eine isolierte GUI-Welt; (b) **DOM-Annotation** im Browser (Elemente labeln, nicht nur screenshotten); (c) **A0 Launcher** als eigene Desktop-App (Docker/Ports/Instanzen verwalten); (d) **Plugin Hub** mit 100+ Community-Plugins; (e) **transparente, editierbare Internals** (Prompts/Tools/Skills/Settings im UI) – OpenAmer ist stärker bei „hartem" Lernen, schwächer bei „transparenter Inspektion".

### 27. Khoj
- **Repo:** https://github.com/khoj-ai/khoj — **37.762 ★** — Python, AGPL-3.0
- **Kern-Feature:** Persönliche „Second Brain"-App, die sich von On-Device bis Enterprise-Cloud skaliert.
- **Was OpenAmer fehlt:** (a) **Editor-Integrationen** (Obsidian, Emacs) – OpenAmer hat keinen Plugin für Fremd-Editoren; (b) **Telefon-/WhatsApp-Zugriff** (Eingangsweg, nicht nur Ausgabekanal); (c) **Enterprise-/Hybrid-Deployment** (Khoj Teams) mit Datenresidenz; (d) **Obsidian-MD-Graph-Integration** (Themen-Graph, nicht nur Embeddings); (e) **datenschutzfreundliche AGPL-Positionierung** für On-Device-Nutzer.

### 28. Open Interpreter
(siehe Abschnitt A/12 – Coding-Agent-Fokus, Low-Cost-Modell-Harness)

---

## F. Lokale Modell-Infrastruktur

### 29. Ollama
- **Repo:** https://github.com/ollama/ollama — **184.064 ★** — Go, MIT
- **Kern-Feature:** Standard-Runtime für lokale und Cloud-Modelle mit REST-API.
- **Was OpenAmer fehlt:** (a) **Ollama Cloud** (Modelle in der Cloud) – OpenAmer ist strikt lokal; (b) **extrem große Verbreitung** → Ökosystemeffekt: `ollama` ist *der* De-facto-Standard, OpenAmer ist nur ein Consumer; (c) **First-Class-Partner-Rollen**: Ollama wirbt aktiv mit Claude Code, OpenClaw, OpenCode, Codex, Copilot als Clients; (d) **eigene Cloud-Model-Registry** mit API-Key-Management; (e) **Update-/Model-Curriculum-UX** (`ollama pull` als Einstieg).
- *Nicht-Gap:* OpenAmer nutzt Ollama bereits als lokalen Provider.

### 30. LocalAI
- **Repo:** https://github.com/mudler/LocalAI — **49.796 ★** — Go, MIT
- **Kern-Feature:** Open-Source-AI-Engine für alle Modelltypen (LLM, Vision, Voice, Image, Video) – ohne GPU, mit OpenAI-kompatibler API.
- **Was OpenAmer fehlt:** (a) **Multimodal-Server**: TTS, STT, Image- und Video-Generierung **im selben Server** – OpenAmer delegiert TTS an externe Provider (ElevenLabs/OpenAI/Neural); (b) **MCP-Server-Modus** von LocalAI (Agenten können LocalAI-Tools nutzen); (c) **libp2p-basierte verteilte Inferenz** über mehrere Nodes; (d) **GPU-loser CPU-Betrieb** → OpenAmer braucht für lokale Modelle zwingend GPU/Cloud; (e) **Mamba/alternative Architekturen** nativ.

---

## G. Chat-UIs / Plattformen (Web-Oberfläche als Hauptprodukt)

### 31. LobeHub (früher LobeChat)
- **Repo:** https://github.com/lobehub/lobehub — **83.362 ★** — TypeScript, NOASSERTION
- **Kern-Feature:** „Chief Agent Operator" – organisiert Agenten in 7×24-Betrieb, mit Agent Builder, Agent Groups, Workspace und 10.000+ Skills.
- **Was OpenAmer fehlt:** (a) **10.000+ Skill-Bibliothek** + MCP-kompatible Plugins – OpenAmer hat 259 Skills; (b) **Agent Groups** (assembliert mehrere Agenten ad hoc für eine Aufgabe, parallele Kollaboration); (c) **Workspace** als Shared Space für Teams (klare Ownership + Sichtbarkeit); (d) **reifes Plugin-Ökosystem** mit eigenem SDK, Template-Repo und Gateway-Service (Vercel Edge) – OpenAmer-Hub hat keine öffentliche Plugin-Entwicklung; (e) **polierte Web-Oberfläche** als Kern-Produkt; (f) **Agent-Hiring/Scheduling/Reporting** als UI-Metapher.

### 32. AnythingLLM
- **Repo:** https://github.com/Mintplex-Labs/anything-llm — **67.359 ★** — JavaScript, MIT
- **Kern-Feature:** All-in-One-„privater ChatGPT" mit Agenten, RAG, Multi-User und Mobile-App – läuft lokal per Default.
- **Was OpenAmer fehlt:** (a) **AnythingLLM Mobile (Android, open source)** – separates offizielles Mobile-Repo; (b) **Multi-User-Instanzen mit Permissioning** (Docker-Variante) – OpenAmer hat keine Granularrechte; (c) **PostHog-Telemetrie mit Opt-out** (`DISABLE_TELEMETRY`) als Transparenz-Muster; (d) **Dokument-Pipelines** (Ingestion, Chunking, Vektor-DBs) als fertiges Produkt; (e) **hermes-agent / agent-computer / agent-orchestration** Topics – Spezial-Agenten-Bibliothek; (f) **CDN-Mirror für Modelle** (VPN-Regionen).

### 33. Open WebUI
- **Repo:** https://github.com/open-webui/open-webui — **156.293 ★** — Python, NOASSERTION
- **Kern-Feature:** Self-hosted „Zuhause für AI" – komplett offline, provider-agnostisch, mit Terminal-Agenten und Kanälen.
- **Was OpenAmer fehlt:** (a) **Granulares RBAC + User Groups** (Rollen, Gruppen, Permissions pro User) – OpenAmer hat **kein** RBAC; (b) **Channels** (Echtzeit-Shared-Spaces, Threads, Reactions, Pins, Access-Control) – OpenAmer hat Chat-Kanäle, aber keine Team-Spaces; (c) **Open Terminal + isolierte Terminals pro User** (Enterprise: Ressourcenlimits, Auto-Lifecycle) – OpenAmer hat `code_kernel`, aber keine mandantenfähige Terminal-Isolation; (d) **PWA/mobile Responsiveness** mit Offline-Fähigkeit; (e) **Hands-Free Voice/Video-Calls** mit mehreren STT- (Whisper lokal, Deepgram, Azure) und TTS-Engines; (f) **Filter/Actions/Pipes/Tools/Skills** als Plugin-Architektur; (g) **MCPO** (MCP-over-HTTP) – OpenAmer hat MCP, aber kein MCPO; (h) **native Ollama-Integration** als Kern.

### 34. LibreChat
- **Repo:** https://github.com/LibreChat-AI/LibreChat — **46.081 ★** — TypeScript, MIT
- **Kern-Feature:** Enterprise-fähiger ChatGPT-Clone mit Agents, MCP, Skills, Artifacts, Code Interpreter und Multi-User-Auth.
- **Was OpenAmer fehlt:** (a) **Agent Marketplace** (Community-Agents entdecken und deployen) – OpenAmer-Marktplatz existiert, ist aber nicht kuratiert/öffentlich; (b) **Code-Approval-Modi Ask / Allow / Deny** (plus „Full access" für vertrauenswürdige Umgebungen) als *dokumentierte* Admin-Richtlinie – OpenAmer hat Modi, aber ohne Rollen-Sperre; (c) **Agent Management API** (CRUD über Agents, Dateien, Skills) mit **deployment-gebundenen OIDC-Identitäten** und OpenAPI/Swagger-UI; (d) **Checkpoint-Recovery für Agents** (Agent-Continuation + Checkpoint-Wiederherstellung); (e) **Redis-Liveness-Detection, DocumentDB-Koordination, Tenant-Isolation, Shared-Link-Throttling** – klassische Multi-Tenant-Härtung, die OpenAmer fehlt; (f) **MCP OAuth Sessions**; (g) **Artifacts** (reproduzierbare Code-/Doku-Artefakte) als UI-Feature.

### 35. n8n
- **Repo:** https://github.com/n8n-io/n8n — **208.154 ★** — TypeScript, NOASSERTION (Fair-Code / Sustainable Use License)
- **Kern-Feature:** Workflow-Automation-Plattform mit visuellem Canvas + Code, 1500+ Integrationen und AI-Agenten-Fähigkeiten.
- **Was OpenAmer fehlt:** (a) **1.500+ Integrationen** und 9.000+ Workflow-Templates – OpenAmer hat 122 Tools, aber keine Integrations-Bibliothek; (b) **visueller Canvas** für Nicht-Entwickler; (c) **Human-Approvals** als Workflow-Knoten; (d) **Audit-Trails + RBAC** für Enterprise; (e) **kommerzielle SaaS-Cloud** (n8n Cloud) neben Self-Host; (f) **Fair-Code-Lizenzmodell** mit Sustainability-Äquivalent; (g) **Community-Größe** (~208k Stars).

### 36. Dify
- **Repo:** https://github.com/langgenius/dify — **159.057 ★** — Python, NOASSERTION
- **Kern-Feature:** LLM-App-Entwicklungsplattform mit Workflow-Canvas, RAG-Pipeline, Agent-Sandbox, Model-Management und Observability.
- **Was OpenAmer fehlt:** (a) **Dify Marketplace** (Tool-Marktplatz) – OpenAmer-Hub hat keine öffentliche Tool-Registry; (b) **RAG-Pipeline als Produkt** (Dokumenten-Ingestion → Extraktion → Retrieval) mit PDF/PPT-Parsern; (c) **Observability-Integrationen** (Opik, Langfuse, Arize Phoenix) – OpenAmer hat keinen OTEL-Export; (d) **Agent mit eigenem Sandbox** (Befehle ausführen, Software installieren, Dateien verwalten) – abgegrenzt pro Agent; (e) **Cloud/VPC/Self-Host-Deployment-Tiers** für Teams; (f) **Modell-Management** (ein Provider-Deck für alle Workflows).

### 37. Flowise
- **Repo:** https://github.com/FlowiseAI/Flowise — **55.511 ★** — TypeScript, NOASSERTION
- **Kern-Feature:** Visueller Drag-and-Drop-Builder für AI-Agenten und Flows.
- **Was OpenAmer fehlt:** (a) **rein visuelle Agent-/Flow-Erstellung** ohne Text – OpenAmer braucht CLI/Prompt; (b) **Multi-Agent-Systems-Builder** als visuelles Feature; (c) **Flowise Cloud**; (d) **Self-Host-Deployment-Doku** als Erstes; (e) **Chatbot/Embed-Widget** als fertiges Deliverable.
- *Hinweis:* Letzter Push 2026-08-13 – Projekt aktiv, aber deutlich langsamer als Dify/Langflow.

### 38. Langflow
- **Repo:** https://github.com/langflow-ai/langflow — **155.868 ★** — Python, MIT
- **Kern-Feature:** Plattform für visuelle Agent-/Workflow-Autorenschaft, die jeden Flow **als MCP-Server** und API bereitstellt.
- **Was OpenAmer fehlt:** (a) **„Deploy as MCP-Server"** – jeder Flow wird ein Tool für MCP-Clients; OpenAmer kann MCP nur *konsumieren*, nicht eigenen Flows als MCP-Server anbieten (eigener `mcp_serve.py` existiert, aber nicht als Flow-Feature); (b) **React-Flow-Canvas** mit sofort teilbaren, versionierten Flows; (c) **Multi-Agent-Orchestrierung** mit Conversation-Management und Retrieval; (d) **Superuser-Admin-Passwort-Setup** (dokumentierter Deployment-Pfad); (e) **große Star-Zahl** (~156k) bei rein visueller Zielgruppe.

---

## H. Gesamtbewertung

### Die fünf schärfsten Wettbewerber für OpenAmer
| # | Wettbewerber | Stars | Warum er OpenAmer direkt angreift |
|---|---|---|---|
| 1 | **OpenClaw** | 392.676 | Identische Produktdefinition (lokaler Agent + 20+ Channels + Skills + Plugins) **plus** iOS-/Android-Apps, Team-Deployment, Foundation, ClawHub-Marktplatz. |
| 2 | **OpenHands / Agent Canvas** | 91.411 | Kontrollzentrum für *beliebige* ACP-Agenten + Self-Hosting + Automationen. |
| 3 | **Goose (AAIF)** | 55.462 | Gleiche Zielgruppe, native Rust-Desktop-App, ACP-Abo-Auth, 70+ MCP-Extensions, Foundation. |
| 4 | **OpenCode** | 218.852 | De-facto-Open-Source-Referenz; 27.000× mehr Community. |
| 5 | **Open WebUI / LibreChat / AnythingLLM** | 46k–156k | Multi-User, RBAC, Mobile, Voice/Video, MCP-Ökosystem – genau die Lücken von OpenAmer. |

### Geschätzete Nachrüst-Priorität für OpenAmer
| Priorität | Feature | Begründung |
|---|---|---|
| **P0** | **Mobile-App (iOS/Android)** | OpenClaw + AnythingLLM haben sie; OpenAmer hat *keine*. Einziger echter „Missing Core Surface". |
| **P0** | **Community/Stars** (8 → 1.000+) | Größter Einzelunterschied zu allen Wettbewerbern; ohne Doku/Story kein Durchbruch. |
| **P1** | **Granulares Multi-User-RBAC + Tenant-Isolation** | Open WebUI, LibreChat, n8n, Agno, Chatwoot haben es; OpenAmer hat keinerlei Rollenmodell. |
| **P1** | **OpenTelemetry-Export** | Einzeilig umzusetzen, schließt Lücke zu Pydantic AI, LangGraph, CrewAI, Mastra, Dify. |
| **P1** | **Standard-A2A-Agent-Card** (`/.well-known/agent-card.json`) | OpenAmer hat schon 26 A2A-Module – nur die Spec-Konformität fehlt, um mit AutoGen/MAF, Agno, CrewAI interoperabel zu sein. |
| **P2** | **Eval-/Benchmark-Harness** | Nötig, um OpenAmer gegen OpenHands/SWE-agent messbar zu machen. |
| **P2** | **Visueller Flow-Canvas** (à Dify/Langflow) | Einzige fehlende „Surface" gegenüber der No-Code-Fraktion. |
| **P2** | **Dauerhafte Delegation** (Temporal/DBOS-Review) | `delegate_task` stirbt mit dem Parent-Prozess – dokumentierte Schwachstelle. |
| **P3** | **Native LSP-Integration** | Crush-Niveau bei Code-Kontextqualität. |
| **P3** | **Budget-Limits / Kosten-Alarme** | Pydantic-AI-Gateway-Niveau. |

### Wo OpenAmer **stärker** bleibt (Vorsprung, nicht Lücke)
- **Selbst-lernende Skills** (Curator, Darwin-Engine) – kein Wettbewerber hat Skill-Lifecycle-Automatisierung.
- **Windows-Native** (PTY-Bridge, Voice, Computer-Use) – die meisten Wettbewerber sind macOS/Linux-first.
- **A2A-Mesh mit Lern-Netzwerk** (mesh_learning, beacon, trust, privacy) – einzigartig in dieser Tiefe.
- **Memory + Skills + Delegation + Cron + Kanban in einem Paket** – Wettbewerber decken jeweils 2–3 Facetten ab.
- **Privacy-by-default** (Secrets-Redaction vor Speicherung, Telemetrie standardmäßig aus).
- **Selbstmodifikation mit Test-Gate** + atomarem Rollback.

---

## Anhang: Verifikationsprotokoll

- **Sternzahlen/URLs/Lizenzen:** `GET https://api.github.com/repos/<owner>/<repo>`, 44 Repos + 4 Nachprüfungen, alle HTTP 200, 21.10.2026.
- **Feature-Angaben:** offizielle READMEs via `raw.githubusercontent.com` (Default-Branch je Repo geprüft; `master` vs. `main` bei 6 Repos unterschiedlich).
- **OpenAmer-Baseline:** lokale Quellcode-Inspektion (`grep`/`find`) in `C:\Users\amer7\AppData\Local\openamer\openamer-agent`, nicht README-Selbstauskunft.
- **Redirects verifiziert:** `sst/opencode` → `anomalyco/opencode` (HTTP 301); `getzep/zep` ist nur noch Beispiel-Repo, Kern ist `getzep/graphiti` (32.085 ★); `letta-ai/letta` verweist auf `letta-ai/letta-code`; `continuedev/continue` ist read-only (kein Wettbewerber).
- **Nicht verifiziert / als unbestätigt markiert:** genaue Download-Zahlen, Enterprise-Feature-Tiefe hinter Paywalls (n8n, Dify Cloud, CrewAI AMP, Letta Cloud, Open WebUI Enterprise, Browser Use Cloud), sowie alle Preise – nur die öffentlich im README genannten ($0.02/Std. Browser Use Cloud, $0.02/hr-Stealth-Browser) wurden übernommen.
- **Grenze der GitHub-API:** 60 unauthentifizierte Requests/h; alle Daten stammen aus einem Fenster von ~15 Minuten um 2026-10-21 00:37–00:50 UTC.
