from typing import Dict, List, Optional, Tuple
from src.managers.state_manager import StateManager, ConversationState
from src.config.config_manager import ConfigManager
from src.managers.risk_assessment_manager import RiskAssessmentManager
from src.utils.llm_utils import LLMUtils
import json
import re

class ConversationManager:
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.risk_manager = RiskAssessmentManager()
        
    async def analyze_input(self, user_input: str) -> Dict:
        """分析用户输入，提取意图和信息"""
        print("\n=== 开始分析用户输入 ===")
        print(f"用户输入: {user_input}")
        
        # 如果是风险评估阶段，直接处理答案
        if self.state_manager.current_state == ConversationState.RISK_ASSESSMENT:
            print("当前处于风险评估阶段")
            # 清理和标准化输入
            answer = user_input.strip().upper()
            if len(answer) == 1 and answer in "ABCD":
                print(f"检测到有效的风险评估答案: {answer}")
                return {
                    "intent": "provide_info",
                    "emotion": "neutral",
                    "extracted_info": {
                        "answer": answer
                    }
                }
        
        try:
            # 调用 LLM 进行分析
            prompt = self._build_analysis_prompt(user_input)
            print("\n分析用的Prompt:")
            print(prompt)
            
            print("\n调用 LLM 进行分析...")
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.2
            )
            
            # 提取 JSON 结果
            analysis_result = LLMUtils.extract_json_from_response(response["text"])
            if not analysis_result:
                raise ValueError("无法解析 LLM 响应中的 JSON 数据")
            
            # 打印推理过程
            if "reasoning" in analysis_result:
                print("\n解析推理过程:")
                print(json.dumps(analysis_result["reasoning"], ensure_ascii=False, indent=2))
            
            # 确保保留已有信息
            if "extracted_info" in analysis_result:
                extracted_info = analysis_result["extracted_info"]
                
                # 获取当前配置
                current_config = self.config_manager.to_dict()
                core_investment = current_config.get('core_investment', {})
                portfolio = current_config.get('portfolio', {})
                
                # 保留核心投资信息
                if "core_investment" in extracted_info:
                    core_info = extracted_info["core_investment"]
                    # 只更新新提供的信息，保留已有信息
                    if core_info.get("target_value") is None:
                        core_info["target_value"] = core_investment.get("target_value")
                    if core_info.get("years") is None:
                        core_info["years"] = core_investment.get("years")
                    if core_info.get("initial_investment") is None:
                        core_info["initial_investment"] = core_investment.get("initial_investment")
                
                # 保留投资组合信息
                if "portfolio" in extracted_info:
                    portfolio_info = extracted_info["portfolio"]
                    # 检查是否是用户主动提供的资产配置信息
                    if analysis_result.get("intent") == "provide_info":
                        # 只在没有新信息时保留旧信息
                        if not portfolio_info.get("assets") and portfolio.get("assets"):
                            portfolio_info["assets"] = portfolio["assets"]
                        if not portfolio_info.get("weights") and portfolio.get("weights"):
                            portfolio_info["weights"] = portfolio["weights"]
                    else:
                        # 如果不是主动提供信息，保持原有的资产配置
                        portfolio_info["assets"] = portfolio.get("assets", [])
                        portfolio_info["weights"] = portfolio.get("weights", [])
            
            print("\n分析结果:")
            print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
            
            # 更新配置
            print("\n更新配置...")
            self._update_config_from_analysis(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            print(f"\n❌ 分析用户输入时出错: {str(e)}")
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
            target_value = None
            years = None
            initial_investment = None
            
            # 直接从extracted_info中获取值
            if "target_value" in extracted_info:
                target_value = extracted_info["target_value"]
                print(f"直接提取到目标金额: {target_value}")
            if "years" in extracted_info:
                years = extracted_info["years"]
                print(f"直接提取到投资年限: {years}")
            if "initial_investment" in extracted_info:
                initial_investment = extracted_info["initial_investment"]
                print(f"直接提取到初始投资: {initial_investment}")
            
            # 从core_investment中获取值
            if "core_investment" in extracted_info:
                core_info = extracted_info["core_investment"]
                print("\n从core_investment中提取:")
                print(json.dumps(core_info, ensure_ascii=False, indent=2))
                
                if core_info.get("target_value") is not None:
                    target_value = core_info["target_value"]
                    print(f"更新目标金额: {target_value}")
                if core_info.get("years") is not None:
                    years = core_info["years"]
                    print(f"更新投资年限: {years}")
                if core_info.get("initial_investment") is not None:
                    initial_investment = core_info["initial_investment"]
                    print(f"更新初始投资: {initial_investment}")
            
            # 更新配置
            if any(v is not None for v in [target_value, years, initial_investment]):
                print("\n更新核心投资信息...")
                self.config_manager.update_core_investment(
                    target_value=target_value,
                    years=years,
                    initial_investment=initial_investment
                )
                print("核心投资信息更新完成")
            
            # 获取当前配置中的用户信息
            current_config = self.config_manager.to_dict()
            current_personal_info = current_config.get('user_info', {}).get('personal', {})
            current_financial_info = current_config.get('user_info', {}).get('financial', {})
            
            # 更新个人信息，保留已有信息
            if "personal_info" in extracted_info:
                personal_info = extracted_info["personal_info"]
                # 只更新新提供的信息
                updated_personal_info = {
                    k: v if v is not None else current_personal_info.get(k)
                    for k, v in personal_info.items()
                }
                if any(v is not None for v in updated_personal_info.values()):
                    self.config_manager.update_user_info("personal", **updated_personal_info)
            
            # 更新财务信息，保留已有信息
            if "financial_info" in extracted_info:
                financial_info = extracted_info["financial_info"]
                # 只更新新提供的信息
                updated_financial_info = {
                    k: v if v is not None else current_financial_info.get(k)
                    for k, v in financial_info.items()
                }
                if any(v is not None for v in updated_financial_info.values()):
                    self.config_manager.update_user_info("financial", **updated_financial_info)
            
            # 更新投资组合信息
            if "portfolio" in extracted_info:
                portfolio = extracted_info["portfolio"]
                if portfolio.get("assets") or portfolio.get("weights"):
                    # 确保资产列表中包含现金
                    assets = portfolio.get("assets", [])
                    weights = portfolio.get("weights", [])
                    
                    # 如果没有资产，则全部为现金
                    if not assets:
                        assets = ["cash"]
                        weights = [1.0]
                    else:
                        # 计算现有权重之和
                        current_weight_sum = sum(weights)
                        
                        # 如果权重之和小于1且没有现金，将剩余部分分配给现金
                        if current_weight_sum < 1 and "cash" not in assets:
                            assets.append("cash")
                            weights.append(1 - current_weight_sum)
                        # 如果权重之和等于1，不需要添加现金
                        # 权重之和大于1的情况由其他验证逻辑处理
                    
                    print("\n更新投资组合...")
                    print(f"资产: {assets}")
                    print(f"权重: {weights}")
                    self.config_manager.update_portfolio(
                        assets=assets,
                        weights=weights
                    )
            
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
        
        # 如果已经在风险评估阶段
        if self.state_manager.current_state == ConversationState.RISK_ASSESSMENT:
            print("当前处于风险评估阶段")
            return self._determine_risk_assessment_strategy(analysis)
        
        # 如果用户提出问题
        if analysis.get("intent") == "ask_question":
            # 如果当前不在自由问答状态，尝试转换
            if self.state_manager.current_state != ConversationState.FREE_CHAT:
                if self.state_manager.can_transition_to(ConversationState.FREE_CHAT):
                    self.state_manager.transition_to(ConversationState.FREE_CHAT)
            
            # 获取问题类型
            question_type = analysis.get("question_info", {}).get("type", "")
            
            # 根据问题类型返回不同的策略
            if question_type == "investment_advice":
                return {
                    "primary_goal": "provide_investment_advice",
                    "secondary_goal": "maintain_engagement",
                    "approach": "professional",
                    "next_action": "analyze_market",
                    "allow_free_chat": True,
                    "question_type": question_type
                }
            elif question_type == "market_analysis":
                return {
                    "primary_goal": "provide_market_insight",
                    "secondary_goal": "maintain_engagement",
                    "approach": "analytical",
                    "next_action": "analyze_market",
                    "allow_free_chat": True,
                    "question_type": question_type
                }
            else:
                return {
                    "primary_goal": "answer_question",
                    "secondary_goal": "maintain_engagement",
                    "approach": "informative",
                    "next_action": "provide_answer",
                    "allow_free_chat": True,
                    "question_type": question_type
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
                    "allow_free_chat": True,
                    "extra_info_to_collect": ["family_status", "employment"]
                }
            
            # 如果缺少投资年限
            if not has_years:
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "collect_extra_info",
                    "approach": "direct",
                    "next_action": "ask_for_years",
                    "allow_free_chat": True,
                    "extra_info_to_collect": ["wealth_source"]
                }
            
            # 如果缺少初始投资
            if not has_initial:
                return {
                    "primary_goal": "collect_core_info",
                    "secondary_goal": "collect_extra_info",
                    "approach": "direct",
                    "next_action": "ask_for_initial_investment",
                    "allow_free_chat": True,
                    "extra_info_to_collect": ["cash_deposits", "investments"]
                }
            
            # 如果核心信息已收集但缺少投资目的
            if not has_investment_goal:
                return {
                    "primary_goal": "collect_investment_goal",
                    "secondary_goal": "prepare_for_risk_assessment",
                    "approach": "conversational",
                    "next_action": "ask_for_investment_goal",
                    "allow_free_chat": True
                }
            
            # 如果投资目的已知但未询问投资组合
            if not has_portfolio:
                return {
                    "primary_goal": "collect_portfolio_info",
                    "secondary_goal": "prepare_for_risk_assessment",
                    "approach": "conversational",
                    "next_action": "ask_for_portfolio",
                    "allow_free_chat": True
                }
            
            # 如果所有必要信息都已收集
            return {
                "primary_goal": "summarize_info",
                "secondary_goal": "guide_next_step",
                "approach": "informative",
                "next_action": "suggest_risk_assessment",
                "allow_free_chat": True
            }
        
        # 默认策略
        return {
            "primary_goal": "maintain_conversation",
            "secondary_goal": "collect_info",
            "approach": "casual",
            "next_action": "chat_response",
            "allow_free_chat": True
        }
    
    def _determine_risk_assessment_strategy(self, analysis: Dict) -> Dict:
        """风险评估策略"""
        current_question = self.risk_manager.get_current_question()
        
        if not current_question:  # 如果没有问题了
            return {
                "primary_goal": "transition",
                "next_action": "complete_assessment",
                "allow_free_chat": True
            }
        
        return {
            "primary_goal": "complete_assessment",
            "secondary_goal": "maintain_focus",
            "approach": "structured",
            "next_action": "ask_risk_question",
            "allow_free_chat": False,  # 风险评估阶段需要保持专注
            "current_question": current_question
        }
    
    async def generate_response(self, strategy: Dict, analysis: Dict) -> str:
        """根据策略生成回复"""
        print("\n=== 生成回复 ===")
        print(f"当前状态: {self.state_manager.current_state.value}")
        
        # 获取状态信息
        state_info = self.state_manager.get_state_info()
        print("\n原始状态信息:")
        print(json.dumps(state_info, ensure_ascii=False, indent=2))
        
        # 获取策略信息
        print("\n策略信息:")
        print(json.dumps(strategy, ensure_ascii=False, indent=2))
        
        # 如果是风险评估阶段
        if self.state_manager.current_state == ConversationState.RISK_ASSESSMENT:
            print("\n处理风险评估答案...")
            result = self._process_risk_assessment_answer(analysis)
            print("处理结果:", json.dumps(result, ensure_ascii=False, indent=2))
            return result.get("message", "无效的答案，请选择提供的选项之一")
        
        # 如果是投资建议类问题
        if strategy.get("primary_goal") == "provide_investment_advice":
            # 获取当前配置
            config = self.config_manager.to_dict()
            portfolio = config.get('portfolio', {})
            risk_profile = config.get('risk_profile', {})
            
            # 构建市场分析 prompt
            prompt = f"""作为专业的投资顾问，请分析当前市场情况并提供专业建议。

用户问题：{analysis.get('question_info', {}).get('original_question', '关于投资建议的咨询')}

当前投资组合：
{self._format_portfolio(portfolio)}

风险承受能力：{risk_profile.get('tolerance', '未评估')}

请提供：
1. 对当前市场的简要分析
2. 针对用户当前投资组合的具体建议
3. 需要注意的风险点

注意：
- 建议要具体且可操作
- 要考虑用户的风险承受能力
- 解释说明理由
"""
            
            # 调用 LLM 生成建议
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.7
            )
            
            return response["text"]
        
        # 如果是市场分析类问题
        if strategy.get("primary_goal") == "provide_market_insight":
            # 构建市场分析 prompt
            prompt = f"""作为专业的投资顾问，请分析当前市场情况。

用户问题：{analysis.get('question_info', {}).get('original_question', '关于市场的咨询')}

请提供：
1. 当前市场环境分析
2. 主要影响因素
3. 未来趋势展望
4. 投资机会和风险

注意：
- 分析要客观专业
- 数据支持论点
- 避免过于主观的判断
"""
            
            # 调用 LLM 生成分析
            response = await LLMUtils.call_llm(
                prompt=prompt,
                temperature=0.7
            )
            
            return response["text"]
        
        # 获取当前配置
        config = self.config_manager.to_dict()
        core_investment = config.get('core_investment', {})
        
        # 如果需要收集核心信息
        if strategy.get("primary_goal") == "collect_core_info":
            extra_info = strategy.get("extra_info_to_collect", [])
            extra_info_prompts = {
                "family_status": "另外，方便的话您能告诉我您的家庭状况吗？",
                "employment": "您目前的职业状况如何？",
                "wealth_source": "您的主要收入来源是什么？",
                "cash_deposits": "除了计划投资的资金，您还有其他储蓄吗？",
                "investments": "您目前有其他投资吗？"
            }
            
            base_prompts = {
                "ask_for_target_value": "请问您的投资目标金额是多少？",
                "ask_for_years": "请问您计划的投资年限是多少年？",
                "ask_for_initial_investment": "请问您计划的初始投资金额是多少？"
            }
            
            base_prompt = base_prompts.get(strategy["next_action"], "请告诉我更多关于您的投资计划。")
            extra_prompt = ""
            if extra_info:
                extra_prompt = f"\n\n{extra_info_prompts.get(extra_info[0], '')}"
            
            return base_prompt + extra_prompt
        
        # 如果需要收集投资目的
        if strategy.get("primary_goal") == "collect_investment_goal":
            return "在我们继续之前，能具体说说您的投资目的是什么吗？比如是为了退休、买房、子女教育等。这将帮助我们更好地为您规划投资策略。"
        
        # 如果需要收集投资组合信息
        if strategy.get("primary_goal") == "collect_portfolio_info":
            return "您目前有任何投资组合吗？如果有的话，能告诉我具体的资产配置情况吗？比如股票、基金、债券等的比例。"
        
        # 如果所有必要信息都已收集，准备建议风险评估
        if strategy.get("next_action") == "suggest_risk_assessment":
            target_value = core_investment.get('target_value', 0)
            years = core_investment.get('years', 0)
            initial_investment = core_investment.get('initial_investment', 0)
            
            # 计算所需年化收益率
            target_return = ((target_value / initial_investment) ** (1/years)) - 1 if initial_investment > 0 and years > 0 else 0
            target_return_percentage = target_return * 100
            
            # 获取投资目的
            user_info = config.get('user_info', {}).get('personal', {})
            investment_goal = user_info.get('investment_goal', '未指定')
            
            # 获取投资组合信息
            portfolio = config.get('portfolio', {})
            portfolio_str = self._format_portfolio(portfolio)
            
            return f"""感谢您提供详细信息！我已经记录了您的投资目标：

投资概要：
- 投资目的：{investment_goal}
- 目标金额：{self._format_amount(target_value)}
- 投资年限：{years}年
- 初始资金：{self._format_amount(initial_investment)}
{portfolio_str}

要达到您的目标，需要获得约{target_return_percentage:.1f}%的年化收益率。

建议您点击侧边栏的"去做风险评估"按钮，完成风险承受能力评估。这将帮助我们为您制定更合适的投资策略。"""
        
        # 如果是自由问答阶段的问题
        if analysis.get("intent") == "ask_question":
            question_type = analysis.get("question_info", {}).get("type", "")
            original_question = analysis.get("question_info", {}).get("original_question", "")
            
            # 根据问题类型构建不同的 prompt
            if question_type == "investment_timing" or question_type == "market_analysis":
                prompt = f"""作为专业的投资顾问，请分析当前市场情况。

用户问题：{original_question}

请简要分析：
1. 当前市场环境
2. 主要影响因素
3. 投资建议

注意：分析要客观专业，避免过于主观的判断。"""
            else:
                prompt = f"""作为专业的投资顾问，请回答用户的问题。

用户问题：{original_question}

请提供专业、简洁的回答。如果涉及投资建议，请说明相关风险。"""
            
            try:
                # 调用 LLM 生成回答，设置较短的超时时间
                response = await LLMUtils.call_llm(
                    prompt=prompt,
                    temperature=0.7,
                    timeout=10  # 设置10秒超时
                )
                return response["text"]
            except Exception as e:
                print(f"生成回答时出错: {str(e)}")
                return "抱歉，我现在无法提供准确的市场分析。建议您查看最新的市场报告或咨询您的投资顾问。"
        
        # 默认回复
        return "我明白了。请告诉我更多关于您的投资需求。"
    
    def _format_portfolio(self, portfolio: Dict) -> str:
        """格式化投资组合信息"""
        if not portfolio.get('assets') or not portfolio.get('weights'):
            return "\n\n您目前没有投资组合。"
        
        portfolio_str = "\n\n当前投资组合："
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
            portfolio_str += f"\n- {asset_name}: {weight*100:.1f}%"
        return portfolio_str
    
    def _process_risk_assessment_answer(self, analysis: Dict) -> Dict:
        """处理风险评估答案"""
        answer = analysis.get("extracted_info", {}).get("answer", "")
        if not answer:
            return {
                "success": False,
                "message": "请选择提供的选项之一"
            }
        
        result = self.risk_manager.process_answer(answer)
        if not result["success"]:
            return {
                "success": False,
                "message": result["message"]
            }
        
        if result["is_complete"]:
            # 更新风险评估结果
            risk_tolerance = self.risk_manager.calculate_risk_tolerance()
            self.config_manager.update_risk_profile(
                score=self.risk_manager.total_score,
                tolerance=risk_tolerance
            )
            # 转换到下一个状态
            if self.state_manager.can_transition_to(ConversationState.COLLECTING_EXTRA_INFO):
                self.state_manager.transition_to(ConversationState.COLLECTING_EXTRA_INFO)
            return {
                "success": True,
                "message": f"风险评估完成！根据您的回答，您的风险承受能力类型为：{risk_tolerance}"
            }
        
        return {
            "success": True,
            "message": "感谢您的回答，我们将根据您的风险承受能力为您制定合适的投资策略。"
        }
    
    async def chat(self, user_input: str) -> str:
        """处理用户输入并生成回复"""
        print("\n=== 开始对话流程 ===")
        print("当前状态:", self.state_manager.current_state.value)
        
        # 打印当前配置
        print("\n当前配置信息:")
        config = self.config_manager.to_dict()
        print(json.dumps(config, ensure_ascii=False, indent=2))
        
        # 打印当前对话历史
        print("\n当前对话历史:")
        history = self.state_manager.history
        print(json.dumps(history, ensure_ascii=False, indent=2))
        
        try:
            # 1. 分析用户输入
            print("\n1. 分析用户输入...")
            analysis = await self.analyze_input(user_input)
            
            # 打印分析结果
            print("\n分析结果详情:")
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
            
            # 2. 确定对话策略
            print("\n2. 确定对话策略...")
            strategy = self.determine_strategy(analysis)
            
            # 打印策略详情
            print("\n策略详情:")
            print(json.dumps(strategy, ensure_ascii=False, indent=2))
            
            # 3. 生成回复
            print("\n3. 生成回复...")
            response = await self.generate_response(strategy, analysis)
            
            # 4. 更新对话历史
            print("\n4. 更新对话历史...")
            # 添加用户消息
            user_message = {
                "role": "user",
                "content": user_input,
                "state": self.state_manager.current_state.value,
                "extracted_info": analysis.get("extracted_info", {})
            }
            print("\n添加用户消息:")
            print(json.dumps(user_message, ensure_ascii=False, indent=2))
            self.state_manager.add_to_history(user_message)
            
            # 添加助手回复
            assistant_message = {
                "role": "assistant",
                "content": response,
                "state": self.state_manager.current_state.value,
                "strategy": strategy
            }
            print("\n添加助手回复:")
            print(json.dumps(assistant_message, ensure_ascii=False, indent=2))
            self.state_manager.add_to_history(assistant_message)
            
            # 打印更新后的配置
            print("\n更新后的配置信息:")
            updated_config = self.config_manager.to_dict()
            print(json.dumps(updated_config, ensure_ascii=False, indent=2))
            
            # 打印更新后的对话历史
            print("\n更新后的对话历史:")
            updated_history = self.state_manager.history
            print(json.dumps(updated_history, ensure_ascii=False, indent=2))
            
            print("\n5. 返回生成的回复")
            return response
            
        except Exception as e:
            print(f"\n❌ 对话处理过程中出错: {str(e)}")
            print("错误堆栈:")
            import traceback
            print(traceback.format_exc())
            return "抱歉，我在处理您的消息时遇到了问题。请再说一遍您的需求。" 