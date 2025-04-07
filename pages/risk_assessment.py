import streamlit as st
import json
from pathlib import Path
import os
from typing import Dict, Optional

class RiskAssessmentUI:
    def __init__(self):
        self.questions = self.load_questions()
        self.init_session_state()
    
    def load_questions(self) -> list:
        """加载风险评估问题"""
        try:
            # 尝试多个可能的路径
            possible_paths = [
                Path(__file__).parent.parent / "risk_question.json",  # 相对于当前文件的路径
                Path.cwd() / "risk_question.json",  # 相对于当前工作目录的路径
                Path(os.path.dirname(os.path.abspath(__file__))).parent / "risk_question.json"  # 使用绝对路径
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                        print(f"成功从路径加载问题: {path}")
                        return questions
            
            # 如果所有路径都失败，尝试直接从streamlit的运行目录加载
            with open("risk_question.json", 'r', encoding='utf-8') as f:
                questions = json.load(f)
                print("成功从当前目录加载问题")
                return questions
                
        except Exception as e:
            st.error(f"加载风险评估问题时出错: {str(e)}")
            print(f"错误详情: {str(e)}")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"尝试的路径: {[str(p) for p in possible_paths]}")
            return []
    
    def init_session_state(self):
        """初始化session state"""
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        if 'total_score' not in st.session_state:
            st.session_state.total_score = 0
        if 'answers' not in st.session_state:
            st.session_state.answers = []
        if 'risk_assessment_complete' not in st.session_state:
            st.session_state.risk_assessment_complete = False
    
    def calculate_risk_tolerance(self) -> str:
        """计算风险承受能力类型"""
        total_score = st.session_state.total_score
        if total_score <= 20:
            return "保守型"
        elif total_score <= 30:
            return "稳健型"
        elif total_score <= 40:
            return "进取型"
        else:
            return "激进型"
    
    def reset_assessment(self):
        """重置评估"""
        st.session_state.current_question = 0
        st.session_state.total_score = 0
        st.session_state.answers = []
        st.session_state.risk_assessment_complete = False
    
    def render(self):
        """渲染风险评估页面"""
        st.title("投资风险评估问卷")
        
        if st.session_state.risk_assessment_complete:
            st.success(f"风险评估已完成！您的风险承受能力类型为：{self.calculate_risk_tolerance()}")
            if st.button("重新评估"):
                self.reset_assessment()
            return
        
        if not self.questions:
            st.error("无法加载风险评估问题")
            return
        
        # 显示进度
        progress = st.session_state.current_question / len(self.questions)
        st.progress(progress)
        st.write(f"问题 {st.session_state.current_question + 1}/{len(self.questions)}")
        
        # 显示当前问题
        current_q = self.questions[st.session_state.current_question]
        st.write(f"### {current_q['question']}")
        
        # 创建选项按钮
        col1, col2 = st.columns(2)
        with col1:
            for i, option in enumerate(current_q['options'][:len(current_q['options'])//2]):
                if st.button(option, key=f"option_{i}"):
                    answer = chr(65 + i)  # 转换为A、B、C、D
                    st.session_state.total_score += current_q['scores'][answer]
                    st.session_state.answers.append(answer)
                    st.session_state.current_question += 1
                    
                    if st.session_state.current_question >= len(self.questions):
                        st.session_state.risk_assessment_complete = True
                    st.rerun()
        
        with col2:
            for i, option in enumerate(current_q['options'][len(current_q['options'])//2:], start=len(current_q['options'])//2):
                if st.button(option, key=f"option_{i}"):
                    answer = chr(65 + i)  # 转换为A、B、C、D
                    st.session_state.total_score += current_q['scores'][answer]
                    st.session_state.answers.append(answer)
                    st.session_state.current_question += 1
                    
                    if st.session_state.current_question >= len(self.questions):
                        st.session_state.risk_assessment_complete = True
                    st.rerun()

def main():
    risk_assessment = RiskAssessmentUI()
    risk_assessment.render()

if __name__ == "__main__":
    main() 