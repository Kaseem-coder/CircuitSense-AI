"""
Heartbeat Monitor — OpenClaw-style proactive safety loop
Continuously watches the camera and checks against the safe state.
"""

import time
import cv2
from PIL import Image


class HeartbeatMonitor:
    def __init__(self, rag, vision, alert, interval: int = 5):
        self.rag = rag
        self.vision = vision
        self.alert = alert
        self.interval = interval  # seconds between checks
        self._running = False
        self._safe_state = True

    def run(self):
        """Start the monitoring loop. Run in a background thread."""
        self._running = True
        print("[Heartbeat] Starting monitoring loop...")
        cap = cv2.VideoCapture(0)  # Default webcam

        if not cap.isOpened():
            print("[Heartbeat] Could not open webcam. Heartbeat disabled.")
            return

        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    print("[Heartbeat] Failed to read frame.")
                    time.sleep(self.interval)
                    continue

                # Convert OpenCV BGR → PIL RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)

                # Analyze
                result = self.vision.analyze(image)
                chip = result.get("chip", "Unknown")
                connections = result.get("connections", [])

                violations = []
                for conn in connections:
                    rag_result = self.rag.query(f"{chip} {conn} voltage safety")
                    if rag_result and any(w in rag_result.lower() for w in ["danger", "exceeds", "violation", "not recommended", "maximum"]):
                        violations.append(f"{conn} → {rag_result[:100]}")

                if violations:
                    msg = f"STOP! Safety violation on {chip}:\n" + "\n".join(violations)
                    self.alert.send(msg)
                    self._safe_state = False
                else:
                    self._safe_state = True

                time.sleep(self.interval)
        finally:
            cap.release()
            print("[Heartbeat] Stopped.")

    def stop(self):
        self._running = False
