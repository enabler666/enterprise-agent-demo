# 文档索引

本目录保存跨模块且需要长期维护的正式说明。第一次阅读项目时，建议先看仓库总览，再按需查看当前调用链和 API 契约；模块自身的详细启动、配置和测试说明放在对应 README 中。

| 文档 | 用途 | 何时更新 |
| --- | --- | --- |
| [requirement-api.md](requirement-api.md) | Java 需求查询 API 的权威契约，包括参数、响应和错误码 | API 行为或数据结构变化时 |
| [current-flow.md](current-flow.md) | 当前 Java 后端、Python Agent、四个 Tool 与 RAG 的职责、调用链和架构边界 | 跨模块调用或关键组件变化时 |
| [development-history.md](development-history.md) | 唯一的开发路径与版本式更新记录，包含阶段目标、状态和实际变化 | 新阶段开始、完成或验收时 |

模块文档：

- [仓库总览](../README.md)：项目定位、架构、已实现能力、快速启动和当前边界。
- [Java 后端 README](../backend/README.md)：后端 Profile、运行、测试和代码结构。
- [Python Agent README](../agent/README.md)：Agent、SSE、知识索引、聊天接口、运行和验证。

维护约定：接口细节只写入 API 契约；跨模块实现只写入调用链；开发路径、阶段状态和迭代内容统一写入开发迭代记录。其他文档引用这些权威来源，不复制大段内容。
