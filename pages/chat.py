import streamlit as st
from src.managers.conversation_manager import ConversationManager
from src.managers.state_manager import StateManager
from src.config.config_manager import ConfigManager
import asyncio

class ChatUI:
    def __init__(self):
        self.init_session_state()
        
        # 从session_state获取或初始化managers
        if 'managers' not in st.session_state:
            print("初始化管理器...")
            st.session_state.managers = {
                'config_manager': ConfigManager(),
                'state_manager': StateManager(),
            }
            st.session_state.managers['conversation_manager'] = ConversationManager(
                config_manager=st.session_state.managers['config_manager'],
                state_manager=st.session_state.managers['state_manager']
            )
        
        # 使用session_state中的managers
        self.config_manager = st.session_state.managers['config_manager']
        self.state_manager = st.session_state.managers['state_manager']
        self.conversation_manager = st.session_state.managers['conversation_manager']
    
    def init_session_state(self):
        """初始化session state"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'risk_assessment_complete' not in st.session_state:
            st.session_state.risk_assessment_complete = False
    
    def format_amount(self, amount):
        """格式化金额显示"""
        if amount is None:
            return '未设置'
        if amount >= 10000000:  # 大于1000万
            return f"{amount/10000000:.1f}千万"
        elif amount >= 10000:   # 大于1万
            return f"{amount/10000:.1f}万"
        else:
            return f"{amount:,.0f}"
    
    async def process_message(self, user_input: str):
        """处理用户消息"""
        if not user_input:
            return
        
        try:
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 获取助手回复
            with st.spinner('思考中...'):
                response = await self.conversation_manager.chat(user_input)
                print(f"\n获取到助手回复: {response}")
                
                if response:
                    # 添加助手消息
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    print("消息已添加到会话状态")
                else:
                    print("警告：收到空回复")
                    st.error("抱歉，我现在无法生成回复。请重试。")
            
        except Exception as e:
            print(f"\n❌ 处理消息时出错: {str(e)}")
            st.error(f"处理消息时出错: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "抱歉，我现在遇到了一些问题。请稍后再试。"
            })
    
    def render(self):
        """渲染对话界面"""
        st.title("💬 智能对话")
        
        # 侧边栏显示系统状态
        with st.sidebar:
            st.subheader("系统状态")
            config = self.config_manager.to_dict()
            
            # 显示当前对话阶段
            state_labels = {
                'initial': '初始状态',
                'collecting_core_info': '收集核心信息',
                'risk_assessment': '风险评估',
                'collecting_extra_info': '收集额外信息',
                'completed': '已完成'
            }
            current_state = self.state_manager.current_state.value
            st.info(f"当前阶段：{state_labels.get(current_state, current_state)}")
            
            # 显示风险评估状态
            if st.session_state.get("risk_assessment_complete"):
                st.success("✅ 风险评估已完成")
                if config.get('risk_profile', {}).get('score') is not None:
                    st.write("\n📊 风险评估结果:")
                    st.write(f"- 评估得分: {config['risk_profile']['score']}")
                    st.write(f"- 风险承受能力: {config['risk_profile']['tolerance']}")
            else:
                st.warning("⚠️ 风险评估未完成")
                st.write("完成风险评估后可以获得更个性化的建议")
                if st.button("👉 去做风险评估"):
                    st.switch_page("pages/risk_assessment.py")
            
            st.markdown("---")
            
            # 显示核心投资信息
            st.write("💰 核心投资信息:")
            core_investment = config.get('core_investment', {})
            target_value = core_investment.get('target_value')
            years = core_investment.get('years')
            initial_investment = core_investment.get('initial_investment')
            
            st.write(f"- 目标金额: {self.format_amount(target_value)}")
            st.write(f"- 投资年限: {f'{years}年' if years else '未设置'}")
            st.write(f"- 初始资金: {self.format_amount(initial_investment)}")
            
            # 显示投资组合
            portfolio = config.get('portfolio', {})
            if portfolio.get('assets') and portfolio.get('weights'):
                st.write("\n📈 当前投资组合:")
                for asset, weight in zip(portfolio['assets'], portfolio['weights']):
                    st.write(f"- {asset}: {weight*100:.1f}%")
        
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # 输入框
        if user_input := st.chat_input("请输入您的问题或需求"):
            # 创建新的事件循环来处理异步操作
            async def run_async():
                await self.process_message(user_input)
            
            asyncio.run(run_async())
            st.rerun()

def main():
    chat_ui = ChatUI()
    chat_ui.render()

if __name__ == "__main__":
    main() 
