import os
from dotenv import load_dotenv

load_dotenv()

# 支持的提供商列表
SUPPORTED_PROVIDERS = ["openai", "anthropic", "minimax"]

def _get_openai_summary(diff_text, model="gpt-4o-mini"):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = _build_prompt(diff_text)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    return response.choices[0].message.content

def _get_anthropic_summary(diff_text, model="claude-3-5-sonnet-20240620"):
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = _build_prompt(diff_text)
    message = client.messages.create(
        model=model,
        max_tokens=500,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def _get_minimax_summary(diff_text, model="MiniMax-M2.7"):
    from openai import OpenAI

    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")  # 可选
    base_url = "https://api.minimax.chat/v1"

    # 构造客户端，如有 group_id 可通过 default_headers 注入
    extra_headers = {}
    if group_id:
        extra_headers["X-Minimax-Group-Id"] = group_id

    client = OpenAI(api_key=api_key, base_url=base_url, default_headers=extra_headers)

    prompt = _build_prompt(diff_text)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
        # MiniMax 不需要 reasoning_split，直接正常返回即可
    )
    return response.choices[0].message.content

# 提供商标识到实际函数的映射
_PROVIDER_FUNCTIONS = {
    "openai": _get_openai_summary,
    "anthropic": _get_anthropic_summary,
    "minimax": _get_minimax_summary,
}

def _build_prompt(diff_text):
    return f"""你是一名资深代码评审员。请阅读以下 PR diff，用简洁的中文总结本次变更的核心内容，包括：
1. 修改了哪些文件/模块
2. 变更的主要功能或修复的问题
3. 潜在影响范围

PR diff:
{diff_text[:8000]}

请用 3-5 句话的摘要回复，不需要列出细节。"""

def generate_summary(diff_text, provider="openai"):
    """统一的摘要生成入口，provider 需在 SUPPORTED_PROVIDERS 中"""
    if provider not in _PROVIDER_FUNCTIONS:
        raise ValueError(f"不支持的 LLM 提供商: {provider}，当前支持: {list(_PROVIDER_FUNCTIONS.keys())}")
    
    # 简单检查对应的 API Key 是否存在
    key_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "minimax": "MINIMAX_API_KEY",
    }
    if provider in key_env_map and not os.getenv(key_env_map[provider]):
        raise ValueError(f"缺少 {key_env_map[provider]}，请在 .env 中配置")
    
    func = _PROVIDER_FUNCTIONS[provider]
    return func(diff_text)
