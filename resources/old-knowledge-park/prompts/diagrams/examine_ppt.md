---
identifier: examine-ppt-123456abc
title: "EXAMINE AND UPDATE PPT Scheme"
categories: ["analysis"]

help_prompt_description: "EXAMINE AND UPDATE PPT Scheme"

---
## 任务
你需要根据以下规则检查原始PPT制作方案中是否存在问题，如果存在问题则修改原始PPT制作方案并且输出修改后的PPT制作方案

## 原始PPT制作方案
{original_scheme}

## 预定义的版式列表（格式为'版式：['占位符1','占位符2']'）
仅标题:['Title 1']
标题和内容:['Title 1', 'Content Placeholder 2']
1_Title and Content:['Title 1', 'Picture Placeholder 2', 'Picture Placeholder 3']
2_Title and Content:['Title 2', 'Picture Placeholder 1', 'Picture Placeholder 3', 'Picture Placeholder 4', 'Picture Placeholder 5', 'Picture Placeholder 6', 'Picture Placeholder 7']
3_Title and Content:['Title 1', 'Picture Placeholder 2', 'Picture Placeholder 3', 'Picture Placeholder 4', 'Picture Placeholder 5', 'Picture Placeholder 6', 'Picture Placeholder 7']
1_Title Only_Black:['Title 1', 'Picture Placeholder 2', 'Picture Placeholder 3', 'Picture Placeholder 4', 'Picture Placeholder 5', 'Picture Placeholder 6', 'Picture Placeholder 7']
Title and Content_Black:['Title 1', 'Content Placeholder 2']
Two Column Slide:['Title 1', 'Content Placeholder 2', 'Content Placeholder 3']
Two Column Slide_Black:['Title 1', 'Content Placeholder 2', 'Content Placeholder 3']
Three Column Slide:['Title 1', 'Content Placeholder 2', 'Content Placeholder 3', 'Content Placeholder 4']
Three Column Slide_Black:['Title 1', 'Content Placeholder 2', 'Content Placeholder 3', 'Content Placeholder 4']
Title w/Image:['Title 1', 'Content Placeholder 2', 'Picture Placeholder 3']
Title w/Image_Black:['Title 1', 'Content Placeholder 2', 'Picture Placeholder 3']
Quote Layout:['Text Placeholder 1', 'Text Placeholder 2']
Quote Layout_Black:['Text Placeholder 1', 'Text Placeholder 2']
Quote Layout_Color:['Text Placeholder 1', 'Text Placeholder 2']
Content w/ Product:['Title 3', 'Picture Placeholder 1', 'Content Placeholder 2']
Content w/ Product_Black:['Title 3', 'Picture Placeholder 1', 'Content Placeholder 2']

## 规则
使用`#`定义幻灯片主标题，使用 `##` 定义幻灯片副标题，使用 `-`定义列表（支持多级嵌套），使用`---` 定义分割符，包含关系为：幻灯片主标题包含幻灯片副标题，幻灯片副标题包含列表
- 检查所有幻灯片主标题下一行是否为幻灯片副标题
- 检查所有`---` 分隔符下一行是否为幻灯片主标题
- 检查所有幻灯片副标题后是否都标注了预定义的版式（标注的版式与副标题在同一行），并且没有标注到幻灯片主标题后
- 检查幻灯片副标题后标注的版式是否严格对应预定义的版式列表中某个版式（请勿擅自对版式列表中的版式进行中英文转换，需要确保与版式列表中的版式字符完全一致）
- 检查最上层列表项（即`-`前无空格的列表项）后是否都标注了占位符，并且该占位符是列表项所在幻灯片的副标题中标注的版式所包含的占位符之一
- 包含'Picture Placeholder'的占位符前的列表内容需要用以下格式给出
  - 内容不要分行
  - 只包含图片描述和下载地址，二者使用`;`进行分割，并且键名固定为图片描述和下载地址（例如"- 图片描述：xxxxx;下载地址:xxxxxx（Picture Placeholder 3）"）
  - 若该图片不是用户需求中提供的而是你生成的则下载地址后接`none`（例如"- 图片描述：xxxxx;下载地址:none（Picture Placeholder 3）"）
  - 副标题后标注的版式的占位符应该包含包含'Picture Placeholder'的占位符
- 原始原始PPT制作方案中符合规则的部分不要随意更改

             
## 输出格式
直接输出修改后的PPT制作方案，需要附带开始符号 （'```','ppt'），并且输出的修改后的PPT制作方案后不要再输出任何文字

例如

```
ppt
# 幻灯片标题
## 幻灯片副标题（标题和内容）

- 列表项1（Content Placeholder 2）
- 列表项2（Content Placeholder 2）

## 幻灯片副标题（注释）（Title and Content_Black）

- 列表项1（Content Placeholder 2）
  - 列表项1-1
- 列表项2（Content Placeholder 2）

---
# 幻灯片标题
## 幻灯片副标题（Title w/Image）

- 列表项1（Content Placeholder 2）
- 图片描述：一张用户下单流程图，需要涵盖用户下单的完整流程;下载地址:none（Picture Placeholder 3）