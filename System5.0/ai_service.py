# ai_service.py - AI服务模块（新建文件）
import json
import requests
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class AIService(QObject):
    summary_ready = pyqtSignal(str, str)
    search_ready = pyqtSignal(str, list)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key=None, base_url="https://api.siliconflow.cn/v1"):
        super().__init__()
        self.api_key = api_key or "YOUR_SILICONFLOW_API_KEY"
        self.base_url = base_url
        self.model = "Qwen/Qwen2-7B-Instruct"
        self.timeout = 30
        
    def generate_summary(self, file_path, content, max_length=150):
        def _generate():
            try:
                self.status_update.emit(f"正在生成摘要: {file_path}")
                truncated = content[:2000] if len(content) > 2000 else content
                prompt = f"请为以下文件内容生成一个简洁的摘要（不超过{max_length}字）：\n文件：{file_path}\n内容：{truncated}\n摘要："
                summary = self._call_api(prompt)
                if summary:
                    self.summary_ready.emit(file_path, summary.strip())
                    self.status_update.emit(f"摘要生成完成: {file_path}")
                else:
                    self.error_occurred.emit(f"生成摘要失败: {file_path}")
            except Exception as e:
                self.error_occurred.emit(f"摘要生成错误: {str(e)}")
        
        threading.Thread(target=_generate, daemon=True).start()
    
    def smart_search(self, query, file_contents):
        def _search():
            try:
                self.status_update.emit(f"正在智能检索: {query}")
                file_list = []
                for path, content in list(file_contents.items())[:20]:
                    preview = content[:300] if len(content) > 300 else content
                    file_list.append(f"文件: {path}\n预览: {preview}")
                files_text = "\n---\n".join(file_list)
                
                prompt = f"""用户查询: {query}

文件列表:
{files_text}

请找出最相关的文件，以JSON数组格式返回：[{{"file":"路径","reason":"原因","relevance":0.9}}]"""

                response = self._call_api(prompt)
                if response:
                    results = self._parse_results(response)
                    self.search_ready.emit(query, results)
                    self.status_update.emit(f"检索完成: 找到 {len(results)} 个相关文件")
                else:
                    self.error_occurred.emit(f"智能检索失败: {query}")
            except Exception as e:
                self.error_occurred.emit(f"智能检索错误: {str(e)}")
        
        threading.Thread(target=_search, daemon=True).start()
    
    def _call_api(self, prompt):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": self.model,
            "messages": [{"role": "system", "content": "你是专业的文件管理助手。"},
                         {"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 800
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            self.error_occurred.emit(f"API错误: {resp.status_code}")
            return None
        except Exception as e:
            self.error_occurred.emit(f"请求异常: {str(e)}")
            return None
    
    def _parse_results(self, response):
        try:
            results = json.loads(response)
            if isinstance(results, list):
                return results
        except:
            import re
            results = []
            files = re.findall(r'"file"\s*:\s*"([^"]+)"', response)
            reasons = re.findall(r'"reason"\s*:\s*"([^"]+)"', response)
            for i, f in enumerate(files):
                results.append({"file": f, "reason": reasons[i] if i < len(reasons) else "相关", "relevance": 0.8})
        return results
