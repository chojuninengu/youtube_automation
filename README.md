# 🎬 SketchTales V2 — Open Source YouTube Automation

Transform a hand-drawn sketch into a fully narrated, animated video — automatically generated and published to YouTube using **free or low-cost AI tools**.

This is V2 of the original Blotato workflow, modified to run completely independently using a self-hosted n8n environment, saving you >$40/month on subscriptions and reducing per-video costs to near zero.

## 🌟 Key Features
- **Self-Hosted Engine**: Runs on your own machine using Docker and n8n (replaces paid n8n cloud).
- **Gemini Powered**: Uses Google Gemini 1.5 Flash (Generous Free Tier) instead of Claude Sonnet 4.5.
- **Budget Video**: Uses Ken Burns pan/zoom on generated images via Shotstack instead of expensive AI video generation like Kling.
- **Direct Publishing**: Uses n8n's native YouTube node instead of a paid Blotato subscription.

---

## 🚀 Step 1: Spin Up the Self-Hosted n8n

You need Docker installed on your machine.

1. Clone this repository.
2. Open `.env.example`, fill in your desired passwords, and save it as `.env`.
3. Open a terminal in the folder and run:
   ```bash
   docker-compose up -d
   ```
4. Access your new n8n instance at `http://localhost:5678`.
5. Set up your admin account.

---

## 🔐 Step 2: Set Up Credentials in n8n

Before importing the workflows, you need three key APIs:

1. **Google Gemini API**: 
   - Go to Google AI Studio and get a free API key.
   - Add a new credential in n8n for `Google Gemini(PaLM) Api account`.
2. **Shotstack API**: 
   - Get a free key from shotstack.io (used for assembling the video).
3. **ElevenLabs API**:
   - Get a key from ElevenLabs for AI voice narration. (The free tier gives 10k chars/month. $5/mo gives 30k chars/month).
4. **Google YouTube OAuth2 API**:
   - You need to create a Google Cloud Project, enable the YouTube Data API v3, and set up an OAuth Consent Screen. Add the Client ID and Secret to a new credential in n8n.
5. **Cloudinary API**:
   - Get a free Cloudinary account for temporary image hosting and add the credentials.

---

## ⚙️ Step 3: Import the Workflows

The system uses three interconnected workflows:

1. Import `Part_1_V2.json` into a new workflow and save it.
2. Import `Part_2_V2.json` into a new workflow and save it.
3. Import `Part_3_V2.json` into a new workflow and save it.

### Link the Webhooks
The workflows trigger each other sequentially.
1. Open Part 2, double-click the `Webhook` trigger node, and copy the **Test URL**.
2. Open Part 1, double-click the `Trigger Scene Workflow` node, and paste the URL.
3. Open Part 3, double-click the `Webhook1` trigger node, and copy the **Test URL**.
4. Open Part 2, double-click the `Trigger Video Workflow` node, and paste the URL.

> **Note**: For production use, you must switch the Webhooks from "Test URL" to "Production URL" and activate all 3 workflows.

---

## 🎨 How to Use

1. Open the form URL provided by the first node in **Part 1**.
2. Upload a photo of a child's drawing.
3. The workflow will automatically analyze it, write a story, generate consistent character images, generate scene illustrations, narrate it with AI audio, assemble the video, and upload it as a Private draft to your YouTube channel!
