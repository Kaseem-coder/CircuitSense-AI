# HEARTBEAT.md 
 
## Proactive Monitoring Loop

Every 5 seconds, Circuit-Sense autonomously:

1. Captures a webcam frame of the breadboard
2. Sends image to Gemini Vision for component identification
3. Queries ChromaDB RAG for datasheet voltage constraints
4. Compares detected wiring against safe operating limits
5. If violation found → fires Telegram alert immediately
6. Logs result to agent memory for session history

## Trigger Conditions
- Any GPIO pin receiving voltage above 3.3V on ESP32
- LED connected without current-limiting resistor
- Sensor VCC connected to wrong voltage rail
- Unknown chip detected with no datasheet in knowledge base

## Autonomous Behavior
The heartbeat runs without user prompting.
Circuit-Sense is always watching, even when you're not