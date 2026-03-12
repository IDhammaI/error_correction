import logging
import time
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_CONNECTION_CACHE_TTL = 60  # 连通性检测缓存有效期（秒）

_BACKEND_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_ROOT.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# LLM Provider 配置（每个供应商一个 Config 子类，含工厂方法）
# ---------------------------------------------------------------------------

class LLMProviderConfig(BaseSettings):
    """单个 LLM 供应商配置基类

    字段名匹配环境变量后缀（如 OPENAI_API_KEY → api_key），
    由子类通过 env_prefix 绑定具体前缀。
    子类实现 create_llm() 工厂方法以创建对应的 LangChain Chat 模型。
    """
    model_config = SettingsConfigDict(extra="ignore")

    # 连接参数（从环境变量读取）
    api_key: str = ""
    base_url: str = ""

    # 模型名称
    model_name: str                         # 默认模型
    light_model_name: str | None = None     # 轻量模型（科目识别等），未配置时回退默认

    # 供应商能力
    supports_function_calling: bool = True

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _ping(self):
        """发起轻量 API 请求验证连通性（子类实现），成功无异常，失败抛异常"""
        raise NotImplementedError

    def check_connection(self) -> str:
        """测试 API 连通性（带缓存）

        Returns:
            "配置成功" | "连接失败" | "" (未配置)
        """
        if not self.api_key:
            return ""

        now = time.monotonic()
        cache = getattr(self, "_conn_cache", None)
        if cache and (now - cache[1]) < _CONNECTION_CACHE_TTL:
            return cache[0]

        try:
            self._ping()
            result = "配置成功"
        except Exception as e:
            logger.warning("%s 连通性检测失败: %s", type(self).__name__, e)
            result = "连接失败"

        # BaseSettings 实例无法直接赋值，用 object.__setattr__
        object.__setattr__(self, "_conn_cache", (result, now))
        return result

    def resolve_model_name(
        self, model_name: str | None = None, *, use_light: bool = False
    ) -> str:
        """解析最终模型名：显式指定 > 轻量模型 > 默认模型"""
        if model_name is not None:
            return model_name
        if use_light and self.light_model_name:
            return self.light_model_name
        return self.model_name

    def create_llm(self, *, model: str, temperature: float):
        """创建 LangChain Chat 模型实例（子类必须实现）"""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 按接口协议分类的供应商基类（含 create_llm 工厂方法）
# ---------------------------------------------------------------------------

class OpenAICompatibleConfig(LLMProviderConfig):
    """OpenAI 兼容接口供应商（DeepSeek、Qwen、Moonshot 等均可通过 base_url 接入）"""
    model_config = SettingsConfigDict(env_prefix="OPENAI_", env_file=_ENV_FILE, extra="ignore")
    model_name: str = "gpt-4o-mini"

    def _ping(self):
        from openai import OpenAI
        kwargs = {"api_key": self.api_key, "timeout": 5}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        OpenAI(**kwargs).models.list(limit=1)

    def create_llm(self, *, model: str, temperature: float):
        from langchain_openai import ChatOpenAI
        kwargs = dict(model=model, api_key=self.api_key, temperature=temperature)
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return ChatOpenAI(**kwargs)


class AnthropicCompatibleConfig(LLMProviderConfig):
    """Anthropic 接口供应商"""
    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_", env_file=_ENV_FILE, extra="ignore")
    model_name: str = "claude-sonnet-4-20250514"

    def _ping(self):
        from anthropic import Anthropic
        kwargs = {"api_key": self.api_key, "timeout": 5}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        Anthropic(**kwargs).models.list(limit=1)

    def create_llm(self, *, model: str, temperature: float):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model, api_key=self.api_key,
            base_url=self.base_url or None, temperature=temperature,
        )


# ---------------------------------------------------------------------------
# 应用全局配置
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    # 基础路径（不从环境变量读取，仅作为默认值）
    backend_root: Path = _BACKEND_ROOT
    project_root: Path = _PROJECT_ROOT

    # 统一运行产物根目录，可通过 APP_RUNTIME_DIR 覆盖
    runtime_dir: Path = _BACKEND_ROOT / "runtime_data"

    # 错题库数据库路径，可通过 APP_DB_PATH 覆盖
    db_path: Path | None = None

    # 各类子目录（由 validator 从 runtime_dir 派生，可独立覆盖以便测试）
    upload_dir: Path | None = None
    pages_dir: Path | None = None
    struct_dir: Path | None = None
    results_dir: Path | None = None

    # 上传 & 请求限制
    max_file_size_mb: int = 50
    allowed_extensions: set[str] = {"pdf", "png", "jpg", "jpeg", "bmp", "tiff", "webp"}

    # LLM 供应商注册表
    llm_providers: dict[str, LLMProviderConfig] | None = None

    @model_validator(mode="after")
    def _resolve_defaults(self):
        if self.db_path is None:
            self.db_path = self.runtime_dir / "error_book.db"
        if self.upload_dir is None:
            self.upload_dir = self.runtime_dir / "uploads"
        if self.pages_dir is None:
            self.pages_dir = self.runtime_dir / "pages"
        if self.struct_dir is None:
            self.struct_dir = self.runtime_dir / "struct"
        if self.results_dir is None:
            self.results_dir = self.runtime_dir / "results"

        # 初始化 LLM 供应商注册表
        if self.llm_providers is None:
            self.llm_providers = {
                "openai": OpenAICompatibleConfig(),
                "anthropic": AnthropicCompatibleConfig(),
            }
        return self

    def ensure_dirs(self):
        """确保必要目录存在（应在应用启动入口显式调用）"""
        for d in [self.upload_dir, self.pages_dir, self.struct_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ----- LLM 供应商查询方法 -----

    @staticmethod
    def _normalize_provider(name: str) -> str:
        return (name or "").strip().lower()

    def get_provider(self, name: str) -> LLMProviderConfig:
        """按名称获取供应商配置，不存在则抛出 ValueError"""
        key = self._normalize_provider(name)
        if key not in self.llm_providers:
            known = ", ".join(self.llm_providers.keys())
            raise ValueError(f"不支持的模型供应商: {key}（可选: {known}）")
        return self.llm_providers[key]

    def is_valid_provider(self, name: str) -> bool:
        return self._normalize_provider(name) in self.llm_providers

    def get_available_models(self) -> list[dict]:
        """返回可用模型列表，供 /api/status 等接口使用（含连通性检测）"""
        from concurrent.futures import ThreadPoolExecutor

        items = list(self.llm_providers.items())
        with ThreadPoolExecutor(max_workers=len(items)) as pool:
            statuses = list(pool.map(lambda kv: kv[1].check_connection(), items))

        return [
            {
                "value": key,
                "label": cfg.model_name,
                "configured": status == "配置成功",
                "status": status or "未配置",
            }
            for (key, cfg), status in zip(items, statuses)
        ]


settings = Settings()
