import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 默认使用的模型
DEFAULT_MODEL = "gpt-4o-mini"          # 或 "claude-3-5-sonnet-20240620"

def get_openai_summary(diff_text, model=DEFAULT_MODEL):
    """使用 OpenAI 生成 PR 变更摘要"""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""你是一名资深代码评审员。请阅读以下 PR diff，用简洁的中文总结本次变更的核心内容，包括：
1. 修改了哪些文件/模块
2. 变更的主要功能或修复的问题
3. 潜在影响范围

PR diff:
{diff_text[:8000]}

请用 3-5 句话的摘要回复，不需要列出细节。"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    return response.choices[0].message.content

def get_anthropic_summary(diff_text, model="claude-3-5-sonnet-20240620"):
    """使用 Anthropic Claude 生成 PR 变更摘要"""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""你是一名资深代码评审员。请阅读以下 PR diff，用简洁的中文总结本次变更的核心内容，包括：
1. 修改了哪些文件/模块
2. 变更的主要功能或修复的问题
3. 潜在影响范围

PR diff:
{diff_text[:8000]}

请用 3-5 句话的摘要回复，不需要列出细节。"""

    message = client.messages.create(
        model=model,
        max_tokens=500,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def generate_summary(diff_text, provider="openai"):
    """统一的摘要生成入口，provider 可选 'openai' 或 'anthropic'"""
    if provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("请在 .env 中设置 OPENAI_API_KEY")
        return get_openai_summary(diff_text)
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ValueError("请在 .env 中设置 ANTHROPIC_API_KEY")
        return get_anthropic_summary(diff_text)
    else:
        raise ValueError("不支持的 LLM 提供商")
