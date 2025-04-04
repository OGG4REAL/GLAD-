from typing import Dict, Optional, List
import json
import asyncio
import aiohttp
from ..config.api_config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_TOKENS,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_INTERVAL
)

class LLMUtils:
    @staticmethod
    async def call_llm(
        prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        system_prompt: str = None,
        model: str = DEFAULT_MODEL
    ) -> Dict:
        """调用语言模型"""
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": MAX_TOKENS
        }
        
        # 发送请求
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{OPENAI_API_BASE}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=REQUEST_TIMEOUT
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "text": result["choices"][0]["message"]["content"],
                                "finish_reason": result["choices"][0]["finish_reason"]
                            }
                        else:
                            error_text = await response.text()
                            print(f"API请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}):")
                            print(f"状态码: {response.status}")
                            print(f"错误信息: {error_text}")
                            
            except asyncio.TimeoutError:
                print(f"请求超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
            except Exception as e:
                print(f"请求异常 (尝试 {attempt + 1}/{MAX_RETRIES}): {str(e)}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_INTERVAL)
        
        raise Exception("LLM 调用失败，已达到最大重试次数")
    
    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict]:
        """从响应中提取 JSON 数据"""
        try:
            # 查找 JSON 开始和结束的位置
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def validate_llm_response(response: Dict) -> bool:
        """验证 LLM 响应是否有效"""
        required_fields = ["text", "finish_reason"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def format_prompt(template: str, **kwargs) -> str:
        """格式化 prompt 模板"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required prompt parameter: {e}")
        except Exception as e:
            raise ValueError(f"Error formatting prompt: {e}")
            
    @staticmethod
    async def retry_with_fallback(prompt: str, max_retries: int = 2) -> Dict:
        """带有降级重试的 LLM 调用"""
        for attempt in range(max_retries):
            try:
                # 第一次尝试使用正常温度
                if attempt == 0:
                    return await LLMUtils.call_llm(prompt)
                # 后续尝试增加温度以获得不同的结果
                else:
                    return await LLMUtils.call_llm(
                        prompt,
                        temperature=DEFAULT_TEMPERATURE + 0.1 * attempt
                    )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"重试 LLM 调用 (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(RETRY_INTERVAL) 
