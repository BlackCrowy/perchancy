from DrissionPage import ChromiumPage, ChromiumOptions
from typing import List, Dict, Optional, Tuple, Any, Union, Generator
import urllib.request
import base64
import json
import pickle
import os
import time

COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".perchancy_cookies.pkl")

DEFAULT_INPUT_SELECTORS = [
    "[data-name='description']", "textarea[data-name='description']", ".paragraph-input", "#instructionEl", "#instruction", "#prompt", "#textInput", "#userInput", "#chatInput", "textarea[id*='input' i]", "textarea", "input[type='text']"
]
DEFAULT_BUTTON_SELECTORS = [
    "[data-name='generateButton']", "#generateBtn", "#generateButton", "#generateButtonEl", "#sendButton", "#submitButton", "text=✨ generate", "text=generate", ".generate-btn", "button[onclick*='generate' i]", "#resultImgEl", "#resultEl", "button[id*='generate' i]", "button[id*='send' i]", "button"
]
DEFAULT_OUTPUT_SELECTORS = [
    "[data-name='output']", "#output", "#responseEl", "#response", ".message", ".chatMessage", "#chat div", ".output-box", "div[id*='chat'] div"
]

DEFAULT_PARAM_MAPPINGS = {
    "style": ["[data-name='artStyle']"],
    "shape": ["data-name='shape'"],
    "seed": ['data-name="seed"'],
}

class BrowserCore:
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.page = None
        self.cookies_loaded_this_session = False

    def log(self, msg: str) -> None:
        if self.debug:
            print(f"[DEBUG] {msg}")

    def init_driver(self) -> ChromiumPage:
        if self.page is not None:
            return self.page
        self.log("Initializing browser...")
        options = ChromiumOptions()
        if self.headless:
            options.headless()
            
        options.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        options.set_argument("--disable-blink-features=AutomationControlled")
        options.set_argument("--window-size=1920,1080")
        options.set_argument("--disable-popup-blocking")
        options.set_argument("--no-sandbox")
        options.set_argument("--disable-dev-shm-usage")
        options.set_argument("--disable-extensions")
        options.set_argument("--disable-background-networking")
        options.set_argument("--disable-features=Translate,OptimizationHints,MediaRouter")
        options.set_argument("--disable-sync")
        options.set_argument("--mute-audio")
        options.set_argument("--disable-web-security")
        options.set_argument("--disable-site-isolation-trials")
        self.page = ChromiumPage(options)
        self.log("Browser initialized successfully.")
        return self.page

    def clear_cache(self) -> None:
        if self.page:
            try:
                self.log("Clearing cache...")
                self.page.clear_cache(cookies=False)
            except Exception:
                pass

    def load_cookies(self) -> bool:
        if os.path.exists(COOKIE_FILE) and self.page:
            try:
                self.log("Loading saved cookies from file...")
                with open(COOKIE_FILE, "rb") as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    self.page.set.cookies(cookie)
                return True
            except Exception:
                self.log("Failed to load cookies. Removing invalid file.")
                os.remove(COOKIE_FILE)
        return False

    def quit(self) -> None:
        if self.page is not None:
            self.log("Closing browser...")
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None

    def _get_all_frames(self) -> List[Any]:
        frames = [self.page]
        visited_ids = {id(self.page)}
        
        queue = [self.page]
        while queue:
            curr = queue.pop(0)
            try:
                iframes = curr.eles('tag:iframe', timeout=0)
                for ele in iframes:
                    try:
                        f = None
                        if hasattr(curr, 'get_frame'):
                            f = curr.get_frame(ele)
                        elif hasattr(self.page, 'get_frame'):
                            f = self.page.get_frame(ele)
                            
                        if f and id(f) not in visited_ids:
                            visited_ids.add(id(f))
                            frames.append(f)
                            queue.append(f)
                    except Exception:
                        pass
            except Exception:
                pass
        return frames

    def _type_in_element_js(self, frame: Any, selectors: List[str], text: str) -> Optional[str]:
        js = """
        try {
            let sels = __SELS__;
            let text = __TEXT__;
            function isVis(el) {
                if (!el || el.disabled) return false;
                if (el.offsetWidth > 0 && el.offsetHeight > 0) return true;
                let rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }
            for (let sel of sels) {
                let els = null;
                try { els = document.querySelectorAll(sel); } catch(e) { continue; }
                if (!els) continue;
                for (let el of els) {
                    if (isVis(el)) {
                        el.focus();
                        let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
                        if (!nativeSetter || el.tagName === 'INPUT') {
                            nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value");
                        }
                        if (nativeSetter && nativeSetter.set) {
                            nativeSetter.set.call(el, text);
                        } else {
                            el.value = text;
                        }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }));
                        return sel;
                    }
                }
            }
            return null;
        } catch(e) { return null; }
        """.replace('__SELS__', json.dumps(selectors)).replace('__TEXT__', json.dumps(text))
        try:
            return frame.run_js(js)
        except Exception:
            return None

    def _click_button_js(self, frame: Any, selectors: List[str]) -> Optional[str]:
        js = """
        try {
            let sels = __SELS__;
            function isVis(el) {
                if (!el || el.disabled) return false;
                if (el.offsetWidth > 0 && el.offsetHeight > 0) return true;
                let rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }
            function trigger(el) {
                el.focus();
                el.click();
                ['mousedown', 'mouseup', 'click'].forEach(evt => {
                    el.dispatchEvent(new MouseEvent(evt, {bubbles: true, cancelable: true, view: window}));
                });
            }
            for (let sel of sels) {
                if (sel.startsWith("text=")) {
                    let btnText = sel.replace("text=", "").toLowerCase();
                    let btns = document.querySelectorAll("button, .button, .generate-btn,[role='button']");
                    for (let b of btns) {
                        let t = (b.innerText || b.value || '').toLowerCase();
                        if (t.includes(btnText) && isVis(b)) {
                            trigger(b); return sel;
                        }
                    }
                } else {
                    let els = null;
                    try { els = document.querySelectorAll(sel); } catch(e) { continue; }
                    if (els) {
                        for(let el of els) {
                            if (isVis(el)) {
                                trigger(el); return sel;
                            }
                        }
                    }
                }
            }
            let fallbacks = document.querySelectorAll("button, .generate-btn");
            for (let b of fallbacks) {
                let t = (b.innerText || b.value || '').toLowerCase();
                if ((t.includes("generate") || t.includes("send")) && isVis(b)) { 
                    trigger(b); return "fallback_button"; 
                }
            }
            return null;
        } catch(e) { return null; }
        """.replace('__SELS__', json.dumps(selectors))
        try:
            return frame.run_js(js)
        except Exception:
            return None

    def _get_last_visible_text_js(self, frame: Any, selectors: List[str]) -> str:
        js = """
        try {
            let sels = __SELS__;
            for (let sel of sels) {
                let els = null;
                try { els = document.querySelectorAll(sel); } catch(e) { continue; }
                if (els && els.length > 0) {
                    for (let i = els.length - 1; i >= 0; i--) {
                        let text = els[i].innerText || els[i].value;
                        if (text && text.trim().length > 0) return text.trim();
                    }
                }
            }
            return "";
        } catch(e) { return ""; }
        """.replace('__SELS__', json.dumps(selectors))
        try:
            return frame.run_js(js) or ""
        except Exception:
            return ""

    def _clean_output_text(self, text: str) -> str:
        ui_words = ["copy", "continue", "retry", "stop", "generate", "delete", "output", "regenerate"]
        emojis = ["📋", "▶️", "🔁", "🛑", "✨", "🗑️", "—"]
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.lower() in ui_words: continue
            if stripped.startswith("AI:"): stripped = stripped[3:].strip()
            for emoji in emojis: stripped = stripped.replace(emoji, "")
            if stripped: cleaned_lines.append(stripped)
        return "\n".join(cleaned_lines).strip()

    def _scan_and_extract_images(self, frame: Any, disable_safety: bool = False) -> Tuple[List[str], bool]:
        ds_str = 'true' if disable_safety else 'false'
        js = f"""
        try {{
            let disableSafety = {ds_str};
            let results = {{ srcs: [], blocked: false }};
            
            function processWindow(win) {{
                try {{
                    let guard = win.document.getElementById('contentGuardEl');
                    if (!guard) {{
                        let guards = win.document.querySelectorAll('[id*="contentGuard"],[class*="contentGuard"], .nsfw-warning');
                        if (guards.length > 0) guard = guards[0];
                    }}
                    
                    if (guard && (guard.offsetWidth > 0 || guard.getBoundingClientRect().width > 0)) {{
                        if (disableSafety) {{
                            guard.remove();
                        }} else {{
                            results.blocked = true;
                            return;
                        }}
                    }}
                    
                    if (!results.blocked && !disableSafety && win.document.body) {{
                        let text = win.document.body.innerText.toLowerCase();
                        if (text.includes("safety settings have blocked") || text.includes("unsafe content") || text.includes("inappropriate content")) {{
                            results.blocked = true;
                            return;
                        }}
                    }}
                    
                    let imgs = win.document.querySelectorAll('img');
                    for (let img of imgs) {{
                        let src = img.src || '';
                        let w = img.naturalWidth || img.offsetWidth || 0;
                        let h = img.naturalHeight || img.offsetHeight || 0;
                        
                        if (src.startsWith('data:image/') && src.length > 30000) {{
                            results.srcs.push(src);
                        }} else if (src.startsWith('blob:')) {{
                            results.srcs.push(src);
                        }} else if (src.startsWith('http')) {{
                            if (w > 100 && h > 100) {{
                                results.srcs.push(src);
                            }}
                        }}
                    }}
                }} catch(e) {{}}
                
                try {{
                    for (let i = 0; i < win.frames.length; i++) {{
                        processWindow(win.frames[i]);
                    }}
                }} catch(e) {{}}
            }}
            
            processWindow(window);
            results.srcs = [...new Set(results.srcs)];
            return JSON.stringify(results);
            
        }} catch(e) {{ return JSON.stringify({{srcs:[], blocked:false}}); }}
        """
        try:
            res = frame.run_js(js)
            if res:
                data = json.loads(res)
                return data.get('srcs', []), data.get('blocked', False)
        except Exception:
            pass
        return [], False

    def execute(self, model: str, prompt: str, is_image: bool = False, num_images: int = 1, stream: bool = False, extra_params: Optional[Dict[str, Any]] = None, param_mappings: Optional[Dict[str, Union[str, List[str]]]] = None, input_selectors: Optional[List[str]] = None, button_selectors: Optional[List[str]] = None, output_selectors: Optional[List[str]] = None, disable_safety_settings: bool = False) -> Any:
        self.init_driver()
        self.clear_cache()
        self.log(f"Navigating to generator model: https://perchance.org/{model}")
        self.page.get(f"https://perchance.org/{model}")
        
        if not self.cookies_loaded_this_session:
            if self.load_cookies():
                self.log("Cookies applied, refreshing page...")
                time.sleep(0.5)
                self.page.refresh()
            self.cookies_loaded_this_session = True
            
        in_sels = input_selectors if input_selectors else DEFAULT_INPUT_SELECTORS
        btn_sels = button_selectors if button_selectors else DEFAULT_BUTTON_SELECTORS
        out_sels = output_selectors if output_selectors else DEFAULT_OUTPUT_SELECTORS
        
        active_mappings = DEFAULT_PARAM_MAPPINGS.copy()
        if param_mappings:
            for k, v in param_mappings.items():
                if isinstance(v, str):
                    active_mappings[k] = [v]
                elif isinstance(v, list):
                    active_mappings[k] = v
                    
        try:
            self.log("Searching for the generator iframe...")
            generator_frame = None
            
            for _ in range(60):
                for f in self._get_all_frames():
                    js_check = """
                    try {
                        let in_sels = __INSELS__;
                        let btn_sels = __BTNSELS__;
                        function isVis(el) {
                            if (!el) return false;
                            if (el.offsetWidth > 0 && el.offsetHeight > 0) return true;
                            let rect = el.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                        }
                        
                        let hasIn = false;
                        for(let sel of in_sels) { 
                            try { 
                                let els = document.querySelectorAll(sel);
                                for(let e of els) { if(isVis(e)) { hasIn = true; break; } }
                            } catch(e){} 
                            if(hasIn) break;
                        }
                        
                        let hasBtn = false;
                        for(let sel of btn_sels) { 
                            if(sel.startsWith('text=')) continue; 
                            try { 
                                let els = document.querySelectorAll(sel);
                                for(let e of els) { if(isVis(e)) { hasBtn = true; break; } }
                            } catch(e){} 
                            if(hasBtn) break;
                        }
                        if(!hasBtn) {
                            let btns = document.querySelectorAll('button, .button, .generate-btn, [role="button"]');
                            for(let b of btns) { 
                                let t = (b.innerText || b.value || '').toLowerCase();
                                if((t.includes('generate') || t.includes('send')) && isVis(b)) { hasBtn = true; break; } 
                            }
                        }
                        return hasIn && hasBtn;
                    } catch(e) { return false; }
                    """.replace('__INSELS__', json.dumps(in_sels)).replace('__BTNSELS__', json.dumps(btn_sels))
                    
                    try:
                        if f.run_js(js_check):
                            generator_frame = f
                            break
                    except Exception:
                        pass
                if generator_frame:
                    break
                time.sleep(0.25)
                
            if not generator_frame:
                self.log("Error: Generator iframe not found.")
                return "Execution Error: Could not find the generator iframe."
                
            self.log("Generator iframe successfully identified.")
            initial_text = ""
            old_srcs = set()
            
            if is_image:
                self.log("Capturing baseline image state before generation...")
                for f in self._get_all_frames():
                    srcs, _ = self._scan_and_extract_images(f, disable_safety=disable_safety_settings)
                    old_srcs.update(srcs)
                
            if extra_params:
                self.log(f"Applying {len(extra_params)} extra parameters...")
                for param_key, param_value in extra_params.items():
                    try:
                        selectors = active_mappings.get(param_key, [param_key])
                        if isinstance(selectors, str): selectors = [selectors]
                        js_script = """
                        try {
                            let sels = __SELS__;
                            let val = __VAL__;
                            for (let sel of sels) {
                                let el = null;
                                try { el = document.querySelector(sel); } catch(e) { continue; }
                                if (!el) {
                                    let byName = document.getElementsByName(sel);
                                    if (byName.length > 0) el = byName[0];
                                }
                                if(el) { 
                                    el.focus();
                                    let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value");
                                    if(!nativeSetter || el.tagName==='INPUT' || el.tagName==='TEXTAREA'){
                                        nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value") || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
                                    }
                                    if (nativeSetter && nativeSetter.set) {
                                        nativeSetter.set.call(el, val);
                                    } else {
                                        el.value = val;
                                    }
                                    el.dispatchEvent(new Event('input', { bubbles: true })); 
                                    el.dispatchEvent(new Event('change', { bubbles: true })); 
                                    return sel; 
                                }
                            }
                            return null;
                        } catch(e) { return null; }
                        """.replace('__SELS__', json.dumps(selectors)).replace('__VAL__', json.dumps(param_value))
                        generator_frame.run_js(js_script)
                    except Exception:
                        pass
                        
            target_num_images = 1
            if is_image:
                try:
                    js_num = """
                    try {
                        let targetNum = __TNUM__;
                        let sels = document.querySelectorAll('select[data-name="numImages"], select[name="numImages"], select[id*="numImages" i], [data-name="numImages"]');
                        if (sels.length > 0) {
                            let sel = sels[0];
                            if (sel.tagName !== 'SELECT') {
                                let innerSel = sel.querySelector('select');
                                if (innerSel) sel = innerSel;
                            }
                            if(sel.tagName !== 'SELECT') return targetNum;
                            
                            let maxVal = 1;
                            for (let i = 0; i < sel.options.length; i++) {
                                let val = parseInt(sel.options[i].value);
                                if (!isNaN(val) && val > maxVal) maxVal = val;
                            }
                            let finalNum = Math.min(targetNum, maxVal);
                            
                            let exists = Array.from(sel.options).some(opt => parseInt(opt.value) === finalNum);
                            if (!exists) {
                                let newOpt = document.createElement('option');
                                newOpt.value = finalNum.toString();
                                newOpt.innerText = 'Custom (' + finalNum + ')';
                                sel.appendChild(newOpt);
                            }
                            sel.value = finalNum.toString();
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            sel.dispatchEvent(new Event('input', { bubbles: true }));
                            return finalNum;
                        }
                        return 1;
                    } catch(e) { return 1; }
                    """.replace('__TNUM__', str(num_images))
                    
                    res_num = generator_frame.run_js(js_num)
                    if res_num is not None:
                        target_num_images = int(res_num)
                        self.log(f"Requested {num_images} images. Target successfully set to {target_num_images}.")
                    else:
                        target_num_images = 1
                except Exception:
                    target_num_images = 1
                    
            if not is_image:
                initial_text = self._get_last_visible_text_js(generator_frame, out_sels)
                
            self.log(f"Typing prompt into input field...")
            typed_selector = self._type_in_element_js(generator_frame, in_sels, prompt)
            if not typed_selector:
                self.log("Error: Input field not found or not interactable.")
                return "Execution Error: Input field not found or not interactable."
                
            time.sleep(0.5)
            
            self.log("Clicking the generate button...")
            clicked_selector = self._click_button_js(generator_frame, btn_sels)
            if not clicked_selector:
                self.log("Error: Generate button not found.")
                return "Execution Error: Generate button not found."
                
            if is_image:
                timeout_seconds = 90 * target_num_images
                max_iterations = int(timeout_seconds / 0.25)
                self.log(f"Waiting for {target_num_images} new images to render...")
                new_generated = []
                
                for i in range(max_iterations):
                    current_srcs = set()
                    is_blocked = False
                    
                    for f in self._get_all_frames():
                        srcs, blocked = self._scan_and_extract_images(f, disable_safety=disable_safety_settings)
                        current_srcs.update(srcs)
                        if blocked: is_blocked = True
                        
                    if is_blocked and not disable_safety_settings:
                        self.log("Safety filter triggered on screen.")
                        return "Execution Error: Safety filter triggered. (Pass disable_safety_settings=True to Client to ignore)"
                        
                    new_srcs = list(current_srcs - old_srcs)
                    
                    if len(new_srcs) >= target_num_images:
                        self.log(f"Successfully extracted {target_num_images} images.")
                        new_generated = new_srcs[:target_num_images]
                        break
                                
                    time.sleep(0.25)
                    if i > 0 and i % 4 == 0:
                        self.log(f"Still waiting... ({len(new_srcs)}/{target_num_images})")
                        
                if not new_generated:
                    self.log("Image generation failed or timed out.")
                    return "Image generation failed or timed out."

                final_b64_list = []
                for src in new_generated:
                    if src.startswith("data:image/"):
                        final_b64_list.append(src.split(",", 1)[1])
                    elif src.startswith("http"):
                        try:
                            self.log(f"Downloading external image URL: {src[:50]}...")
                            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=15) as response:
                                b64 = base64.b64encode(response.read()).decode('utf-8')
                                final_b64_list.append(b64)
                        except Exception as e:
                            self.log(f"Warning: URL download failed ({e}). Returning fallback transparent pixel.")
                            fallback_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                            final_b64_list.append(fallback_b64)
                    else:
                        final_b64_list.append(src)
                        
                return final_b64_list
                
            else:
                if stream:
                    def stream_generator() -> Generator[str, None, None]:
                        last_text = ""
                        last_yielded_len = 0
                        stable_checks = 0
                        for _ in range(300):
                            time.sleep(0.2)
                            current_text = self._get_last_visible_text_js(generator_frame, out_sels)
                            text_no_loading = current_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                            initial_no_loading = initial_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                            if text_no_loading != initial_no_loading and len(text_no_loading) > 0:
                                break
                        for _ in range(1200):
                            time.sleep(0.2)
                            current_text = self._get_last_visible_text_js(generator_frame, out_sels)
                            if "generating" in current_text.lower() or "loading" in current_text.lower():
                                stable_checks = 0
                                last_text = current_text
                                continue
                            cleaned_current = self._clean_output_text(current_text)
                            if len(cleaned_current) > last_yielded_len:
                                chunk = cleaned_current[last_yielded_len:]
                                yield chunk
                                last_yielded_len = len(cleaned_current)
                            if current_text and current_text == last_text:
                                stable_checks += 1
                                if stable_checks >= 25:
                                    self.log("Text generation stabilized (stream ended).")
                                    break
                            else:
                                stable_checks = 0
                                last_text = current_text
                    return stream_generator()
                else:
                    self.log("Waiting for text generation to start...")
                    started = False
                    for _ in range(300):
                        time.sleep(0.2)
                        current_text = self._get_last_visible_text_js(generator_frame, out_sels)
                        text_no_loading = current_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                        initial_no_loading = initial_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                        if text_no_loading != initial_no_loading and len(text_no_loading) > 0:
                            started = True
                            self.log("Text generation started. Waiting for output to stabilize...")
                            break
                    if not started:
                        self.log("Error: Generation did not start within timeout.")
                        return "Execution Error: Generation did not start within 60 seconds."
                    last_text = ""
                    stable_checks = 0
                    for _ in range(1200):
                        time.sleep(0.2)
                        current_text = self._get_last_visible_text_js(generator_frame, out_sels)
                        if "generating" in current_text.lower() or "loading" in current_text.lower():
                            stable_checks = 0
                            last_text = current_text
                            continue
                        if current_text and current_text == last_text:
                            stable_checks += 1
                            if stable_checks >= 25:
                                self.log("Text generation stabilized. Finishing.")
                                return self._clean_output_text(current_text)
                        else:
                            stable_checks = 0
                            last_text = current_text
                    self.log("Text generation finished (reached max timeout).")
                    return self._clean_output_text(last_text) if last_text else "Execution Error: Output timeout."
                    
        except Exception as e:
            error_name = e.__class__.__name__
            self.log(f"Exception encountered: {error_name} - {str(e)}")
            try:
                if self.page and hasattr(self.page, 'url') and self.page.url and "login" in str(self.page.url).lower():
                    if os.path.exists(COOKIE_FILE): 
                        os.remove(COOKIE_FILE)
            except Exception:
                pass
            return f"Execution Error ({error_name}). Failed to load page or element."