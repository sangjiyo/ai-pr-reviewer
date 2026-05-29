import argparse
from github_fetcher import get_pr_diff, get_pr_files, get_file_content, get_default_branch
from llm_client import generate_summary, SUPPORTED_PROVIDERS

def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub PR diff and file contents")
    parser.add_argument("--repo", required=True, help="仓库名，格式 owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR 编号")
    parser.add_argument("--provider", default="openai", choices=SUPPORTED_PROVIDERS, help="选择LLM 提供商")
    args = parser.parse_args()

    owner, repo = args.repo.split("/")

    print(f" 正在获取 PR #{args.pr} 的变更...\n")

    # 动态获取仓库默认分支
    try:
        default_branch = get_default_branch(owner, repo)
        print(f"ℹ️  仓库默认分支: {default_branch}\n")
    except Exception as e:
        print(f"⚠️ 无法获取默认分支，将使用 main: {e}")
        default_branch = "main"
        
    # 获取 diff
    try:
        diff = get_pr_diff(owner, repo, args.pr)
        print("=" * 60)
        print("PR DIFF")
        print("=" * 60)
        print(diff[:3000])  # 先打印前 3000 字符，避免输出过长
        if len(diff) > 3000:
            print("\n... (输出截断，完整内容请查看变量)")
    except Exception as e:
        print(f" 获取 diff 失败: {e}")
        return
    
    # 生成 LLM 摘要
    print("\n" + "=" * 60)
    print("AI 变更摘要")
    print("=" * 60)
    try:
        summary = generate_summary(diff, provider=args.provider)
        print(summary)
    except Exception as e:
        print(f"生成摘要失败: {e}")

    # 获取修改过的文件列表及内容
    try:
        files = get_pr_files(owner, repo, args.pr)
        print("\n" + "=" * 60)
        print(f"修改文件列表 ({len(files)} 个文件)")
        print("=" * 60)
        for f in files:
            print(f"{f['status']:6} | {f['filename']} (变化行数: +{f['additions']} -{f['deletions']})")

        # 3. 获取每个修改文件的完整内容（可选，用 --full-files 开关控制）
        print("\n" + "=" * 60)
        print("修改文件完整内容（前 2000 字符预览）")
        print("=" * 60)
        for f in files:
            filename = f['filename']
            if f['status'] == 'removed':
                continue
            # 从 PR 的 base 分支获取内容（通常是 main）
            content = get_file_content(owner, repo, filename, ref=default_branch)
            print(f"\n--- {filename} ---")
            print(content[:2000] if content else "(无法获取内容)")
            if content and len(content) > 2000:
                print("... (截断)")
    except Exception as e:
        print(f" 获取文件信息失败: {e}")

if __name__ == "__main__":
    main()
