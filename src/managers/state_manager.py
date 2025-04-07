from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

class ConversationState(Enum):
    """对话状态"""
    INITIALIZING = "INITIALIZING"      # 初始化状态
    COLLECTING_INFO = "COLLECTING_INFO" # 收集投资信息状态
    FREE_CHAT = "FREE_CHAT"            # 自由问答状态
    RISK_ASSESSMENT = "RISK_ASSESSMENT" # 风险评估状态
    PORTFOLIO_PLANNING = "PORTFOLIO_PLANNING" # 投资组合规划状态

@dataclass
class ConversationContext:
    """对话上下文"""
    current_focus: Optional[str] = None  # 当前关注点
    history: List[Dict] = field(default_factory=list)  # 对话历史
    max_history: int = 10  # 最大历史记录数
    consecutive_questions: int = 0  # 连续提问计数器
    state_history: List[str] = field(default_factory=list)  # 状态历史

class StateManager:
    def __init__(self):
        self.current_state = ConversationState.INITIALIZING
        self.context = ConversationContext()
        self._state_transitions = {
            ConversationState.INITIALIZING: [
                ConversationState.COLLECTING_INFO,
                ConversationState.FREE_CHAT
            ],
            ConversationState.COLLECTING_INFO: [
                ConversationState.FREE_CHAT,
                ConversationState.RISK_ASSESSMENT
            ],
            ConversationState.FREE_CHAT: [
                ConversationState.COLLECTING_INFO,
                ConversationState.RISK_ASSESSMENT,
                ConversationState.PORTFOLIO_PLANNING
            ],
            ConversationState.RISK_ASSESSMENT: [
                ConversationState.FREE_CHAT,
                ConversationState.PORTFOLIO_PLANNING
            ],
            ConversationState.PORTFOLIO_PLANNING: [
                ConversationState.FREE_CHAT,
                ConversationState.COLLECTING_INFO
            ]
        }
        # 初始化信息收集进度
        self.info_collection_progress = {
            'core_info': 0,          # 核心信息收集进度
            'risk_assessment': 0,     # 风险评估进度
            'portfolio': 0,           # 投资组合信息收集进度
            'additional_info': 0      # 额外信息收集进度
        }
        # 初始化状态数据
        self.state_data = {
            'previous_state': None,  # 上一个状态
            'state_entry_time': None,  # 进入当前状态的时间
            'state_duration': 0,      # 当前状态持续时间
            'transition_count': 0,    # 状态转换次数
        }
    
    def can_transition_to(self, target_state: ConversationState) -> bool:
        """检查是否可以转换到目标状态"""
        # 允许从任何状态转换到 FREE_CHAT
        if target_state == ConversationState.FREE_CHAT:
            return True
        # 检查是否在允许的转换列表中
        return target_state in self._state_transitions[self.current_state]
    
    def transition_to(self, target_state: ConversationState) -> None:
        """转换到目标状态"""
        import time
        
        if not isinstance(target_state, ConversationState):
            raise ValueError(f"无效的目标状态: {target_state}")
            
        if self.current_state == target_state:
            return  # 如果是相同状态，直接返回
            
        if not self.can_transition_to(target_state):
            print(f"警告: 不建议从 {self.current_state.value} 转换到 {target_state.value}")
            # 不再抛出异常，而是记录警告
            
        # 更新状态数据
        current_time = time.time()
        if self.state_data['state_entry_time']:
            self.state_data['state_duration'] = current_time - self.state_data['state_entry_time']
            
        self.state_data['previous_state'] = self.current_state
        self.current_state = target_state
        self.state_data['state_entry_time'] = current_time
        self.state_data['transition_count'] += 1
        
        # 记录状态历史
        self.context.state_history.append(target_state.value)
        
        print(f"\n状态转换: {self.state_data['previous_state'].value} -> {target_state.value}")
        print(f"状态持续时间: {self.state_data['state_duration']:.2f}秒")
        print(f"总转换次数: {self.state_data['transition_count']}")
        
    def add_to_history(self, message: Dict) -> None:
        """添加消息到历史记录"""
        self.context.history.append(message)
        # 保持历史记录在最大限制内
        if len(self.context.history) > self.context.max_history:
            self.context.history = self.context.history[-self.context.max_history:]
    
    def get_recent_context(self, state_filter: Optional[ConversationState] = None) -> List[Dict]:
        """获取最近的对话历史
        
        Args:
            state_filter: 可选的状态过滤器，只返回特定状态的消息
        """
        if state_filter:
            return [
                msg for msg in self.context.history[-6:]  # 最多返回最近3轮对话
                if msg.get("state") == state_filter.value
            ]
        return self.context.history[-6:]  # 最多返回最近3轮对话
    
    def clear_history(self) -> None:
        """清空对话历史"""
        self.context.history = []
    
    def add_message(self, role: str, content: str) -> None:
        """添加对话消息"""
        self.context.history.append({
            "role": role,
            "content": content
        })
        
    def set_focus(self, focus_item: str) -> None:
        """设置当前关注的信息项"""
        self.context.current_focus = focus_item
        
    def should_switch_topic(self) -> bool:
        """判断是否应该转换话题"""
        # 如果连续提问次数过多，建议转换话题
        return self.context.consecutive_questions >= 3
    
    def update_question_counter(self, is_question: bool) -> None:
        """更新连续提问计数器"""
        if is_question:
            self.context.consecutive_questions += 1
        else:
            self.context.consecutive_questions = 0
    
    def update_info_collection_progress(self, info_type: str = None):
        """更新信息收集进度
        
        Args:
            info_type: 要更新的信息类型，可以是 'core_info', 'risk_assessment', 'portfolio', 'additional_info'
                      如果不指定，则根据当前状态自动判断
        """
        print("\n=== 更新信息收集进度 ===")
        print(f"当前状态: {self.current_state.value}")
        print("更新前进度:", self.info_collection_progress)
        
        if info_type and info_type in self.info_collection_progress:
            self.info_collection_progress[info_type] += 1
        else:
            # 根据当前状态自动判断要更新的进度
            if self.current_state == ConversationState.COLLECTING_INFO:
                # 在收集信息状态下，优先更新核心信息进度
                if self.info_collection_progress['core_info'] < 3:  # 假设核心信息有3项
                    self.info_collection_progress['core_info'] += 1
                # 如果核心信息已收集完，更新投资组合进度
                elif self.info_collection_progress['portfolio'] < 1:
                    self.info_collection_progress['portfolio'] += 1
                # 最后更新额外信息进度
                else:
                    self.info_collection_progress['additional_info'] += 1
            elif self.current_state == ConversationState.FREE_CHAT:
                # 在自由问答状态下，可能在进行风险评估
                if self.info_collection_progress['core_info'] >= 3:  # 只有在核心信息收集完后才更新风险评估进度
                    self.info_collection_progress['risk_assessment'] += 1
            
        print("更新后进度:", self.info_collection_progress)
        
    def get_info_collection_progress(self) -> dict:
        """获取信息收集进度"""
        return self.info_collection_progress.copy()  # 返回副本以防止外部修改
    
    def get_state_info(self) -> dict:
        """获取当前状态信息"""
        print("\n=== 获取状态信息 ===")
        state_info = {
            "current_state": self.current_state.value,
            "current_focus": self.context.current_focus,
            "info_collection_progress": self.info_collection_progress
        }
        print("状态信息:")
        print(json.dumps(state_info, ensure_ascii=False, indent=2))
        return state_info
    
    def can_ask_for_info(self) -> bool:
        """判断当前是否适合询问信息"""
        # 如果连续提问次数过多，或者刚刚问过问题，则不适合继续提问
        return (self.context.consecutive_questions < 3 and 
                len(self.context.history) > 0 and 
                self.context.history[-1]["role"] == "user")
    
    def get_state_history(self) -> List[str]:
        """获取状态历史"""
        return self.context.state_history.copy() 
