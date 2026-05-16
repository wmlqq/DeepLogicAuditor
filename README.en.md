<div align="center">

# DeepLogicAuditor

**Academic Paper Logic Audit Agent**

Slice papers, build semantic graphs, and audit logical consistency with NLI models and rule-based checks.

[![License: MIT](https://img.shields.io/github/license/wmlqq/DeepLogicAuditor?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/wmlqq/DeepLogicAuditor/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/wmlqq/DeepLogicAuditor/actions)

**[简体中文](README.md)**

</div>

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📄 **Paper Slicing** | Split Markdown papers into proposition-level segments |
| 🧠 **Semantic Modeling** | NLI-based entailment / neutral / contradiction detection |
| 🔍 **Logic Audit** | Contradictions, unsupported claims, missing transitions |
| 🔗 **Integrated Audit** | Load papers from PostgreSQL, score with LOG-001–LOG-007, persist results |
| 🌐 **REST API** | FastAPI endpoints with interactive Swagger UI |

---

## 🛠 Tech Stack

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"/>
  <img src="https://img.shields.io/badge/🤗_Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Transformers"/>
  <img src="https://img.shields.io/badge/NetworkX-2C5BB4?style=for-the-badge" alt="NetworkX"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge" alt="Pydantic"/>
</p>

| Layer | Technology | Role |
|-------|------------|------|
| Runtime | Python 3.10+ | Core language |
| Web | FastAPI · Uvicorn | REST API & ASGI server |
| NLP | PyTorch · Transformers | [`cross-encoder/nli-deberta-v3-base`](https://huggingface.co/cross-encoder/nli-deberta-v3-base) |
| Graph | NetworkX | Semantic relation graphs |
| Data | PostgreSQL · psycopg2 | Papers, rules, audit results |
| Config | python-dotenv | Environment variables |

---

## 🏗 Architecture

```mermaid
flowchart LR
    DB[(PostgreSQL)] --> Slicer[Paper Slicer]
    Slicer --> Semantic[Semantic NLI]
    Semantic --> Auditor[Logic Auditor]
    Auditor --> API[FastAPI]
    API --> DB
    API --> Output[(output/ JSON)]
```

```
Paper in DB → Slicing → Semantic modeling → Logic audit → DB + local JSON
```

---

## 📁 Project Layout

```
DeepLogicAuditor/
├── src/
│   ├── config.py
│   ├── database_connector.py
│   ├── logic_auditor/          # FastAPI entry & audit core
│   ├── semantic/               # NLI semantic modeling
│   └── slicer/                 # Paper slicing
├── prompts/keywords.json
├── tests/test_three_modules.py
├── docs/GITHUB_UPLOAD.md
├── .env.example
├── requirements.txt
└── run_api.py
```

---

## 🚀 Quick Start

**Requirements:** Python 3.10+ · PostgreSQL 12+ · (optional) CUDA

```bash
git clone https://github.com/wmlqq/DeepLogicAuditor.git
cd DeepLogicAuditor
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / macOS
```

Edit `.env` with your database credentials. Optional: `HF_MIRROR`, `MODEL_CACHE_DIR`, `OUTPUT_DIR`.

```bash
python run_api.py
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Integration test (requires paper data in the database):

```bash
python tests/test_three_modules.py
```

---

## 📡 API Overview

| Method | Path | Description |
|:------:|------|-------------|
| `POST` | `/audit/integrated?paper_id={uuid}` | Full audit pipeline from database |
| `POST` | `/audit/paper` | Audit a proposition graph (JSON body) |
| `POST` | `/audit/logic` | Audit a single text chunk |

<details>
<summary><b>Integrated audit rules (LOG-001–LOG-007)</b></summary>

| Rule ID | Name |
|---------|------|
| LOG-001 | Five-part abstract structure |
| LOG-002 | Three-level logic closure |
| LOG-004 | Terminology consistency |
| LOG-005 | Related-work section flow |
| LOG-006 | Experiments answer research questions |
| LOG-007 | Innovation count in conclusion |

</details>

---

## 🤖 Models & Cache

On first run, the NLI model is downloaded to `src/model_cache/` (override with `MODEL_CACHE_DIR`). **Do not commit model weights.**

```env
HF_MIRROR=https://hf-mirror.com
```

---

## 📄 License

[MIT License](LICENSE)

---

<div align="center">

**[简体中文](README.md)** · [Report an issue](https://github.com/wmlqq/DeepLogicAuditor/issues) · [Actions](https://github.com/wmlqq/DeepLogicAuditor/actions)

**Star ⭐ if this project helps you**

</div>
