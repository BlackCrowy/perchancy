# Perchancy 🚀

**Perchancy** is a high-speed, OpenAI-compatible Python wrapper for **Perchance AI** generators. It allows you to programmatically generate text and images using the vast community-driven generators on Perchance without the hassle of manual browser automation.

---

## ✨ Key Features

*   **⚡ Blazing Fast:** Optimized scanning algorithms for near-instant image and text extraction.
*   **🔄 Auto-Sync Chrome:** Automatically downloads and matches the correct version of *Chrome for Testing* to prevent "SessionNotCreated" driver errors.
*   **📽️ Streaming Support:** Real-time text generation streaming (just like the native OpenAI API).
*   **🌍 Auto-Translation:** Built-in support to translate AI responses into English, Russian, or any other language automatically.
*   **🛡️ Filter Bypass:** Optional `disable_safety_settings` to ignore safety filters and guardrails during generation.
*   **🧩 Universal Compatibility:** Designed to work with almost any generator hosted on Perchance.

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

client = perchancy.Client()

response = client.chat.completions.create(
    model="ai-text-generator",
    messages=[{"role": "user", "content": "Tell me a short story about a golden dragon."}],
    stream=True,
    translation="auto" # Detects your prompt language and translates the AI answer back to it
)

for chunk in response:
    content = chunk["choices"][0]["delta"].get("content", "")
    if content:
        print(content, end="", flush=True)

client.close()
```

### Image Generation
```python
import perchancy
import base64

client = perchancy.Client(disable_safety_settings=True)

response = client.images.generate(
    model="ai-text-to-image-generator",
    prompt="cyberpunk city, neon lights, 8k resolution",
    num_images=2
)

if "error" not in response:
    for i, img in enumerate(response["data"]):
        # Save images from Base64
        with open(f"output_{i}.png", "wb") as f:
            f.write(base64.b64decode(img["url"]))
```

---

## 📖 Documentation

### 1. Finding "Models" (Endpoints)
Perchance does not have a fixed list of models. A "model" is simply the name of the specific generator in the URL.
*   Go to [perchance.org](https://perchance.org).
*   Find a generator you like (e.g., `ai-text-generator` or `ai-character-generator`).
*   The word after the slash in the URL `perchance.org/NAME` is your `model` parameter.

### 2. `Client` Parameters
*   `headless` (bool): Run the browser in the background (default: `True`).
*   `debug` (bool): Enable detailed logs in the console (default: `False`).
*   `disable_safety_settings` (bool): If `True`, the script removes safety overlays and attempts to extract NSFW or "blocked" content (default: `False`).

### 3. `chat.completions.create` Parameters
*   `model` (str): The name of the Perchance generator.
*   `messages` (list): A list of message objects (supports `role` and `content`).
*   `stream` (bool): Enable real-time streaming output.
*   `translation` (str): Target language for translation (e.g., `"russian"`, `"ru"`, `"auto"`). Using `"auto"` will match the language used in your prompt.

### 4. `images.generate` Parameters
*   `model` (str): The name of the image generator.
*   `prompt` (str): The description of the image.
*   `num_images` (int): Number of images to generate. The library automatically selects the maximum allowed by the UI if you request more than possible.

---

## 🔐 Authentication (Optional)

The library includes an `auth` module that allows you to save cookies from your Perchance account.

**Please Note:** 
*   **Authentication is NOT required.** The library works perfectly fine as a guest.
*   This module was added for "advanced users" who might want to bypass guest limits or use specific account-linked features.
*   **Disclaimer:** The `auth` module's functionality has **not been verified** because there was no practical necessity for it during the development of the main features.

Use at your own discretion:
```python
from perchancy.auth import login_and_save_cookies
login_and_save_cookies()
```

---

## ⚠️ Disclaimer

This project is an unofficial wrapper and is not affiliated with, endorsed by, or sponsored by Perchance. The author is not responsible for any misuse of this library, IP bans, or account suspensions. Use this tool strictly for educational and research purposes.

## 📝 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---
*Created with ❤️ by BlackCrowy*