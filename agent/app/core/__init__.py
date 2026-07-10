"""跨模块配置与异常包，避免路由、工具和 Client 各自读取环境变量。"""

from app.core.config import Settings

__all__ = ["Settings"]
