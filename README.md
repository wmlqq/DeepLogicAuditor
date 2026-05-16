<div align="center">

# DeepLogicAuditor

**学术论文逻辑审计智能体**

对论文进行切片、语义建模与规则化逻辑审计，检测逻辑矛盾、逻辑跳跃、结构不完整等问题。

[![License: MIT](https://img.shields.io/github/license/wmlqq/DeepLogicAuditor?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/wmlqq/DeepLogicAuditor/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/wmlqq/DeepLogicAuditor/actions)

[快速开始](#-快速开始) · [API](#api-概览) · [架构](#-架构) · [文档](docs/GITHUB_UPLOAD.md)


</div>

---

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 📄 **论文切片** | 将 Markdown 论文切分为命题级片段 |
| 🧠 **语义建模** | 基于 NLI 模型识别命题间蕴含 / 中立 / 矛盾关系 |
| 🔍 **逻辑审计** | 检测矛盾陈述、无支撑论证、衔接词缺失等 |
| 🔗 **一体化审计** | 从 PostgreSQL 读取论文，按 LOG-001～LOG-007 规则评分并写回 |
| 🌐 **REST API** | FastAPI 提供 HTTP 接口，自带 Swagger 文档 |

---

## 🛠 技术栈

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"/>
  <img src="https://img.shields.io/badge/🤗_Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Transformers"/>
  <img src="https://img.shields.io/badge/NetworkX-2C5BB4?style=for-the-badge" alt="NetworkX"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge" alt="Pydantic"/>
</p>

| 层级 | 技术 | 说明 |
|------|------|------|
| 运行时 | Python 3.10+ | 主语言 |
| Web | FastAPI · Uvicorn | REST API 与 ASGI 服务 |
| NLP | PyTorch · Transformers | [`cross-encoder/nli-deberta-v3-base`](https://huggingface.co/cross-encoder/nli-deberta-v3-base) |
| 图分析 | NetworkX | 语义关系图构建 |
| 数据 | PostgreSQL · psycopg2 | 论文、规则与审计结果存储 |
| 配置 | python-dotenv | 环境变量管理 |

---

## 🏗 架构

```mermaid
flowchart LR
    DB[(PostgreSQL)] --> Slicer[论文切片]
    Slicer --> Semantic[语义建模 NLI]
    Semantic --> Auditor[逻辑审计]
    Auditor --> API[FastAPI]
    API --> DB
    API --> Output[(output/ JSON)]
```

```
数据库论文 → 切片模块 → 语义建模 → 逻辑审计 → 写回数据库 + 本地 JSON
```

---

## 📁 项目结构

```
DeepLogicAuditor/
├── src/
│   ├── config.py                 # 环境变量与路径
│   ├── database_connector.py     # 数据库访问
│   ├── logic_auditor/
│   │   ├── main.py               # FastAPI 入口
│   │   ├── auditor.py            # 逻辑审计核心
│   │   └── schemas.py            # API 数据模型
│   ├── semantic/
│   │   └── semantic_modeling.py  # 命题提取与 NLI 关系识别
│   └── slicer/
│       └── paper_slicer.py       # 论文内容切片
├── prompts/keywords.json         # 关键词配置示例
├── tests/test_three_modules.py   # 三模块联调脚本
├── docs/GITHUB_UPLOAD.md
├── .env.example
├── requirements.txt
└── run_api.py
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 12+
- （可选）CUDA，用于 GPU 加速推理

### 1. 克隆仓库

```bash
git clone https://github.com/wmlqq/DeepLogicAuditor.git
cd DeepLogicAuditor
```

### 2. 安装依赖

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # Linux / macOS
```

编辑 `.env`：

```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_user
DB_PASSWORD=your_password
```

可选：`HF_MIRROR`（国内镜像）、`MODEL_CACHE_DIR`、`OUTPUT_DIR`。

### 4. 启动服务

```bash
python run_api.py
```

访问 **[http://localhost:8000/docs](http://localhost:8000/docs)** 查看交互式 API 文档。

### 5. 运行联调测试

需已配置数据库且存在论文数据：

```bash
python tests/test_three_modules.py
```

---

## 📡 API 概览

| 方法 | 路径 | 说明 |
|:----:|------|------|
| `POST` | `/audit/integrated?paper_id={uuid}` | 从数据库读取论文，完成完整审计流程 |
| `POST` | `/audit/paper` | 对 JSON 命题图进行逻辑审计 |
| `POST` | `/audit/logic` | 对单一切片进行逻辑审计 |

<details>
<summary><b>一体化审计规则（LOG-001～LOG-007）</b></summary>

| 规则 ID | 名称 |
|---------|------|
| LOG-001 | 摘要五段式结构 |
| LOG-002 | 三级逻辑闭环 |
| LOG-004 | 术语一致性 |
| LOG-005 | 相关技术章节衔接 |
| LOG-006 | 实验回应研究问题 |
| LOG-007 | 创新点数量 |

</details>

---

## 🤖 模型与缓存

首次运行会自动下载 NLI 模型到 `src/model_cache/`（可通过 `MODEL_CACHE_DIR` 修改）。**请勿将模型文件提交到 Git。**

国内用户建议在 `.env` 中配置镜像：

```env
HF_MIRROR=https://hf-mirror.com
```

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐**

[报告问题](https://github.com/wmlqq/DeepLogicAuditor/issues) · [查看 Actions](https://github.com/wmlqq/DeepLogicAuditor/actions)


</div>
