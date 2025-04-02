from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

class ConversationState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"                    # 初始状态
    FREE_CHAT = "free_chat"  # 新增自由问答状态
    COLLECTING_CORE_INFO = "collecting_core_info"  # 收集核心信息
    RISK_ASSESSMENT = "risk_assessment"    # 风险评估
    COLLECTING_EXTRA_INFO = "collecting_extra_info"  # 收集额外信息
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    COMPLETED = "completed"

@dataclass
class ConversationContext:
    """对话上下文"""
    messages: List[Dict] = field(default_factory=list)
    current_focus: Optional[str] = None  # 当前关注的信息项
    last_question: Optional[str] = None  # 上一个问题
    consecutive_questions: int = 0       # 连续提问次数
    last_response_time: Optional[float] = None  # 上次回复时间
    topic_switch_count: int = 0  # 话题切换次数

class StateManager:
    def __init__(self):
        print("\n=== 初始化状态管理器 ===")
        self._current_state = ConversationState.INITIAL
        print(f"初始状态: {self._current_state.value}")
        self.context = ConversationContext()
        self.history = []  # 对话历史
        self.state_history = []  # 状态历史
        self.info_collection_progress = {
            'core_info': 0,
            'risk_assessment': 0,
            'extra_info': 0
        }
        
    @property
    def current_state(self) -> ConversationState:
        return self._current_state
    
    def transition_to(self, new_state: ConversationState) -> None:
        """状态转换"""
        print(f"\n=== 状态转换 ===")
        print(f"从 {self._current_state.value} 转换到 {new_state.value}")
        self.state_history.append(self._current_state)
        self._current_state = new_state
        print(f"状态历史: {[state.value for state in self.state_history]}")
        
    def can_transition_to(self, new_state: ConversationState) -> bool:
        """检查是否可以转换到新状态"""
        # 定义有效的状态转换
        valid_transitions = {
            ConversationState.INITIAL: [
                ConversationState.FREE_CHAT,
                ConversationState.RISK_ASSESSMENT
            ],
            ConversationState.FREE_CHAT: [
                ConversationState.RISK_ASSESSMENT,
                ConversationState.COLLECTING_EXTRA_INFO
            ],
            ConversationState.RISK_ASSESSMENT: [
                ConversationState.COLLECTING_EXTRA_INFO,
                ConversationState.PORTFOLIO_OPTIMIZATION
            ],
            ConversationState.COLLECTING_EXTRA_INFO: [
                ConversationState.PORTFOLIO_OPTIMIZATION,
                ConversationState.COMPLETED
            ],
            ConversationState.PORTFOLIO_OPTIMIZATION: [
                ConversationState.COMPLETED
            ]
        }
        
        return new_state in valid_transitions.get(self._current_state, [])
    
    def add_message(self, role: str, content: str) -> None:
        """添加对话消息"""
        self.context.messages.append({
            "role": role,
            "content": content
        })
        
    def set_focus(self, focus_item: str) -> None:
        """设置当前关注的信息项"""
        self.context.current_focus = focus_item
        
    def get_recent_context(self) -> List[dict]:
        """获取最近的对话历史"""
        print("\n=== 获取最近对话历史 ===")
        print(f"当前历史记录数量: {len(self.history)}")
        
        # 过滤出对话消息（包含 role 和 content 的消息）
        dialogue_history = [
            msg for msg in self.history 
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        print(f"有效对话消息数量: {len(dialogue_history)}")
        
        # 获取最近5条消息
        recent_messages = dialogue_history[-5:]
        print(f"最近消息数量: {len(recent_messages)}")
        
        # 为每条消息添加状态信息
        context_with_state = []
        for msg in recent_messages:
            msg_with_state = msg.copy()
            if "state" not in msg_with_state:
                msg_with_state["state"] = self._current_state.value
            context_with_state.append(msg_with_state)
        
        print("返回的上下文:")
        print(json.dumps(context_with_state, ensure_ascii=False, indent=2))
        return context_with_state
    
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
        print(f"当前状态: {self._current_state.value}")
        print("更新前进度:", self.info_collection_progress)
        
        if self._current_state == ConversationState.COLLECTING_CORE_INFO:
            self.info_collection_progress['core_info'] += 1
        elif self._current_state == ConversationState.RISK_ASSESSMENT:
            self.info_collection_progress['risk_assessment'] += 1
        elif self._current_state == ConversationState.COLLECTING_EXTRA_INFO:
            self.info_collection_progress['extra_info'] += 1
            
        print("更新后进度:", self.info_collection_progress)
    
    def get_info_collection_progress(self) -> dict:
        """获取信息收集进度"""
        return self.info_collection_progress
    
    def add_to_history(self, message: dict):
        """添加消息到历史记录"""
        print("\n=== 添加消息到历史记录 ===")
        print("添加消息:")
        print(json.dumps(message, ensure_ascii=False, indent=2))
        
        # 确保消息包含状态信息
        if "state" not in message:
            message["state"] = self._current_state.value
        
        self.history.append(message)
        print(f"当前历史记录数量: {len(self.history)}")
        
        # 保持历史记录在合理范围内
        if len(self.history) > 10:
            removed = self.history.pop(0)
            print("移除最早的消息:")
            print(json.dumps(removed, ensure_ascii=False, indent=2))
        
        print(f"更新后的历史记录数量: {len(self.history)}")
    
    def get_state_info(self) -> dict:
        """获取当前状态信息"""
        print("\n=== 获取状态信息 ===")
        state_info = {
            "current_state": self._current_state.value,
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
                len(self.context.messages) > 0 and 
                self.context.messages[-1]["role"] == "user") 