# Jev 单轮训练候选数据

这里新增 **14,800 条训练判断**和 **3,630 条验证判断**，按 choice（选项选择）、noul（是／否）、score（有序评分）分开。原来的 `data/` 仍是 21,461 条评测题，不参与训练或校准。一个 typed-decisions 案例含五个判断，所以“判断数”不等于独立案例数。

本目录对应《jev数据格式.md》的**单轮／短程监督训练**部分。SFT（监督微调）指用已给出的参考标签训练模型；验证集用于挑选训练方案和调整输出概率。这里提供数据，**尚未训练模型，也未完成组内人工标签复核**。

| 来源 | 训练判断 | 验证判断 | 标签与许可 |
|---|---:|---:|---|
| [Jevify BANKING77](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 2,000 | 459 | 银行意图原标签；CC BY 4.0 |
| [Jevify GoEmotions](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 2,000 | 499 | 原标签及部分人工投票分布；Apache 2.0 |
| [Jevify BoolQ](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 2,000 | 472 | 阅读问答原标签；CC BY-SA 3.0 |
| [Jevify HelpSteer2 helpfulness](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 2,000 | 500 | 回答帮助程度原评分；CC BY 4.0 |
| [Jevify Measuring Hate Speech](https://huggingface.co/datasets/Praveenrajus/jev-bench) | 2,000 | 500 | 原评分及部分人工投票分布；CC BY 4.0 |
| [typed-decisions](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) | 4,800 | 1,200 | **教师模型参考标签**；Apache 2.0 |

Jevify 使用官方 train/validation 文件，从每个来源的 8,000 条训练候选中，按原始 ID 的 SHA-256 排序确定性选取 2,000 条；不人为平衡标签。官方验证题保留可用部分。先按标准化题面排除与现有评测集完全相同的内容，再排除训练／验证间相同题面。BANKING77 原训练候选排除了 625 条与评测重合的题面，验证候选排除了 41 条；GoEmotions 分别排除了 13 条和 1 条。其他来源没有发现这种精确重合。**这不保证没有语义相近的题目**，正式使用前仍需人工或更强的去重检查。

typed-decisions 的官方 train 划分有四类工作流、每类 300 个案例。按案例 ID 固定排序，每类取 60 个案例作本地验证，其余 240 个作训练；同一案例的五个问题始终在同一边。其 6,000 个判断中，4,800 用于训练、1,200 用于验证。教师模型给出的分布写在 `gold.distribution` 并标明来源，不能称作人工真值或模型实测成绩。

## 文件怎么用

- `data/train/{choice,noul,score}/`：监督训练候选。每行一个 JSON，`input` 是模型可见内容，`gold` 是参考标签。
- `data/validation/{choice,noul,score}/`：独立于训练的验证题，用于选择方案、做概率校准；不要当训练题。
- `sources/` 和 [source_manifest.json](source_manifest.json)：选中原始行的压缩快照、原网址、固定版本、整文件与分片的 SHA-256。较大文件分片保存；按清单顺序拼回、解压即可还原选中的原始行。
- [reports/validation.json](reports/validation.json)：自动结构、来源哈希、训练／验证／评测精确重合检查结果。

三组沿用评测数据的字段结构，但 `metadata.split` 写 `train` 或 `validation`。`metadata.original_split` 保留来源划分。参考标签不填凭空猜测的 `confidence_label`；有来源的人工或教师分布才作为附加字段保存。BANKING77 有 77 个选项，若训练模型只支持较少候选，须另设计候选召回，不能悄悄截断选项和答案。

本次没有加入真正的长程训练轨迹：目录里的 embodied-jev 是仿真配置，eve-rlcd 的公开训练形式主要是单步决策。长程 SFT（有专家逐步示范的监督训练）需要逐步状态、可执行动作、专家动作与结果；长程 RL（强化学习）还需要可运行的环境、终止条件和可计算奖励。不能把 typed-decisions 中的“轨迹摘要”当成逐步轨迹。

## 检查和重建

在仓库根目录运行 `python scripts/validate_training.py` 检查已提交数据，无需联网。需要从固定上游文件重新选样时，先安装 `pyarrow`，然后运行：

```sh
python scripts/download_training_sources.py
python scripts/select_training_sources.py
python scripts/build_training.py
python scripts/validate_training.py
```

前两步下载的完整上游文件只放在忽略提交的 `.local/`；仓库保存选中行的来源快照和哈希。重建会覆盖本目录的转换结果，并将审核状态恢复为 `pending`。自动检查通过只说明格式和精确重合检查通过，不代表标签已被本组确认，也不保证模型在实际游戏或其他新场景中有效。
