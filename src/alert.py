"""
Alert Engine — Telegram Bot Notifications
Sends safety alerts when violations are detected.
"""

import os
import asyncio
import threading

class AlertEngine:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self._last_alert = ""  # Prevent duplicate alerts

    def send(self, message: str):
        """Send a Telegram message (non-blocking)."""
        if message == self._last_alert:
            return  # Don't spam the same alert
        self._last_alert = message

        if not self.bot_token or not self.chat_id:
            print(f"[Alert] (No Telegram configured) Would send: {message}")
            return

        thread = threading.Thread(target=self._send_sync, args=(message,), daemon=True)
        thread.start()

    def _send_sync(self, message: str):
        import requests
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            r = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": f"🔴 Circuit-Sense AI Alert\n\n{message}",
                "parse_mode": "HTML"
            }, timeout=10)
            if r.ok:
                print(f"[Alert] Telegram sent: {message[:80]}...")
            else:
                print(f"[Alert] Telegram error: {r.text}")
        except Exception as e:
            print(f"[Alert] Failed to send Telegram message: {e}")

    def test(self):
        """Send a test alert."""
        self.send("🧪 Test alert from Circuit-Sense AI. System online.")
