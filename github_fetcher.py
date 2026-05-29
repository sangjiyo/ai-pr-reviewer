import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else ""
}
BASE_URL = "https://api.github.com"

def get_pr_diff(owner, repo, pr_number):
    """获取 PR 的 unified diff 文本"""
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {**HEADERS, "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def get_pr_files(owner, repo, pr_number):
    """获取 PR 中修改过的文件列表（含文件名、状态、补丁）"""
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_file_content(owner, repo, file_path, ref="main"):
    """获取仓库中某个文件的完整内容（默认使用 main 分支作为基准）"""
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    params = {"ref": ref}
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        # 文件可能被删除或重命名，返回空字符串
        return ""
    resp.raise_for_status()
    # 文件内容经 Base64 编码
    import base64
    content_b64 = resp.json().get("content", "")
    if content_b64:
        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
    return ""
