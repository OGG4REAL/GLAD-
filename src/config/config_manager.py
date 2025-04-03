from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class CoreInvestment:
    target_value: Optional[float] = None
    years: Optional[float] = None
    initial_investment: Optional[float] = None

@dataclass
class RiskProfile:
    score: Optional[int] = None
    tolerance: Optional[str] = None

@dataclass
class Portfolio:
    assets: Optional[List[str]] = None
    weights: Optional[List[float]] = None

@dataclass
class PersonalInfo:
    family_status: Optional[str] = None
    employment: Optional[str] = None
    wealth_source: Optional[str] = None
    investment_goal: Optional[str] = None

@dataclass
class FinancialInfo:
    cash_deposits: Optional[float] = None
    investments: Optional[float] = None
    employee_benefits: Optional[float] = None
    private_ownership: Optional[float] = None
    life_insurance: Optional[float] = None
    consumer_debt: Optional[float] = None
    mortgage: Optional[float] = None
    other_debt: Optional[float] = None
    account_debt: Optional[float] = None

@dataclass
class UserInfo:
    personal: PersonalInfo = field(default_factory=PersonalInfo)
    financial: FinancialInfo = field(default_factory=FinancialInfo)

class ConfigManager:
    def __init__(self):
        self.core_investment = CoreInvestment()
        self.risk_profile = RiskProfile()
        self.portfolio = Portfolio()
        self.user_info = UserInfo()
        
    def is_core_info_complete(self) -> bool:
        """检查核心投资信息是否完整"""
        return all([
            self.core_investment.target_value is not None,
            self.core_investment.years is not None,
            self.core_investment.initial_investment is not None,
            self.portfolio.assets is not None and len(self.portfolio.assets) > 0,
            self.portfolio.weights is not None and len(self.portfolio.weights) > 0
        ])
    
    def get_missing_core_info(self) -> List[str]:
        """获取缺失的核心信息项"""
        missing = []
        if self.core_investment.target_value is None:
            missing.append("target_value")
        if self.core_investment.years is None:
            missing.append("years")
        if self.core_investment.initial_investment is None:
            missing.append("initial_investment")
        if self.portfolio.assets is None or len(self.portfolio.assets) == 0:
            missing.append("portfolio_assets")
        if self.portfolio.weights is None or len(self.portfolio.weights) == 0:
            missing.append("portfolio_weights")
        return missing
    
    def get_missing_user_info(self) -> Dict[str, List[str]]:
        """获取缺失的用户信息项"""
        missing = {"personal": [], "financial": []}
        
        # 检查个人信息
        for field in PersonalInfo.__dataclass_fields__:
            if getattr(self.user_info.personal, field) is None:
                missing["personal"].append(field)
        
        # 检查财务信息
        for field in FinancialInfo.__dataclass_fields__:
            if getattr(self.user_info.financial, field) is None:
                missing["financial"].append(field)
        
        return missing
    
    def update_core_investment(self, **kwargs) -> None:
        """更新核心投资信息"""
        for key, value in kwargs.items():
            if hasattr(self.core_investment, key):
                setattr(self.core_investment, key, value)
    
    def update_risk_profile(self, score: Optional[int] = None, tolerance: Optional[str] = None) -> None:
        """更新风险评估信息"""
        if score is not None:
            self.risk_profile.score = score
        if tolerance is not None:
            self.risk_profile.tolerance = tolerance
    
    def update_portfolio(self, assets: List[str] = None, weights: List[float] = None) -> None:
        """更新投资组合信息"""
        if assets is not None:
            self.portfolio.assets = assets
        if weights is not None:
            self.portfolio.weights = weights
    
    def update_user_info(self, info_type: str, **kwargs) -> None:
        """更新用户信息"""
        if info_type == "personal":
            for key, value in kwargs.items():
                if hasattr(self.user_info.personal, key):
                    setattr(self.user_info.personal, key, value)
        elif info_type == "financial":
            for key, value in kwargs.items():
                if hasattr(self.user_info.financial, key):
                    setattr(self.user_info.financial, key, value)
    
    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            "core_investment": {
                "target_value": self.core_investment.target_value,
                "years": self.core_investment.years,
                "initial_investment": self.core_investment.initial_investment
            },
            "risk_profile": {
                "score": self.risk_profile.score,
                "tolerance": self.risk_profile.tolerance
            },
            "portfolio": {
                "assets": self.portfolio.assets,
                "weights": self.portfolio.weights
            },
            "user_info": {
                "personal": {
                    field: getattr(self.user_info.personal, field)
                    for field in PersonalInfo.__dataclass_fields__
                },
                "financial": {
                    field: getattr(self.user_info.financial, field)
                    for field in FinancialInfo.__dataclass_fields__
                }
            }
        }