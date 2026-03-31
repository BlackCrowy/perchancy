# Perchancy 🚀

[![PyPI version](https://img.shields.io/pypi/v/perchancy.svg)](https://pypi.org/project/perchancy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Perchancy** is a high-speed, OpenAI-compatible Python wrapper for **Perchance AI** generators. It allows you to programmatically generate text and images using the vast community-driven generators on Perchance with zero manual browser management.

---

## ✨ Key Features

*   **⚡ Blazing Fast:** Optimized scanning algorithms for near-instant image and text extraction.
*   **🤖 Automatic Lifecycle:** No need to call `close()`. The browser closes automatically when your script finishes or encounters an error.
*   **🔄 Auto-Sync Chrome:** Automatically downloads and matches the correct version of *Chrome for Testing* to prevent driver errors.
*   **📽️ Streaming Support:** Real-time text generation streaming (just like the native OpenAI API).
*   **🌍 Auto-Translation:** Built-in support to translate AI responses into English, Russian, or any other language automatically.
*   **🛡️ Filter Bypass:** Optional `disable_safety_settings` to ignore safety filters and overlays.

---

## 📦 Installation

```bash
pip install perchancy
```

---

## 🚀 Quick Start

### Text Generation with Streaming
```python
import perchancy

# Initialize once - the browser will close itself when the script ends
client = perchancy.Client(headless=True)

response = client.chat.completions.create(
    model="ai-text-generator",
    messages=[{"role": "user", "content": "Tell me a short story about a golden dragon."}],
    stream=True,
    translation="auto" # Translates the response back to your prompt's language
)

for chunk in response:
    content = chunk["choices"][0]["delta"].get("content", "")
    if content:
        print(content, end="", flush=True)
```

### Image Generation
```python
import perchancy
import base64

client = perchancy.Client(headless=True, disable_safety_settings=True)

response = client.images.generate(
    model="ai-text-to-image-generator",
    prompt="cyberpunk city, neon lights, 8k resolution",
    num_images=2
)

if "error" not in response:
    for i, img in enumerate(response["data"]):
        with open(f"output_{i}.png", "wb") as f:
            f.write(base64.b64decode(img["url"]))
```

---

## 📖 Documentation

### 1. Finding "Models" (Endpoints)
Perchance doesn't have a fixed list of models. A "model" is simply the name of the specific generator in the URL.
*   Visit [perchance.org](https://perchance.org).
*   Find a generator (e.g., `ai-text-generator`).
*   The word after the slash in the URL `perchance.org/NAME` is your `model` parameter.

### 2. `Client` Configuration
*   `headless` (bool): Run the browser in the background (default: `True`).
*   `debug` (bool): Enable detailed status logs in the console.
*   `disable_safety_settings` (bool): If `True`, the script removes safety overlays to extract "blocked" content.
*   **Lifecycle:** The library uses `atexit` to ensure all browser processes are killed cleanly when your Python process exits.

### 3. `chat.completions.create` Parameters
*   `model` (str): The name of the Perchance generator.
*   `messages` (list): Message objects (supports `role` and `content`).
*   `stream` (bool): Enable real-time streaming output.
*   `translation` (str): Target language (e.g., `"russian"`, `"ru"`, `"auto"`).

### 4. `images.generate` Parameters
*   `model` (str): The name of the image generator.
*   `prompt` (str): The visual description.
*   `num_images` (int): Number of images. The library automatically selects the maximum allowed by that specific generator's UI if you request more than its limit.

---

## 🔐 Authentication (Optional)

The library includes an `auth` utility for saving cookies from your Perchance account.

**Note:** 
*   **Authentication is NOT required.** The library works perfectly as a guest.
*   This is intended for advanced users to bypass guest limits.
*   **Disclaimer:** The `auth` module's functionality has **not been verified** as guest mode proved sufficient during development.

```python
from perchancy.auth import login_and_save_cookies
login_and_save_cookies()
```

---

## ⚠️ Disclaimer

This project is an unofficial wrapper and is not affiliated with, endorsed by, or sponsored by Perchance. The author is not responsible for any misuse, IP bans, or account suspensions. Use this tool strictly for educational and research purposes.

## 📝 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---
*Created with ❤️ by BlackCrowy*