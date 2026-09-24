# Jev 数据整合试用版

我把现有公开数据统一为 **choice、noul、score** 三组，确定来源记录、质量审核和改造规则。

本版整合 JevBench 固定版本的 231 条公开题：choice 139 条、noul 74 条、score 18 条。保留原题和原标签，不翻译、不扩写。**目前全部用于评测，全部待本组人工复核。** 数据量较小、来源单一，不能据此判断模型的整体能力。

## 先看哪里

| 内容 | 位置 |
|---|---|
| 来源、质量判定、改造方式 | [GUIDELINE.md](GUIDELINE.md) |
| 本版采用的方案及原因 | [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) |
| 数据来源、固定版本、许可证 | [SOURCES.md](SOURCES.md) |
| 三组数据 | [choice](data/choice/eval.jsonl) · [noul](data/noul/eval.jsonl) · [score](data/score/eval.jsonl) |
| 每组一条完整示例 | [examples](examples) |
| 自动检查结果 | [reports/validation.json](reports/validation.json) |
| 审核表 | [REVIEW.md](REVIEW.md) |

## 字段结构

每行是一条 JSON，外层分为 `input`、`gold`、`metadata`。`input` 沿用郭导群里给出的 `state/questions`，直接提取即可作为请求主体；模型名称、调用参数在运行时配置。

- `input`：模型可见的材料、问题、选项或评分标准。
- `gold`：源数据提供的标准答案；不写模型生成的 confidence。
- `metadata`：来源网址、版本、原始样本 ID、分组、许可证和审核状态。

数据中的 `q` 是问题 ID。导师例子中的 `department` 也可以作为问题 ID，格式并不要求写死为 `q`。

## 本地试跑

需要 Python 3.10 或更新版本，无需安装第三方包。在仓库根目录执行：

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/export_inputs.py
```

最后一个命令生成 `exports/requests.jsonl`，仅保留样本 ID 和模型输入，避免把标准答案一起传给模型。

仓库已包含原始快照和转换后的数据，无需联网即可检查。重建数据用 `python scripts/prepare.py`；缺失的原始文件会从固定版本下载。重建会覆盖三组数据，也会把审核状态恢复为 pending，因此审核结果应先记录在 REVIEW.md，审核开始后不要直接覆盖正式数据。

`python scripts/validate.py --release` 是正式发布检查：在全部数据完成本组审核前，应当返回失败。普通检查通过只表示格式及基础一致性通过。

## 当前交付边界

已完成实际数据导入、格式转换、来源快照、校验及设计记录。本版没有运行 Jev 推理，没有模型得分；自动检查报告不是评测成绩。下一步按 REVIEW.md 试标，再决定是否扩充来源和引入训练集。
