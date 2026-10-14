# AI-Assisted Cybersecurity Incident Report and Risk Analyzer

A small final-year project that turns a free-text cybersecurity incident into validated structured facts, a transparent risk rating, and a downloadable incident report. It uses Streamlit, Pydantic, an OpenAI-compatible LLM API or local Ollama, and editable YAML rules.

> **Advisory only:** The scoring is deterministic and intended to support human review. It must not replace an incident commander, security team, or legal/compliance decision.

## What it does

- Accepts a pasted or `.txt` incident description and an optional alerts `.csv`.
- Uses an LLM to return JSON matching a Pydantic schema, with one retry for invalid output.
- Flags CVEs and IoCs that cannot be found in the original source text after case/whitespace normalization.
- Calculates likelihood (1-5), impact (1-5), total score, and Low/Medium/High/Critical band from [`rules.yaml`](rules.yaml).
- Builds a Markdown report and PDF with Summary, Incident Details, Affected Assets, Indicators of Compromise, Risk Assessment, Recommended Actions, and Data Quality Notes.

## Setup (under 10 minutes)

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
2. In PowerShell, open this project directory and create an environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Choose one LLM provider. The included `.env` file is loaded automatically,
   so you only need to configure it once. It starts with local Ollama settings.
   Keep `.env` private; it is excluded from Git.

   OpenAI or another OpenAI-compatible API:

   ```powershell
   $env:LLM_PROVIDER = "openai"
   $env:LLM_MODEL = "gpt-4o-mini"
   $env:OPENAI_API_KEY = "your-api-key"
   # Optional for compatible providers:
   # $env:OPENAI_BASE_URL = "https://your-provider.example/v1"
   ```

   Local Ollama (start Ollama and pull a JSON-capable model first):

   ```powershell
   ollama pull llama3.2
   ```

   For OpenAI, edit `.env` and replace the Ollama values with the OpenAI block
   shown in that file. You do not need to enter environment variables in PowerShell.

4. Launch the app:

   ```powershell
   streamlit run app.py
   ```

5. Select one of the three demo incidents or paste your own, then choose **Analyze incident**.

## Run tests

```powershell
pytest -q
```

The tests do not make network calls: the extractor test mocks the LLM completion function.

## Project layout

```text
app.py                 Streamlit user interface
schema.py              Pydantic incident schema
extractor.py           Schema-guided LLM extraction
validator.py           Source traceability checks
risk.py / rules.yaml   Deterministic scoring and editable rules
report.py              Markdown report and PDF conversion
llm.py                 Minimal OpenAI-compatible/Ollama wrapper
data/samples/          Phishing, malware, and unauthorized-access demos
tests/                 Pytest coverage for core behavior
```

## Rule customisation

Edit `rules.yaml` to adjust likelihood points, sensitivity and impact bands, asset criticality keywords, or risk-band thresholds. The app reads it every time it analyzes an incident, so no code changes are needed.
