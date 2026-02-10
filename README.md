# 🚀 AI-Powered Feedback System - Backend

FastAPI backend with MongoDB and Groq LLM integration for intelligent feedback collection and analysis.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb)
![Groq](https://img.shields.io/badge/AI-Groq_LLama_3.3-FF6B35?style=flat-square)

## ✨ Features

- **AI-Powered Responses**: Automatic, contextual responses using Groq LLM (LLama 3.3 70B)
- **Sentiment Analysis**: Real-time sentiment classification (Positive/Neutral/Negative)
- **Smart Summaries**: AI-generated summaries for admin review
- **Actionable Insights**: Auto-generated action items based on feedback
- **Real-time Analytics**: Rating distribution, sentiment breakdown, trend analysis
- **Async MongoDB**: Fast, scalable database operations with Motor
- **Protected Admin Routes**: Secure API key authentication

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- [Groq API Key](https://console.groq.com/)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo MONGODB_URL=mongodb+srv://your-connection-string > .env
echo MONGODB_DB_NAME=feedback_db >> .env
echo GROQ_API_KEY=gsk_your_api_key >> .env
echo API_KEY=your_admin_api_key >> .env

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

📍 API Docs: http://localhost:8000/docs

## 🔌 API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/feedback` | Submit new feedback |
| `GET` | `/api/health` | Health check |

### Admin Endpoints (Requires `X-API-Key` header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/feedbacks` | Get all feedbacks with AI analysis |
| `GET` | `/api/admin/analytics` | Get analytics dashboard data |

### Example: Submit Feedback

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "review": "Excellent service, very responsive!"}'
```

### Example Response

```json
{
  "id": "507f1f77bcf86cd799439011",
  "rating": 5,
  "review": "Excellent service, very responsive!",
  "sentiment": "positive",
  "summary": "Positive feedback highlighting responsive service",
  "response": "Thank you for your wonderful feedback! We're thrilled to hear you found our service responsive...",
  "action_items": ["Continue maintaining high response times"],
  "timestamp": "2026-02-10T17:00:00Z"
}
```

## 🔧 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGODB_URL` | MongoDB connection string | ✅ | - |
| `MONGODB_DB_NAME` | Database name | ❌ | feedback_db |
| `GROQ_API_KEY` | Groq LLM API key | ✅ | - |
| `API_KEY` | Admin dashboard auth key | ✅ | - |
| `GROQ_MODEL` | LLM model to use | ❌ | llama-3.3-70b-versatile |

## 📦 Project Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # MongoDB connection
│   ├── schemas.py           # Pydantic models
│   ├── routers/
│   │   ├── feedback.py      # User feedback endpoints
│   │   └── admin.py         # Admin endpoints (protected)
│   ├── services/
│   │   ├── feedback_service.py
│   │   └── llm_service.py
│   └── utils/               # Utilities & exceptions
├── requirements.txt
└── Dockerfile
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t feedback-backend .

# Run container
docker run -p 8000:7860 --env-file .env feedback-backend
```

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.115
- **Database**: MongoDB Atlas with Motor (async driver)
- **AI**: Groq Cloud (LLama 3.3 70B Versatile)
- **Validation**: Pydantic v2
- **Server**: Uvicorn

## 📄 License

MIT License - feel free to use this for your own projects!
