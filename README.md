# PDF Chatbot with Chatwoot Integration

This project is an AI-powered chatbot that answers questions based on the content of uploaded PDF documents. It features a Streamlit web interface for PDF upload and chat, and integrates with [Chatwoot](https://www.chatwoot.com/) to provide real-time conversational support via a website widget or any Chatwoot inbox.

---

## Features

- **PDF Knowledge Base:** Upload PDFs and ask questions about their content.
- **AI-Powered Answers:** Uses a Retrieval-Augmented Generation (RAG) pipeline for accurate responses.
- **Streamlit Interface:** User-friendly web UI for uploading documents and chatting.
- **Chatwoot Integration:** Seamless support via Chatwoot widget or inbox, with bot replies powered by your AI.
- **Configurable via `.env`:** All sensitive and environment-specific settings are managed via environment variables.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/rishishanbhag/pdf-chatbot-chatwoot.git
cd pdf-chatbot-chatwoot/CWP
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `CWP` directory with the following content:

```env
# Chatwoot Configuration
CHATWOOT_URL=https://your-chatwoot-domain/
CHATWOOT_API_TOKEN=your_chatwoot_api_token
CHATWOOT_ACCOUNT_ID=your_account_id

# FastAPI Configuration (optional)
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_SERVER_URL=http://localhost:8000

# API keys (if needed)
YOUR_API_KEY=your_api_key_here

# Webhook URL (for external access)
WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app
```

### 4. Run the FastAPI Server

```bash
python fastapi_server.py
```

### 5. Run the Streamlit App

```bash
streamlit run app.py
```

### 6. (Optional) Expose FastAPI Server for Webhooks

If running locally, use [ngrok](https://ngrok.com/) to expose your FastAPI server:

```bash
ngrok http 8000
```
Update your Chatwoot webhook URL to use the generated ngrok URL.

---

## Chatwoot Integration

1. **Add the Chatwoot Widget to Streamlit:**  
   Insert the provided JavaScript snippet or use an iframe in your Streamlit app to enable the chat widget.

2. **Configure Chatwoot Webhook:**  
   - Go to Chatwoot Dashboard → Settings → Webhooks.
   - Add a webhook pointing to `https://your-ngrok-url.ngrok-free.app/chatwoot-webhook`.
   - Select "Message Created" event.

3. **Create/Configure Bot:**  
   - Go to Settings → Agent Bots.
   - Add a new bot with the outgoing URL set to your webhook endpoint.
   - Set the bot status to **Online**.
   - Add the bot to your inbox as a collaborator.

---

## Usage

- **Upload PDFs** in the Streamlit interface.
- **Ask questions** in the Streamlit chat or via the Chatwoot widget.
- **Get instant answers** powered by your AI model and PDF knowledge base.

---

## Endpoints

- `POST /chat` — Ask a question (used by both Streamlit and Chatwoot)
- `POST /answer` — Store answers (internal)
- `POST /chatwoot-webhook` — Receives Chatwoot messages and triggers bot replies
- `GET /answers/all` — View all stored answers
- `GET /answers/latest` — View the latest answer
- `GET /` — API root with navigation

---

## Troubleshooting

- **Bot not replying in Chatwoot?**  
  - Ensure the webhook URL is correct and accessible.
  - Make sure the bot is set to **Online** in Chatwoot.
  - Check FastAPI logs for errors.

- **PDF answers not accurate?**  
  - Ensure PDFs are processed in Streamlit before asking questions.

---

## License

MIT License

---

## Credits

- [Chatwoot](https://www.chatwoot.com/)
