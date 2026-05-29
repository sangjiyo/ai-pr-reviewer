# AI PR Review 助手

一个基于大模型的 Pull Request 自动审查工具，可快速生成 PR 变更摘要、识别风险代码并提供修改建议。

## 快速开始

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. GitHub Token（可选但推荐）：
   bash
   cp .env.example .env
   # 编辑 .env，填入你的 GitHub Personal Access Token
4. 运行
   bash
   python cli.py --repo owner/repo --pr 123 
