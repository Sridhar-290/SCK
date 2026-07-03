# 🚀 Resume Matcher: Premium Analysis Dashboard

**Version:** 2.0 (Stable)  
**Developed by:** SCK  

---

## 📋 Project Overview
The **Resume Matcher** is a state-of-the-art web application designed to help job seekers bypass Applicant Tracking Systems (ATS) by providing deep, AI-driven insights into how well their resume matches specific job requirements. It uses a clean, **Glassmorphic UI** to deliver a premium user experience.

---

## ✨ Core Features

### 1. Standard Match Mode
*   **Role-Based Comparison:** Users select from a list of industry-standard roles (e.g., DevOps, AI Engineer, Full Stack).
*   **Intelligent Scoring:** The system calculates a % match based on weighted keywords (Must-have vs. Optional skills) stored in the database.
*   **Gap Analysis:** Instantly identifies missing keywords and provides actionable suggestions to improve the score.

### 2. AI JD Analyzer (Agent Mode)
*   **Dynamic Extraction:** Instead of pre-defined roles, users can paste a specific Job Description from any company.
*   **Smart "Agent" Insights:** The backend logic parses the JD in real-time to identify technical requirements and compares them to the user's resume.
*   **Lagging Indicators:** Highlights specific "Critical Missing Skills" that the user should learn or add to their resume.

### 3. User & History Management
*   **Secure Authentication:** A simple, secure Email and Full Name login system. 
*   **Persistent Dashboard:** Every scan is saved. Users can see their progress over time and revisit past evaluations.
*   **Privacy-First:** User data is stored in a local SQLite database, ensuring no third-party access to personal resumes.

### 4. Admin Command Center
*   A dedicated dashboard for administrators to monitor total users, global scan statistics, and a full log of every evaluation performed on the platform.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python (Flask) | Server-side logic, API routing, and score calculation. |
| **Database** | SQLite3 | Lightweight, persistent storage for users, roles, and history. |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Responsive UI with premium animations and glassmorphism. |
| **PDF Parser** | PyPDF | Used to extract raw text data from uploaded .pdf resumes. |
| **Architecture** | RESTful APIs | Clean communication between the frontend and backend. |

---

## 🏗️ Technical Architecture & Data Security

### Database Schema
1.  **`users`**: Securely stores Email and Full Name.
2.  **`job_roles`**: Maps specific roles to their descriptions.
3.  **`keywords`**: Stores weighted skill sets (Importance 1-3) for standard roles.
4.  **`assessments`**: Stores the 100% history of every scan, including scores and JSON-formatted results.

### Security Implementation
*   **Login Required Decorators**: Every analysis route is protected; data cannot be intercepted without a valid session.
*   **Data Persistence**: Tables are configured with `IF NOT EXISTS` logic. Data is never deleted during server restarts, ensuring long-term record keeping.

---

## 🎨 Design Philosophy
The UI follows a **"Modern Dark SaaS"** aesthetic:
*   **Glassmorphism**: Translucent cards with blur effects for depth.
*   **Dynamic UI**: Floating background blobs and smooth fade-in animations.
*   **Mobile-First**: Fully responsive layouts that work perfectly on smartphones and tablets.

---

## 🚀 How to Launch
1.  Initialize Database: `python init_db.py`
2.  (Optional) Create Admin: `python create_admin.py <email> <name>`
3.  Run Server: `python app.py`
4.  Access: `http://127.0.0.1:5000`

---
**Developed by SCK © 2026**