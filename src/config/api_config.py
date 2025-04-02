"""API配置文件"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

# LLM 配置
DEFAULT_MODEL = "deepseek-chat"  # 使用 deepseek 的聊天模型
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 2000

# API 请求配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
MAX_RETRIES = 3      # 最大重试次数
RETRY_INTERVAL = 1   # 重试间隔（秒）