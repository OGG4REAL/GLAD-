from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

class ConversationState(Enum):
    """对话状态"""
    COLLECTING_INFO = "COLLECTING_INFO"  # 收集投资信息状态
    FREE_CHAT = "FREE_CHAT"              # 自由问答状态

@dataclass
class ConversationContext:
    """对话上下文"""
    current_focus: Optional[str] = None  # 当前关注点
    history: List[Dict] = field(default_factory=list)  # 对话历史
    max_history: int = 10  # 最大历史记录数

class StateManager:
    def __init__(self):
        self.current_state = ConversationState.FREE_CHAT
        self.context = ConversationContext()
        self._state_transitions = {
            ConversationState.COLLECTING_INFO: [ConversationState.FREE_CHAT],
            ConversationState.FREE_CHAT: [ConversationState.COLLECTING_INFO]
        }
    
    def can_transition_to(self, target_state: ConversationState) -> bool:
        """检查是否可以转换到目标状态"""
        return target_state in self._state_transitions[self.current_state]
    
    def transition_to(self, target_state: ConversationState) -> None:
        """转换到目标状态"""
        if not self.can_transition_to(target_state):
            raise ValueError(f"不能从 {self.current_state.value} 转换到 {target_state.value}")
        self.current_state = target_state
    
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
    
    def update_info_collection_progress(self):
        """更新信息收集进度"""
        print("\n=== 更新信息收集进度 ===")
        print(f"当前状态: {self.current_state.value}")
        print("更新前进度:", self.info_collection_progress)
        
        if self.current_state == ConversationState.COLLECTING_INFO:
            self.info_collection_progress['core_info'] += 1
        elif self.current_state == ConversationState.FREE_CHAT:
            self.info_collection_progress['risk_assessment'] += 1
            
        print("更新后进度:", self.info_collection_progress)
    
    def get_info_collection_progress(self) -> dict:
        """获取信息收集进度"""
        return self.info_collection_progress
    
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