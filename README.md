# GLAD 智能投顾助手

这是一个基于 AI 的智能投资顾问系统，可以帮助用户进行投资规划和咨询。

## 功能特点

- 💬 智能对话：自然语言交互，理解用户需求
- 📊 投资规划：根据用户目标提供个性化建议
- 🎯 风险评估：科学评估用户风险承受能力
- 💰 资产配置：智能推荐合理的资产配置方案

## 在线访问

访问 [Streamlit Cloud 链接] 即可使用本系统。

## 本地部署

1. 克隆仓库：
```bash
git clone https://github.com/OGG4REAL/GLAD-.git
cd GLAD-
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并设置以下变量：
```
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.deepseek.com/v1
```

4. 运行应用：
```bash
streamlit run app.py
```

## Streamlit Cloud 部署

1. Fork 本仓库到您的 GitHub 账号
2. 访问 [Streamlit Cloud](https://share.streamlit.io/)
3. 使用 GitHub 账号登录
4. 点击 "New app" 按钮
5. 选择本仓库和 main 分支
6. 设置以下部署参数：
   - Python 版本：3.12
   - Main file path：app.py
7. 在 Advanced Settings 中添加环境变量：
   - OPENAI_API_KEY
   - OPENAI_API_BASE

## 注意事项

- 使用前请确保已配置正确的 API 密钥
- 所有投资建议仅供参考，请结合实际情况决策
- 如遇问题请提交 Issue 或联系管理员

## 技术栈

- 前端：Streamlit
- 后端：Python
- AI 模型：DeepSeek Chat
- 异步处理：aiohttp, asyncio

## 开发团队

- 产品设计：[团队成员]
- 技术开发：[团队成员]
- 内容支持：[团队成员]

## 版权声明

© 2024 GLAD Investment. All rights reserved.