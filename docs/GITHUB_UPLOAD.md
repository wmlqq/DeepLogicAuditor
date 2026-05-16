# 上传到 GitHub 完整指南

本文说明如何在 GitHub 网站创建仓库，以及如何在本地把本项目推送到远程。

## 一、上传前本地准备

### 1. 确认目录结构

仓库根目录应为 `holiday/`（或你重命名后的项目文件夹），包含：

```
.
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── pyproject.toml
├── run_api.py
├── src/
├── tests/
├── prompts/
└── docs/
```

**不要**把 `venv/`、`src/model_cache/`、`.env` 提交上去（已在 `.gitignore` 中排除）。

### 2. 配置环境变量（本地开发用）

```bash
copy .env.example .env
```

编辑 `.env`，填入你的 PostgreSQL 连接信息。

### 3. 初始化 Git 并首次提交

在项目根目录打开终端（PowerShell 或 Git Bash）：

```powershell
cd "d:\桌面文件\20261\holiday"

# 若之前 git 状态混乱，可先清理索引（不删文件）
git reset
git add .
git status

git commit -m "Initial commit: DeepLogicAuditor academic paper logic audit agent"
```

## 二、在 GitHub 网站上要做的操作

### 1. 登录并新建仓库

1. 打开 [https://github.com/new](https://github.com/new)
2. **Repository name**：例如 `DeepLogicAuditor` 或 `deep-logic-auditor`
3. **Description**（可选）：学术论文逻辑审计智能体
4. **Public / Private**：按需选择
5. **不要**勾选 “Add a README file”（本地已有 README）
6. **不要**勾选 “Add .gitignore”（本地已有）
7. **不要**勾选 “Choose a license”（本地已有 LICENSE）
8. 点击 **Create repository**

### 2. 关于 “技术栈 / Add file / 模板”

GitHub **创建空仓库时通常没有** “选择技术栈” 的必填项。你可能在以下位置看到类似选项，**均可跳过或事后设置**：

| 位置 | 说明 | 建议 |
|------|------|------|
| 创建仓库页 | 无技术栈下拉框 | 直接创建空仓库即可 |
| **About** 齿轮（仓库首页右侧） | Topics、Website、Description | 可添加 topics：`python` `fastapi` `nlp` `pytorch` |
| **Settings → General** | 无强制技术栈 | 保持默认 |
| **Insights → Dependency graph** | 推送后自动识别 `requirements.txt` | 推送后等待扫描即可 |
| **Actions** | CI 使用 `.github/workflows/ci.yml` | 首次 push 后自动出现 |

若使用 **GitHub Copilot / 模板生成**，才可能出现 “Python / Node” 等选择；**手动 push 本项目时不需要**。

### 3. 关联远程并推送

创建仓库后，GitHub 会显示命令。在本地执行（把 `YOUR_USER` 和 `YOUR_REPO` 换成你的）：

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

若使用 SSH：

```powershell
git remote add origin git@github.com:YOUR_USER/YOUR_REPO.git
git push -u origin main
```

首次 push 若要求登录，按提示使用 **Personal Access Token**（HTTPS）或配置 **SSH key**。

## 三、推送后建议检查

1. 打开仓库 **Code** 页，确认 `src/`、`README.md` 等文件齐全
2. 打开 **Actions**，确认 `CI` workflow 是否通过（需已配置 `DB_*` 环境变量仅用于 import 检查）
3. 在 **About** 中添加 Topics：`python`, `fastapi`, `transformers`, `academic-paper`
4. 确认 **未泄露** `.env` 或数据库密码（若曾提交过密码，应在数据库侧**轮换密码**并改写历史或删除敏感提交）

## 四、克隆与在新机器上运行

```bash
git clone https://github.com/YOUR_USER/YOUR_REPO.git
cd YOUR_REPO
python -m venv venv
# Windows:
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env 后：
python run_api.py
```

首次运行会从 Hugging Face（或镜像）下载 NLI 模型到 `src/model_cache/`。

## 五、常见问题

**Q: push 被拒绝（large file）？**  
A: 确保未提交 `src/model_cache/` 或 `venv/`。若已误提交，用 `git rm -r --cached src/model_cache` 后重新 commit。

**Q: 需要 Git LFS 吗？**  
A: 一般不需要；模型应在运行时下载，不要入库。

**Q: 旧目录 `DeepLogicAuditorAgent2/` 还要吗？**  
A: 不需要，已扁平化到仓库根目录，可本地删除该文件夹。
