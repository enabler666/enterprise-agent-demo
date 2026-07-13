# 文档索引

本目录只保存跨模块且需要长期维护的文档。模块自身的启动、配置和测试说明放在对应模块 README 中，避免同一操作在多处重复。

| 文档 | 用途 | 何时更新 |
| --- | --- | --- |
| [requirement-api.md](requirement-api.md) | Java 需求查询 API 的权威契约，包括参数、响应和错误码 | API 行为或数据结构变化时 |
| [current-flow.md](current-flow.md) | 当前 Java 后端与 Python Agent 的职责、调用链和架构边界 | 跨模块调用或关键组件变化时 |
| [development-history.md](development-history.md) | 唯一的开发路径与版本式更新记录，包含阶段目标、状态和实际变化 | 新阶段开始、完成或验收时 |

模块文档：

- [仓库总览](../README.md)：项目范围、目录和最短启动路径。
- [Java 后端 README](../backend/README.md)：后端 Profile、运行、测试和代码结构。
- [Python Agent README](../agent/README.md)：Agent 配置、聊天接口、运行和验证。

维护约定：接口细节只写入 API 契约；跨模块实现只写入调用链；开发路径、阶段状态和迭代内容统一写入开发迭代记录。其他文档引用这些权威来源，不复制大段内容。
