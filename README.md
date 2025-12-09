---
title: Feedback System API
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# 🚀 Feedback System API

The **Feedback System API** powers the AI-driven sentiment feedback platform, enabling analysis of user reviews and generating star-based ratings using LLMs.  
Deployed via **Hugging Face Spaces** using a containerized FastAPI backend.

---

## 🔍 Overview

This backend handles feedback collection, LLM-based sentiment inference, and structured output in JSON. It connects seamlessly with both **User** and **Admin Dashboards** for real-time feedback visualization and management.

---

## ⚙️ Features

- LLM-driven sentiment & rating prediction  
- JSON-structured responses for ease of integration  
- Pinecone / Firebase integration (optional)  
- RESTful API endpoints for feedback CRUD operations  
- Configured for Hugging Face Spaces deployment via Docker  
- Chain-of-thought prompting for explainable predictions  

---

## 🧠 LLM Configuration

- **Model:** Llama-3.1-8b-instant (via Groq API)  
- **Temperature:** 0.1 (consistency)  
- **Max Tokens:** 250  
- **Structured Output:** JSON with explanation  

---

## 🏗️ Local Development Setup

### 1. Clone Repository
git clone https://github.com/Nachikxt91/feedback-backend.git  
cd feedback-backend

### 2. Set Up Python Environment
python -m venv venv  
source venv/bin/activate  # (Windows: venv\Scripts\activate)  
pip install -r requirements.txt

### 3. Configure Environment Variables
Create a `.env` file in the root directory:

# Groq LLM Configuration  
GROQ_API_KEY=your_groq_api_key_here  
MODEL_NAME=llama-3.1-8b-instant  

# Pinecone (Optional)  
PINECONE_API_KEY=your_pinecone_api_key_here  
PINECONE_INDEX_NAME=feedback-index  

# Server Configuration  
PORT=7860

### 4. Run the App Locally
python main.py

The API will be available at [**http://localhost:7860**](http://localhost:7860)

---

## ☁️ Deployment (Hugging Face Spaces)

This repository is pre-configured for Hugging Face Spaces.  
Simply set the environment variables in your Space secrets and push your Docker build.

---

## 📊 Key Metrics (from Testing)

| Metric | Zero-Shot | CoT |
|---------|------------|-----|
| JSON Validity | 100% | 99.5% |
| Exact Match | 64.5% | 64.8% |
| MAE | 0.375 | 0.372 |

---

## 📚 References

- [Yelp Dataset (Kaggle)](https://www.kaggle.com/datasets/yelp-dataset/yelp-dataset)
- [Groq API](https://console.groq.com/)
- [Hugging Face Spaces](https://huggingface.co/spaces)

---

## 🧾 License

MIT License © 2025  
Developed by **Nachiket & Fynd AI Team**

---

# 🌟 Feedback User Dashboard

The **User Dashboard** is the interactive front-end interface where customers can provide feedback, view AI-generated sentiment summaries, and receive real-time rating predictions.

---

## 🧩 Tech Stack

- **Frontend Framework:** React (with Expo / React Native Web support)  
- **Styling:** TailwindCSS or Styled Components  
- **API Integration:** Feedback Backend (Hugging Face Spaces)  
- **Deployment:** Vercel / Expo  
- **State Management:** Context API / Redux (optional)

---

## 🚀 Features

- Submit and view feedback in real-time  
- LLM-powered sentiment response visualization  
- Intuitive and responsive UI  
- Firebase Authentication integration  
- Cloudinary image upload  
- Supports both web and mobile via Expo  

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
git clone https://github.com/Nachikxt91/feedback-user-dashboard.git  
cd feedback-user-dashboard

### 2. Install Dependencies
npm install  
# or  
yarn install

### 3. Configure Environment Variables
Create a `.env` file in the root directory:

# Backend API Endpoint  
EXPO_PUBLIC_API_URL=https://your-feedback-backend.hf.space  

# Firebase Configuration  
EXPO_PUBLIC_FIREBASE_API_KEY=your_api_key  
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com  
EXPO_PUBLIC_FIREBASE_PROJECT_ID=your_project_id  
EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com  
EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id  
EXPO_PUBLIC_FIREBASE_APP_ID=your_app_id  

# Cloudinary Configuration  
CLOUDINARY_API_KEY=your_cloudinary_key  
CLOUDINARY_API_SECRET=your_cloudinary_secret  
CLOUDINARY_CLOUD_NAME=your_cloud_name

### 4. Run the App
npx expo start

- Press **i** for iOS  
- Press **a** for Android  
- Scan QR Code with Expo Go

---

## 🖥️ UI Overview

- **📝 Feedback Input:** Submit textual or image-based feedback  
- **⭐ Rating Display:** Shows LLM-generated star ratings  
- **📈 History:** Retrieve past feedback submitted by user  
- **💬 Explanation:** AI-generated reasoning behind star rating  

---

## 🧠 Backend Integration

This dashboard communicates directly with the **Feedback Backend API** deployed via Hugging Face Spaces for rating and sentiment prediction.

---

## 🧾 License

MIT License © 2025  
Developed by **Nachiket & Fynd AI Team**

---

# 🛠️ Feedback Admin Dashboard

The **Admin Dashboard** provides tools to monitor, analyze, and manage user feedback collected through the feedback system. It integrates with the backend API for data insights and system configuration.

---

## 🧩 Tech Stack

- **Framework:** React.js / Next.js  
- **Charts & Visualization:** Chart.js or Recharts  
- **Backend API:** Feedback Backend (Hugging Face Spaces)  
- **Authentication:** Firebase Admin SDK  
- **Deployment:** Vercel / Netlify  

---

## 🚀 Features

- View and filter user feedback by sentiment or rating  
- Track model performance (Exact Accuracy, MAE, etc.)  
- Analytics dashboard for sentiment distribution  
- Manage users and configure API keys  
- Export feedback data as CSV / JSON  

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
git clone https://github.com/Nachikxt91/feedback-admin-dashboard.git  
cd feedback-admin-dashboard

### 2. Install Dependencies
npm install  
# or  
yarn install

### 3. Configure Environment Variables
Create a `.env` file with the following configuration:

# Backend API Endpoint  
NEXT_PUBLIC_API_URL=https://your-feedback-backend.hf.space  

# Firebase Configuration  
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key  
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com  
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id  
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com  
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id  
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id  

# Admin Role Key  
ADMIN_SECRET_KEY=your_admin_secret_key

### 4. Run Locally
npm run dev

The dashboard will be available at [**http://localhost:3000**](http://localhost:3000)

---

## 📊 Dashboard Modules

- **📈 Analytics:** View distribution of sentiment & ratings  
- **🗂️ Review List:** Browse all collected feedback  
- **🧠 Model Performance:** Displays accuracy & MAE from evaluation pipeline  
- **⚙️ Admin Settings:** Manage keys, thresholds, and access controls  

---

## ⚡ Deployment

Deploy easily on:
- [Vercel](https://vercel.com/)
- [Hugging Face Spaces (Gradio/Streamlit UI)](https://huggingface.co/spaces)
- [Netlify](https://www.netlify.com/)

---

## 🧾 License

MIT License © 2025  
Developed by **Nachiket & Fynd AI Team**
