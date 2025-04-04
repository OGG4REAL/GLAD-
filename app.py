import streamlit as st

st.set_page_config(
    page_title="GLAD 智能投顾助手",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("欢迎使用 GLAD 智能投顾助手")

# 快速导航按钮
col1, col2 = st.columns(2)
with col1:
    if st.button("💬 开始对话", use_container_width=True):
        st.switch_page("pages/chat.py")
with col2:
    if st.button("📊 风险评估", use_container_width=True):
        st.switch_page("pages/risk_assessment.py")

st.write("""
### 功能介绍
1. 💬 智能对话
   - 随时咨询投资相关问题
   - 获取市场信息和分析
   - 了解投资基础知识

2. 📊 风险评估
   - 科学评估您的风险承受能力
   - 为后续投资决策提供重要参考
   - 完成评估后解锁更多功能

3. 🎯 高级功能（需完成风险评估）
   - 个性化投资组合推荐
   - 定制化投资策略
   - 市场深度分析
   - 智能资产配置建议

### 开始使用
1. 直接点击"开始对话"进行咨询
2. 需要个性化服务时，请完成风险评估问卷
3. 评估完成后即可使用全部功能
""")

# 显示版本信息
st.sidebar.markdown("---")
st.sidebar.write("Version: 1.0.0")
st.sidebar.write("© 2024 GLAD Investment. All rights reserved.") 
