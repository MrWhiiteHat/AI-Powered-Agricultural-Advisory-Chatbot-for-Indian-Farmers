# 📱 KrishiMitra — WhatsApp & Twilio Integration Guide

This guide provides step-by-step instructions on how to connect your locally running KrishiMitra backend to the live WhatsApp network so that farmers can interact with the bot from their mobile phones.

---

## 🛠️ Prerequisites
Before starting, ensure that:
1. Your FastAPI server is running (`python run.py`).
2. You have a free Twilio Account ([Sign up here](https://www.twilio.com/)).
3. You have Node.js installed to run `ngrok` (or you have the Ngrok executable).

---

## 🔑 Phase 1: Retrieve Twilio Credentials

By default, the `.env` file contains placeholder credentials that look like this:
```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```
Without your real credentials, the bot **cannot** send replies back to WhatsApp.

1. Log in to your **Twilio Console**.
2. On your dashboard homepage, locate your **Account SID** and **Auth Token**.
3. Open `d:\AI CLG Project\.env` in your code editor.
4. Replace the dummy strings with your actual Twilio credentials.

*(Note: Do not put quotes around the credentials in the `.env` file.)*

---

## 🤝 Phase 2: Join the Twilio Sandbox

To prevent spam, WhatsApp requires users to explicitly "join" a Sandbox before a development bot can message them. You must do this to test your bot on your own phone number (e.g., `8917512439`).

1. In the Twilio Console, go to **Messaging > Try it out > Send a WhatsApp message**.
2. Twilio will display a **Sandbox Number** (e.g., `+1 415 523 8886`) and a **Join Code** (e.g., `join smooth-ocean`).
3. Save the Twilio Sandbox Number in your phone's contacts as "KrishiMitra Bot".
4. Open WhatsApp on your phone and send the exact Join Code to the Twilio number.
5. Twilio will reply with a confirmation message: *"You are all set!"*

Your phone is now connected to the Sandbox and can receive messages from the bot!

---

## 🌐 Phase 3: Expose Localhost to the Internet using Ngrok

Twilio operates on the public internet and cannot send webhooks to `http://localhost:8000`. We need to use **Ngrok** to create a secure, public tunnel to your local server.

1. Open a **new terminal/command prompt**.
2. Run the following command:
   ```cmd
   npx ngrok http 8000
   ```
3. Ngrok will start up and display a **Forwarding URL** that looks something like this:
   `https://1234-abcd.ngrok-free.app -> http://localhost:8000`
4. Copy the public `https://...` URL. **Do not close this terminal**; if you close it, the URL dies and WhatsApp will stop working.

---

## 🔌 Phase 4: Configure the Twilio Webhook

Now that your server is public, you must tell Twilio where to send incoming WhatsApp messages.

1. Go back to the **Twilio Console**.
2. Navigate to your **WhatsApp Sandbox Settings** (Messaging > Try it out > Sandbox settings).
3. Find the section labeled **"When a message comes in"**.
4. Paste your Ngrok URL into the box and append `/webhook/whatsapp` to the end.
   - Example: `https://1234-abcd.ngrok-free.app/webhook/whatsapp`
5. Ensure the HTTP method is set to **POST**.
6. Click **Save**.

---

## 🚀 Phase 5: Test the Bot!

Everything is now fully wired up. 

1. Take out your phone and open your WhatsApp chat with the Sandbox number.
2. Send a message like:
   - *"Hello!"*
   - *"Tomato price"*
   - *"What are some government schemes?"*
   - Send an **image** of a sick plant leaf.
   - Send a **voice note** in Hindi or English.
3. Watch your local terminal (`python run.py`)—you will see the webhook trigger and the Gemini AI classification process happening live!
4. A few seconds later, the AI's formulated response will arrive directly on your WhatsApp screen.
