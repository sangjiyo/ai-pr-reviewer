# 🤖 AI PR Review 助手

> 基于大语言模型的 Pull Request 智能审查工具，自动生成变更摘要、识别潜在风险并给出修改建议，帮助开发者提升 Code Review 效率与质量。

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心功能

- **PR 变更摘要** —— 用简洁的自然语言概括本次 PR 修改了哪些文件、解决了什么问题、影响了哪些模块。
- **风险代码识别** —— 自动检测安全漏洞、逻辑缺陷、性能陷阱、破坏性变更等，并按 `高/中/低` 严重度分级展示，附带具体修改建议。
- **多模型支持** —— 同时兼容 OpenAI、Anthropic、MiniMax 等主流 LLM，并预留便捷的自定义扩展接口。
- **灵活的命令行工具** —— 仅需一条命令即可完成全部分析，结果清晰可读，支持 diff 与文件内容预览。

## 📸 效果预览

```bash
$ python cli.py --repo octocat/Hello-World --pr 32 --provider openai

🔍 正在获取 PR #32 的变更...

============================================================
📄 PR DIFF
============================================================
diff --git a/README b/README
...

============================================================
🤖 AI 变更摘要
============================================================
本次 PR 修改了 README 文件，在原有 "Hello World!" 后新增一行 "Hello Earthlings!"，属于文档内容的简单扩展，不影响功能或 API。

============================================================
⚠️ 风险代码识别
============================================================
✅ 未发现显著风险

============================================================
📁 修改文件列表 (1 个文件)
============================================================
modified | README (变化行数: +1 -0)
...
```

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/sangjiyo/ai-pr-reviewer.git
cd ai-pr-reviewer
```

### 2. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入必要的 API 密钥（至少填一个 LLM 提供商的 Key 和 GitHub Token）：

```env
# GitHub（可选，但推荐用于提升 API 频率限额）
GITHUB_TOKEN=your_github_token_here

# LLM 提供商（至少选填一个）
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_group_id_here   # 可选，企业版可能需要
```

### 4. 运行

```bash
python cli.py --repo 仓库所有者/仓库名 --pr PR编号 --provider 模型提供商
```

示例：

```bash
# 使用 OpenAI 审查公共 PR
python cli.py --repo python/cpython --pr 105000 --provider openai

# 使用 Anthropic Claude
python cli.py --repo pytorch/pytorch --pr 80000 --provider anthropic
```

## 📖 使用说明

| 参数         | 说明                                                       | 必填 | 可选值                     |
| ------------ | ---------------------------------------------------------- | ---- | -------------------------- |
| `--repo`     | 目标仓库，格式 `owner/repo`                                | 是   | -                          |
| `--pr`       | PR 编号                                                   | 是   | -                          |
| `--provider` | LLM 提供商                                                | 否   | `openai`, `anthropic`, `minimax` |

工具将依次输出： **AI 变更摘要** → **风险代码识别报告** → **修改文件列表**。

## 🧠 设计思路

### 1. 模型选择

- **多模型抽象层**：通过 `llm_client.py` 中的 `_call_llm` 统一入口，根据 `--provider` 参数动态路由到不同提供商（OpenAI、Anthropic、MiniMax），各实现均基于官方 SDK 或推荐兼容方式编写。
- **默认推荐**：优先使用 `gpt-4o-mini`（OpenAI）或 `claude-3-5-sonnet`（Anthropic），在代码理解、指令遵循和长上下文处理上表现优异；同时支持国产模型如 MiniMax，以应对不同网络环境与成本需求。
- **可扩展性**：开发者只需在 `_PROVIDER_CALL_MAP` 中注册新的调用函数，并在 `.env` 中添加对应 Key，即可零侵入接入任意第三方模型。

### 2. 上下文获取方式

上下文质量直接决定 AI 分析的准确性，本工具采用 **多层上下文组装策略** 来降低“断章取义”的误判：

- **第 0 层（基础）**：直接获取 PR 的完整 `unified diff`，包含修改行前后若干行代码。
- **第 1 层（文件背景）**：通过 GitHub API 拉取被修改文件的**完整内容**（或函数体附近代码），并自动适配仓库的默认分支（`main` / `master`），让模型看到变量来源、函数签名、异常处理等关键信息。
- **第 2 层（项目知识，规划中）**：未来将支持索引项目核心文件（如类型定义、配置文件）到向量数据库，分析时动态检索相关背景，进一步增强深层逻辑理解。

### 3. 误报与漏报控制

- **Prompt 约束**：在风险识别 Prompt 中明确要求“只报告有明确代码证据的问题，忽略纯格式偏好”，并特别强调对高危害漏洞（如 SQL 注入、XSS、权限绕过）的关注，降低漏报。
- **结构化输出**：要求 LLM 返回固定 JSON 格式，包含文件、行号、严重度、证据和修改建议，便于程序校验、过滤和去重。
- **置信度过滤（规划中）**：后续将要求模型输出置信度分数，仅展示中高置信度结果，减少噪音。
- **用户反馈闭环（规划中）**：收集开发者对 AI 建议的“有用/误报”反馈，持续微调 Prompt 或构建个性化规则，逐步逼近团队真实容忍度。

### 4. 响应速度与使用体验

- **轻量级设计**：采用单次 API 调用完成摘要与风险分析（未来可拆分为独立异步任务），避免重依赖；diff 截断至 8000 字符，确保主流模型均能在秒级返回。
- **流式输出（计划支持）**：未来将支持实时打印 AI 思考过程，提升交互感。
- **集成友好**：目前以 CLI 为主，但代码模块化分离（`github_fetcher`、`llm_client`），可轻松嵌入 CI/CD 流程或构建 GitHub App，直接向 PR 添加评论。

## 🔭 未来扩展方向

- **跨平台支持**：抽象 Git 平台接口，支持 GitLab、Gitee 等。
- **深度 CI/CD 集成**：作为 GitHub Action 或 Jenkins 插件，在合入前自动审查并卡点。
- **自适应学习**：基于开发者反馈微调模型，形成“懂团队规范”的专属 Reviewer。
- **语义增强分析**：结合静态分析工具（如 Semgrep）先筛选确定性漏洞，再由 LLM 做语义推理，进一步降低误报。
- **IDE 实时提示**：开发 IDE 插件，在本地编写代码时即时预警，将问题消灭在提交前。
- **多模态支持**：未来可解析 PR 中附带的 UI 截图，辅助前端变更审查。

## 📁 项目结构

```
.
├── cli.py                  # 命令行入口，组装功能
├── github_fetcher.py       # GitHub API 交互（获取 diff、文件、默认分支）
├── llm_client.py           # LLM 抽象层，支持多模型、摘要与风险审查
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
├── .env                    # 本地环境变量（不提交）
└── README.md               # 项目文档
```

## 🔧 依赖清单

所有依赖已在 `requirements.txt` 中声明，核心三方库如下：

| 库名            | 用途                       | 版权/协议   |
| --------------- | -------------------------- | ----------- |
| `requests`      | HTTP 请求 (GitHub API)     | Apache 2.0  |
| `python-dotenv` | 读取 .env 环境变量         | MIT         |
| `openai`        | OpenAI / MiniMax SDK 调用   | Apache 2.0  |
| `anthropic`     | Anthropic Claude SDK 调用   | MIT         |

## 🤝 贡献与 PR 规范

本项目遵循“一个 PR 只做一件事”原则，所有功能通过小粒度、独立 PR 逐步合入。  
提交 PR 时请确保：

- 标题简洁明确，描述包含：功能说明、实现思路、测试方式。
- 代码可运行，主分支随时可复现演示效果。
- 新引入的第三方依赖需在 `requirements.txt` 及本 README 中注明。

欢迎提交 Issue 或 PR 共同改进！

## 📜 开源协议
```
注意事项：

1. 请将仓库地址 `https://github.com/sangjiyo/ai-pr-reviewer.git` 改为你实际的远程仓库地址。
2. 如果当前还没添加 `LICENSE` 文件，建议补一个 MIT License（或你偏好的协议），并在 README 底部链接过去。
3. 若已有 `README.md`，请覆盖或按此结构整合，重点保留“设计思路”章节，这是评委最关注的核心阐述。
4. 未来扩展部分可根据你的真实想法微调，确保与比赛议题契合（AI 辅助分析、准确性、体验等）。
```
