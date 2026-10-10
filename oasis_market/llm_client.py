# oasis_market/llm_client.py
"""统一 LLM 接口。

桥接 CAMEL 的 ModelFactory + ChatAgent。
不走 OASIS SocialAgent，因为本仿真的 action space 是自定义互动信号，
不需要 OASIS 的社交图谱结构。
"""
import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class LLMClient:
    """包装 CAMEL ChatAgent 的最小 LLM 客户端。"""

    def __init__(self, model_platform=None, model_type=None,
                 api_key=None, base_url=None,
                 temperature: float = 0.7, max_tokens: int = 2000):
        from camel.models import ModelFactory

        self.model_platform = model_platform or os.getenv("MODEL_PLATFORM", "openai")
        self.model_type = model_type or os.getenv("MODEL_TYPE", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("MODEL_API_KEY")
        # 显式确保 OPENAI_API_KEY 已设置
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = self.api_key or os.getenv("MODEL_API_KEY", "")
        self.base_url = (base_url
                         or os.getenv("MODEL_BASE_URL")
                         or os.getenv("MODEL_API_BASE")
                         or os.getenv("OPENAI_BASE_URL")
                         or os.getenv("OPENAI_API_BASE"))
        self.temperature = temperature
        self.max_tokens = max_tokens

        model_config = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 关键：base_url 不能放进 model_config_dict，否则 CAMEL 会把它当 create() 的
        # 参数传给 OpenAI SDK，报 TypeError。改为写进环境变量，让 SDK 自己读。
        if self.base_url:
            os.environ["OPENAI_API_BASE"] = self.base_url
            os.environ["OPENAI_BASE_URL"] = self.base_url

        self.model = ModelFactory.create(
            model_platform=self.model_platform,
            model_type=self.model_type,
            api_key=self.api_key,
            model_config_dict=model_config,
        )

    def chat(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> str:
        from camel.agents import ChatAgent

        for attempt in range(max_retries + 1):
            agent = ChatAgent(system_message=system_prompt, model=self.model)
            resp = agent.step(user_prompt)

            # 1) 优先从 resp.msgs 找非空
            if hasattr(resp, "msgs") and resp.msgs:
                for m in reversed(resp.msgs):
                    content = m if isinstance(m, str) else getattr(m, "content", None)
                    if content:
                        return content

            # 2) 回退到 resp.msg
            if hasattr(resp, "msg") and resp.msg is not None:
                msg = resp.msg
                if isinstance(msg, str) and msg:
                    return msg
                c = getattr(msg, "content", None)
                if c:
                    return c

            # 3) 第一次空返回时，打印诊断
            if attempt == 0:
                print(f"[DEBUG-EMPTY] resp type={type(resp).__name__}")
                print(f"[DEBUG-EMPTY] attrs={[a for a in dir(resp) if not a.startswith('_')]}")
                if hasattr(resp, "info"):
                    print(f"[DEBUG-EMPTY] info={getattr(resp, 'info', None)!r}")

        return ""


class DummyLLMClient:
    """离线测试用：不调 API，返回空字符串。

    用途：验证 pipeline 逻辑，或在没有 API key 的环境下跑通 run_live_commerce.py。
    """

    def __init__(self, *args, **kwargs):
        pass

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        return ""