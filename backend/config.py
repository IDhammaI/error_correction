from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
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
        return self

    def ensure_dirs(self):
        """确保必要目录存在（应在应用启动入口显式调用）"""
        for d in [self.upload_dir, self.pages_dir, self.struct_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
