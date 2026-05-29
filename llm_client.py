import os
import json
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = ["openai", "anthropic", "minimax"]

# ==================== 通用 Prompt 模板 ====================

def _build_summary_prompt(diff_text):
    return f"""你是一名资深代码评审员。请阅读以下 PR diff，用简洁的中文总结本次变更的核心内容，包括：
1. 修改了哪些文件/模块
2. 变更的主要功能或修复的问题
3. 潜在影响范围

PR diff:
{diff_text[:8000]}

请用 3-5 句话的摘要回复，不需要列出细节。"""

def _build_review_prompt(diff_text):
    return f"""你是一名资深代码评审员。请仔细审查以下 PR diff，找出**潜在风险或缺陷**，包括但不限于：
- 安全漏洞（SQL注入、XSS、权限绕过、硬编码密钥等）
- 逻辑错误（空指针、未处理异常、边界条件错误）
- 性能问题（不必要的循环、资源泄漏）
- 破坏性变更（API不兼容、数据格式变化）
- 代码规范严重违反（但忽略缩进、命名风格等纯格式问题）

请以 JSON 格式返回你的发现，格式如下：
{{
  "risks": [
    {{
      "file": "文件路径",
      "line": 行号或 "N/A",
      "severity": "high/medium/low",
      "description": "具体问题描述",
      "suggestion": "修改建议"
    }}
  ]
}}
如果没有发现任何风险，返回 {{ "risks": [] }}。
请确保只返回 JSON，不包含其他文字。

PR diff:
{diff_text[:8000]}"""

# ==================== 通用 LLM 调用封装 ====================

def _call_openai(prompt, model="gpt-4o-mini"):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    return response.choices[0].message.content

def _call_anthropic(prompt, model="claude-3-5-sonnet-20240620"):
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def _call_minimax(prompt, model="MiniMax-M2.7"):
    from openai import OpenAI
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    base_url = "https://api.minimax.chat/v1"
    extra_headers = {}
    if group_id:
        extra_headers["X-Minimax-Group-Id"] = group_id
    client = OpenAI(api_key=api_key, base_url=base_url, default_headers=extra_headers)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    return response.choices[0].message.content

_PROVIDER_CALL_MAP = {
    "openai": _call_openai,
    "anthropic": _call_anthropic,
    "minimax": _call_minimax,
}

def _call_llm(provider, prompt):
    if provider not in _PROVIDER_CALL_MAP:
        raise ValueError(f"不支持的 provider: {provider}，可选: {list(_PROVIDER_CALL_MAP.keys())}")
    env_checks = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "minimax": "MINIMAX_API_KEY",
    }
    if provider in env_checks and not os.getenv(env_checks[provider]):
        raise ValueError(f"缺少 {env_checks[provider]}，请在 .env 中配置")
    return _PROVIDER_CALL_MAP[provider](prompt)

# ==================== 公开接口 ====================

def generate_summary(diff_text, provider="openai"):
    """生成 PR 变更摘要"""
    prompt = _build_summary_prompt(diff_text)
    return _call_llm(provider, prompt)

def generate_review(diff_text, provider="openai"):
    """生成风险识别结果，返回解析后的字典，含 risks 列表"""
    prompt = _build_review_prompt(diff_text)
    raw = _call_llm(provider, prompt)
    # 尝试提取 JSON（有时模型会在 JSON 前后加一些文本）
    try:
        # 寻找第一个 '{' 和最后一个 '}'
        start = raw.index('{')
        end = raw.rindex('}') + 1
        json_str = raw[start:end]
        result = json.loads(json_str)
        if "risks" not in result:
            # 如果不是预期格式，包装一下
            return {"risks": [], "raw": raw}
        return result
    except (ValueError, json.JSONDecodeError) as e:
        # 解析失败，返回空风险并附带原始文本供调试
        return {"risks": [], "raw": raw, "parse_error": str(e)}
