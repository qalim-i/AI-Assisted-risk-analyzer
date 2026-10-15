# AI-Assisted Cybersecurity Incident Report and Risk Analyzer

A Streamlit application that turns a free-text cybersecurity incident into structured, source-checkable facts, a transparent risk assessment, and downloadable reports. It combines an OpenAI-compatible API or local Ollama with Pydantic validation and editable YAML scoring rules.

> **Advisory only:** This tool supports human review. Its deterministic risk rating must not replace incident-response, legal, compliance, or executive decisions.

## Features

- Analyze a pasted incident description or uploaded UTF-8 `.txt` file.
- Optionally upload an alerts `.csv`; two or more alert rows contribute the configured repeated-events likelihood factor.
- Extract incident facts into a strict Pydantic schema, retrying once if the LLM returns invalid JSON.
- Check listed CVEs and indicators of compromise (IoCs) against the original source text after case, Unicode, and whitespace normalization.
- Show likelihood (1–5), impact (1–5), a combined score (2–10), the corresponding Low/Medium/High/Critical band, and every contributing factor.
- Generate a Markdown report, PDF report, and JSON analysis for download.
- Provide seven sample scenarios, including phishing, malware, ransomware/exfiltration, and cloud-account compromise.

## Requirements

- Python 3.11 or newer
- An LLM provider:
  - an OpenAI-compatible chat-completions API and API key, or
  - local [Ollama](https://ollama.com/) with a pulled model

## Setup

From PowerShell in the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Configure exactly one provider in `.env`. The application reads this file automatically when it starts; `.env` is ignored by Git, so do not commit credentials. The copy command preserves an existing `.env` file.

### OpenAI-compatible API

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=replace-with-your-key
# Optional: use a compatible endpoint instead of the provider default.
# OPENAI_BASE_URL=https://your-provider.example/v1
```

### Local Ollama

Pull a model first, then use the following configuration:

```powershell
ollama pull llama3.2
```

```dotenv
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

## Run the application

```powershell
streamlit run app.py
```

Select a sample or enter an incident description, optionally attach an alerts CSV, and select **Analyze incident**. The report, risk breakdown, extracted JSON, and data-quality warnings appear in the right-hand panel.

## How scoring works

The risk engine is deterministic. It starts with configured base values, adds or subtracts only the factors present in the extracted facts, clamps likelihood and impact to 1–5, then adds them for a final 2–10 score.

| Area | Inputs currently considered |
| --- | --- |
| Likelihood | External source, repeated alert events, containment status, and optional caller-supplied CVSS data for a high-severity CVE |
| Impact | Data sensitivity, affected-user count, service-disruption duration, and affected-asset criticality |
| Risk band | The final score and thresholds in `rules.yaml` |

The app does not fetch CVSS information or external threat intelligence. If a fact is absent from the source, the report surfaces a data-quality note instead of treating it as known.

## Configure rules

Edit [`rules.yaml`](rules.yaml) to change likelihood adjustments, data-sensitivity points, impact bands, asset-criticality keywords, or score thresholds. Rules are read for every analysis, so changes take effect without modifying code.

## Test

```powershell
pytest -q
```

The test suite is offline: it mocks LLM completions and verifies the extraction, validation, scoring, report, and PDF behavior.

## Project structure

```text
app.py                 Streamlit interface and downloads
schema.py              Strict Pydantic incident models
extractor.py           Schema-guided LLM extraction
llm.py                 OpenAI-compatible and Ollama completion wrapper
validator.py           Source traceability and completeness checks
risk.py                Deterministic scoring engine
rules.yaml             Editable scoring configuration
report.py              Narrative generation and Markdown/PDF rendering
data/samples/          Demonstration incident descriptions
tests/                 Offline test coverage
```
