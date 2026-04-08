import logging
import os
import threading
import time
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_CONNECTION_CACHE_TTL = 60  # 连通性检测缓存有效期（秒）
_providers_lock = threading.Lock()  # 保护 llm_providers 并发读写

_BACKEND_ROOT = Path(__file__).resolve().parent.parent  # backend/core/ → backend/
_PROJECT_ROOT = _BACKEND_ROOT.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# LLM Provider 配置（每个供应商一个 Config 子类，含工厂方法）
# ---------------------------------------------------------------------------

class LLMProviderConfig(BaseSettings):
    """单个 LLM 供应商配置基类

    凭据通过 load_providers_from_db() 从数据库注入。
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

    def _build_client_kwargs(self, timeout: int = 10) -> dict:
        """构建 SDK 客户端参数（子类共用）"""
        kwargs = {"api_key": self.api_key, "timeout": timeout}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return kwargs

    def _create_raw_client(self, timeout: int = 10):
        """创建原生 SDK 客户端（子类实现）"""
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """通过 API 获取可用模型列表，失败时返回空列表"""
        if not self.api_key:
            return []
        try:
            client = self._create_raw_client(timeout=10)
            result = client.models.list()
            return sorted([m.id for m in result.data])
        except Exception as e:
            logger.warning("%s 获取模型列表失败: %s", type(self).__name__, e)
            return []

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
            self._create_raw_client(timeout=5)
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
    model_config = SettingsConfigDict(extra="ignore")
    model_name: str = "gpt-4o-mini"

    def _create_raw_client(self, timeout: int = 10):
        from openai import OpenAI
        return OpenAI(**self._build_client_kwargs(timeout))

    def create_llm(self, *, model: str, temperature: float):
        from langchain_openai import ChatOpenAI
        kwargs = dict(model=model, api_key=self.api_key, temperature=temperature)
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return ChatOpenAI(**kwargs)


class AnthropicCompatibleConfig(LLMProviderConfig):
    """Anthropic 接口供应商"""
    model_config = SettingsConfigDict(extra="ignore")
    model_name: str = "claude-sonnet-4-20250514"

    def _create_raw_client(self, timeout: int = 10):
        from anthropic import Anthropic
        return Anthropic(**self._build_client_kwargs(timeout))

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
    erased_dir: Path | None = None

    # 文字擦除模型权重路径，可通过 APP_MODEL_PATH 覆盖
    model_path: Path | None = None

    # 上传 & 请求限制
    max_file_size_mb: int = 50
    allowed_extensions: set[str] = {"pdf", "png", "jpg", "jpeg", "bmp", "tiff", "webp"}

    # 注册验证码邮件（SMTP，环境变量前缀仍为 APP_，如 APP_SMTP_HOST）
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    registration_code_ttl_minutes: int = 10
    registration_send_interval_seconds: int = 60
    registration_max_attempts: int = 5

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
        if self.erased_dir is None:
            self.erased_dir = self.runtime_dir / "erased"
        if self.model_path is None:
            self.model_path = _BACKEND_ROOT / "models" / "weight" / "best.pth"

        # 初始化 LLM 供应商注册表
        if self.llm_providers is None:
            self.llm_providers = {
                "openai": OpenAICompatibleConfig(),
                "anthropic": AnthropicCompatibleConfig(),
            }
        return self

    def ensure_dirs(self):
        """确保必要目录存在（应在应用启动入口显式调用）"""
        for d in [self.upload_dir, self.pages_dir, self.struct_dir, self.results_dir, self.erased_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ----- LLM 供应商查询方法 -----

    @staticmethod
    def _normalize_provider(name: str) -> str:
        return (name or "").strip().lower()

    def get_provider(self, name: str) -> LLMProviderConfig:
        """按名称获取供应商配置，不存在则抛出 ValueError"""
        key = self._normalize_provider(name)
        with _providers_lock:
            if key not in self.llm_providers:
                known = ", ".join(self.llm_providers.keys())
                raise ValueError(f"不支持的模型供应商: {key}（可选: {known}）")
            return self.llm_providers[key]

    def is_valid_provider(self, name: str) -> bool:
        with _providers_lock:
            return self._normalize_provider(name) in self.llm_providers

    def reload_providers(self) -> None:
        """重置 LLM 供应商配置为空（清除缓存）

        调用后需通过 load_providers_from_db() 重新加载用户凭据。
        """
        with _providers_lock:
            self.llm_providers["openai"] = OpenAICompatibleConfig()
            self.llm_providers["anthropic"] = AnthropicCompatibleConfig()

        self._clear_agent_cache()

    def load_providers_from_db(self, user_id: int) -> None:
        """从数据库加载用户的 LLM provider 配置，注入到 settings 中

        在请求入口调用，使整个下游链路（init_model / agent 等）
        自动使用数据库中的凭据，无需逐层传参。
        """
        from db import SessionLocal
        from db.crud import get_active_provider

        with SessionLocal() as db:
            for category, ConfigClass in [("openai", OpenAICompatibleConfig), ("anthropic", AnthropicCompatibleConfig)]:
                provider = get_active_provider(db, user_id, category)
                if provider and provider.api_key:
                    cfg = ConfigClass(
                        api_key=provider.api_key,
                        base_url=provider.base_url or "",
                        model_name=provider.model_name or ConfigClass.model_fields["model_name"].default,
                        light_model_name=provider.light_model_name or None,
                        supports_function_calling=provider.supports_function_calling if hasattr(provider, 'supports_function_calling') else True,
                    )
                    with _providers_lock:
                        self.llm_providers[category] = cfg

        self._clear_agent_cache()

    def _clear_agent_cache(self):
        """清除 agent 缓存"""
        try:
            from agents.error_correction.agent import _agent_cache, _agent_cache_lock
            with _agent_cache_lock:
                _agent_cache.clear()
        except ImportError:
            pass



settings = Settings()
