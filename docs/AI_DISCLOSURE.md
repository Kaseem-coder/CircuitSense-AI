# AI Disclosure — Circuit-Sense AI

## Overview

This document discloses all AI tools, models, and frameworks used in the development and operation of Circuit-Sense AI, in accordance with hackathon transparency requirements.

---

## AI Models Used in the Product

### 1. Moondream2 (Primary Vision Engine)
- **Provider**: vikhyatk / HuggingFace
- **Model**: `vikhyatk/moondream2` (revision: 2024-08-26)
- **Purpose**: Analyzing breadboard images to identify microcontroller chips (ESP32, Arduino, etc.) and wiring connections
- **Deployment**: Local inference on device — no data sent to external servers
- **License**: Apache 2.0

### 2. Sentence Transformers — all-MiniLM-L6-v2 (RAG Embeddings)
- **Provider**: HuggingFace / sentence-transformers
- **Purpose**: Embedding PDF datasheet text chunks into vector space for semantic search
- **Deployment**: Local inference
- **License**: Apache 2.0

### 3. GPT-4o Vision (Optional Cloud Fallback)
- **Provider**: OpenAI
- **Purpose**: Alternative vision backend when local GPU is unavailable (enabled via `USE_OPENAI=true`)
- **Data handling**: Images sent to OpenAI API — not used by default in production
- **License**: OpenAI Terms of Service

---

## AI Tools Used During Development

### 4. Claude (Anthropic) — claude-sonnet-4-5
- **Purpose**: Used to assist in writing boilerplate code, debugging FastAPI endpoints, and drafting documentation
- **Scope**: Code suggestions reviewed and modified by team members; all architectural decisions made by humans
- **What we did ourselves**: System architecture design, pipeline design (vision → RAG → alert), datasheet ingestion strategy, UI design, demo scripting

---

## AI Frameworks / Infrastructure

### 5. ChromaDB
- **Purpose**: Vector database for storing and querying embedded datasheet chunks
- **Note**: Not an AI model itself, but the retrieval backbone of our RAG system

---

## What Was NOT AI-Generated

- The overall project idea and problem framing
- The OpenClaw-inspired SOUL.md / HEARTBEAT.md agent personality design
- The decision to use local VLMs (privacy-first approach)
- Hardware testing and validation
- Presentation design and narrative

---

## Responsible AI Commitments

- **No user data stored**: Images analyzed in-memory only; not logged or retained
- **Local-first**: Default deployment uses Moondream2 locally, ensuring privacy for hardware engineers working on proprietary designs
- **Safety-first**: The system only alerts on violations — it does not autonomously disconnect hardware or take physical actions

---

*Prepared by the Circuit-Pulse AI team for RVCE Hackathon submission.*
