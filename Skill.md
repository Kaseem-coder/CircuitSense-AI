# Skill.md 
 
## Skill 1: Vision Analysis
- **Tool**: Google Gemini Flash / Claude Vision
- **Input**: Breadboard image (webcam or photo)
- **Output**: Chip name, wire connections, safety warnings
- **Trigger**: Manual analyze or heartbeat loop

## Skill 2: RAG Datasheet Query
- **Tool**: ChromaDB + Sentence Transformers
- **Input**: Chip name + connection description
- **Output**: Relevant datasheet constraints and voltage limits
- **Trigger**: Called after every vision analysis

## Skill 3: Telegram Alert
- **Tool**: Telegram Bot API
- **Input**: Violation message
- **Output**: Instant push notification to engineer
- **Trigger**: Any safety violation detected
