# AI PR Review 助手

一个基于大模型的 Pull Request 自动审查工具，可快速生成 PR 变更摘要、识别风险代码并提供修改建议。

## 快速开始

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. GitHub Token（可选但推荐）：
   bash
   cp .env.example .env
   编辑 .env，填入你的 GitHub Personal Access Token
4. 运行
   bash
   python cli.py --repo owner/repo --pr 123

## 自定义 LLM 提供商

本工具采用可扩展的摘要生成架构，你可以轻松接入任意大模型。

1. 在 `llm_client.py` 中编写一个新函数，接收 `diff_text`，返回摘要字符串。
2. 将该函数注册到 `_PROVIDER_FUNCTIONS` 字典，例如：
   python
   _PROVIDER_FUNCTIONS["my_model"] = _get_my_model_summary
3. 在 .env 中添加对应的 API Key，并在 key_env_map 中关联。
4. 重新运行脚本时使用 --provider my_model 即可。
