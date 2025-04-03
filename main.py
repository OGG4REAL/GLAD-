import streamlit as st
from src.managers.conversation_manager import ConversationManager
from src.managers.state_manager import StateManager
from src.config.config_manager import ConfigManager
import asyncio

class ChatUI:
    def __init__(self):
        self.init_session_state()
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.conversation_manager = ConversationManager(
            config_manager=self.config_manager,
            state_manager=self.state_manager
        )
    
    def init_session_state(self):
        """初始化session state"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'risk_assessment_complete' not in st.session_state:
            st.session_state.risk_assessment_complete = False
        if 'current_module' not in st.session_state:
            st.session_state.current_module = 'chat'  # 默认为普通对话模块
    
    def check_module_access(self, module_name: str) -> bool:
        """检查是否可以访问特定模块"""
        if module_name == 'chat':
            return True  # 对话模块永远可以访问
        
        if not st.session_state.risk_assessment_complete:
            st.warning(f"访问{module_name}需要先完成风险评估！您可以在侧边栏的"风险评估"页面完成评估。")
            return False
        return True
    
    async def process_message(self, user_input: str):
        """处理用户消息"""
        if not user_input:
            return
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 获取助手回复
        response = await self.conversation_manager.chat(user_input)
        
        # 添加助手消息
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    def render(self):
        """渲染对话界面"""
        st.title("GLAD 智能投顾助手")
        
        # 侧边栏显示系统状态
        with st.sidebar:
            st.subheader("系统状态")
            config = self.config_manager.to_dict()
            
            # 显示风险评估状态
            if st.session_state.risk_assessment_complete:
                st.success("✅ 风险评估已完成")
            else:
                st.warning("⚠️ 风险评估未完成")
            
            st.markdown("---")
            
            # 显示核心投资信息
            st.write("💰 核心投资信息:")
            st.write(f"- 目标金额: {config['core_investment']['target_value']}")
            st.write(f"- 投资年限: {config['core_investment']['years']}")
            st.write(f"- 初始资金: {config['core_investment']['initial_investment']}")
            
            if config['risk_profile']['score'] is not None:
                st.write("\n📊 风险评估:")
                st.write(f"- 评估得分: {config['risk_profile']['score']}")
                st.write(f"- 风险容忍度: {config['risk_profile']['tolerance']}")
            
            if config['portfolio']['assets']:
                st.write("\n📈 当前投资组合:")
                for asset, weight in zip(config['portfolio']['assets'], config['portfolio']['weights']):
                    st.write(f"- {asset}: {weight*100:.1f}%")
            
            # 模块选择（示例）
            st.markdown("---")
            st.subheader("功能模块")
            modules = {
                'chat': '💬 普通对话',
                'portfolio': '📊 投资组合',
                'analysis': '📈 市场分析',
                'recommendation': '🎯 个性化建议'
            }
            
            for module_id, module_name in modules.items():
                if st.button(module_name, key=f"btn_{module_id}"):
                    if self.check_module_access(module_id):
                        st.session_state.current_module = module_id
                        st.rerun()
        
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # 输入框
        if user_input := st.chat_input("请输入您的问题或需求"):
            # 使用asyncio处理异步操作
            asyncio.run(self.process_message(user_input))
            st.rerun()

def main():
    chat_ui = ChatUI()
    chat_ui.render()

if __name__ == "__main__":
    main()