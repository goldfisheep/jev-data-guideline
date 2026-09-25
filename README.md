# Jev 数据整合试用版

我把现有公开数据统一为 **choice、noul、score** 三组，确定来源记录、质量审核和改造规则。

本版按开源目录逐项核对并整合了 **21,461 条候选判断**：choice 10,657、noul 6,831、score 3,973。记录来自多个来源，部分原题被拆成数个判断，部分底层语料也跨项目出现；计数不能等同于独立题数。**目前全部用于评测，全部待本组人工复核。**

本次范围已确认：**仅收录评测用测试集**，不纳入训练集。

## 先看哪里

| 内容 | 位置 |
|---|---|
| 来源、质量判定、改造方式 | [GUIDELINE.md](GUIDELINE.md) |
| 本版采用的方案及原因 | [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) |
| 数据来源、固定版本、许可证 | [SOURCES.md](SOURCES.md) |
| 开源目录 12 项逐条接入/暂缓原因 | [SOURCE_AUDIT_2026-09-25.md](SOURCE_AUDIT_2026-09-25.md) |
| 三组数据 | [choice](data/choice) · [noul](data/noul) · [score](data/score) |
| 每组一条完整示例 | [examples](examples) |
| 自动检查结果 | [reports/validation.json](reports/validation.json) |
| 来源分布与重复风险 | [reports/integration_audit.json](reports/integration_audit.json) |
| 审核表 | [REVIEW.md](REVIEW.md) |

## 字段结构

每行是一条 JSON，外层分为 `input`、`gold`、`metadata`。`input` 沿用郭导群里给出的 `state/questions`，直接提取即可作为请求主体；模型名称、调用参数在运行时配置。

- `input`：模型可见的材料、问题、选项或评分标准。
- `gold`：源数据提供的参考标签；来源是人工、合成规则还是教师模型，见 metadata。不写待测模型生成的 confidence。
- `metadata`：来源网址、版本、原始样本 ID、分组、许可证和审核状态。

数据中的 `q` 是问题 ID。导师例子中的 `department` 也可以作为问题 ID，格式并不要求写死为 `q`。

## 本地试跑

需要 Python 3.10 或更新版本，无需安装第三方包。在仓库根目录执行：

```sh
python scripts/validate.py
python scripts/audit_integrated.py
python -m unittest discover -s tests -v
python scripts/export_inputs.py
```

最后一个命令在本地生成 `exports/requests.jsonl`，仅保留样本 ID 和模型输入，避免把标准答案一起传给模型。该导出文件可随时重建，不纳入仓库提交。

仓库已包含获准接入的原始快照和转换后的数据，无需联网即可检查。JevBench 原有数据可用 `python scripts/prepare.py` 重建；扩展数据用 `python scripts/prepare_extended.py`，另需安装 `pyarrow` 以读取 typed-decisions 的原始 Parquet。重建会覆盖对应转换文件，也会把审核状态恢复为 pending，因此审核开始后不要直接覆盖正式数据。

`python scripts/validate.py --release` 是正式发布检查：在全部数据完成本组审核前，应当返回失败。普通检查通过只表示格式及基础一致性通过。

## 当前交付边界

已完成实际数据导入、格式转换、来源快照、校验及设计记录。本版没有运行 Jev 推理，没有新的模型得分；自动检查报告不是评测成绩。部分来源使用教师模型或合成规则标签，见逐项清单。下一步按 REVIEW.md 试标，再讨论正式冻结。
