"""
Vision Engine — Google Gemini Flash (new google-genai SDK)
"""

import os
from PIL import Image
from google import genai
from google.genai import types


class VisionEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in .env file")
        self.client = genai.Client(api_key=api_key)
        self._backend = "gemini"
        print("[Vision] Gemini Flash loaded successfully.")

    def analyze(self, image: Image.Image) -> dict:
        prompt = (
    "You are a strict hardware safety expert. Look at this breadboard image carefully. "
    "1. Identify ALL components — microcontrollers, sensors, LEDs, resistors. "
    "2. Identify the MAIN chip (ESP32, Arduino, etc). "
    "3. List every wire connection — pay special attention to RED wires (usually 5V/VCC) "
    "and where they connect on the microcontroller. "
    "4. Flag ANY dangerous connections: 5V to 3.3V GPIO pins, missing resistors on LEDs, "
    "wrong voltage rails. ESP32 GPIO pins are 3.3V tolerant ONLY — connecting 5V to any GPIO is a violation. "
    "Format exactly as:\n"
    "CHIP: <name>\n"
    "COMPONENTS: <comma separated>\n"
    "CONNECTIONS:\n"
    "- <connection>\n"
    "WARNINGS:\n"
    "- <warning or 'none'>\n"
)
        try:
            # Convert PIL image to bytes
            import io
            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            image_bytes = buf.getvalue()

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )
            return self._parse_response(response.text)
        except Exception as e:
            print(f"[Vision] Gemini error: {e}")
            return {"chip": "Unknown", "connections": [], "warnings": [], "raw": str(e), "error": str(e)}

    def analyze_text(self, description: str) -> dict:
        prompt = (
            f"Parse this circuit description and extract structured info.\n\n"
            f"Description: {description}\n\n"
            f"Format your response exactly as:\n"
            f"CHIP: <name>\n"
            f"CONNECTIONS:\n"
            f"- <connection 1>\n"
            f"- <connection 2>"
        )
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt]
            )
            return self._parse_response(response.text)
        except Exception as e:
            print(f"[Vision] Gemini text error: {e}")
            return {"chip": "Unknown", "connections": [], "warnings": [], "raw": str(e), "error": str(e)}

    def _parse_response(self, text: str) -> dict:
        chip = "Unknown"
        connections = []
        in_connections = False

        for line in text.strip().split("\n"):
            line = line.strip()
            if line.lower().startswith("chip:"):
                chip = line.split(":", 1)[1].strip()
            elif line.lower().startswith("connections:"):
                in_connections = True
            elif in_connections and line.startswith("-"):
                connections.append(line[1:].strip())

        return {"chip": chip, "connections": connections, "raw": text}