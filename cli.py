import argparse
from github_fetcher import get_pr_diff, get_pr_files, get_file_content, get_default_branch
from llm_client import generate_summary, generate_review, SUPPORTED_PROVIDERS

def main():
    parser = argparse.ArgumentParser(description="AI PR Review 助手")
    parser.add_argument("--repo", required=True, help="仓库名，格式 owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR 编号")
    parser.add_argument("--provider", default="openai", choices=SUPPORTED_PROVIDERS, help="LLM 提供商")
    args = parser.parse_args()

    owner, repo = args.repo.split("/")
    print(f"正在获取 PR #{args.pr} 的变更...\n")

    # 获取默认分支
    try:
        default_branch = get_default_branch(owner, repo)
        print(f"仓库默认分支: {default_branch}\n")
    except Exception as e:
        print(f"无法获取默认分支，将使用 main: {e}")
        default_branch = "main"

    # 获取 diff
    try:
        diff = get_pr_diff(owner, repo, args.pr)
        print("=" * 60)
        print("PR DIFF")
        print("=" * 60)
        print(diff[:3000])
        if len(diff) > 3000:
            print("\n... (输出截断，完整内容用于 AI 分析)")
    except Exception as e:
        print(f" 获取 diff 失败: {e}")
        return

    # ---------- AI 变更摘要 ----------
    print("\n" + "=" * 60)
    print("AI 变更摘要")
    print("=" * 60)
    try:
        summary = generate_summary(diff, provider=args.provider)
        print(summary)
    except Exception as e:
        print(f"生成摘要失败: {e}")

    # ---------- AI 风险识别 ----------
    print("\n" + "=" * 60)
    print("风险代码识别")
    print("=" * 60)
    try:
        review = generate_review(diff, provider=args.provider)
        risks = review.get("risks", [])
        if not risks:
            print("未发现显著风险")
        else:
            for i, risk in enumerate(risks, 1):
                severity_icon = {"high": "高", "medium": "中", "low": "低"}.get(risk.get("severity", "low"), "⚪")
                print(f"\n{i}. {severity_icon} [{risk.get('severity', 'low').upper()}] {risk.get('file', 'N/A')}:{risk.get('line', 'N/A')}")
                print(f"   描述: {risk.get('description', '无')}")
                print(f"   建议: {risk.get('suggestion', '无')}")
        if "parse_error" in review:
            print(f"\n风险数据解析警告: {review['parse_error']}")
            if "raw" in review:
                print(f"原始响应片段: {review['raw'][:200]}...")
    except Exception as e:
        print(f"风险识别失败: {e}")

    # ---------- 修改文件列表（保留原有逻辑）----------
    try:
        files = get_pr_files(owner, repo, args.pr)
        print("\n" + "=" * 60)
        print(f"修改文件列表 ({len(files)} 个文件)")
        print("=" * 60)
        for f in files:
            print(f"{f['status']:6} | {f['filename']} (变化行数: +{f['additions']} -{f['deletions']})")

        print("\n" + "=" * 60)
        print("修改文件完整内容（前 2000 字符预览）")
        print("=" * 60)
        for f in files:
            filename = f['filename']
            if f['status'] == 'removed':
                continue
            content = get_file_content(owner, repo, filename, ref=default_branch)
            print(f"\n--- {filename} ---")
            print(content[:2000] if content else "(无法获取内容)")
            if content and len(content) > 2000:
                print("... (截断)")
    except Exception as e:
        print(f"获取文件信息失败: {e}")

if __name__ == "__main__":
    main()
