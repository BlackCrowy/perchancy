# Perchancy 🚀

[![PyPI version](https://img.shields.io/pypi/v/perchancy.svg)](https://pypi.org/project/perchancy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Perchancy** is a high-speed, OpenAI-compatible Python wrapper for **Perchance AI** generators. Generate text and images programmatically with zero manual browser management.

---

## ✨ Key Features

*   **⚡ Blazing Fast:** Optimized DOM scanning for instant extraction.
*   **🤖 Auto Lifecycle:** Browser closes automatically via `atexit`.
*   **🔄 Auto-Sync Chrome:** Automatically downloads matching *Chrome for Testing*.
*   **📽️ Streaming Support:** Real-time text generation.
*   **🌍 Auto-Translation:** Built-in Google Translate support for prompt/response.
*   **🛡️ Per-Request Safety:** Toggle `disable_safety_settings` individually for each call.

---

## 📦 Installation

```bash
pip install perchancy
```

---

## 🚀 Quick Start


### Text Generation (Non-Streaming)
```python
import perchancy

client = perchancy.Client(headless=True)

# Generate full text synchronously
response = client.chat.completions.create(
    model="ai-text-generator",
    messages=[{"role": "user", "content": "Write a 3-sentence horror story."}],
    stream=False,                 # Wait for the complete response
    translation="auto",           # Automatically translate back to your prompt's language
)

# Access content using standard OpenAI dictionary keys
content = response["choices"][0]["message"]["content"]

print(f"ID: {response['id']}")
print(f"Model: {response['model']}")
print("-" * 20)
print(content)
```

### Text Generation (Streaming)
```python
import perchancy

client = perchancy.Client(headless=True)

response = client.chat.completions.create(
    model="ai-text-generator",
    messages=[{"role": "user", "content": "Write a short sci-fi intro."}],
    stream=True,
    translation="auto",
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

client = perchancy.Client(headless=True)

response = client.images.generate(
    model="ai-text-to-image-generator",
    prompt="cyberpunk city, neon lights",
    num_images=2,
    disable_safety_settings=True
)

for i, img in enumerate(response.get("data", [])):
    with open(f"out_{i}.png", "wb") as f:
        f.write(base64.b64decode(img["url"]))
```

---

## 🛠 Advanced: Extra Params & Mappings

Perchance generators often have sliders, dropdowns, or input fields (like `seed`, `guidanceScale`, or `negativePrompt`). You can control these using `extra_params`.

### 1. How to find parameters?
1. Open the generator in your browser.
2. Right-click any UI element (slider, input, etc.) and click **Inspect**.
3. Note the `id`, `name`, or `data-name` (e.g., `id="seedInput"`).

### 2. Usage Example
```python
client.images.generate(
    model="ai-text-to-image-generator",
    prompt="A magical forest",
    # Set values directly using element IDs
    extra_params={
        "guidanceScale": "7.5",
        "negativePrompt": "low quality, blurry"
    },
    # Use mappings to create aliases for complex selectors
    param_mappings={
        "quality": ["#resolution-dropdown-id", "[data-name='qualitySelect']"]
    },
    quality="high" # Now 'quality' works as a direct argument via **kwargs
)
```

---

## 🔐 Authentication (Optional)

```python
from perchancy.auth import login_and_save_cookies
login_and_save_cookies()
```

**Note:**
*   **Authentication is NOT required.** The library works perfectly as a guest.
*   This is intended for advanced users to bypass guest limits.
*   **Disclaimer:** The `auth` module's functionality has **not been verified** as guest mode proved sufficient during development.

---

## 📖 Documentation Summary

*   **Finding Models:** The "model" is the slug in the URL: `perchance.org/NAME`.
*   **Client Configuration:**
    *   `headless` (bool): Run in background (default: `True`).
    *   `debug` (bool): Enable detailed status logs.
*   **Custom Selectors:** You can manually override `input_selectors`, `button_selectors`, or `output_selectors` in the `create`/`generate` methods if a specific generator has a non-standard layout.

---

## ⚠️ Disclaimer
Unofficial wrapper. Use for educational purposes only. Author is not responsible for any misuse or bans.

## 📝 License
**MIT License**.

---
*Created with ❤️ by BlackCrowy*