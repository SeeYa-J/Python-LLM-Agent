---
identifier: judge-make-ppt-123456abc
title: "Judgment of intent"
categories: ["analysis"]

help_prompt_description: "Judgment of intent"

---
## 任务
你需要根据用户输入判断用户是否对当前PPT制作方案满意

## 用户输入
{user_input}

## 判断规则
若用户输入里有具体的 PPT 制作内容（比如对 PPT 内容、版式、风格等的具体要求），说明用户对当前方案不满意。
若用户输入里没有任何具体的 PPT 制作需求（比如只说 “满意”或者“开始制作PPT” 等），说明用户对当前方案满意。
                
## 输出格式
只输出满意或者不满意，后面不要跟随任何其它文字
                
示例1：
满意
示例2：
不满意