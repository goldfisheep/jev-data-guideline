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

## 后续已接入来源

12 个目录项目的逐项状态、实际新增数量与未接入原因见 [SOURCE_AUDIT_2026-09-25.md](SOURCE_AUDIT_2026-09-25.md)。下表列原始文件入口；确切 commit、文件 SHA-256 和筛选信息统一写在 [sources/extended_manifest.json](sources/extended_manifest.json)。

| 来源快照 | 上游入口 | 本次记录 | 标签性质 |
|---|---|---:|---|
| [Jevify 14 个测试配置](sources/jevify) | [Hugging Face 数据集](https://huggingface.co/datasets/Praveenrajus/jev-bench) · [来源与许可清单](https://github.com/uspraveen/Jevify/blob/main/docs/DATASETS.md) | 14,374 | 原数据集标签；部分含人工投票分布 |
| [Jev Frontier 100](sources/jev-frontier-100/items.jsonl) | [项目数据](https://github.com/softpudding/jev-frontier-100/tree/main/data) | 100 | AI 辅助合成参考答案 |
| [Laya 中文案例](sources/laya-feishu/cases.jsonl) | [原案例](https://github.com/NandhaKishorM/laya/tree/main/research/benchmarks/feishu_zh) | 64 | AI 辅助合成参考答案 |
| [typed-decisions 原始测试文件](sources/typed-decisions/test.parquet) | [Hugging Face 数据集](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) | 2,000 | 教师模型参考标签，400 案例 × 5 判断 |
| [eve-rlcd 许可明确的测试子集](sources/eve-rlcd) | [data-v1 发布包](https://github.com/anthony-maio/eve-rlcd/releases/tag/data-v1) | 3,822 | 原来源/代码生成标签；原许可子集共 4,000 条，178 条评分暂缓 |
| [jev-decision-bench 生成脚本与结果](sources/jev-decision-bench) | [项目构建脚本](https://github.com/OmarMujahid/jev-decision-bench/tree/main/builders) | 870 | 固定种子的程序计算答案 |

本次只提交许可声明可确认的数据。项目仓库本身的开源许可证，不会自动覆盖其引用的第三方数据；每条样本的 `metadata.license` 记录对应的来源声明。原始文件中若包含不属于统一格式的记录，仍在来源快照保留；转换脚本会说明暂缓原因。

较大的快照按字节分片保存在来源目录，`extended_manifest.json` 为每片记录 SHA-256，同时保留完整原文件的 SHA-256。`prepare_extended.py` 会自动拼接和验证，不需要手工还原。
