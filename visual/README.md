# CLEVR 图像评测试用子集

本目录单独存放 32 条带真实图片的 VLM（视觉语言模型）评测候选，不计入根目录的 21,461 条纯文本评测题。每张验证集图片选取遇到的第一道问题；同一图片的其他问题不重复计数。本子集只用于检查图像输入、是非判断和选项选择链路，规模和题型都不足以代表完整 VLM 能力。

- 来源：[CLEVR v1.0 官方数据](https://cs.stanford.edu/people/jcjohns/clevr/)，[原始 ZIP](https://dl.fbaipublicfiles.com/clevr/CLEVR_v1.0.zip)。作者：Justin Johnson、Bharath Hariharan、Laurens van der Maaten、Fei-Fei Li、Larry Zitnick、Ross Girshick；[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。本仓库只选取部分样本并增加固定选项、路径和元数据；图片本身未修改。
- `clevr_val_pilot.jsonl`：题目、选项、参考答案、相对图片路径、来源与待审核状态。参考答案是程序生成的上游标签，未经过本组人工复核。
- `images/`：对应的 32 张原始 PNG 图片。
- `manifest.json`：官方 ZIP 的版本与长度、完整验证题标注的 SHA-256、每张图片和整理后记录的 SHA-256。ZIP 很大，导入脚本按 HTTP 字节范围读取所需部分；没有保存整个 ZIP 的哈希。

运行 `python scripts/validate_visual.py` 可检查结构、图片存在性和提交文件哈希。运行 `python scripts/import_clevr.py` 可从官方 ZIP 重建；重建会覆盖本目录的数据文件。评测程序必须实际加载并传入 `input.image_path` 所指的图片字节。只把路径文字传给纯文本 Jev 请求不构成 VLM 评测。这里没有 VLM 推理结果，也没有人工审核结论。

公开的 `val` 划分有答案，因此这里将其作为本地 `eval` 候选；如果用这些题调提示词或参数，同一批题上的成绩应标记为开发成绩。
