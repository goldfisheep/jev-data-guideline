# 开源评测目录逐项核对（2026-09-25）

对照 `Jev-Fudan/开源评测数据目录.md` 的 12 项。这里的“入库”是数据整理状态，不表示经过本组人工复核或取得新的模型成绩。所列数量是**决策记录数**；同一原题可以衍生多条记录，不能当作独立样本数。

按本次确认的范围，仅收录评测用测试集，不收录训练集。

| # | 项目 | 本仓库处理 | 本次新入库 | 依据及需要注意的地方 |
|---:|---|---|---:|---|
| 1 | [JevBench](https://github.com/fstandhartinger/jevbench) | 已在试用版 | 0（原有 231） | 固定公开文件与 MIT 许可；保留原题和原标签。 |
| 2 | [jev-bench / Jevify](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 22 配置中接入 14 个测试配置 | 14,374 | 选取 [逐来源许可清单](https://github.com/uspraveen/Jevify/blob/main/docs/DATASETS.md)可明确记录的任务；上游数据按固定数据集版本保存。其余 8 配置见下文。 |
| 3 | [jev-decision-bench](https://github.com/OmarMujahid/jev-decision-bench) | 接入可独立复现的代码生成题 | 870 | 固定 MIT 版本的 `fresh_math`、`known_weakness` 生成脚本；其他任务从第三方数据动态构建，未有固定题包，其部分来源与第 2 项重合，暂列为“仅构建脚本”。 |
| 4 | [BANKING77 全量实验](https://github.com/simonmesmith/jev-banking77-experiment) | 登记，未复制该项目文件 | 0 | 项目仓库未标明许可证；其底层 BANKING77 在第 2、11 项以各自题面/候选集出现，不另将此实验的标签文件计成一套新来源。 |
| 5 | [三数据集分类对照](https://github.com/dhruvmehra/jevbench) | 登记，未重造该次随机抽样 | 0 | 项目 MIT；脚本从 SST-2、AG News、BANKING77 拉取并抽样，未发布独立题包。前两个数据许可需分别核对；BANKING77 已在其他来源出现。 |
| 6 | [BTZSC pilot](https://github.com/AbdelStark/jev-benchmarks) | 登记，暂不复制底层数据 | 0 | 评测代码 Apache-2.0；依赖的 [BTZSC 数据集](https://huggingface.co/datasets/btzsc/btzsc)目前未见明确许可证字段，配置只给抽样规则。 |
| 7 | [KaLM-Jev](https://github.com/KaLM-Embedding/KaLM-Jev) | 登记，暂不复制 36 案例 | 0 | `tests/semantic_cases.json` 确实存在，但仓库未见明确许可证；另外引用的 JevBench 231 条与第 1 项重复。 |
| 8 | [Laya](https://github.com/NandhaKishorM/laya) | 接入引用的 typed-decisions 和单独公开的中文案例 | 2,064 | [typed-decisions](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) 400 个测试案例拆成 2,000 个判断，Apache-2.0，**参考标签来自教师模型**；[中文 64 案例](https://github.com/NandhaKishorM/laya/tree/main/research/benchmarks/feishu_zh) 为另一个公开子基准，标明合成来源及独立 MIT 许可。两者各计一次。 |
| 9 | [embodied-jev](https://github.com/FBddcz/embodied-jev) | 登记为仿真配置 | 0 | `benchmarks/*.json` 给出机器人任务和随机种子；需要执行环境生成观察与成功/失败结果，不是可直接转成静态 `state/questions/gold` 的题包。 |
| 10 | [Open-Jev](https://github.com/Zefan-Cai/Open-Jev) | 登记为重复评测 | 0 | 报告复用 JevBench 公开 231 题；不重复复制或加总。 |
| 11 | [eve-rlcd](https://github.com/anthony-maio/eve-rlcd/releases/tag/data-v1) | 固定发布包中许可清楚的四个子源 | 3,822 | bitext、BANKING77、BoolQ、合成 triage：原测试包共 4,000 条，178 条有序评分含“以上都不是”，无法直接保持评分档位含义，原样保存在许可范围内的来源子集中，未强制改造。其他 4,000 条涉及 AG News、MNLI、SST-5、Yelp 等，许可不够清晰，未复制。 |
| 12 | [Jev Frontier 100](https://github.com/softpudding/jev-frontier-100) | 全量接入 | 100 | MIT，AI 辅助合成题；50 组变体以 pair_id 关联，不按 100 个独立原题处理。 |

本次新增 21,230 条，加上原有 231 条，共 **21,461 条候选记录**。其中 choice 10,657、noul 6,831、score 3,973。全部保持 `metadata.review.status=pending`；人工审核尚未完成。

## 暂缓的 Jevify 配置

共 8 个：`mnli`、`sst5`、`yelp5`、`stsb`、`fever_evidence`、`paws`、`sms_spam`、`chaosnli`。上游清单中有“research/other/unspecified/unknown”声明，或原始数据源展示空许可证、混合许可证。保存名称、来源和暂缓原因；不将原始测试文件放入已提交仓库。若后续确认具体许可，再逐配置加入。

## 质量及重复风险

- JevBench、Jev Frontier 100、代码生成题和中文案例存在合成样本；保留生成方式，不能称作人类自然问题。
- typed-decisions 的 `gold.distribution` 是教师模型三次输出均值。它按你确认的方式单独标记为 `teacher_model`；不当作人工投票分布。已收录的 Jevify 配置中，`go_emotions`、`civil_comments`、`measuring_hate_speech` 报告了人工标注者分布，逐条保留来源说明；第四个 `chaosnli` 因许可待核而暂缓。
- BANKING77、BoolQ 等在多个项目重复出现，但问题说明、候选集或抽样可能不同。评测汇总必须报告来源子集，不应把相同底层语料计成完全独立覆盖。
- 评分中带“以上都不是”的 178 条仍可查看原始文件；若要纳入统一评分集，需要另定规则，目前没有改动其任务含义。
- 精确文本核查发现 1,067 个输入内容跨来源重复出现，其中 HelpSteer2 的同一回答被用在两个不同的评分维度，另有 BANKING77 跨项目复用。详见 `reports/integration_audit.json`。这些是风险提示，不是自动去重或人工确认的语义重复数。
- 自动格式检查只证明结构及基本一致性；语义近重复、许可原文和标签正确性仍需专项复核。

已固定版本、原始文件网址和校验值见 `sources/manifest.json` 与 `sources/extended_manifest.json`，各条记录的 metadata 也指向原始数据。这个清单不是法律意见；对许可不明确的数据遵照本次“先登记、暂不复制”的选择。
