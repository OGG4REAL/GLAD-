import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main()) 