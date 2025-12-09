---
title: Feedback System API
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# Feedback System API
Production-grade AI-powered feedback system with sentiment analysis.


# 🤖 AI-Powered Feedback System

A production-ready, dual-dashboard feedback platform with AI-powered response generation, sentiment analysis, and real-time analytics. Built with FastAPI, MongoDB, Groq LLM, and Streamlit.

---

## 🌐 Live Deployments

- **User Dashboard:** [https://user-feedback.streamlit.app](https://user-feedback.streamlit.app)
- **Admin Dashboard:** [https://feedback-dashboard.streamlit.app](https://feedback-dashboard.streamlit.app)
- **Backend API:** [https://nachikxt91-feedback-api.hf.space/docs](https://nachikxt91-feedback-api.hf.space/docs)

**Admin API Key:** `HuhclC1_E2fy146SNVET6lDr93YriOW2PVOJT8wyBXQ`

---

## 📋 Executive Summary

A three-tier production system enabling users to submit ratings and reviews through a public interface while administrators monitor submissions with AI-enriched insights through a secure dashboard. The system leverages Groq's Llama 3.3 70B for real-time response generation, automated sentiment analysis, and actionable recommendations.

**Development Time:** 2 days

---

## 🏗️ System Architecture

### Three-Tier Architecture

**Frontend Layer:**
- User Dashboard (Streamlit)
- Admin Dashboard (Streamlit)

**Backend API:**
- FastAPI with async LLM integration
- OpenAPI auto-documentation

**Data Layer:**
- MongoDB Atlas (cloud database)

### Data Flow

User → Streamlit UI → FastAPI Backend → MongoDB
↓
Groq LLM API
↓
AI Enrichments


### User Journey Flow

1. User visits public dashboard
2. Selects rating (1-5 stars) via slider or star buttons
3. Writes review (10-1000 characters)
4. Submits feedback
5. Receives instant AI-personalized response

### Admin Journey Flow

1. Admin logs in with API key
2. Views real-time analytics dashboard
3. Filters feedback by rating, sentiment, or date
4. Reviews AI-enriched summaries and recommendations
5. Exports data for further analysis

---

## 🛠️ Tech Stack & Justification

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend API | FastAPI | Async support for concurrent LLM calls, auto-generated OpenAPI docs |
| Database | MongoDB Atlas | Schema flexibility, free M0 cluster, global availability |
| LLM Service | Groq (Llama 3.3 70B) | Fastest inference speed, free tier, high-quality outputs |
| User Dashboard | Streamlit | Rapid prototyping, no frontend expertise needed |
| Admin Dashboard | Streamlit | Consistent stack, built-in widgets for analytics |
| Deployment | HuggingFace Spaces + Streamlit Cloud | Zero-cost hosting, automatic deployments |

---

## ✨ Features Implemented

### User Dashboard

- **Interactive Rating:** Dual input (slider + star buttons) with synchronized state
- **Character Validation:** 10-1000 character limit with live counter
- **AI Response:** Instant personalized acknowledgment based on rating and review content
- **Error Handling:** Timeout, connection, and validation error messages
- **Responsive Design:** Custom CSS with cyberpunk-inspired UI

### Admin Dashboard

- **Authentication:** API key-based access control
- **Real-time Metrics:**
  - Total feedback count
  - Average rating with trend indicators
  - Positive sentiment rate
  - Last sync timestamp

- **Interactive Visualizations:**
  - Rating distribution (radar chart)
  - Sentiment gauge (0-100% positive rate)

- **Advanced Filtering:**
  - Rating filter (1-5 stars)
  - Sentiment filter (Positive/Neutral/Negative)
  - Date range selector
  - Full-text search across reviews and summaries

- **AI Enrichments:**
  - Concise summary (admin-focused)
  - Actionable recommendations
  - Sentiment classification
  - Auto-processing: Unprocessed feedback automatically enriched on first admin view

---

## 📡 API Endpoints

### Public Endpoints

**POST /api/feedback** - Submit new feedback
- Request Body:
  - `rating` (int): 1-5 stars
  - `review` (string): 10-1000 characters
- Response: AI-generated personalized message

**GET /api/feedback/health** - Health check
- Response: System status

### Protected Endpoints

Requires `X-API-Key` header with admin API key

**GET /api/admin/analytics** - Dashboard metrics
- Response: Total count, average rating, sentiment distribution, last sync

**GET /api/admin/feedbacks?limit=100** - All feedback with enrichments
- Query Parameters:
  - `limit` (int): Max results
  - `rating` (int): Filter by rating
  - `sentiment` (string): Filter by sentiment
- Response: Array of feedback with AI summaries, actions, sentiment

---

## 🧠 LLM Prompting Strategy

### User Response (Temperature 0.7)
- Warm, conversational tone
- Acknowledgment based on rating sentiment
- 2-3 sentences maximum

### Admin Summary (Temperature 0.3)
- Single-sentence factual summary
- Focuses on actionable insights

### Action Items (Temperature 0.5)
- 2-3 numbered recommendations
- Specific and implementable

### Sentiment Analysis (Temperature 0.1)
- One-word output: Positive/Neutral/Negative
- High consistency for analytics

---

## ⚙️ System Behavior

### User Submission Flow

1. User selects rating (1-5 stars) and writes review (10+ characters)
2. Frontend sends POST request to `/api/feedback`
3. Backend calls Groq LLM to generate personalized response
4. Feedback stored in MongoDB with `processed: false`
5. AI response returned to user immediately

### Admin Processing Flow

1. Admin dashboard fetches all feedback via `/api/admin/feedbacks`
2. Backend identifies unprocessed entries
3. Three parallel LLM calls: summary, actions, sentiment
4. Results stored in MongoDB with `processed: true`
5. Future requests serve cached data

### Performance Metrics

- **Average submission response time:** 2-3 seconds
- **Admin enrichment time:** 4-6 seconds (parallel processing)
- **Concurrent user capacity:** 50+ (FastAPI async)

---

## 🚀 Local Development Setup

### Backend Setup

1. Clone the repository:
   `git clone https://github.com/Nachikxt91/feedback-backend.git`
   `cd feedback-backend`

2. Install dependencies:
   `pip install -r requirements.txt`

3. Configure environment variables (create `.env` file):
   `GROQ_API_KEY=your_groq_api_key`
   `MONGODB_URI=your_mongodb_connection_string`
   `ADMIN_API_KEY=your_admin_secret_key`
   `MODEL_NAME=llama-3.3-70b-versatile`

4. Run the backend:
   `uvicorn app.main:app --reload --port 8000`

   Backend available at [**http://localhost:8000**](http://localhost:8000)

### User Dashboard Setup

1. Navigate to user dashboard:
   `cd user-dashboard`

2. Install dependencies:
   `pip install -r requirements.txt`

3. Configure environment (create `.env` file):
   `API_URL=http://localhost:8000`

4. Run the dashboard:
   `streamlit run app.py`

   Dashboard available at [**http://localhost:8501**](http://localhost:8501)

### Admin Dashboard Setup

1. Navigate to admin dashboard:
   `cd admin-dashboard`

2. Install dependencies:
   `pip install -r requirements.txt`

3. Configure environment (create `.env` file):
   `API_URL=http://localhost:8000`
   `ADMIN_API_KEY=your_admin_secret_key`

4. Run the dashboard:
   `streamlit run app.py`

   Dashboard available at [**http://localhost:8502**](http://localhost:8502)

---

## 🎯 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **MongoDB over CSV/JSON** | Scalability, concurrent writes, cloud-native |
| **Groq over OpenAI** | Free tier, faster inference (2x-3x), sufficient quality for task |
| **Lazy admin enrichment** | Reduces LLM costs, faster user responses |
| **Streamlit over React** | Faster development, Python-native, no frontend skills needed |
| **API-first architecture** | Enables future mobile/web clients, clean separation of concerns |
| **Parallel LLM processing** | 3 admin enrichments in parallel reduces latency by 60% |
| **Character limits (10-1000)** | Prevents spam, ensures quality feedback |

---

## 📊 Project Statistics

- **Total Lines of Code:** ~1,200
- **API Endpoints:** 4
- **LLM Calls per User Submission:** 1
- **LLM Calls per Admin View (unprocessed):** 3 (parallel)
- **Deployment Platforms:** 3 (HuggingFace, Streamlit Cloud x2)
- **Database Collections:** 1 (feedbacks)

---

## 🔮 Future Enhancements

- Email notifications for admins on negative feedback
- Multi-language support for international users
- Export analytics as PDF reports
- User authentication for personalized feedback history
- Webhook integrations (Slack, Discord)
- Fine-tuned sentiment model for domain-specific accuracy
- A/B testing framework for prompt optimization

---

## 🧪 Testing Results

### From Task 1 (Yelp Dataset - 200 reviews)

| Metric | Zero-Shot | Chain-of-Thought |
|--------|-----------|------------------|
| JSON Validity | 100% | 99.5% |
| Exact Match | 64.5% | 64.8% |
| Within-1 Accuracy | 99.0% | 99.0% |
| MAE | 0.375 | 0.372 |

**Chosen Approach:** Chain-of-Thought for best accuracy and explainability

---

## 🧾 License

MIT License © 2025  
Developed by **Nachiket (Nachikxt91)**  
For **Fynd AI Internship Assessment**

---

## 📞 Contact

- **GitHub:** [Nachikxt91](https://github.com/Nachikxt91)
- **LinkedIn:** [Nachiket Sarode](https://www.linkedin.com/in/nachiket-sarode-8979a9257/)

---

## 🙏 Acknowledgments

- **Groq** for providing fast LLM inference
- **MongoDB Atlas** for free cloud database hosting
- **Streamlit** for rapid dashboard development
- **HuggingFace Spaces** for free backend deployment





