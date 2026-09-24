# 数据来源

## 已实际接入

来源：[fstandhartinger/jevbench](https://github.com/fstandhartinger/jevbench)

固定版本：[f8ce71361165846101d02ebc83ad44e47ae44fc3](https://github.com/fstandhartinger/jevbench/tree/f8ce71361165846101d02ebc83ad44e47ae44fc3)。本版以固定快照为准，不声称它是最新版本。

| 原始文件 | 条数 | 在线定位 |
|---|---:|---|
| original.jsonl | 72 | [原文件](https://github.com/fstandhartinger/jevbench/blob/f8ce71361165846101d02ebc83ad44e47ae44fc3/datasets/public/original.jsonl) |
| easy.jsonl | 48 | [原文件](https://github.com/fstandhartinger/jevbench/blob/f8ce71361165846101d02ebc83ad44e47ae44fc3/datasets/public/easy.jsonl) |
| hard.jsonl | 111 | [原文件](https://github.com/fstandhartinger/jevbench/blob/f8ce71361165846101d02ebc83ad44e47ae44fc3/datasets/public/hard.jsonl) |

三文件合计 231 条，转换后 choice 139、noul 74、score 18。样本级 label_basis 和 license 取自原文件 provenance，不代表本组已独立验证标签。

许可证：MIT；[固定版本许可证](https://github.com/fstandhartinger/jevbench/blob/f8ce71361165846101d02ebc83ad44e47ae44fc3/LICENSE)，本地保留于 [sources/jevbench/LICENSE](sources/jevbench/LICENSE)。原始数据及其改造副本沿用上游许可和归属。本仓库自己的规范与工具暂未另行指定开源许可证。

原始快照、逐文件 URL 和 SHA-256 见 [sources/manifest.json](sources/manifest.json)。复现顺序：核对快照哈希 → 运行 prepare.py → 运行 validate.py。

## 格式参考

导师提供的 choice 请求示例是本版字段结构的起点。类型解释参考 TypeSafe 文档：[Score](https://docs.typesafe.ai/primitives/score)、[Noul](https://docs.typesafe.ai/primitives/noul)。查阅日期：2026-09-24。本版是组内数据容器规范，不声明完全覆盖当前 API 的所有输入形式。

其他项目暂未接入本仓库；没有下载和核查的数据不计入数据量。
