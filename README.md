# Perchancy 🚀

[![PyPI version](https://img.shields.io/pypi/v/perchancy.svg)](https://pypi.org/project/perchancy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Perchancy** is a high-speed, thread-safe, OpenAI-compatible Python wrapper for **Perchance AI** generators. Generate text and images programmatically with absolute zero manual browser management, bypassing anti-bot protections automatically.

---

## ✨ Key Features

* **⚡ Blazing Fast Extraction:** Deep iframe search & Regex-based DOM scanning for instant text and image extraction without timeouts.
* **🧵 Thread-Safe Concurrency:** Run multiple generators safely. Features a built-in queue system via `max_concurrent_tabs` to prevent browser crashes.
* **🖼️ On-the-Fly Image Conversion:** Automatically converts base64 blobs into desired formats (`png`, `jpeg`, `webp`) directly inside the browser engine.
* **🛡️ Built-in Anti-Bot Bypass:** Uses a pristine automated stealth environment. Defeats Cloudflare and invisible pop-ups automatically.
* **🌍 Auto-Translation:** Built-in Google Translate support for prompt/response.
* **🌐 Integrated VPN Support:** Pass VLESS links and the library sets up `Xray-core` automatically.

---

## 📦 Installation

To automatically install all dependencies required for the engine, run the included script:

```bash
python install.py
```

Alternatively, install manually via pip:

```bash
pip install DrissionPage requests
```

---

## 🚀 Quick Start

### Text Generation (Synchronous)

```python
import perchancy

client = perchancy.Client(headless=True)

response = client.chat.completions.create(
    model="ai-text-generator",
    messages=[{"role": "user", "content": "Write a 3-sentence horror story."}],
    stream=False,
    translation="auto"
)

content = response["choices"][0]["message"]["content"]
print(content)
```

### Text Generation (Streaming)

```python
import perchancy
import sys

client = perchancy.Client(headless=True)

response = client.chat.completions.create(
    model="ai-character-chat",
    messages=[{"role": "user", "content": "Tell me a short sci-fi intro."}],
    stream=True
)

for chunk in response:
    content = chunk["choices"][0]["delta"].get("content", "")
    sys.stdout.write(content)
    sys.stdout.flush()
```

### Image Generation

```python
import perchancy
import base64
import threading

client = perchancy.Client(headless=True, max_concurrent_tabs=4)

def run_image_task(thread_id, fmt):
    response = client.images.generate(
        model="ai-text-to-image-generator",
        prompt="cyberpunk city, neon lights",
        num_images=1,
        image_format=fmt,
        disable_safety_settings=True
    )

    for i, img in enumerate(response.get("data",[])):
        file_name = f"out_t{thread_id}_{i}.{fmt}"
        with open(file_name, "wb") as f:
            f.write(base64.b64decode(img["url"]))

t1 = threading.Thread(target=run_image_task, args=(1, "png"))
t2 = threading.Thread(target=run_image_task, args=(2, "jpeg"))

t1.start()
t2.start()

t1.join()
t2.join()
```

---

## 📚 API Documentation

### Client Configuration

`perchancy.Client(**kwargs)` initializes the main browser engine.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `headless` | `bool` | `True` | Runs the browser in the background without a UI. |
| `debug` | `bool` | `False` | Prints detailed execution status logs to the console. |
| `max_concurrent_tabs`| `int` | `4` | Maximum number of active tabs allowed at the same time. Extra threads will wait in a queue. |
| `vpn_configs` | `List[str]`| `None` | A list of VLESS/Proxy URIs for connection rotation. |

### Chat Completions

`client.chat.completions.create(**kwargs)`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model` | `str` | *Required*| The URL slug of the Perchance generator (e.g., `ai-character-chat`). |
| `messages` | `List[Dict]`| *Required*| Standard OpenAI messages array. Uses the content of the last message as the prompt. |
| `stream` | `bool` | `False` | Returns a generator yielding text chunks as they are generated. |
| `translation` | `str` | `None` | Translates the final output. Set to `"auto"` to translate back to the prompt's detected language. |

### Image Generation Parameters

`client.images.generate(**kwargs)`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model` | `str` | *Required*| The URL slug of the generator. |
| `prompt` | `str` | *Required*| The text description for the image generation. |
| `num_images` | `int` | `1` | Number of images to generate in the current task. |
| `image_format` | `str` | `"png"` | Target output format (`png`, `jpeg`, `webp`). Conversions happen automatically. |
| `time_for_image` | `int` | `90` | Maximum wait time per image in seconds. Calculates `time * num_images`. Set to `0` for infinite. |
| `disable_safety_settings`| `bool` | `False` | Attempts to bypass strict NSFW filters. Returns an error if blocked when `False`. |

---

## 🛠 Advanced Features

### Custom Parameters & Selectors

Perchance generators often have sliders or dropdowns (like `seed`, `guidanceScale`). You can control these using `extra_params` and `param_mappings` directly in the `create` or `generate` methods.

If the generator layout is non-standard, you can override the default CSS selectors via `input_selectors`, `button_selectors`, and `output_selectors`.

```python
client.images.generate(
    model="ai-text-to-image-generator",
    prompt="A magical forest",
    extra_params={
        "guidanceScale": "7.5",
        "negativePrompt": "low quality, blurry"
    },
    param_mappings={
        "quality":["#resolution-dropdown-id", "[data-name='qualitySelect']"]
    },
    quality="high"
)
```

### VPN & VLESS Proxy Rotation (EXPERIMENTAL)

> ⚠️ **WARNING:** The VPN and proxy rotation feature has only been superficially tested. You may encounter unexpected bugs, routing issues, or failures when using proxy lists. Use with caution.

You can pass a list of VLESS links or proxy configurations to the `Client`. The library will automatically rotate them on a per-request basis. If it's the first time running a VLESS proxy, it will prompt you to download `Xray-core` locally to handle the protocol.

Pass `"disabled"` inside the list to occasionally route traffic without a proxy.

```python
import perchancy

vpn_list =[
    "disabled",
    "vless://uuid@server:port?type=ws&security=tls#Proxy1",
    "vless://uuid@server:port?type=tcp&security=reality#Proxy2"
]

client = perchancy.Client(vpn_configs=vpn_list)

client.images.generate(
    model="ai-text-to-image-generator",
    prompt="Testing VPN connection"
)
```

---

## ⚠️ Disclaimer
Unofficial wrapper. Use for educational purposes only. The author is not responsible for any misuse, account bans, or IP blocks.

## 📝 License
**MIT License**.