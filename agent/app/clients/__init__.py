"""外部服务 Client 包。

在此集中导出 Client，调用方无需记住具体文件路径；后续替换实现时可保持导入路径不变。
"""

from app.clients.requirement_client import RequirementClient

__all__ = ["RequirementClient"]
