# DeepLogicAuditor

学术论文逻辑审计智能体：对论文进行切片、语义建模与规则化逻辑审计，检测逻辑矛盾、逻辑跳跃、结构不完整等问题。

## 功能

- **论文切片**：将 Markdown 论文切分为命题级片段
- **语义建模**：基于 NLI 模型识别命题间蕴含 / 中立 / 矛盾关系
- **逻辑审计**：检测矛盾陈述、无支撑论证、衔接词缺失等
- **一体化审计**：从 PostgreSQL 读取论文，按 `LOG-001`～`LOG-007` 规则评分并写回数据库
- **REST API**：FastAPI 对外提供 HTTP 接口

## 技术栈

| 组件 | 用途 |
|------|------|
| Python 3.10+ | 运行环境 |
| FastAPI + Uvicorn | API 服务 |
| PyTorch + Transformers | `cross-encoder/nli-deberta-v3-base` |
| NetworkX | 语义关系图 |
| PostgreSQL | 论文与规则数据 |

## 项目结构

```
.
├── src/
│   ├── config.py              # 环境变量与路径
│   ├── database_connector.py  # 数据库访问
│   ├── logic_auditor/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── auditor.py         # 逻辑审计核心
│   │   └── schemas.py         # API 数据模型
│   ├── semantic/
│   │   └── semantic_modeling.py
│   └── slicer/
│       └── paper_slicer.py
├── prompts/
│   └── keywords.json          # 关键词配置示例
├── tests/
│   └── test_three_modules.py  # 三模块联调脚本
├── docs/
│   └── GITHUB_UPLOAD.md       # 上传到 GitHub 的详细步骤
├── .env.example
├── requirements.txt
├── run_api.py
└── LICENSE
```

## 快速开始

### 1. 克隆与安装

```bash
git clone <your-repo-url>
cd DeepLogicAuditor
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS
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

### 3. 启动 API

在项目根目录执行：

```bash
python run_api.py
```

或：

```bash
uvicorn src.logic_auditor.main:app --host 0.0.0.0 --port 8000
```

文档地址： [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. 运行三模块测试

需已配置数据库且存在论文数据：

```bash
python tests/test_three_modules.py
```

结果输出到 `tests/results/`（该目录已在 `.gitignore` 中忽略生成文件）。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/audit/integrated?paper_id={uuid}` | 从数据库读取论文并完整审计 |
| POST | `/audit/paper` | 对 JSON 中的命题图进行审计 |
| POST | `/audit/logic` | 对单一切片进行逻辑审计 |

## 审计规则（一体化接口）

| 规则 ID | 名称 |
|---------|------|
| LOG-001 | 摘要五段式结构 |
| LOG-002 | 三级逻辑闭环 |
| LOG-004 | 术语一致性 |
| LOG-005 | 相关技术章节衔接 |
| LOG-006 | 实验回应研究问题 |
| LOG-007 | 创新点数量 |

## 模型缓存

首次运行会自动下载 NLI 模型到 `src/model_cache/`（可通过 `MODEL_CACHE_DIR` 修改）。该目录**不应**提交到 Git。

国内用户可在 `.env` 中设置：

```env
HF_MIRROR=https://hf-mirror.com
```

## 上传到 GitHub

完整步骤（含 GitHub 网页操作说明）见：[docs/GITHUB_UPLOAD.md](docs/GITHUB_UPLOAD.md)

## 许可证

[MIT](LICENSE)
