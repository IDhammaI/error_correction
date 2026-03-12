"""
公共 LLM 初始化工具

所有智能体模块共享的模型初始化逻辑。
供应商配置和工厂方法统一在 config.py 的 LLMProviderConfig 子类中定义。
"""

from config import settings


def init_model(
    temperature: float = 0.1,
    provider: str = "openai",
    model_name: str | None = None,
    use_light: bool = False,
):
    """初始化 LLM 模型

    Args:
        temperature: 温度参数
        provider: 模型供应商名称
        model_name: 指定模型名称，为 None 时使用配置默认值
        use_light: 使用轻量模型（用于科目识别等低成本任务）
    """
    cfg = settings.get_provider(provider)

    if not cfg.configured:
        raise ValueError(f"使用 {provider} 需要配置 API Key 环境变量")

    effective_model = cfg.resolve_model_name(model_name, use_light=use_light)

    return cfg.create_llm(model=effective_model, temperature=temperature)
