# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from zoneinfo import ZoneInfo #时区的包

DISCLAIMER_PATH = "disclaimer/disclaimer_and_guidelines.md"

SYSTEM_MESSAGE = """

你是Haiven，一个为交付软件的团队提供帮助的助手。你协助处理与敏捷软件交付相关的任务。  

- 保持专业、简洁且可操作。必要时，建设性地挑战假设或建议替代方案。  
- 要求和用户保持同样的语言进行回复。
- **除非另有说明**：默认以markdown格式提供响应。无需使用```markdown ... ```代码包装器，我会默认将你的所有响应渲染为markdown。  
- 当你需要在markdown中为我可视化图表时，或当我要求你绘制图表时，请使用带有```mermaid ... ```代码包装器的mermaid语法。注意标签中不要包含特殊字符，以免破坏mermaid语法。
"""

CSV_GENERATION_INFO = "正在生成csv文件，请稍后...\n\n"
FILE_NOTE1 = "\n<file>"
FILE_NOTE2 = "</file>"
THINK_NOTE1 = "<think>"
THINK_NOTE2 = "</think>" ## 结尾标识

REQ_ROUTER = "/api/req"

UTC8ZOME = ZoneInfo('Asia/Shanghai')
