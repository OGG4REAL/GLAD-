from typing import Dict, List, Optional, Tuple
from src.managers.state_manager import StateManager, ConversationState
from src.config.config_manager import ConfigManager
from src.utils.llm_utils import LLMUtils
import json
import re

class ConversationManager:
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config_manager = config_manager
        self.state_manager = state_manager
        # 设置初始状态为信息收集
        self.state_manager.transition_to(ConversationState.COLLECTING_INFO)
        self.collection_stages = {
            'core_info': {
                'fields': ['target_value', 'years', 'initial_investment'],
                'completed': False,
                'modifiable': True
            },
            'portfolio': {
                'fields': ['assets', 'weights'],
                'completed': False,
                'modifiable': True
            },
            'additional_info': {
                'fields': [
                    'family_status',
                    'employment',
                    'income_level',
                    'debt_status',
                    'financial_obligations'
                ],
                'completed': False,
                'modifiable': True,
                'optional': True  # 标记为可选
            }
        }
        self.modification_keywords = {
            'target_value': ['目标金额', '目标', '金额'],
            'years': ['年限', '时间', '期限'],
            'initial_investment': ['初始投资', '本金', '起始资金'],
            'portfolio': ['资产配置', '投资组合', '配置']
        }
    
    async def analyze_input(self, user_input: str) -> Dict:
        """分析用户输入，提取意图和信息"""
        try:
            # 调用 LLM 进行分析
            prompt = self._build_analysis_prompt(user_input)
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.2
            )
            
            # 提取 JSON 结果
            analysis_result = LLMUtils.extract_json_from_response(response["text"])
            if not analysis_result:
                raise ValueError("无法解析 LLM 响应中的 JSON 数据")
            
            return analysis_result
            
        except Exception as e:
            return {
                "intent": "unknown",
                "emotion": "neutral",
                "extracted_info": {},
                "requires_immediate_response": True
            }
    
    def determine_strategy(self, analysis: Dict) -> Dict:
        """根据分析结果确定对话策略"""
        strategy = {
            "next_action": "continue_chat",
            "response_type": "normal",
            "focus_points": [],
            "missing_info": []
        }
        
        # 根据意图和当前状态确定策略
        if analysis["intent"] == "provide_info":
            strategy["next_action"] = "process_info"
        elif analysis["intent"] == "ask_question":
            strategy["next_action"] = "answer_question"
        elif analysis["intent"] == "express_concern":
            strategy["next_action"] = "address_concern"
        
        return strategy
    
    async def generate_response(self, strategy: Dict, analysis: Dict) -> str:
        """根据策略生成回复"""
        try:
            # 根据策略类型生成回复
            if strategy["next_action"] == "process_info":
                return await self._generate_info_response(analysis)
            elif strategy["next_action"] == "answer_question":
                return await self._generate_question_response(analysis)
            elif strategy["next_action"] == "address_concern":
                return await self._generate_concern_response(analysis)
            else:
                return "我明白了。让我们继续讨论您的投资需求。"
        except Exception as e:
            return f"抱歉，我现在无法正确处理您的请求。请您重新表述，或稍后再试。"
    
    async def _generate_info_response(self, analysis: Dict) -> str:
        """生成处理信息的回复"""
        # 更新配置
        self._update_config_from_analysis(analysis)
        
        # 获取当前配置
        config = self.config_manager.to_dict()
        
        # 检查是否需要继续收集信息
        missing_info = self.config_manager.get_missing_core_info()
        if missing_info:
            return f"感谢您提供的信息。为了更好地为您服务，我还需要了解：{', '.join(missing_info)}。"
        else:
            return "非常感谢您提供的完整信息。现在我可以为您提供更具针对性的投资建议了。"
    
    async def _generate_question_response(self, analysis: Dict) -> str:
        """生成回答问题的回复"""
        question_info = analysis.get("question_info", {})
        question_type = question_info.get("type", "general")
        
        if question_type == "investment":
            return "这是一个很好的投资问题。让我为您详细解答..."
        elif question_type == "risk":
            return "关于风险的问题很重要。我的建议是..."
        else:
            return "我理解您的问题。让我为您解答..."
    
    async def _generate_concern_response(self, analysis: Dict) -> str:
        """生成处理担忧的回复"""
        return "我理解您的担忧。让我们一起分析这个问题，找到最适合您的解决方案。"
    
    def _build_analysis_prompt(self, user_input: str) -> str:
        """构建用于分析用户输入的 prompt"""
        # 获取当前配置信息
        config = self.config_manager.to_dict()
        
        # 构建 prompt
        prompt = f"""请分析以下用户输入，提取关键信息并确定用户意图：

用户输入：{user_input}

当前配置：
{json.dumps(config, ensure_ascii=False, indent=2)}

请返回 JSON 格式的分析结果，包含以下字段：
- intent: 用户意图（provide_info/ask_question/express_concern）
- emotion: 情感倾向（positive/neutral/negative）
- extracted_info: 提取的信息（如有）
- requires_immediate_response: 是否需要立即响应（true/false）"""
        
        return prompt