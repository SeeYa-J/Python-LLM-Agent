# 需求智能体后端服务 (Requirement Agent Backend)

本文档大部分由AI生成。

## 项目架构

本项目采用类Spring风格的依赖注入设计，代码结构和部分可以参考的代码如下：

```
models/         # 业务实体模型层
├── base_entity.py          # 基础实体类，包含公共字段
└── business_entities.py    # 业务实体模型，对应到表

dao/            # 数据访问层
├── base_dao.py             # 基础DAO类，提供通用数据库操作
├── ai_prompt_dao.py        # AI提示词DAO
├── project_dao.py          # 项目DAO
└── domain_dao.py           # 域DAO

services/       # 业务服务层
├── prompt_service.py       # 提示词服务

controllers/    # 控制器层
├── userstory_controller.py # 用户故事控制器

api/            # API接口层
├── api_userstory.py        # 用户故事API接口

utils/          # 工具类
├── stream_utils.py        # 流式响应处理工具
└── response_utils.py       # API响应工具类
```

## 开发环境搭建

### 环境要求
- Python 3.11.8

### 安装步骤

1. 克隆项目
```bash
git clone <项目地址>
cd requirement-agent-backend
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/MacOS
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
# 复制并修改配置文件
cp .env.dev .env
# 编辑config/local.yaml设置数据库连接等参数
```

5启动服务
```bash
python main.py
```

## 依赖注入系统

本项目采用类Spring风格的依赖注入设计

### 组件声明方式

```python
# 服务层组件
@service
class PromptService:
    # 类型注解定义为类变量 - IDE友好
    ai_prompt_dao: AiSystemPromptDAO
    project_dao: BizJiraProjectDAO
    domain_dao: BizDomainDAO
    
    def __init__(self):
        pass
```

```python
# 控制器组件
@controller
class UserStoryController:
    user_story_service: PromptService
    
    def __init__(self):
        pass
```

```python
# 数据访问层组件
@repository
class AiSystemPromptDAO(BaseDAO):
    # ...
```

## 开发建议

1. **单一职责原则**
   - 每个Service和Controller只关注自己的业务领域
   - 使用依赖注入实现关注点分离
   - service和controller层细节可参考`services/prompt_service.py`和`controllers/userstory_controller.py`中的实现

2. **API接口设计原则**
   - API接口应尽量简洁明了
   - 使用RESTful风格设计API，只使用GET、POST方法
   - 返回数据格式统一，使用标准的响应模型
   - 细节可参考`api/api_userstory.py`中的实现
   - 流式响应可参考`utils/stream_utils.py`中的实现和引用


## API文档

使用swagger查看API，访问地址：`http://base_url/docs`


## 分支管理要求

1. Fork项目并克隆到本地
2. 从main拉取新的分支
   - 命名规范：`feature/your-feature-name`
   - 示例：`git checkout -b feature/add-new-feature`
3. 提交更改：push之后合并到dev分支
4. 发布测试：在gitlab网页中创建合并请求到test分支，assign给maintainer审批合并

