from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#  BaseSettings 自动从 .env 读同名变量覆盖默认值。
class AppSettings(BaseSettings):
    app_name: str = "智能研究系统"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    #SettingsConfigDict 新版写法，用来获取.env 文件的完整路径， 只要创建这个类实例 BaseSettings 子类就能自动找.env 并校验读取到配置
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),  #Path(__file__) 获取当前文件的完整绝对路径， .parentsz找当前文件所处的目录
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def cors_origins(self) -> list[str]:
        values = [item.strip() for item in self.cors_allow_origins.split(",")]
        return [item for item in values if item]
