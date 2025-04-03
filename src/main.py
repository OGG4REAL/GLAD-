from typing import Dict, Optional
from src.managers.state_manager import StateManager, ConversationState
from src.managers.conversation_manager import ConversationManager
from src.config.config_manager import ConfigManager

class FinancialAdvisor:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.conversation_manager = ConversationManager(
            config_manager=self.config_manager,
            state_manager=self.state_manager
        )
    
    async def chat(self, user_input: str) -> str:
        """处理用户输入并生成回复"""
        # 1. 记录用户输入
        self.state_manager.add_message("user", user_input)
        
        # 2. 分析用户输入
        analysis = await self.conversation_manager.analyze_input(user_input)
        
        # 3. 确定对话策略
        strategy = self.conversation_manager.determine_strategy(analysis)
        
        # 4. 根据策略更新状态
        self._update_state(strategy, analysis)
        
        # 5. 生成回复
        response = await self.conversation_manager.generate_response(strategy, analysis)
        
        # 6. 记录系统回复
        self.state_manager.add_message("assistant", response)
        
        return response
    
    def _update_state(self, strategy: Dict, analysis: Dict) -> None:
        """根据策略和分析结果更新状态"""
        current_state = self.state_manager.current_state
        
        # 处理状态转换
        if strategy["next_action"] == "start_risk_assessment":
            if self.state_manager.can_transition_to(ConversationState.RISK_ASSESSMENT):
                self.state_manager.transition_to(ConversationState.RISK_ASSESSMENT)
        
        elif strategy["next_action"] == "summarize_and_conclude":
            if self.state_manager.can_transition_to(ConversationState.FREE_CHAT):
                self.state_manager.transition_to(ConversationState.FREE_CHAT)
        
        # 更新问题计数器
        is_question = analysis.get("intent") == "question"
        self.state_manager.update_question_counter(is_question)
        
        # 更新当前关注点
        if strategy.get("next_action", "").startswith("ask_for_"):
            focus_item = strategy["next_action"].replace("ask_for_", "")
            self.state_manager.set_focus(focus_item)
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return self.config_manager.to_dict()
    
    def is_core_info_complete(self) -> bool:
        """检查核心信息是否完整"""
        return self.config_manager.is_core_info_complete()

async def main():
    advisor = FinancialAdvisor()
    
    print("GLAD 智能投顾助手已启动。")
    print("我们将帮助您：")
    print("1. 收集投资目标信息")
    print("2. 评估风险承受能力")
    print("3. 了解您的个人情况")
    print("\n输入 'quit' 退出对话。")
    
    while True:
        try:
            user_input = input("\n用户: ")
            if user_input.lower() == 'quit':
                break
                
            response = await advisor.chat(user_input)
            print(f"\n助手: {response}")
            
            # 每次都打印当前配置
            print("\n当前系统状态:")
            config = advisor.get_config()
            print("核心投资信息:")
            print(f"  目标金额: {config['core_investment']['target_value']}")
            print(f"  投资年限: {config['core_investment']['years']}")
            print(f"  初始资金: {config['core_investment']['initial_investment']}")
            
            if config['risk_profile']['score'] is not None:
                print("\n风险评估:")
                print(f"  评估得分: {config['risk_profile']['score']}")
                print(f"  风险容忍度: {config['risk_profile']['tolerance']}")
            
            if config['portfolio']['assets']:
                print("\n当前投资组合:")
                for asset, weight in zip(config['portfolio']['assets'], config['portfolio']['weights']):
                    print(f"  {asset}: {weight*100:.1f}%")
            
            print("\n" + "-"*50)
                
        except Exception as e:
            print(f"\n系统错误: {str(e)}")
            print("请重试或输入 'quit' 退出对话。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())