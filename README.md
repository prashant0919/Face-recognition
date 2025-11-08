🧠 Face Recognition Attendance & Access Control System

An AI-powered attendance and access control system using FastAPI, React, and OpenCV.
The project automates attendance marking through facial recognition, allowing secure and contactless check-ins and check-outs.

🚀 Features

🔐 JWT-secured Admin Login

👤 Register Users via camera or image upload

🤖 Face Recognition Terminal for automatic IN/OUT marking

📅 Daily Attendance Logs

⏱️ Total Working Hours and Time Outside Calculation

📊 Overall & Personal Analytics with Charts

⚙️ Remote Control (Start / Pause / Shutdown the terminal)

🧾 User Management (Edit & Delete Users)

🏗️ System Architecture

Three-tier architecture:

Frontend (React + Tailwind + Recharts)
          ↓
Backend (FastAPI + SQLite)
          ↓
Face Recognition Terminal (Python + OpenCV + face_recognition)

Layer	Technology	Description
Frontend	React.js, Tailwind CSS	Admin dashboard & analytics
Backend	FastAPI, SQLAlchemy, SQLite	API & authentication layer
Terminal	Python, OpenCV, face_recognition	Face recognition at door camera
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/<your-username>/face-recognition-attendance.git
cd face-recognition-attendance

2️⃣ Backend Setup (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn backend:app --reload


Runs at http://127.0.0.1:8000

3️⃣ Frontend Setup (React)
cd frontend
npm install
npm run dev


Runs at http://localhost:5173

4️⃣ Face Recognition Terminal (Python)
cd kiosk
pip install opencv-python face_recognition numpy requests pytz
python kiosk.py


It automatically connects to the backend and updates attendance in real-time.

🧠 How It Works

Admin registers user via dashboard (camera or upload).

Backend stores user’s face embedding using face_recognition.

Terminal fetches encodings and detects faces in real-time.

When a known face appears:

First detection → IN

Next reappearance → OUT

Attendance and working hours are computed automatically.

Admin dashboard displays analytics, logs, and reports.

🧩 Key Modules
Module	Description
backend.py	Main FastAPI app for attendance APIs
kiosk.py	Python terminal for door-camera detection
App.jsx	React frontend for dashboard and analytics
auth.py	JWT authentication & password hashing
models.py	SQLAlchemy ORM models
schemas.py	Pydantic data schemas
🛡️ Security

Passwords stored as bcrypt hashes

Admin access via JWT tokens

Protected API endpoints

Only numerical face embeddings stored, no raw photos

CORS enabled for frontend communication

📈 Analytics Provided

Overall Summary:

Total users

Average working hours

Percentage present

Personal Summary:

Total hours worked

Time spent outside

👨‍💻 Authors
Name	Roll No	Role
Prashant Bastola	24MCI10266	AI Developer & Frontend
Kunwar Siddhant Rai	24MCI10095	Backend & Database Developer

Guide: Ms. Nisha Sharma
University Institute of Computing, Chandigarh University (Session 2025–26)

🧾 License

This project is licensed under the MIT License.
You are free to use and modify this project with proper attribution.
