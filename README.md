# 🚢 Captain Cargo

**The voice agent that actually knows where your package is.**

You know the drill. You call customer support, wait 10 minutes on hold, finally get through, and then... "Could you hold while I check that?" 😤

Captain Cargo is different. Pick up the phone, ask "Where's my stuff?", and get an answer in milliseconds. No hold music. No sighing. Just your package status.

Built with FastAPI + Vapi + Sanity.io. Tested with 75 tests. Deployed and ready to go.

---

## 🎯 What Does This Do?

Imagine this:

> **You:** "Hey, where's my package?"  
> **Captain Cargo:** "Your package TRK123456789 is on its way! Expected delivery: tomorrow by 5 PM."  
> **You:** "Thanks!"  
> **Captain Cargo:** "You're welcome! 🚚"

That's it. That's the whole interaction. No menus, no "press 1 for...", no "your call is important to us."

---

## ✨ Why Captain Cargo?

| Feature | What It Means For You |
|---------|----------------------|
| 🤖 **Conversational** | Talk like a human, get human answers |
| 🛡️ **Bulletproof** | Circuit breaker, retries, cache — won't crash when your database sneezes |
| 📊 **Observable** | Health checks, metrics, logs — know what's happening |
| 🎪 **Hallucination-Safe** | Only tells you what the database actually says |
| 🧪 **Tested** | 75 tests. Every. Single. One. Passes. |

---

## 🚀 Get It Running

### One-Line Setup

```bash
git clone https://github.com/Koushik0901/Captain-Cargo---AI-Delivery-Tracking-System.git
cd Captain-Cargo---AI-Delivery-Tracking-System
pip install -r requirements.txt
cp .env.example .env  # Fill in your Sanity credentials
```

### Start the Server

```bash
# For development (auto-reload on changes)
uvicorn server:app --reload

# For production
python server.py
```

Your webhook will be live at `http://127.0.0.1:8000/webhook` 🎉

---

## 🔧 Configuration

Captain Cargo needs to know where your data lives. Here's the deal:

| Variable | What It Is | Default | Required? |
|---------|-----------|---------|-----------|
| `SANITY_PROJECT_ID` | Your Sanity project ID | — | ✅ Yes |
| `SANITY_DATASET` | Which dataset to query | `production` | ❌ |
| `SANITY_API_TOKEN` | Read-only API token | — | ✅ Yes |
| `CACHE_TTL` | How long to cache results (seconds) | `60` | ❌ |
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR | `INFO` | ❌ |

Drop these in your `.env` file and you're golden.

---

## 📡 API Endpoints

### Health Checks — "Is this thing on?"

```bash
# Kubernetes liveness probe
curl http://localhost:8000/healthz
# → {"status":"ok"}

# Readiness (includes dependency status)
curl http://localhost:8000/readyz
# → {"status":"ready","dependencies":{"circuit_breaker":"closed","failure_count":0}}

# Metrics for monitoring
curl http://localhost:8000/metrics
# → {"requests_total":100,"cache_hits_total":60,"cache_hit_rate":0.6,...}
```

### The Main Event — Vapi Webhook

```json
POST /webhook

{
  "message": {
    "content": "Where's my package ABC123?",
    "toolCalls": [
      {
        "function": {
          "name": "track_delivery",
          "arguments": "{\"trackingId\": \"ABC123\"}"
        }
      }
    ]
  }
}
```

Response:

```json
{
  "status": "success",
  "message": "Your package ABC123 is in transit.",
  "delivery_details": {
    "tracking_number": "ABC123",
    "status": "in_transit",
    "estimated_delivery": "2024-01-16T17:00:00Z"
  }
}
```

---

## 🏗️ Under the Hood

```
                    📞 CALLER
                        │
                        ▼
                ┌───────────────┐
                │     VAPI      │  ← Speech → Text, Text → Speech
                │   (The Voice)  │
                └───────┬───────┘
                        │
                        │ POST /webhook 📩
                        ▼
                ┌───────────────┐
                │  CAPTAIN CARGO │  ← FastAPI webhook handler
                │   (The Brain) │
                └───────┬───────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
           ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   🗄️     │  │   📊     │  │   📝     │
    │  Cache   │  │ Metrics  │  │  Logger  │
    │ (60s TTL)│  │          │  │          │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                ┌───────────────┐
                │    SANITY     │  ← Your delivery data
                │     CMS       │
                └───────────────┘
```

---

## 🧪 Testing (Because We Care)

```bash
# Run all 75 tests
pytest tests/ -v

# 75 passed in 3.67s 🎉
```

### Test Coverage

| Category | What It Tests |
|----------|---------------|
| 🧱 Unit | Individual functions and classes |
| 📝 Contract | Pydantic model validation |
| 🔗 Integration | Full request/response cycles |

---

## 🎭 Evaluation Harness

Think of this as a "simulated caller" that runs through dozens of scenarios and scores Captain Cargo:

```bash
python scripts/eval_replay.py \
  --input eval/cases.jsonl \
  --server http://localhost:8000 \
  --report eval/report.md
```

Sample output:

```
Total Cases: 50 | Passed: 47 | Accuracy: 94%
Avg Latency: 127ms | P95 Latency: 312ms
```

Check out [eval/report.md](eval/report.md) for a real example.

---

## 🎬 Demo Video

**Watch Captain Cargo in action →** [Demo Video](https://your-demo-video-url)

Shows: User calls → Agent asks tracking ID → Tool call → Status response → Fallback when backend's down

---

## 🗣️ The Conversation Flow

### Happy Path 🦄

```
📞 Caller: "Where's my package?"

🤖 Vapi (STT): "Where's my package?"
🤖 Vapi (NLU): Intent: track_delivery

🤖 Vapi → Captain Cargo: POST /webhook {trackingId: "ABC123"}

📦 Captain Cargo → Sanity: "Give me ABC123"
📦 Sanity → Captain Cargo: {status: "in_transit", ...}

🤖 Captain Cargo → Vapi: {message: "Your package is in transit!"}

🤖 Vapi (TTS): "Your package ABC123 is in transit!"
📞 Caller: "Oh great, thanks!"
```

### When Things Go Wrong 😬

```
📞 Caller: "Where's TRK999?"

🤖 Vapi → Captain Cargo: POST /webhook {trackingId: "TRK999"}

⚡ Captain Cargo → Sanity: (circuit breaker OPEN - Sanity is down)

🤖 Captain Cargo → Vapi: {status: "fallback", message: "Having trouble accessing latest data..."}

🤖 Vapi (TTS): "I'm having trouble accessing the latest data. Please try again in a moment."
📞 Caller: "Okay, thanks anyway."
```

---

## 🎛️ Vapi Provider Configuration

Captain Cargo is **provider-agnostic**. Your webhook doesn't care about voice stuff — Vapi handles all that.

### Speech-to-Text (STT) — "What did they say?"

| Provider | When To Use | Setup |
|----------|-------------|-------|
| **Deepgram** | Fast & accurate | Vapi Dashboard → Add Deepgram Key |
| **AssemblyAI** | Good streaming | Vapi Dashboard → Add AssemblyAI Key |
| **OpenAI Whisper** | Highest accuracy | Vapi Dashboard → Add OpenAI Key |

### Text-to-Speech (TTS) — "What should I say?"

| Provider | When To Use | Setup |
|----------|-------------|-------|
| **ElevenLabs** | Natural, emotional voices | Vapi Dashboard → Add ElevenLabs Key |
| **OpenAI** | Fast, decent quality | Vapi Dashboard → Add OpenAI Key |
| **Azure** | Enterprise needs | Vapi Dashboard → Add Azure Key |

### Want to Switch Providers?

1. Go to Vapi Dashboard
2. Pick your provider
3. Enter API key
4. **That's it.** Captain Cargo doesn't need to know. 😎

---

## 🏢 Project Structure

```
captain-cargo/
├── server.py                 # FastAPI entry point 🚪
├── requirements.txt          # Python packages 📦
├── .env.example              # Environment template 📝
├── README.md                 # You are here 👋
├── specs/                    # Master plans 🗺️
│   └── 001-voice-agent-prod/
├── models/                   # Pydantic models 🧱
│   ├── webhook.py           # Webhook payload shapes
│   └── delivery.py          # Delivery entity shapes
├── services/                 # Business logic 🧠
│   ├── cache.py             # 60s TTL cache
│   ├── sanity_client.py     # Sanity API + circuit breaker
│   └── response_builder.py   # Hallucination-safe responses
├── middleware/               # HTTP middleware 🍵
│   ├── correlation.py       # Correlation IDs
│   └── validation.py        # Request validation
├── utils/                    # Utilities 🛠️
│   ├── config.py            # Environment validation
│   ├── logger.py            # JSON structured logs
│   └── normalization.py     # Tracking ID cleaning
├── endpoints/               # API endpoints 🔌
│   ├── health.py            # /healthz, /readyz
│   └── metrics.py           # /metrics
├── scripts/                  # Tools 🔧
│   └── eval_replay.py      # Evaluation harness
└── tests/                    # 75 tests passing ✅
    ├── unit/
    ├── contract/
    └── integration/
```

---

## 🚀 Deployment

### Docker (One Command)

```bash
docker build -t captain-cargo .
docker run -p 8000:8000 \
  -e SANITY_PROJECT_ID=xxx \
  -e SANITY_API_TOKEN=xxx \
  captain-cargo
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: captain-cargo
spec:
  replicas: 3
  containers:
  - name: captain-cargo
    image: captain-cargo-agent
    ports: [8000]
    env:
    - name: SANITY_PROJECT_ID
      valueFrom:
        secretKeyRef:
          name: sanity-creds
          key: project-id
```

---

## 🧑‍💻 Contributing

See [AGENTS.md](AGENTS.md) for guidelines. We're friendly! 🙌

---

## 📄 License

MIT. Go forth and ship! 🚢

---

**Captain Cargo** — Because your customers deserve to know where their stuff is. 📦✨
