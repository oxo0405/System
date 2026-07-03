#!/usr/bin/env python3
import os
import json
import requests
from typing import Optional, Dict, Any, List, Tuple

class SiliconFlowAI:
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY", "sk-psppfclovqencgwdhvsfsyabncmtvnobfqlrwgoezgfxpwsb")
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        if not self.is_available():
            return "错误: API密钥未配置"
        
        if not content or len(content.strip()) == 0:
            return "文件内容为空"
        
        if len(content) > 10000:
            content = content[:10000] + "...(内容已截断)"
        
        prompt = f"""请为以下文本生成一个简洁的摘要，摘要长度控制在{max_length}字以内，突出核心内容：

{content}

摘要："""
        
        try:
            response = self._call_api(prompt)
            return response.strip()
        except Exception as e:
            return f"生成摘要失败: {str(e)}"
    
    def smart_search(self, query: str, files_content: List[Tuple[str, str]]) -> List[Tuple[str, str, float]]:
        if not self.is_available():
            return [("错误", "API密钥未配置", 0.0)]
        
        if not query.strip():
            return []
        
        if not files_content:
            return []
        
        files_text = ""
        for idx, (name, content) in enumerate(files_content[:20]):
            if len(content) > 2000:
                content = content[:2000] + "..."
            files_text += f"\n文件{idx+1} [{name}]:\n{content}\n"
        
        prompt = f"""请根据用户的查询，从以下文件中找出最相关的内容。
返回格式为JSON数组，每个元素包含：文件名、相关片段、相关性评分(0-1之间的小数)。

用户查询：{query}

文件列表：
{files_text}

请返回JSON格式的结果："""
        
        try:
            response = self._call_api(prompt)
            results = self._parse_search_results(response)
            return results
        except Exception as e:
            return [("错误", f"搜索失败: {str(e)}", 0.0)]
    
    def _call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")
    
    def _parse_search_results(self, response: str) -> List[Tuple[str, str, float]]:
        try:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                results = []
                for item in data:
                    name = item.get("文件名", "未知")
                    snippet = item.get("相关片段", "")
                    score = float(item.get("相关性评分", 0.0))
                    results.append((name, snippet, score))
                return sorted(results, key=lambda x: x[2], reverse=True)
        except:
            pass
        
        return [("AI响应", response[:500], 0.5)]


_ai_service = None

def get_ai_service(api_key: str = None) -> SiliconFlowAI:
    global _ai_service
    if _ai_service is None:
        _ai_service = SiliconFlowAI(api_key)
    return _ai_service
