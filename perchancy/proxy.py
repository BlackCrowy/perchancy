import os
import subprocess
import json
import platform
import zipfile
import urllib.parse
import time
from typing import Optional
from .download import download_with_prompt

XRAY_DIR = os.path.join(os.path.expanduser("~"), ".perchancy_xray")

def get_xray_executable() -> str:
    ext = ".exe" if platform.system() == "Windows" else ""
    return os.path.join(XRAY_DIR, f"xray{ext}")

def download_xray_if_needed() -> bool:
    xray_path = get_xray_executable()
    if os.path.exists(xray_path):
        return True
        
    os.makedirs(XRAY_DIR, exist_ok=True)
    sys_os = platform.system().lower()
    machine = platform.machine().lower()
    
    if "windows" in sys_os:
        url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-windows-64.zip"
    elif "linux" in sys_os:
        if "aarch64" in machine or "arm64" in machine:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-arm64-v8a.zip"
        else:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
    elif "darwin" in sys_os:
        if "arm64" in machine:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-macos-arm64-v8a.zip"
        else:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-macos-64.zip"
    else:
        print("Unsupported OS for automatic Xray download.")
        return False
        
    zip_path = os.path.join(XRAY_DIR, "xray.zip")
    success = download_with_prompt(
        url=url,
        dest_path=zip_path,
        what="Xray-core",
        why="routing web connections through VLESS/VMESS proxy protocols."
    )
    
    if not success:
        return False
        
    print("Extracting Xray-core files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(XRAY_DIR)
        
    os.remove(zip_path)
    
    if sys_os != "windows":
        os.chmod(xray_path, 0o755)
        
    return True

def parse_vless(link: str, local_port: int) -> dict:
    link = link.replace("vless://", "")
    user_info, rest = link.split("@", 1)
    server_info, params_str = rest.split("?", 1)
    
    if ":" in server_info:
        address, port = server_info.split(":", 1)
    else:
        address = server_info
        port = "443"
        
    params = {}
    if "#" in params_str:
        params_str, _ = params_str.split("#", 1)
    for pair in params_str.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
            
    config = {
        "inbounds":[{
            "port": local_port,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds":[{
            "protocol": "vless",
            "settings": {
                "vnext":[{
                    "address": address,
                    "port": int(port),
                    "users":[{"id": user_info, "encryption": "none", "flow": params.get("flow", "")}]
                }]
            },
            "streamSettings": {
                "network": params.get("type", "tcp"),
                "security": params.get("security", "none")
            }
        }]
    }
    
    if params.get("security") == "reality":
        config["outbounds"][0]["streamSettings"]["realitySettings"] = {
            "serverName": params.get("sni", ""),
            "publicKey": params.get("pbk", ""),
            "fingerprint": params.get("fp", "chrome"),
            "shortId": params.get("sid", ""),
            "spiderX": params.get("spx", "")
        }
    elif params.get("security") == "tls":
        config["outbounds"][0]["streamSettings"]["tlsSettings"] = {
            "serverName": params.get("sni", ""),
            "fingerprint": params.get("fp", "chrome")
        }
        
    if params.get("type") == "ws":
        config["outbounds"][0]["streamSettings"]["wsSettings"] = {
            "path": urllib.parse.unquote(params.get("path", "/")),
            "headers": {"Host": params.get("host", params.get("sni", ""))}
        }
        
    return config

class VPNManager:
    def __init__(self):
        self.process = None
        self.local_port = 10808
        
    def start_proxy(self, config_str: str) -> str:
        self.stop_proxy()
        
        if not config_str.startswith("vless://"):
            return config_str
            
        if not download_xray_if_needed():
            print("Notice: Failed or declined to setup Xray-core. Proceeding without VPN.")
            return ""
            
        config_json = parse_vless(config_str, self.local_port)
        config_path = os.path.join(XRAY_DIR, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_json, f, indent=2)
            
        xray_exec = get_xray_executable()
        self.process = subprocess.Popen(
            [xray_exec, "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)
        
        return f"socks5://127.0.0.1:{self.local_port}"
        
    def stop_proxy(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None