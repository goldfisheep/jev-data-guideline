# 试用版验证记录

2026-09-24 本地运行：

- `python scripts/prepare.py`：生成 choice 139、noul 74、score 18 条。
- `python scripts/validate.py`：231 条通过自动检查，错误 0；231 条仍待人工审核。
- `python scripts/export_inputs.py`：导出 231 条，仅含 id 和 input。
- `python -m unittest discover -s tests -v`：10 项测试通过。

测试覆盖三种类型、未知选项、布尔/数值混淆、错误概率、重复 ID、跨 split 泄漏、无审核者却声称审核通过、全量转换前后内容与标签一致、导出字段不含 gold。

没有实施：模型推理、人工标签复核、人工语义近重复检查。当前不满足正式发布条件，属于可检查、可试跑的候选数据。

2026-09-25 扩展核对：

- 总计 21,461 条候选判断：choice 10,657、noul 6,831、score 3,973；新增 21,230 条。
- `python scripts/validate.py`：结构、来源文件 SHA-256 和跨 split 基础检查通过；错误 0，待本组人工审核 21,461 条。
- `python scripts/export_inputs.py`：生成 21,461 个只含输入的请求，标准答案未进入导出文件。
- `python scripts/audit_integrated.py`：按来源统计，并识别 1,067 个在不同来源中出现的相同输入文本。
- `python -m unittest discover -s tests -v`：13 项测试通过，包括配对题与拆分后的五问题案例检查。

扩展数据仍未做模型推理、人工标注复核或人工语义去重。`teacher_model` 标签与报告为人工来源的分布分开标记。
