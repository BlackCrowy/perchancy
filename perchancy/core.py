import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
import urllib.error
import subprocess
import json
import zipfile
import platform
import stat
import pickle
import shutil
import os
import time
import re
import ssl

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

if hasattr(uc.Chrome, "__del__"):
    original_del = uc.Chrome.__del__
    def patched_del(self):
        try:
            original_del(self)
        except Exception:
            pass
    uc.Chrome.__del__ = patched_del

COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".perchancy_cookies.pkl")

DEFAULT_INPUT_SELECTORS = [
    "[data-name='description']", "textarea[data-name='description']", 
    ".paragraph-input", "#instructionEl", "#instruction", "#prompt", 
    "#textInput", "#userInput", "#chatInput", "textarea[id*='input' i]", 
    "textarea", "input[type='text']"
]
DEFAULT_BUTTON_SELECTORS = [
    "[data-name='generateButton']", "#generateBtn", "#generateButton", 
    "#generateButtonEl", "#sendButton", "#submitButton", "text=✨ generate", 
    "text=generate", ".generate-btn", "button[onclick*='generate' i]", 
    "#resultImgEl", "#resultEl", "button[id*='generate' i]", "button[id*='send' i]", "button"
]
DEFAULT_OUTPUT_SELECTORS = [
    "[data-name='output']", "#output", "#responseEl", "#response", ".message", 
    ".chatMessage", "#chat div", ".output-box", "div[id*='chat'] div"
]

DEFAULT_PARAM_MAPPINGS = {
    "style": ["[data-name='artStyle']"],
    "shape": ["data-name='shape'"],
    "seed": ['data-name="seed"'],
}

def get_chrome_main_version(executable_path):
    if not executable_path or not os.path.exists(executable_path):
        return None
    try:
        if platform.system() == "Windows":
            cmd = f'wmic datafile where name="{executable_path.replace("\\", "\\\\")}" get Version /value'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode(errors='ignore')
            match = re.search(r'Version=(\d+)', output)
            if match: return int(match.group(1))
        else:
            output = subprocess.check_output([executable_path, "--version"], stderr=subprocess.DEVNULL).decode(errors='ignore')
            match = re.search(r'(?:Google Chrome|Chromium)(?: for Testing)?\s+(\d+)', output)
            if match: return int(match.group(1))
    except:
        pass
    return None

def get_chrome_path(debug=False):
    base_dir = os.path.join(os.path.expanduser("~"), ".perchancy", "chrome")
    os.makedirs(base_dir, exist_ok=True)
    
    sys_plat = platform.system().lower()
    machine = platform.machine().lower()
    
    if "win" in sys_plat:
        os_name = "win64"
        exe_name = "chrome.exe"
    elif "linux" in sys_plat:
        os_name = "linux64"
        exe_name = "chrome"
    elif "darwin" in sys_plat:
        os_name = "mac-arm64" if "arm" in machine else "mac-x64"
        exe_name = "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    else:
        raise Exception("Unsupported OS for auto-install")

    version_file = os.path.join(base_dir, "version.txt")
    exe_path = os.path.join(base_dir, f"chrome-{os_name}", exe_name)

    url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    data = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
            break
        except Exception:
            time.sleep(1)

    if not data:
        if os.path.exists(exe_path): return exe_path
        return uc.find_chrome_executable()

    stable_version = data["channels"]["Stable"]["version"]
    downloads = data["channels"]["Stable"]["downloads"]["chrome"]
    download_url = next((d["url"] for d in downloads if d["platform"] == os_name), None)

    if os.path.exists(exe_path) and os.path.exists(version_file):
        with open(version_file, "r") as f:
            local_version = f.read().strip()
        if local_version == stable_version:
            return exe_path 

    if not download_url:
        return uc.find_chrome_executable()

    extract_dir = os.path.join(base_dir, f"chrome-{os_name}")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir, ignore_errors=True)

    zip_path = os.path.join(base_dir, "chrome.zip")
    
    for attempt in range(5):
        try:
            urllib.request.urlretrieve(download_url, zip_path)
            break
        except Exception as e:
            time.sleep(3)
            if attempt == 4: raise e
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(base_dir)
        
    os.remove(zip_path)
    
    if "linux" in sys_plat or "darwin" in sys_plat:
        os.chmod(exe_path, os.stat(exe_path).st_mode | stat.S_IEXEC)

    with open(version_file, "w") as f:
        f.write(stable_version)
        
    return exe_path

class BrowserCore:
    def __init__(self, headless: bool = True, debug: bool = False, disable_safety_settings: bool = False):
        self.headless = headless
        self.debug = debug
        self.disable_safety_settings = disable_safety_settings
        self.driver = None
        self.cookies_loaded_this_session = False

    def log(self, msg: str):
        if self.debug:
            print(f"[DEBUG] {msg}")

    def _get_optimized_options(self):
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        
        options.page_load_strategy = 'eager'
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-features=Translate,OptimizationHints,MediaRouter")
        options.add_argument("--disable-sync")
        options.add_argument("--disk-cache-size=1")
        options.add_argument("--media-cache-size=1")
        prefs = {
            "profile.managed_default_content_settings.stylesheet": 2, 
            "profile.managed_default_content_settings.fonts": 2       
        }
        options.add_experimental_option("prefs", prefs)
        return options

    def init_driver(self):
        if self.driver is not None:
            return self.driver

        self.log("Initializing Chrome driver...")
        browser_path = get_chrome_path(self.debug)
        v_main = get_chrome_main_version(browser_path) 
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver = uc.Chrome(
                    options=self._get_optimized_options(), 
                    headless=self.headless, 
                    browser_executable_path=browser_path,
                    version_main=v_main 
                )
                self.log("Chrome driver initialized successfully.")
                return self.driver
            except Exception as e:
                self.log(f"Driver init error: {e}")
                try:
                    if platform.system() == "Windows":
                        os.system("taskkill /f /im chrome.exe >nul 2>&1")
                        os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
                except: pass
                time.sleep(2)
                if attempt == max_retries - 1:
                    raise e
        return self.driver

    def clear_cache(self):
        if self.driver:
            try:
                self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            except Exception:
                pass

    def load_cookies(self):
        if os.path.exists(COOKIE_FILE) and self.driver:
            try:
                self.log("Loading authorization cookies...")
                cookies = pickle.load(open(COOKIE_FILE, "rb"))
                added = False
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                    added = True
                return added
            except Exception:
                self.log("Failed to load cookies. File might be corrupted.")
                os.remove(COOKIE_FILE)
        return False

    def quit(self):
        if self.driver is not None:
            self.log("Closing browser...")
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _type_in_element_js(self, selectors, text) -> str:
        js = """
        let sels = arguments[0];
        let text = arguments[1];
        for (let sel of sels) {
            let els = document.querySelectorAll(sel);
            for (let el of els) {
                if (el) {
                    let temp = el;
                    while(temp && temp.tagName !== 'BODY' && temp.tagName !== 'HTML') {
                        temp.style.display = 'block';
                        temp.style.visibility = 'visible';
                        temp = temp.parentElement;
                    }
                    el.value = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return sel;
                }
            }
        }
        return null;
        """
        try:
            return self.driver.execute_script(js, selectors, text)
        except:
            return None

    def _click_button_js(self, selectors) -> str:
        js = """
        let sels = arguments[0];
        for (let sel of sels) {
            if (sel.startsWith("text=")) {
                let btnText = sel.replace("text=", "").toLowerCase();
                let btns = document.querySelectorAll("button, .button, .generate-btn");
                for (let b of btns) {
                    if (b.innerText.toLowerCase().includes(btnText)) {
                        b.click(); return sel;
                    }
                }
            } else {
                let els = document.querySelectorAll(sel);
                if (els.length > 0) { els[0].click(); return sel; }
            }
        }
        
        let fallbacks = document.querySelectorAll("button");
        for (let b of fallbacks) {
            let t = b.innerText.toLowerCase();
            if (t.includes("generate") || t.includes("send")) { b.click(); return "fallback_button"; }
        }
        return null;
        """
        try:
            return self.driver.execute_script(js, selectors)
        except:
            return None

    def _get_last_visible_text_js(self, selectors) -> str:
        js = """
        let sels = arguments[0];
        for (let sel of sels) {
            let els = document.querySelectorAll(sel);
            if (els.length > 0) {
                for (let i = els.length - 1; i >= 0; i--) {
                    let text = els[i].innerText || els[i].value;
                    if (text && text.trim().length > 0) return text.trim();
                }
            }
        }
        return "";
        """
        try:
            return self.driver.execute_script(js, selectors) or ""
        except:
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

    def _scan_images_fast(self, frame_path=None, disable_safety=False):
        if frame_path is None:
            frame_path = []
            
        found_pids = []
        is_blocked = False
            
        try:
            self.driver.switch_to.default_content()
        except:
            return found_pids, is_blocked

        for idx in frame_path:
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(frames[idx])
            except:
                return found_pids, is_blocked

        js = """
        let disableSafety = arguments[0];
        let result = { pids: [], blocked: false };

        let guardNodes = document.querySelectorAll('[id*="contentGuard"], [class*="contentGuard"], [id*="safetyBlock"], .nsfw-warning');
        for (let guardNode of guardNodes) {
            let style = window.getComputedStyle(guardNode);
            if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                if (disableSafety) {
                    guardNode.remove();
                } else {
                    result.blocked = true;
                }
            }
        }
        
        if (!result.blocked && !disableSafety) {
            let blockedTexts = ["safety settings have blocked", "safety filter", "inappropriate content", "unsafe content"];
            let bodyText = document.body.innerText.toLowerCase();
            for (let bt of blockedTexts) {
                if (bodyText.includes(bt)) {
                    result.blocked = true;
                    break;
                }
            }
        }

        if (result.blocked && !disableSafety) {
            return JSON.stringify(result);
        }

        let imgs = document.querySelectorAll('img');
        for (let i = 0; i < imgs.length; i++) {
            let img = imgs[i];
            if (disableSafety) img.style.filter = 'none';
            
            if (img.naturalWidth < 150 || img.naturalHeight < 150) continue;
            if (img.src.includes('chrome-error') || img.src.includes('data:image/svg')) continue;
            
            let cls = (img.className || '').toLowerCase();
            if (cls.includes('icon') || cls.includes('avatar') || cls.includes('logo') || cls.includes('btn')) continue;
            
            if (!img.dataset.pid) {
                img.dataset.pid = Math.random().toString(36).substring(2, 15);
            }
            result.pids.push(img.dataset.pid);
        }
        
        return JSON.stringify(result);
        """
        try:
            raw_res = self.driver.execute_script(js, disable_safety)
            if raw_res:
                data = json.loads(raw_res)
                if data.get("blocked"):
                    is_blocked = True
                if data.get("pids"):
                    found_pids.extend(data["pids"])
        except:
            pass

        try:
            frames_count = len(self.driver.find_elements(By.TAG_NAME, "iframe"))
        except:
            return list(set(found_pids)), is_blocked

        for i in range(frames_count):
            sub_pids, sub_blocked = self._scan_images_fast(frame_path + [i], disable_safety)
            found_pids.extend(sub_pids)
            if sub_blocked:
                is_blocked = True

        return list(set(found_pids)), is_blocked

    def _extract_base64_for_pids(self, target_pids, frame_path=None):
        if frame_path is None:
            frame_path = []
            
        results = {}
            
        try:
            self.driver.switch_to.default_content()
        except:
            return results

        for idx in frame_path:
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(frames[idx])
            except:
                return results

        js = """
        let tPids = arguments[0];
        let res = {};
        let imgs = document.querySelectorAll('img');
        for (let i = 0; i < imgs.length; i++) {
            let img = imgs[i];
            if (tPids.includes(img.dataset.pid)) {
                if (img.src.includes('base64,')) {
                    res[img.dataset.pid] = img.src;
                } else {
                    try {
                        let canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        let ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        let b64 = canvas.toDataURL('image/jpeg', 0.95);
                        if (b64.length > 15000) {
                            res[img.dataset.pid] = b64;
                        }
                    } catch(e) { }
                }
            }
        }
        return JSON.stringify(res);
        """
        try:
            raw = self.driver.execute_script(js, target_pids)
            if raw:
                data = json.loads(raw)
                results.update(data)
        except:
            pass

        try:
            frames_count = len(self.driver.find_elements(By.TAG_NAME, "iframe"))
        except:
            return results

        for i in range(frames_count):
            sub_res = self._extract_base64_for_pids(target_pids, frame_path + [i])
            results.update(sub_res)

        return results

    def execute(self, model: str, prompt: str, is_image: bool = False, num_images: int = 1, stream: bool = False, extra_params: dict = None, param_mappings: dict = None, input_selectors: list = None, button_selectors: list = None, output_selectors: list = None):
        self.init_driver()
        self.clear_cache()
        
        self.log(f"Navigating to generator model: https://perchance.org/{model}")
        self.driver.get(f"https://perchance.org/{model}")
        
        if not self.cookies_loaded_this_session:
            if self.load_cookies():
                self.log("Cookies applied, refreshing page to log in...")
                time.sleep(1.0)
                self.driver.refresh()
            self.cookies_loaded_this_session = True
            
        wait = WebDriverWait(self.driver, 30)

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
            self.log("Waiting for main iframe to load...")
            self.driver.switch_to.default_content()
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            except:
                self.log("Initial wait for iframe failed. Refreshing and retrying...")
                self.driver.refresh()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                
            time.sleep(2.0)
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            generator_iframe = None
            
            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    js_check = """
                    let in_sels = arguments[0];
                    let btn_sels = arguments[1];
                    for(let sel of in_sels) { if(document.querySelector(sel)) return true; }
                    for(let sel of btn_sels) { 
                        if(sel.startsWith('text=')) continue; 
                        if(document.querySelector(sel)) return true; 
                    }
                    let btns = document.querySelectorAll('button');
                    for(let b of btns) { if(b.innerText.toLowerCase().includes('generate')) return true; }
                    return false;
                    """
                    if self.driver.execute_script(js_check, in_sels, btn_sels):
                        generator_iframe = iframe
                        self.log("Generator iframe successfully identified.")
                        break
                    self.driver.switch_to.default_content()
                except:
                    self.driver.switch_to.default_content()
            
            if not generator_iframe:
                self.log("ERROR: Could not find the generator iframe.")
                return "Execution Error: Could not find the generator iframe."

            initial_text = ""
            old_pids = set()

            if is_image:
                self.log("Capturing baseline image state before generation...")
                pids, _ = self._scan_images_fast(disable_safety=self.disable_safety_settings)
                old_pids = set(pids)
                
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(generator_iframe)

            if extra_params:
                self.log(f"Applying {len(extra_params)} extra parameters...")
                for param_key, param_value in extra_params.items():
                    try:
                        selectors = active_mappings.get(param_key, [param_key])
                        if isinstance(selectors, str): selectors = [selectors]
                        
                        js_script = """
                        let sels = arguments[0];
                        let val = arguments[1];
                        for (let sel of sels) {
                            let el = null;
                            try { el = document.querySelector(sel); } catch(e) {}
                            if (!el) el = document.getElementById(sel);
                            if (!el) {
                                let byName = document.getElementsByName(sel);
                                if (byName.length > 0) el = byName[0];
                            }
                            if(el) { 
                                el.value = val; 
                                el.dispatchEvent(new Event('input', { bubbles: true })); 
                                el.dispatchEvent(new Event('change', { bubbles: true })); 
                                return sel; 
                            }
                        }
                        return null;
                        """
                        self.driver.execute_script(js_script, selectors, param_value)
                    except Exception as e:
                        pass

            target_num_images = 1
            if is_image:
                try:
                    js_num = """
                    let targetNum = arguments[0];
                    let sels = document.querySelectorAll('select[data-name="numImages"], select[name="numImages"], select[id*="numImages" i], [data-name="numImages"]');
                    
                    if (sels.length > 0) {
                        let sel = sels[0];
                        if (sel.tagName !== 'SELECT') {
                            let innerSel = sel.querySelector('select');
                            if (innerSel) sel = innerSel;
                        }
                        
                        let p = sel;
                        while(p && p !== document.body && p !== document.documentElement) {
                            if (window.getComputedStyle(p).display === 'none') p.style.display = 'block';
                            if (window.getComputedStyle(p).visibility === 'hidden') p.style.visibility = 'visible';
                            p = p.parentElement;
                        }
                        
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
                    """
                    target_num_images = self.driver.execute_script(js_num, num_images)
                    self.log(f"Requested {num_images} images. Target successfully set to {target_num_images}.")
                except Exception as e:
                    self.log(f"WARNING: Could not set numImages. Error: {e} (Ignored)")
                    target_num_images = 1

            if not is_image:
                initial_text = self._get_last_visible_text_js(out_sels)

            self.log(f"Typing prompt: '{prompt[:30]}...'")
            typed_selector = self._type_in_element_js(in_sels, prompt)
            if not typed_selector:
                self.log("ERROR: Input field not found or not interactable.")
                return "Execution Error: Input field not found or not interactable."

            self.log("Waiting 0.3s for frontend state to sync...")
            time.sleep(0.3)

            self.log("Clicking generate button...")
            clicked_selector = self._click_button_js(btn_sels)
            if not clicked_selector:
                self.log("ERROR: Generate button not found.")
                return "Execution Error: Generate button not found."

            if is_image:
                timeout_seconds = 90 * target_num_images
                max_iterations = int(timeout_seconds / 0.15)
                
                self.log(f"Waiting for {target_num_images} new valid images to appear (up to {timeout_seconds} seconds)...")
                new_generated = []
                
                for i in range(max_iterations):
                    current_pids, is_blocked = self._scan_images_fast(disable_safety=self.disable_safety_settings)
                    
                    if is_blocked and not self.disable_safety_settings:
                        self.log("ERROR: Safety filter warning detected on screen!")
                        return "Execution Error: Safety filter triggered. (Pass disable_safety_settings=True to Client to ignore)"
                    
                    new_pids = [p for p in current_pids if p not in old_pids]
                    
                    if len(new_pids) >= target_num_images:
                        new_generated_pids = new_pids[:target_num_images]
                        extracted_b64 = self._extract_base64_for_pids(new_generated_pids)
                        
                        if len(extracted_b64) >= target_num_images:
                            self.log(f"Successfully generated and extracted {target_num_images} new image(s)!")
                            new_generated = [extracted_b64[pid] for pid in new_generated_pids]
                            break
                    
                    time.sleep(0.15)
                    if i > 0 and i % 30 == 0:
                        self.log(f"Still waiting for images... ({len(new_pids)}/{target_num_images} ready. {round(i*0.15, 1)}s elapsed)")

                if not new_generated:
                    self.log(f"ERROR: Image generation timed out after {timeout_seconds}s and no complete images found.")
                    return "Image generation failed or timed out."

                return [img.split("base64,")[1] if "base64," in img else img for img in new_generated]
            
            else:
                if stream:
                    def stream_generator():
                        try:
                            last_text = ""
                            last_yielded_len = 0
                            stable_checks = 0
                            
                            for _ in range(300):
                                time.sleep(0.2)
                                current_text = self._get_last_visible_text_js(out_sels)
                                text_no_loading = current_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                                initial_no_loading = initial_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                                if text_no_loading != initial_no_loading and len(text_no_loading) > 0:
                                    break
                                    
                            for _ in range(600):
                                time.sleep(0.2)
                                current_text = self._get_last_visible_text_js(out_sels)
                                
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
                                    if stable_checks >= 10:
                                        break
                                else:
                                    stable_checks = 0
                                    last_text = current_text
                        finally:
                            try:
                                self.driver.switch_to.default_content()
                            except:
                                pass
                                
                    return stream_generator()
                else:
                    self.log("Waiting up to 60s for the real text generation to start...")
                    started = False
                    
                    for _ in range(300):
                        time.sleep(0.2)
                        current_text = self._get_last_visible_text_js(out_sels)
                        
                        text_no_loading = current_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                        initial_no_loading = initial_text.lower().replace("generating...", "").replace("generating", "").replace("loading...", "").strip()
                        
                        if text_no_loading != initial_no_loading and len(text_no_loading) > 0:
                            started = True
                            break
                    
                    if not started:
                        return "Execution Error: Generation did not start within 60 seconds."

                    self.log("Text generation started. Waiting for output to stabilize...")
                    last_text = ""
                    stable_checks = 0
                    
                    for _ in range(600):
                        time.sleep(0.2)
                        current_text = self._get_last_visible_text_js(out_sels)
                        
                        if "generating" in current_text.lower() or "loading" in current_text.lower():
                            stable_checks = 0
                            last_text = current_text
                            continue

                        if current_text and current_text == last_text:
                            stable_checks += 1
                            if stable_checks >= 10:
                                return self._clean_output_text(current_text)
                        else:
                            stable_checks = 0
                            last_text = current_text
                    
                    return self._clean_output_text(last_text) if last_text else "Execution Error: Output timeout."

        except Exception as e:
            error_name = e.__class__.__name__
            self.log(f"EXCEPTION ENCOUNTERED: {error_name} - {str(e)}")
            if "login" in self.driver.current_url.lower():
                if os.path.exists(COOKIE_FILE): 
                    os.remove(COOKIE_FILE)
            return f"Execution Error ({error_name}). Failed to load page or element."
        
        finally:
            if not stream or is_image:
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass