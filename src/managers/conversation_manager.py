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
        print("\n=== 开始分析用户输入 ===")
        print(f"用户输入: {user_input}")
        print(f"当前状态: {self.state_manager.current_state.value}")
        
        # 优先检查是否包含投资相关信息
        investment_pattern = r'([0-9]+[万亿]|[0-9]+\s*年|目标|计划投资|买房|理财|投资|基金|股票|债券)'
        if re.search(investment_pattern, user_input):
            print("检测到投资相关信息，将意图设置为 provide_info")
            try:
                # 调用 LLM 进行分析
                prompt = self._build_analysis_prompt(user_input)
                print("\n调用 LLM 进行分析...")
                
                response = await LLMUtils.call_llm(
                    prompt=prompt,
                    temperature=0.2
                )
                
                # 提取 JSON 结果
                analysis_result = LLMUtils.extract_json_from_response(response["text"])
                if not analysis_result:
                    raise ValueError("无法解析 LLM 响应中的 JSON 数据")
                
                # 强制设置意图为 provide_info
                analysis_result["intent"] = "provide_info"
                
                print("\n分析结果:")
                print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
                
                return analysis_result
            except Exception as e:
                print(f"\n❌ 分析用户输入时出错: {str(e)}")
                # 即使出错也返回 provide_info 意图
                return {
                    "intent": "provide_info",
                    "emotion": "neutral",
                    "extracted_info": {},
                    "requires_immediate_response": True
                }
        
        # 如果没有检测到投资相关信息，且在自由问答状态，返回简化分析
        if self.state_manager.current_state == ConversationState.FREE_CHAT:
            print("当前处于自由问答状态，返回简化的分析结果")
            return {
                "intent": "ask_question",
                "emotion": "neutral",
                "question_info": {
                    "type": "general",
                    "original_question": user_input,
                    "requires_immediate_response": True
                    }
                }
        
        try:
            # 调用 LLM 进行分析
            prompt = self._build_analysis_prompt(user_input)
            print("\n调用 LLM 进行分析...")
            
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.2
            )
            
            # 提取 JSON 结果
            analysis_result = LLMUtils.extract_json_from_response(response["text"])
            if not analysis_result:
                raise ValueError("无法解析 LLM 响应中的 JSON 数据")
            
            print("\n分析结果:")
            print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
            
            return analysis_result
            
        except Exception as e:
            print(f"\n❌ 分析用户输入时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("错误堆栈:")
            import traceback
            print(traceback.format_exc())
            return {
                "intent": "unknown",
                "emotion": "neutral",
                "extracted_info": {},
                "requires_immediate_response": True
            }
    
    def _update_config_from_analysis(self, analysis: Dict) -> None:
        """根据分析结果更新配置"""
        print("\n=== 开始更新配置 ===")
        if "extracted_info" in analysis:
            extracted_info = analysis["extracted_info"]
            print("\n提取的信息:")
            print(json.dumps(extracted_info, ensure_ascii=False, indent=2))
            
            # 更新核心投资信息
            if "core_investment" in extracted_info:
                core_info = extracted_info["core_investment"]
                print("\n更新核心投资信息...")
                self.config_manager.update_core_investment(
                    target_value=core_info.get("target_value"),
                    years=core_info.get("years"),
                    initial_investment=core_info.get("initial_investment")
                )
                print("核心投资信息更新完成")
            
            # 更新个人信息
            if "personal_info" in extracted_info:
                personal_info = extracted_info["personal_info"]
                if any(v is not None for v in personal_info.values()):
                    print("\n更新个人信息...")
                    self.config_manager.update_user_info("personal", **personal_info)
                    print("个人信息更新完成")
            
            # 更新财务信息
            if "financial_info" in extracted_info:
                financial_info = extracted_info["financial_info"]
                if any(v is not None for v in financial_info.values()):
                    print("\n更新财务信息...")
                    self.config_manager.update_user_info("financial", **financial_info)
                    print("财务信息更新完成")
            
            # 更新投资组合信息
            if "portfolio" in extracted_info:
                portfolio = extracted_info["portfolio"]
                portfolio_reasoning = analysis.get("reasoning", {}).get("portfolio_parsing", "")
                
                # 只有在明确提供了资产配置信息时才更新
                if portfolio.get("assets") and portfolio.get("weights"):
                    print("\n更新投资组合...")
                    print(f"资产: {portfolio['assets']}")
                    print(f"权重: {portfolio['weights']}")
                    
                    # 验证权重总和
                    weights_sum = sum(portfolio['weights'])
                    if abs(weights_sum - 1.0) > 0.01:  # 允许1%的误差
                        print(f"警告：权重总和 ({weights_sum}) 不等于1，进行归一化")
                        normalized_weights = [w/weights_sum for w in portfolio['weights']]
                        portfolio['weights'] = normalized_weights
                    
                    self.config_manager.update_portfolio(
                        assets=portfolio['assets'],
                        weights=portfolio['weights']
                    )
                    print("投资组合更新完成")
                    
                    # 标记投资组合阶段完成
                    self.collection_stages['portfolio']['completed'] = True
            
            # 检查是否完成了额外信息的收集
            user_info = self.config_manager.to_dict().get('user_info', {})
            personal_info = user_info.get('personal', {})
            financial_info = user_info.get('financial', {})
            
            # 如果收集了足够的额外信息，标记为完成
            additional_info_count = sum(
                1 for field in self.collection_stages['additional_info']['fields']
                if personal_info.get(field) is not None or financial_info.get(field) is not None
            )
            if additional_info_count >= 2:  # 如果至少收集了2项额外信息
                self.collection_stages['additional_info']['completed'] = True
            
            print("\n配置更新完成")
    
    def _build_analysis_prompt(self, user_input: str) -> str:
        """构建用于分析用户输入的 prompt"""
        # 获取最近的对话历史
        context = self.state_manager.get_recent_context()
        
        # 获取当前配置信息
        config = self.config_manager.to_dict()
        core_investment = config.get('core_investment', {})
        
        # 获取缺失的信息
        missing_core = self.config_manager.get_missing_core_info()
        missing_user = self.config_manager.get_missing_user_info()
        
        # 格式化对话历史
        context_str = ""
        if context:
            context_str = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')} "
                f"(状态: {msg.get('state', 'unknown')})"
                for msg in context
            ])
        
        # 获取当前已知信息
        current_info = {
            "target_value": core_investment.get('target_value'),
            "years": core_investment.get('years'),
            "initial_investment": core_investment.get('initial_investment')
        }
        
        # 获取当前投资组合
        portfolio = config.get('portfolio', {})
        portfolio_str = ""
        if portfolio.get('assets') and portfolio.get('weights'):
            portfolio_str = "\n当前投资组合："
            for asset, weight in zip(portfolio['assets'], portfolio['weights']):
                portfolio_str += f"\n- {asset}: {weight*100:.1f}%"
        
        prompt = f"""作为一个专业的投资顾问，请分析用户的输入并提取关键信息。

用户输入："{user_input}"

当前状态：
- 对话阶段：{self.state_manager.current_state.value}
- 缺失的核心信息：{missing_core}
- 当前关注点：{self.state_manager.context.current_focus}

当前已知信息：
- 目标金额：{self._format_amount(current_info['target_value'])}
- 投资年限：{f"{current_info['years']}年" if current_info['years'] is not None else '未知'}
- 初始投资：{self._format_amount(current_info['initial_investment'])}
{portfolio_str}

最近的对话历史：
{context_str}

请仔细分析用户输入中的信息，特别注意：

1. 金额相关表述：
   - 直接金额："20万"、"一百万"等
   - 相对金额："翻一倍"、"增长到原来的3倍"等
   - 增长表述："增长100%"、"收益率100%"等
   - 如果提到相对金额或增长，且已知初始投资，请计算出具体金额

2. 时间相关表述：
   - 具体年限："5年"、"三年"等
   - 时间点："2030年"、"三年后"等
   - 模糊表述："中期"、"长期"等（中期约3-5年，长期约5-10年）

3. 投资目的相关表述：
   - 具体目标："买房"、"子女教育"、"退休"等
   - 模糊表述："保值增值"、"理财"等
   - 复合目标："既要养老又要给孩子攒教育基金"等

4. 投资组合相关表述：
   - 具体配置："股票60%，债券40%"等
   - 风格偏好："稳健型"、"激进型"等
   - 具体产品："股票型基金"、"债券基金"等
   - 明确表示无投资组合的表述：
     * "没有投资组合"
     * "没有"（在询问投资组合时的回答）
     * "全部是现金"
     * "都在银行"等

如果用户明确表示没有投资组合，请在 reasoning.portfolio_parsing 中说明"用户明确表示没有投资组合"，并在 extracted_info.portfolio 中设置：
{{
    "assets": ["cash"],
    "weights": [1.0]
}}

请返回以下 JSON 格式的分析结果：
{{
    "intent": "string",  // 意图类型：provide_info/ask_question/chat/other
    "emotion": "string", // 情绪状态：positive/negative/neutral
    "patience_level": "string",  // 耐心程度：high/medium/low
    "extracted_info": {{
        "core_investment": {{  // 核心投资信息（所有金额必须转换为数字）
            "target_value": {current_info['target_value']},  // 目标金额（例如：'500万' -> 5000000）
            "years": {current_info['years']},         // 投资年限（例如：'5年' -> 5）
            "initial_investment": {current_info['initial_investment']}  // 初始资金（例如：'100万' -> 1000000）
        }},
        "personal_info": {{  // 个人信息
            "family_status": null,  // 家庭状况
            "employment": null,     // 就业状况
            "wealth_source": null,  // 财富来源
            "investment_goal": null // 投资目标/目的
        }},
        "financial_info": {{  // 财务信息（所有金额必须转换为数字）
            "cash_deposits": null,    // 现金存款
            "investments": null,      // 其他投资
            "employee_benefits": null, // 员工福利
            "private_ownership": null, // 私人资产
            "life_insurance": null,    // 人寿保险
            "consumer_debt": null,     // 消费贷款
            "mortgage": null,          // 房贷
            "other_debt": null,        // 其他债务
            "account_debt": null       // 账户负债
        }},
        "portfolio": {{  // 投资组合信息
            "assets": {json.dumps(portfolio.get('assets', []))},    // 资产类别列表
            "weights": {json.dumps(portfolio.get('weights', []))}    // 对应比例列表（百分比必须转换为小数，例如：'50%' -> 0.5）
        }}
    }},
    "question_info": {{  // 如果是提问
        "type": "string",  // 问题类型
        "requires_immediate_response": boolean,  // 是否需要立即回答
        "can_collect_info": boolean  // 是否可以借机收集信息
    }},
    "reasoning": {{  // 推理过程
        "amount_calculation": string,  // 如何得出金额的计算过程
        "time_interpretation": string, // 如何解释时间相关表述
        "goal_understanding": string,  // 如何理解投资目的
        "portfolio_parsing": string    // 如何解析投资组合信息
    }}
}}

注意事项：
1. 所有金额必须转换为数字（例如：'500万' -> 5000000）
2. 所有年限必须转换为数字（例如：'5年' -> 5）
3. 所有百分比必须转换为小数（例如：'50%' -> 0.5）
4. 如果提取到多个可能的值，选择最后提到的或最明确的值
5. 只提取明确提到的信息，不要推测
6. 如果用户表述模糊，在 reasoning 字段中说明解释过程"""
        
        return prompt
    
    def _format_amount(self, amount):
        """格式化金额显示"""
        if amount is None:
            return '未知'
        if amount >= 10000000:  # 大于1000万
            return f"{amount/10000000:.1f}千万"
        elif amount >= 10000:   # 大于1万
            return f"{amount/10000:.1f}万"
        else:
            return f"{amount:,.0f}"
    
    def determine_strategy(self, analysis: Dict) -> Dict:
        """根据分析结果确定对话策略"""
        print("\n=== 确定对话策略 ===")
        print(f"当前状态: {self.state_manager.current_state.value}")
        print(f"用户意图: {analysis.get('intent')}")
        print(f"分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
        
        # 如果用户提出问题
        if analysis.get("intent") == "ask_question":
            print("\n检测到用户提问...")
            # 如果当前是收集信息状态，不要切换到自由问答
            if self.state_manager.current_state == ConversationState.COLLECTING_CORE_INFO:
                print("保持在收集信息状态")
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "maintain_engagement",
                    "approach": "informative",
                    "next_action": "ask_for_initial_investment",
                    "allow_free_chat": False
                }
            
            # 其他状态下可以切换到自由问答
            if self.state_manager.current_state != ConversationState.FREE_CHAT:
                print("尝试转换到自由问答状态...")
                if self.state_manager.can_transition_to(ConversationState.FREE_CHAT):
                    print("转换成功")
                    self.state_manager.transition_to(ConversationState.FREE_CHAT)
                else:
                    print("转换失败")
            else:
                print("已经在自由问答状态")
            
                return {
                    "primary_goal": "answer_question",
                    "secondary_goal": "maintain_engagement",
                    "approach": "informative",
                    "next_action": "provide_answer",
                    "allow_free_chat": True,
                "question_type": "general"
                }
        
        # 如果用户提供了信息
        if analysis.get("intent") == "provide_info":
            print("检测到用户提供了新信息")
            
            # 更新信息收集进度
            self.state_manager.update_info_collection_progress()
            
            # 检查核心信息是否完整
            config = self.config_manager.to_dict()
            core_investment = config.get('core_investment', {})
            user_info = config.get('user_info', {})
            personal_info = user_info.get('personal', {})
            portfolio = config.get('portfolio', {})
            
            print("\n核心信息完整性检查:")
            print(json.dumps(core_investment, ensure_ascii=False, indent=2))
            
            has_target = core_investment.get('target_value') is not None
            has_years = core_investment.get('years') is not None
            has_initial = core_investment.get('initial_investment') is not None
            has_investment_goal = personal_info.get('investment_goal') is not None
            has_portfolio = bool(portfolio.get('assets')) and bool(portfolio.get('weights'))
            
            print(f"目标金额: {'已知' if has_target else '未知'}")
            print(f"投资年限: {'已知' if has_years else '未知'}")
            print(f"初始投资: {'已知' if has_initial else '未知'}")
            print(f"投资目的: {'已知' if has_investment_goal else '未知'}")
            print(f"投资组合: {'已知' if has_portfolio else '未知'}")
            
            # 如果缺少目标金额
            if not has_target:
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "collect_extra_info",
                    "approach": "direct",
                    "next_action": "ask_for_target_value",
                    "allow_free_chat": False,
                    "extra_info_to_collect": ["family_status", "employment"]
                }
            
            # 如果缺少投资年限
            if not has_years:
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "collect_extra_info",
                    "approach": "direct",
                    "next_action": "ask_for_years",
                    "allow_free_chat": False,
                    "extra_info_to_collect": ["wealth_source"]
                }
            
            # 如果缺少初始投资
            if not has_initial:
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "collect_extra_info",
                    "approach": "direct",
                    "next_action": "ask_for_initial_investment",
                    "allow_free_chat": False,
                    "extra_info_to_collect": ["cash_deposits", "investments"]
                }
            
            # 如果核心信息已收集但缺少投资目的
            if not has_investment_goal:
                return {
                    "primary_goal": "collect_investment_goal",
                    "secondary_goal": "prepare_for_risk_assessment",
                    "approach": "conversational",
                    "next_action": "ask_for_investment_goal",
                    "allow_free_chat": False
                }
            
            # 如果投资目的已知但未询问投资组合
            if not has_portfolio:
                # 检查是否刚刚收到了"没有投资组合"的回答
                if analysis.get("extracted_info", {}).get("portfolio", {}).get("assets") == ["cash"]:
                    return {
                        "primary_goal": "summarize_info",
                        "secondary_goal": "guide_next_step",
                        "approach": "informative",
                        "next_action": "suggest_risk_assessment",
                        "allow_free_chat": False
                    }
                return {
                    "primary_goal": "collect_portfolio_info",
                    "secondary_goal": "prepare_for_risk_assessment",
                    "approach": "conversational",
                    "next_action": "ask_for_portfolio",
                    "allow_free_chat": False
                }
            
            # 如果所有必要信息都已收集
            return {
                "primary_goal": "summarize_info",
                "secondary_goal": "guide_next_step",
                "approach": "informative",
                "next_action": "suggest_risk_assessment",
                "allow_free_chat": False
            }
        
        # 默认策略
        return {
            "primary_goal": "maintain_conversation",
            "secondary_goal": "collect_info",
            "approach": "casual",
            "next_action": "chat_response",
            "allow_free_chat": True
        }
    
    async def chat(self, user_input: str) -> str:
        """处理用户输入并生成回复"""
        print("\n=== 开始对话流程 ===")
        print("当前状态:", self.state_manager.current_state.value)
        print("用户输入:", user_input)
        
        try:
            # 1. 分析用户输入
            print("\n1. 分析用户输入...")
            analysis = await self.analyze_input(user_input)
            
            # 2. 检测并更新状态
            print("\n2. 检测对话状态...")
            new_state = await self._detect_state(user_input, analysis)
            if new_state and new_state != self.state_manager.current_state:
                print(f"状态需要从 {self.state_manager.current_state.value} 切换到 {new_state.value}")
                if self.state_manager.can_transition_to(new_state):
                    print("执行状态转换")
                    self.state_manager.transition_to(new_state)
                else:
                    print(f"无法切换到 {new_state.value} 状态")
            
            # 3. 生成回复
            print("\n3. 生成回复...")
            response = await self.generate_response(analysis, user_input)
            
            # 4. 更新对话历史
            print("\n4. 更新对话历史...")
            # 添加用户消息
            user_message = {
                "role": "user",
                "content": user_input,
                "state": self.state_manager.current_state.value,
                "extracted_info": analysis.get("extracted_info", {})
            }
            self.state_manager.add_to_history(user_message)
            
            # 添加助手回复
            assistant_message = {
                "role": "assistant",
                "content": response,
                "state": self.state_manager.current_state.value
            }
            self.state_manager.add_to_history(assistant_message)
            
            return response
            
        except Exception as e:
            print(f"\n❌ 对话处理过程中出错: {str(e)}")
            print("错误堆栈:")
            import traceback
            print(traceback.format_exc())
            return "抱歉，我在处理您的消息时遇到了问题。请再说一遍您的需求。"
    
    async def _detect_state(self, user_input: str, analysis: Dict) -> Optional[ConversationState]:
        """检测用户输入应该对应的状态"""
        print("\n=== 检测对话状态 ===")
        print(f"用户输入: {user_input}")
        print(f"当前状态: {self.state_manager.current_state.value}")
        
        # 优先使用规则检测
        # 如果用户输入包含投资相关信息，切换到信息收集状态
        investment_pattern = r'([0-9]+[万亿]|[0-9]+\s*年|目标|计划投资|买房|理财|投资|基金|股票|债券)'
        if re.search(investment_pattern, user_input):
            print("检测到投资相关信息，切换到信息收集状态")
            return ConversationState.COLLECTING_INFO
        
        # 获取最近的对话历史
        context = self.state_manager.get_recent_context()
        context_str = ""
        if context:
            context_str = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in context[-3:]  # 只取最近3轮对话
            ])
        
        # 构建状态检测的 prompt
        prompt = f"""作为一个专业的投资顾问助手，请分析用户的输入并判断应该进入哪个对话状态。

当前状态：{self.state_manager.current_state.value}
用户输入："{user_input}"

最近的对话历史：
{context_str}

状态说明：
1. COLLECTING_INFO（收集信息）
   - 用户提到具体的投资目标、金额或时间
   - 谈论个人投资需求或计划
   - 提供个人财务信息
   - 讨论风险承受能力
   - 谈论投资组合配置

2. FREE_CHAT（自由问答）
   - 询问一般性的投资知识
   - 市场分析或产品咨询
   - 不涉及个人投资决策
   - 闲聊或其他非投资话题

重要提示：
1. 只要用户提到个人投资相关的具体信息，就应该使用 COLLECTING_INFO
2. 如果是纯咨询或知识探讨，使用 FREE_CHAT

请返回以下 JSON 格式的分析结果：
{{
    "target_state": "COLLECTING_INFO/FREE_CHAT",
    "confidence": 0.1-1.0,  // 置信度，0.1-1.0
    "reasoning": "string"    // 详细的状态判断理由
}}"""

        try:
            print("\n调用 LLM 进行状态检测...")
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.2
            )
            
            result = LLMUtils.extract_json_from_response(response["text"])
            if not result:
                print("无法解析 LLM 响应")
                return None
                
            print("\n状态检测结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            target_state = result.get("target_state")
            confidence = result.get("confidence", 0)
            
            # 只有当置信度超过 0.7 时才考虑转换状态
            if confidence >= 0.7:
                if target_state == "COLLECTING_INFO":
                    return ConversationState.COLLECTING_INFO
                elif target_state == "FREE_CHAT":
                    return ConversationState.FREE_CHAT
            
            return None
            
        except Exception as e:
            print(f"\n❌ 状态检测出错: {str(e)}")
            return None
    
    async def generate_response(self, analysis: Dict, user_input: str) -> str:
        """根据当前状态生成回复"""
        print("\n=== 生成回复 ===")
        print(f"当前状态: {self.state_manager.current_state.value}")
        
        # 如果是自由问答状态，使用自由问答的回复生成逻辑
        if self.state_manager.current_state == ConversationState.FREE_CHAT:
            return await self._generate_free_chat_response(analysis, user_input)
        
        # 如果是信息收集状态
        if self.state_manager.current_state == ConversationState.COLLECTING_INFO:
            # 检查是否是修改请求
            modification = await self._check_modification_intent(user_input, analysis)
            if modification:
                field = modification.get("target_field")
                stage = {
                    'target_value': 'core_info',
                    'years': 'core_info',
                    'initial_investment': 'core_info',
                    'portfolio': 'portfolio'
                }.get(field)
                
                if stage:
                    # 处理修改请求
                    self._handle_modification(field, modification.get("new_value"))
                    # 获取当前配置
                    config = self.config_manager.to_dict()
                    # 重新检查收集阶段
                    current_stage = self._check_collection_stage(config, user_input)
                    if current_stage != 'completed':
                        next_question = self._get_next_question(current_stage, config)
                        return f"好的，已经帮您修改了信息。{next_question}"
                    else:
                        return "好的，已经帮您修改了信息。您可以继续修改其他信息，或者输入'确认'进入风险评估阶段。"
                else:
                    return "抱歉，该信息目前无法修改。让我们继续完成信息收集。"

            # 检查是否是确认进入风险评估
            if user_input.strip() == "确认":
                # 锁定核心信息和投资组合的修改
                self.collection_stages['core_info']['modifiable'] = False
                self.collection_stages['portfolio']['modifiable'] = False
                return "好的，让我们开始风险评估。请回答以下问题..."

            # 更新配置
            if analysis.get("intent") == "provide_info":
                self._update_config_from_analysis(analysis)
            
            # 获取当前配置
            config = self.config_manager.to_dict()
            
            # 检查当前收集阶段
            current_stage = self._check_collection_stage(config, user_input)
            
            if current_stage == 'completed':
                return "我们已经收集了所有必要的信息。您可以继续修改已填写的信息，或者输入\"确认\"进入风险评估阶段。"
            
            # 获取下一个问题
            next_question = self._get_next_question(current_stage, config)
            return next_question
        
        # 如果是其他状态（不应该出现）
        return "抱歉，我现在无法确定如何回复。请告诉我您的投资需求，我会为您提供专业的建议。"
    
    def _check_collection_stage(self, config: Dict, user_input: str = None) -> str:
        """检查当前应该收集哪个阶段的信息"""
        print("\n=== 检查收集阶段 ===")
        print("当前配置:")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        
        # 检查核心信息
        if not self.collection_stages['core_info']['completed']:
            core_investment = config.get('core_investment', {})
            core_fields_complete = all(
                core_investment.get(field) is not None 
                for field in self.collection_stages['core_info']['fields']
            )
            
            print(f"核心信息完整性检查: {core_fields_complete}")
            if core_fields_complete:
                self.collection_stages['core_info']['completed'] = True
                print("核心信息阶段标记为完成")
            else:
                print("需要继续收集核心信息")
                return 'core_info'
                
        # 检查投资组合
        if not self.collection_stages['portfolio']['completed']:
            portfolio = config.get('portfolio', {})
            portfolio_complete = (
                portfolio.get('assets') and 
                portfolio.get('weights') and 
                len(portfolio.get('assets', [])) == len(portfolio.get('weights', []))
            )
            
            print(f"投资组合完整性检查: {portfolio_complete}")
            if portfolio_complete:
                self.collection_stages['portfolio']['completed'] = True
                print("投资组合阶段标记为完成")
            else:
                print("需要继续收集投资组合信息")
                return 'portfolio'
                
        # 检查额外信息
        if not self.collection_stages['additional_info']['completed']:
            # 如果用户选择跳过，也标记为完成
            if user_input and user_input.strip() == "跳过":
                self.collection_stages['additional_info']['completed'] = True
                print("额外信息阶段已跳过")
                return 'completed'
            return 'additional_info'
            
        print("所有必要信息已收集完成")
        return 'completed'

    def _get_next_question(self, stage: str, config: Dict) -> str:
        """根据当前阶段生成下一个问题"""
        if stage == 'core_info':
            core_investment = config.get('core_investment', {})
            if core_investment.get('target_value') is None:
                return "您的投资目标金额是多少？"
            elif core_investment.get('years') is None:
                return "您计划投资多长时间？"
            elif core_investment.get('initial_investment') is None:
                return "您目前可用于投资的资金有多少？"
                
        elif stage == 'portfolio':
            return "请问您目前的资产配置情况是怎样的？比如存款、股票、基金等的占比。"
            
        elif stage == 'additional_info':
            return """为了给您更好的投资建议，您可以提供一些额外信息（可选）：
- 家庭状况（如已婚、有子女等）
- 职业收入情况
- 是否有房贷、车贷等债务
- 每月固定支出
- 其他理财目标

如果不方便提供，您可以说"跳过"，我们继续后续流程。"""
            
        return "让我们开始进行风险评估，这将帮助我们为您制定更合适的投资方案。"
    
    async def _generate_free_chat_response(self, analysis: Dict, user_input: str) -> str:
        """生成自由问答状态的回复"""
        # 只获取自由问答状态的历史记录
        context = self.state_manager.get_recent_context(
            state_filter=ConversationState.FREE_CHAT
        )
        recent_messages = []
        if context:
            for msg in context[-4:]:
                if msg["role"] == "user":
                    recent_messages.append(f"用户: {msg['content']}")
                else:
                    recent_messages.append(f"助手: {msg['content']}")
        
        context_str = "\n".join(recent_messages) if recent_messages else "无历史对话"
        
        # 构建精简的 prompt
        base_prompt = """作为专业的投资顾问，请回答用户的问题。

用户问题：{}

回答要求：
1. 保持专业性，但使用通俗易懂的语言
2. 回答要简洁，控制在200字以内
3. 如果涉及具体数字，要说明数据来源
4. 如果是投资建议，要说明风险提示
5. 如果用户提到个人投资需求，建议切换到信息收集模式

{}

请直接给出回答，不要重复问题。"""
        
        context_part = f"最近的相关对话：\n{context_str}" if recent_messages else ""
        prompt = base_prompt.format(user_input, context_part)

        try:
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.7
            )
            return response["text"]
        except Exception as e:
            print(f"\n❌ 自由问答模式出错: {str(e)}")
            return "抱歉，我现在无法提供准确的回答，请稍后再试。"
    def _format_portfolio_str(self, portfolio: Dict) -> str:
        """格式化投资组合信息"""
        if not portfolio.get('assets') or not portfolio.get('weights'):
            return "未知"
        
        portfolio_items = []
        for asset, weight in zip(portfolio['assets'], portfolio['weights']):
            # 将资产名称转换为中文
            asset_names = {
                "cash": "现金",
                "gold": "黄金",
                "stock": "股票",
                "bond": "债券",
                "fund": "基金",
                "real_estate": "房地产"
            }
            asset_name = asset_names.get(asset, asset)
            portfolio_items.append(f"{asset_name}{weight*100:.1f}%")
        
        return "、".join(portfolio_items)

    async def _check_modification_intent(self, user_input: str, analysis: Dict) -> Optional[Dict]:
        """检查用户是否想要修改之前提供的信息"""
        print("\n=== 开始检查修改意图 ===")
        print(f"用户输入: {user_input}")
        print(f"分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
        
        # 使用更智能的方式检测修改意图
        prompt = f"""分析用户输入是否表达了修改之前信息的意图。

用户输入："{user_input}"

可修改的字段说明：
1. 核心投资信息：
   - target_value: 目标金额
   - years: 投资年限
   - initial_investment: 初始投资金额
2. 投资组合信息：
   - portfolio: 资产配置

请判断：
1. 是否包含修改意图（如"修改"、"改一下"、"重新设置"等）
2. 想要修改哪类信息
3. 新的值是什么

返回JSON格式：
{{
    "has_modification_intent": boolean,
    "target_field": string,  // 目标字段：target_value/years/initial_investment/portfolio
    "new_value": any,       // 新的值
    "confidence": float    // 置信度 0-1
}}"""

        try:
            print("\n调用 LLM 分析修改意图...")
            response = await LLMUtils.call_llm(prompt=prompt, temperature=0.2)
            print(f"LLM 响应: {json.dumps(response, ensure_ascii=False, indent=2)}")
            
            result = LLMUtils.extract_json_from_response(response["text"])
            print(f"解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result:
                has_intent = result.get("has_modification_intent", False)
                confidence = result.get("confidence", 0)
                print(f"是否有修改意图: {has_intent}")
                print(f"置信度: {confidence}")
                
                if has_intent and confidence > 0.7:
                    print("检测到有效的修改意图")
                    return result
                else:
                    print(f"修改意图无效 (has_intent={has_intent}, confidence={confidence})")
            else:
                print("无法从 LLM 响应中提取 JSON 结果")
                
        except Exception as e:
            print(f"❌ 检查修改意图时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("错误堆栈:")
            import traceback
            print(traceback.format_exc())
            
        return None

    def _handle_modification(self, field: str, new_value: any) -> None:
        """处理修改请求"""
        print(f"\n=== 开始处理修改请求 ===")
        print(f"目标字段: {field}")
        print(f"新的值: {new_value}")
        print(f"当前配置状态:")
        print(json.dumps(self.config_manager.to_dict(), ensure_ascii=False, indent=2))
        
        # 确定字段所属的阶段
        field_to_stage = {
            'target_value': 'core_info',
            'years': 'core_info',
            'initial_investment': 'core_info',
            'portfolio': 'portfolio'
        }
        
        stage = field_to_stage.get(field)
        print(f"字段 {field} 所属阶段: {stage}")
        
        if not stage:
            print(f"❌ 未知的修改字段：{field}")
            return
            
        try:
            # 更新配置
            if stage == 'core_info':
                print(f"更新核心信息字段：{field}")
                print(f"更新前的核心信息:")
                print(json.dumps(self.config_manager.to_dict().get('core_investment', {}), ensure_ascii=False, indent=2))
                
                self.config_manager.update_core_investment(**{field: new_value})
                
                print(f"更新后的核心信息:")
                print(json.dumps(self.config_manager.to_dict().get('core_investment', {}), ensure_ascii=False, indent=2))
                
                # 重置核心信息的完成状态
                self.collection_stages['core_info']['completed'] = False
                
            elif stage == 'portfolio':
                print(f"更新投资组合信息")
                print(f"更新前的投资组合:")
                print(json.dumps(self.config_manager.to_dict().get('portfolio', {}), ensure_ascii=False, indent=2))
                
                if isinstance(new_value, dict):
                    self.config_manager.update_portfolio(**new_value)
                else:
                    print(f"❌ 投资组合的新值格式错误: {type(new_value)}")
                    return
                    
                print(f"更新后的投资组合:")
                print(json.dumps(self.config_manager.to_dict().get('portfolio', {}), ensure_ascii=False, indent=2))
                
                # 重置投资组合的完成状态
                self.collection_stages['portfolio']['completed'] = False
                
            print("\n✅ 修改请求处理完成")
            
        except Exception as e:
            print(f"\n❌ 处理修改请求时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("错误堆栈:")
            import traceback
            print(traceback.format_exc())
