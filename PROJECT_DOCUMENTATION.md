# 🌾 KrishiMitra — Complete Architecture & Technical Guide

KrishiMitra (कृषि मित्र) is an AI-powered agricultural advisory chatbot designed to assist Indian small-scale farmers. It provides real-time farming advice, crop disease detection, weather forecasts, market prices, and government scheme recommendations through both **WhatsApp** and a **Web Chat Interface**.

This document breaks down every piece of technology, tool, and file logic that makes the system work.

---

## 🏗️ 1. Complete System Workflow

Whether the farmer messages via WhatsApp or the Web UI, the chatbot follows a strict "Pipeline" to process information:

1. **Incoming Message**: The farmer sends a text, image (leaf), or voice note.
2. **Speech-to-Text (If Voice)**: If the message is audio, the system downloads it and uses **OpenAI Whisper** to transcribe it into text. 
3. **Computer Vision (If Image)**: If the farmer sends an image of a leaf, it passes through our **TensorFlow MobileNetV2** model to diagnose the specific plant disease.
4. **User Profiling (Database)**: The system automatically registers the farmer or fetches their profile from **MongoDB** (checking their location, preferred language, and registered crops).
5. **Intent Classification**: The text message is passed to **Google Gemini**. Gemini analyzes the text to determine the "Intent" (e.g., Is the farmer asking for weather? Or market prices? Or general advice?).
6. **Data Retrieval (APIs)**:
   - **Weather Intent**: Makes a live call to **OpenWeatherMap API**.
   - **Market Intent**: Fetches current mandi prices (Agmarknet).
   - **Scheme Intent**: Searches the local JSON Knowledge Base / RAG for government schemes (PMFBY, PM-Kisan, etc.).
7. **LLM Generation**: The raw data (e.g., "32°C, Sunny") and the farmer's prompt are sent to **Google Gemini**. Gemini writes a friendly, localized response in the farmer's native language (Hindi, English, etc.) with emojis.
8. **Response Dispatch**: The fully formatted message is dispatched back to the web browser or securely pushed via **Twilio API** directly to the farmer's WhatsApp.

---

## 🛠️ 2. The Core Technology Stack & Tools

### A. Backend Framework: FastAPI (Python)
- **Why we use it:** It is incredibly fast and asynchronous. When handling hundreds of WhatsApp messages concurrently, FastAPI doesn't freeze or block while waiting for Gemini to reply.
- **Key Files:** 
  - `app/main.py`: The entry point that boots up the server and loads the AI models into memory.
  - `run.py`: The physical script you use to start Uvicorn (the web server).

### B. Database: MongoDB
- **Why we use it:** It's a NoSQL database perfectly tuned for storing varying JSON documents like chat histories and dynamic farmer profiles.
- **Key Files:** 
  - `app/database.py`: Manages the connection to your local MongoDB server.
  - `app/models/farmer.py` & `app/models/conversation.py`: The schemas defining how a "Farmer" and a "Chat Timeline" look in the database.

### C. Large Language Model (LLM): Google Gemini 2.5 Flash-Lite
- **Why we use it:** We are using via the `google-genai` pip package. Gemini writes the actual human-readable responses, translates between Hindi/English natively, and classifies intents (figuring out what the user wants). Flash-Lite ensures the response is nearly instant without draining your free-tier API Quotas.
- **Key File:** `app/services/gemini_llm.py` (Contains the complex prompts that instruct Gemini to act as a kind, expert agricultural advisor).

### D. Computer Vision (Disease Detection): TensorFlow & MobileNetV2
- **Why we use it:** MobileNetV2 is a lightweight Convolutional Neural Network (CNN) specifically optimized to run fast on CPUs. It was trained on the **PlantVillage dataset** (54,000+ images) to recognize 38 specific leaf diseases.
- **Key Files:** `app/services/disease_detector.py` and `app/ml/train_model.py`.

### E. Speech-to-Text: OpenAI Whisper
- **Why we use it:** Whisper accurately transcribes Indian-accented English and native Hindi voice notes. It converts the farmer's voice into text before we feed it to Gemini.
- **Key File:** `app/services/whisper_stt.py`.

### F. Communication Setup
- **Twilio Sandbox**: Acts as a bridge between the official WhatsApp network and our local FastAPI server. Twilio converts WhatsApp messages into HTTP Webhook packages.
- **Web UI (`templates/index.html`)**: A beautiful frontend written in raw HTML/JS/CSS that mimics a high-end chat app using *Glassmorphism* aesthetics, so you can test the AI completely independent of WhatsApp. 

---

## 📂 3. Code Directory Breakdown

Here is what the folders in your standard project (`d:\AI CLG Project`) actually do:

- 📁 `app/routes/` 
  - **`webhook.py`**: The "brain" of the routing operation. Twilio pings this generic file, and this logic handles everything from downloading media to replying.
  - **`web_ui.py`**: The endpoint serving your gorgeous local web chat at `localhost:8000/chat`.
- 📁 `app/services/`
  - Everything here talks to third parties. `gemini_llm.py` (Google), `whatsapp.py` (Twilio API), `weather.py` (OpenWeather). 
- 📁 `app/utils/`
  - **`logger.py`**: Controls what prints to the terminal using `Loguru`. We engineered this specifically with `utf-8` to prevent Windows from crashing when it tries to print Hindi or Emojis to the console!
- 📁 `data/schemes/`
  - Contains `govt_schemes.json`, which acts as a fallback "Knowledge Base" (RAG) so the bot actually knows real schemes without hallucinating.

---

## 🚀 4. How the "Graceful Degradation" Architecture Works
One of the most complex things implemented in your project is **Graceful Degradation**. 

Loading TensorFlow Neural Networks and gigabytes of Whisper models takes heavy computing power. If the server detects that the `.h5` CNN model is missing, or the laptop lacks the RAM for Whisper, the FastAPI server **will not crash**. Instead, it gracefully logs a warning (`⚠️ CNN model not loaded (will use simulation)`) and boots up in a "Mock" mode, simulating the AI behavior just to keep the chat interface reliably online. This makes the project highly resilient for live-demo and college presentation scenarios!
