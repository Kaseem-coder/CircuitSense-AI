"""
Vision Engine — Moondream2 (local VLM)
Identifies chips, components, and wiring from breadboard images.

Fallback: set USE_OPENAI=true in .env to use GPT-4o vision instead.
"""

import os
from PIL import Image

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"

class VisionEngine:
    def __init__(self):
        if USE_OPENAI:
            self._init_openai()
        else:
            self._init_moondream()

    def _init_moondream(self):
        """Load Moondream2 locally (CPU-compatible, ~2GB RAM)."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print("[Vision] Loading Moondream2... (this takes ~30s on first run)")
        self.model = AutoModelForCausalLM.from_pretrained(
            "vikhyatk/moondream2",
            revision="2024-08-26",
            trust_remote_code=True,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "vikhyatk/moondream2",
            revision="2024-08-26",
            trust_remote_code=True,
        )
        print("[Vision] Moondream2 loaded.")
        self._backend = "moondream"

    def _init_openai(self):
        import openai
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._backend = "openai"
        print("[Vision] Using OpenAI GPT-4o for vision.")

    def analyze(self, image: Image.Image) -> dict:
        """
        Given a PIL Image of a breadboard, return:
          { "chip": "ESP32", "connections": ["Pin 12 connected to 5V rail", ...] }
        """
        prompt = (
            "You are a hardware safety expert. Look at this breadboard image. "
            "1. Identify the main microcontroller or IC chip (e.g. ESP32, Arduino, STM32). "
            "2. List every wire connection you can see, specifying which pin connects to which rail or component. "
            "Format your response as: CHIP: <name>\\nCONNECTIONS:\\n- <connection 1>\\n- <connection 2>\\n..."
        )

        if self._backend == "moondream":
            return self._analyze_moondream(image, prompt)
        else:
            return self._analyze_openai(image, prompt)

    def _analyze_moondream(self, image: Image.Image, prompt: str) -> dict:
        enc_image = self.model.encode_image(image)
        response = self.model.answer_question(enc_image, prompt, self.tokenizer)
        return self._parse_response(response)

    def _analyze_openai(self, image: Image.Image, prompt: str) -> dict:
        import base64
        from io import BytesIO
        buf = BytesIO()
        image.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=500
        )
        return self._parse_response(response.choices[0].message.content)

    def _parse_response(self, text: str) -> dict:
        """Parse vision model output into structured dict."""
        chip = "Unknown"
        connections = []

        lines = text.strip().split("\n")
        in_connections = False
        for line in lines:
            line = line.strip()
            if line.lower().startswith("chip:"):
                chip = line.split(":", 1)[1].strip()
            elif line.lower().startswith("connections:"):
                in_connections = True
            elif in_connections and line.startswith("-"):
                connections.append(line[1:].strip())

        return {"chip": chip, "connections": connections, "raw": text}
