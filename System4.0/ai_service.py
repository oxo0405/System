#!/usr/bin/env python3
import requests
import json


class OllamaService:
    def __init__(self, base_url="http://localhost:11434", model="qwen2:0.5b"):
        self.base_url = base_url
        self.model = model
        self.api_generate = base_url + "/api/generate"
        self.api_chat = base_url + "/api/chat"
        self._check_connection()
    
    def _check_connection(self):
        try:
            response = requests.get(self.base_url + "/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_available(self):
        return self._check_connection()
    
    def generate_summary(self, content, filename=""):
        if not content or len(content.strip()) == 0:
            return False, "文件内容为空，无法生成摘要"
        
        content_preview = content[:2000]
        if len(content) > 2000:
            content_preview += "...\n(内容已截断，仅分析前2000字符)"
        
        prompt = """请为以下文件生成一段简洁的摘要（50-100字），提取核心内容和关键信息：

文件名：""" + (filename if filename else '未命名文件') + """

文件内容：
""" + content_preview + """

要求：
1. 摘要应简洁明了，突出核心内容
2. 如果内容包含代码，说明代码的功能和用途
3. 如果是文本文件，概括主要观点或主题
4. 只返回摘要内容，不要添加额外说明

摘要："""
        
        try:
            response = requests.post(
                self.api_generate,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                    "max_tokens": 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("response", "").strip()
                if summary:
                    return True, summary
                else:
                    return False, "AI 返回结果为空"
            else:
                return False, "API 请求失败: " + str(response.status_code)
                
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查 Ollama 服务是否正常运行"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 Ollama 服务，请确保已启动 ollama serve"
        except Exception as e:
            return False, "生成摘要时出错: " + str(e)
    
    def smart_search(self, query, files):
        if not query or not query.strip():
            return False, "请输入搜索关键词"
        
        if not files:
            return False, "没有可搜索的文件"
        
        file_descriptions = []
        for name, content in files:
            preview = content[:500] if content else ""
            if len(content) > 500:
                preview += "..."
            file_descriptions.append("- " + name + ":\n  " + preview)
        
        files_text = "\n\n".join(file_descriptions)
        
        prompt = """请根据用户的查询需求，在以下文件中找出最相关的内容。

用户查询：""" + query + """

文件列表及内容预览：
""" + files_text + """

请执行以下步骤：
1. 分析每个文件内容与查询的相关性
2. 按相关性从高到低排序
3. 对于相关文件，说明相关的原因和匹配的内容
4. 如果没有相关文件，请明确说明

输出格式：
【相关文件】
1. 文件名 - 相关性：高/中/低
   匹配内容：...
   原因：...
2. ...

如果文件内容不完整，基于已有信息进行判断。

搜索结果："""
        
        try:
            response = requests.post(
                self.api_generate,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,
                    "max_tokens": 500
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                search_result = result.get("response", "").strip()
                if search_result:
                    return True, search_result
                else:
                    return False, "AI 返回结果为空"
            else:
                return False, "API 请求失败: " + str(response.status_code)
                
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查 Ollama 服务是否正常运行"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 Ollama 服务，请确保已启动 ollama serve"
        except Exception as e:
            return False, "智能检索时出错: " + str(e)

    def get_available_models(self):
        try:
            response = requests.get(self.base_url + "/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return [model['name'] for model in models]
            return []
        except:
            return []


_ai_service_instance = None

def get_ai_service():
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = OllamaService()
    return _ai_service_instance
