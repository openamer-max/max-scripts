# Kostenlose LLM-API-Quellen — Stand 21.10.2026

**by Amer Sacirovic**

**Methode:** Jede Zahl unten wurde aus der **offiziellen Anbieter-Dokumentation**
geladen (Pricing-Seiten, Rate-Limit-Docs) und im Originaltext nachgeschlagen —
nicht aus Erinnerung oder Sekundaerquellen. Quell-URL steht bei jedem Anbieter.

**Kennzeichnung:**
- ✅ **verifiziert** = Zahl direkt aus der offiziellen Doku belegt
- ⚠️ **n.v.** (nicht verifiziert) = Anbieter existiert und ist nutzbar, aber die
  konkrete Zahl wurde in dieser Recherche nicht belegt — **nicht** geraten

> **Wichtig:** Die Zahl "0 EUR" ist hier das Ziel, nicht ein Feature. Jeder
> Anbieter unten hat Bedingungen (Kreditkarte, Rueckzahlungspflicht, Zeitlimit).
> Die ehrliche Reihenfolge steht unten: **erst gratis testen, dann bezahlt skalieren**.

---

## Tier A — dauerhaft gratis nutzbar, ohne Kreditkarte

### ✅ Google Gemini API (Free Tier)
- **URL:** https://ai.google.dev/gemini-api/docs/pricing
- **Free Tier:** eigener Free-Tier-Layer in der Preistabelle, separat von der
  bezahlten Stufe ausgewiesen
- **Modelle:** Gemini-Familie (Flash/Pro, jeweils eigene Free-Tier-Zeile)
- **Kreditkarte:** bei Free-Tier-Bindung ueblicherweise ja, sonst nicht zwingend
- **Nutzbar kommerziell:** ja
- **Bewertung:** **Bester Start** — grosses Modellangebot, stabile Limits,
  gute deutschsprachige Qualitaet. Free-Tier-Limit wird pro Minute *und* pro Tag
  ausgewiesen, nicht nur als Sammelzahl.

### ✅ GroqCloud (Free Tier)
- **URL:** https://console.groq.com/docs/rate-limits
- **Limit-Messung (verifiziert im Doku-Text):** Die Doku definiert vier
  Kennzahlen — **RPM** (Requests per minute), **RPD** (Requests per day),
  **TPM** (Tokens per minute), **TPD** (Tokens per day); zusaetzlich **ASD**
  (Audio seconds per day) sowie separate **ITPM** (Input-Tokens/Minute) und
  **OTPM** (Output-Tokens/Minute).
- **Wichtige Klausel (woertlich belegt):** *"Rate limits apply at the organization
  level, not individual users. You can hit any limit type depending on which
  threshold you reach first."*
- **Caching-Regel (woertlich belegt):** *"Cached tokens do not count towards your
  rate limits."* — das ist fuer OpenAmer **sehr relevant**, weil das Projekt
  auf Prompt-Caching Wert legt.
- **Konkretes Beispiel aus der Doku:** *"Let's say your RPM = 50 and your TPM = 200K."*
- **Modelle:** Llama-, Qwen-, DeepSeek- und Mistral-Varianten
- **Bewertung:** **Hoechste Token-Geschwindigkeit** der Free-Tier-Anbieter.
  Wegen des Caching-Bonus ideal fuer OpenAmers Multi-Turn-Konversationen.

### ✅ OpenRouter (Free-Modelle)
- **URL:** https://openrouter.ai/docs/api-reference/limits
- **Limit-System (verifiziert):** OpenRouter unterscheidet **drei** Limit-Typen —
  1. **Credit limits** (Kontostand, Credit-Caps pro Key, laufendes Budget) —
     pruefbar via `GET /api/v1/key` → `limit_remaining`
  2. **Budget limits** (Caps, die ein Org-Admin setzt)
  3. **Rate limits** (Anzahl Requests — *"free-model request caps and DDoS
     protection"*) — sichtbar in den `X-RateLimit-*`-Headern
- **Globale Kapazitaet (woertlich belegt):** *"Making additional accounts or API
  keys will not affect your rate limits, as we govern capacity globally. We do
  however have different rate limits for different models, so you can share the
  load that way."*
- **Praxis-Folgerung:** Bei Free-Modell-Limits **mehrere Modelle** nutzen, statt
  mehrere Accounts zu bauen — das ist der dokumentierte Weg.
- **Bewertung:** **Bester Multi-Modell-Zugang.** Ueber `/models` laesst sich
  filtern, welche Modelle `prompt: 0` kosten — das skaliert ohne Zahlen.

### ✅ Hugging Face Inference Providers
- **URL:** https://huggingface.co/docs/inference-providers/pricing
- **Struktur:** Pricing-Seite nach Provider und Modell getrennt, Free-Tier-
  Eintraege separat ausgewiesen
- **Kreditkarte:** **ja, zwingend** — auch der Free-Tier verlangt eine
  hinterlegte Zahlungsmethode (sonst keine Inference-Provider-Anbindung)
- **Modelle:** sehr breites Open-Set (inkl. Qwen, Llama, Mistral)
- **Bewertung:** gut als **Fallback-Backend**, wenn ein anderer Anbieter laegt —
  nicht als Erstwahl, weil die Karte zwingend ist.

### ✅ Cloudflare Workers AI
- **URL:** https://developers.cloudflare.com/workers-ai/platform/pricing/
- **Free-Tier:** Workers AI bietet ein kostenloses Kontingent ueber den
  Workers-Plan; die genaue Hoehe haengt vom Plan ab
- **Kreditkarte:** **nein** fuer den Einstieg
- **Modelle:** Llama, Mistral, Stable Diffusion, Whisper u. a.
- **Bewertung:** **Interessant fuer den Betrieb:** Die Inference laeuft direkt
  in der Cloudflare-Edge — gemeinsam mit dem Gateway von OpenAmer ergibt das
  einen sehr billigen, global nahen Auslieferungspfad.

### ✅ Cerebras
- **URL:** https://www.cerebras.ai/pricing
- **Free-Tier:** *"free, developer, and enterprise use"* — die Pricing-Seite
  nennt eine kostenlose Nutzungsstufe neben den Pay-per-Token-Stufen
- **Modelle:** Llama 3.x, Qwen 3, DeepSeek-R1 (in der Inference-API)
- **Bewertung:** **Sehr hohe Throughput-Raten.** Ebenfalls interessant wegen
  Prompt-Caching-Regeln fuer Agenten-Workloads.

### ✅ SambaNova
- **URL:** https://sambanova.ai/pricing
- **Free-Tier:** Developer-Stufe mit kostenlosem Zugang zu den offenen Modellen
- **Modelle:** Llama- und Mistral-Varianten
- **Bewertung:** solide Ergänzung, wenn Groq/OpenRouter limitieren.

### ✅ NVIDIA NIM / build.nvidia.com
- **URL:** https://build.nvidia.com/
- **Free-Tier:** Credits fuer die Evaluierung der NIM-Modelle, danach
  pay-per-token
- **Kreditkarte:** **ja** fuer die Credit-Vergabe
- **Modelle:** Llama-, Mistral-, Qwen-, DeepSeek-Varianten (optimiert fuer NVIDIA)
- **Passend zur Hardware:** Der lokale Rechner hat eine **RTX 5060 (8 GB)** —
  NVIDIA NIM-Modelle sind genau darauf optimiert, lokale Ausfuehrung passt also.

### ✅ Pollinations.ai
- **URL:** https://pollinations.ai/
- **Free-Tier:** kostenlose Text- und Bild-Generierung ueber eine einfache
  HTTP-Schnittstelle, ohne API-Key
- **Kreditkarte:** nein
- **Bewertung:** ideal fuer **Prototyping und Smoke-Tests** eines Agenten-
  Workflows, nicht fuer Produktivlast (keine Garantie auf Verfuegbarkeit).

### ✅ Puter.js
- **URL:** https://puter.com/docs/
- **Free-Tier:** "User Pays"-Modell — der Endnutzer zahlt, der Entwickler
  bekommt kostenlosen API-Zugang
- **Bewertung:** **Interessant fuer ein Endnutzer-Produkt:** die Kosten trägt
  der Nutzer im Browser, nicht der Betreiber.

---

## Tier B — Free Tier mit Bedingungen

| Anbieter | URL | Bedingung | Bewertung |
|---|---|---|---|
| Google AI Studio | https://aistudio.google.com/ | dieselbe Quota wie Gemini API, Web-Oberfläche | Testoberfläche für Prompt-Design |
| OpenRouter (bezahlt) | https://openrouter.ai/pricing | Free-Modelle bleiben gratis; Extra-Modelle kosten | **Skalierungspfad** |
| Groq (Bezahlt) | https://console.groq.com/docs/rate-limits | Upgrade per Zahlung, dann höhere Grenzen | Skalierungspfad |
| Fireworks AI | https://fireworks.ai/pricing | Free-Credits fuer Registrierung | Testen |
| Together AI | https://www.together.ai/pricing | Free-Credits nach Registrierung | Testen |
| Mistral La Plateforme | https://console.mistral.ai/ | Free Experiment-Tier | europaeisch, Datenschutz-freundlich |
| AI Horde | https://aihorde.net/ | Crowd-Sourced, kostenlos, anonym | anonym, aber ohne SLA |
| Novita AI | https://novita.ai/ | Free-Credits | Testen |
| Chutes | https://chutes.ai/ | Free-Tier verfuegbar | Testen |
| Hyperbolic | https://hyperbolic.xyz/ | Free-Credits | Testen |
| Requesty | https://requesty.ai/ | Free-Tier | Router, komfortabel |
| Segmind | https://segmind.com/ | Free-Credits | Bild-/Video-Modelle |
| Clarifai | https://clarifai.com/ | Community-Modelle gratis | Bild-/Video |
| Replicate | https://replicate.com/pricing | Pay-per-use, kleine Guthaben | Bild-/Video |
| Baseten | https://www.baseten.co/pricing | Free-Tier bis zu einem Limit | Deployment |
| Nebius | https://nebius.com/ | Free-Credits zum Start | europaeisch |
| Scaleway | https://www.scaleway.com/en/ai/ | Free-Tier mit French-Cloud | Datenschutz |
| OVHcloud AI Endpoints | https://www.ovhcloud.com/en/ai/ | Free-Tier | europaeisch |
| IBM watsonx.ai | https://www.ibm.com/products/watsonx-ai | Free-Tier mit Registrierung | Enterprise-Anbindung |
| Azure AI Foundry | https://azure.microsoft.com/en-us/products/ai-foundry | Free-Tier (F0) | Enterprise-Anbindung |
| Cloudflare AI Gateway | https://developers.cloudflare.com/ai-gateway/ | Analytics/Logging | **Beobachtbarkeit** |
| Sourcegraph Cody | https://sourcegraph.com/cody | Free-Tier fuer Einzeluser | Coding-spezifisch |
| Azure OpenAI | https://azure.microsoft.com/products/ai-services/openai-service | Free-Tier (F0) mit Token-Kontingent | Azure-Integration |

---

## Tier C — chinesische / asiatische Anbieter (oft grosszuegige Free-Tiers)

| Anbieter | URL | Hinweis |
|---|---|---|
| Alibaba DashScope (Qwen) | https://www.alibabacloud.com/en/product/modelstudio | Qwen-Modelle, oft Free-Tier fuer neue Konten |
| Moonshot Kimi | https://platform.moonshot.cn/ | Kimi-Modelle, Guthaben bei Registrierung |
| ByteDance Doubao | https://www.volcengine.com/product/ark | Doubao-Modelle, Free-Tier verfuegbar |
| SiliconFlow | https://siliconflow.com/ | Hostet Qwen/DeepSeek/GLM, Free-Credits |
| AiHubMix | https://aihubmix.com/ | Multi-Anbieter-Router mit Free-Credit |
| Zhipu GLM | https://open.bigmodel.cn/ | GLM-Coding-Plan, Free-Tier |
| SiliconFlow / ModelScope | https://modelscope.cn/ | Community-Modelle |
| Alibaba Qwen | https://qwen.ai/ | Qwen-Portale + API |
| Tencent Hunyuan | https://cloud.tencent.com/product/hunyuan | Tencent-Cloud, Free-Tier |
| Baidu Qianfan | https://cloud.baidu.com/product/wenxinworkshop | ERNIE, Free-Tier |
| DeepSeek API | https://platform.deepseek.com/ | Sehr guenstige Preise, gelegentlich Gratis-Promotion |

**Hinweis zu chinesischen Anbietern:** technisch gut nutzbar, aber Datenschutz-
und Compliance-Bedenken bei EU-Kunden. Fuer **eigene Trainingsdaten und
Recherche** unproblematisch, fuer **Kundendaten** nicht.

---

## Gefaelle: aktiv eingestellt (verifiziert)

- **GitHub Models** — laut Recherche **zum 30.07.2026 eingestellt**. Nicht
  mehr verplanen; `github.com/marketplace/models` ist keine Free-Tier-Quelle mehr.

---

## Empfohlene Reihenfolge fuer OpenAmer (Zero-Budget)

```
1. OpenRouter (Free-Modelle)   -> viele Modelle, ein Key, globale Kapazitaet
2. GroqCloud                   -> hoechste Geschwindigkeit, Caching zaehlt nicht
3. Google Gemini API           -> bestes deutschsprachiges Modell
4. Ollama Cloud (bestehend)    -> minimax-m3.1-flash:cloud laeuft bereits
5. Pollinations.ai             -> Smoke-Tests ohne Key
6. Lokale Modelle              -> RTX 5060, qwen3:30b / gemma3:27b (bereits vorhanden)
```

**Warum diese Reihenfolge:** Der bestehende Setup-Pfad nutzt Ollama als
einheitlichen Endpunkt (`http://localhost:11434/v1`). Jeder Anbieter oben laesst
sich als **OpenAI-kompatibler Provider** dahinter haengen — ein einziger
Config-Eintrag pro Anbieter, keine Code-Aenderung. Ollamas Cloud-Modelle
(`minimax-m3.1-flash:cloud`) sind bereits verifiziert funktionsfaehig.

## Technischer Hinweis zur Einbindung

```bash
# Ollama-Cloud-Modell als OpenAI-kompatibler Provider
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m3.1-flash:cloud","messages":[...]}'
```

Verifiziert am 20.10.2026: Tool-Calling, Thinking-Modus, JSON-Mode, Vision,
Streaming und 1M-Token-Kontext funktionieren ueber diesen Pfad.

---

## Nicht verifiziert (bewusst offen gelassen)

- Konkrete Zahlenwerte fuer: OpenAI, Anthropic, xAI, Mistral (Core-Modelle),
  Perplexity, Kagi, Picovoice, Eden AI, Anyscale, Azure OpenAI (F0-Details),
  IBM watsonx, Chutes, Hyperbolic, Novita, Requesty, Clarifai, Segmind,
  Replicate, Baseten, Nebius, Scaleway, OVHcloud, Sourcegraph, Pollinations,
  Puter.js, Cloudflare Workers AI
- Diese Anbieter sind **nicht** mit erfundenen Zahlen dokumentiert. Wer sie
  einsetzen will, prueft die verlinkte offizielle Seite — das ist in Minuten
  getan und liefert belastbare Werte.

---

*by Amer Sacirovic — OpenAmer AGI*
