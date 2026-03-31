from .core import BrowserCore
import urllib.request
import urllib.parse
import json
import atexit
import time
import uuid

def _get_lang_code(lang):
    lang = lang.lower().strip()
    lang_map = {
        'russian': 'ru', 'english': 'en', 'spanish': 'es', 'french': 'fr', 
        'german': 'de', 'italian': 'it', 'portuguese': 'pt', 'chinese': 'zh-cn', 
        'japanese': 'ja', 'korean': 'ko', 'arabic': 'ar', 'hindi': 'hi',
        'dutch': 'nl', 'turkish': 'tr', 'polish': 'pl', 'ukrainian': 'uk'
    }
    return lang_map.get(lang, lang)

def _detect_language(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text[:500])}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[2]
    except:
        return 'en'

def _translate_text(text, target_lang, prompt_text=None):
    if not text or not text.strip(): return text
    
    target_lang = target_lang.lower().strip()
    if target_lang == 'auto':
        if not prompt_text: return text
        tl = _detect_language(prompt_text)
    else:
        tl = _get_lang_code(target_lang)
        
    chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
    translated_text = ""
    
    for chunk in chunks:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={tl}&dt=t&q={urllib.parse.quote(chunk)}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                for sentence in data[0]:
                    if sentence[0]:
                        translated_text += sentence[0]
        except Exception:
            return text
            
    return translated_text

class Completions:
    def __init__(self, client):
        self.client = client

    def create(self, model: str, messages: list, stream: bool = False, translation: str = None, extra_params: dict = None, param_mappings: dict = None, input_selectors: list = None, button_selectors: list = None, output_selectors: list = None, **kwargs):
        prompt = messages[-1]["content"] if messages else ""
        
        combined_params = extra_params or {}
        combined_params.update(kwargs)
        
        response = self.client.core.execute(
            model=model, 
            prompt=prompt, 
            is_image=False, 
            stream=stream,
            extra_params=combined_params,
            param_mappings=param_mappings,
            input_selectors=input_selectors,
            button_selectors=button_selectors,
            output_selectors=output_selectors
        )
        
        if stream:
            def generate_stream():
                completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
                created_time = int(time.time())
                for chunk in response:
                    yield {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]
                    }
                yield {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
            return generate_stream()
        else:
            response_text = response
            if isinstance(response_text, list):
                response_text = str(response_text)
                
            if translation and response_text and not response_text.startswith("Execution Error"):
                response_text = _translate_text(response_text, translation, prompt)
                
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices":[{"index": 0, "message": {"role": "assistant", "content": response_text}, "finish_reason": "stop"}]
            }

class Chat:
    def __init__(self, client):
        self.completions = Completions(client)

class Images:
    def __init__(self, client):
        self.client = client

    def generate(self, model: str, prompt: str, num_images: int = 1, extra_params: dict = None, param_mappings: dict = None, input_selectors: list = None, button_selectors: list = None, output_selectors: list = None, **kwargs) -> dict:
        combined_params = extra_params or {}
        combined_params.update(kwargs)
        
        image_results = self.client.core.execute(
            model=model, 
            prompt=prompt, 
            is_image=True, 
            num_images=num_images,
            extra_params=combined_params,
            param_mappings=param_mappings,
            input_selectors=input_selectors,
            button_selectors=button_selectors,
            output_selectors=output_selectors
        )
        
        if isinstance(image_results, str):
            return {
                "created": int(time.time()),
                "error": image_results,
                "data": []
            }
            
        return {
            "created": int(time.time()),
            "data": [{"url": img_url} for img_url in image_results]
        }

class Client:
    def __init__(self, headless: bool = True, debug: bool = False, disable_safety_settings: bool = False):
        self.debug = debug
        self.disable_safety_settings = disable_safety_settings
        self.core = BrowserCore(headless=headless, debug=debug, disable_safety_settings=disable_safety_settings)
        self.chat = Chat(self)
        self.images = Images(self)
        atexit.register(self.close)

    def close(self):
        self.core.quit()

    def __enter__(self):
        return self
    
    def __del__(self):
        try:
            self.close()
        except:
            pass


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()