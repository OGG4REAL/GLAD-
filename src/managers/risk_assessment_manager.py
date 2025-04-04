import json
from typing import Dict, List, Optional
from pathlib import Path

class RiskAssessmentManager:
    def __init__(self):
        self.questions = []
        self.current_question_index = 0
        self.total_score = 0
        self.load_questions()
    
    def load_questions(self) -> None:
        """加载风险评估问题"""
        questions_path = Path(__file__).parent.parent.parent / "risk_question.json"
        try:
            with open(questions_path, 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
        except Exception as e:
            print(f"加载风险评估问题时出错: {str(e)}")
            self.questions = []
    
    def get_current_question(self) -> Optional[Dict]:
        """获取当前问题"""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def process_answer(self, answer: str) -> Dict:
        """处理用户答案"""
        current_question = self.get_current_question()
        if not current_question:
            return {
                "success": False,
                "message": "没有更多问题",
                "is_complete": True
            }
        
        # 验证答案
        if answer not in current_question["scores"]:
            return {
                "success": False,
                "message": "无效的答案，请选择提供的选项之一",
                "is_complete": False
            }
        
        # 计算得分
        self.total_score += current_question["scores"][answer]
        self.current_question_index += 1
        
        # 检查是否完成所有问题
        is_complete = self.current_question_index >= len(self.questions)
        
        return {
            "success": True,
            "message": "答案已记录",
            "is_complete": is_complete,
            "total_score": self.total_score if is_complete else None
        }
    
    def calculate_risk_tolerance(self) -> str:
        """根据总分计算风险承受能力"""
        # 假设总分范围是13-46分
        if self.total_score <= 20:
            return "保守型"
        elif self.total_score <= 30:
            return "稳健型"
        elif self.total_score <= 40:
            return "进取型"
        else:
            return "激进型"
    
    def reset(self) -> None:
        """重置评估状态"""
        self.current_question_index = 0
        self.total_score = 0 
