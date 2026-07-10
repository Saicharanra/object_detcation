# Open-Vocabulary Object Detection Web App (YOLO-World)

This repository contains a production-ready, open-vocabulary object detection application. Users can upload images, specify custom text prompts (e.g. "laptop", "red bottle", "keyboard"), run detection using the state-of-the-art **YOLO-World** model, view interactive bounding box overlays with latency reports, and review historical runs on a Chart.js-powered analytics dashboard.

All user profiles, uploaded images (original + annotated), detection statistics, and history are synchronized with **Supabase (Auth, Storage, and PostgreSQL)**.

---

## Technical Architecture

* **Frontend**: React (Vite), Tailwind CSS v3, React Router v6, Axios, React Query (TanStack), Chart.js (react-chartjs-2), Lucide Icons.
* **Backend**: Python, FastAPI, SQLAlchemy ORM, Supabase Python SDK, YOLO-World (via Ultralytics), OpenCV, Pillow, PyTorch.
* **Database & Storage**: Supabase PostgreSQL (with automatic user syncing and live analytics triggers), Supabase Storage.

---

## Folder Structure

```
.
├── supabase/                      # Database configuration scripts
│   ├── schema.sql                 # PostgreSQL tables, triggers, and functions
│   ├── storage-policies.sql       # Storage bucket initialization and RLS
│   └── auth-policies.sql          # Table RLS policies (user data isolation)
├── backend/                       # FastAPI application
│   ├── app/
│   │   ├── api/                   # Auth, Detection, and Analytics routers
│   │   ├── database/              # SQLAlchemy session setup
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── services/              # Supabase storage and processing pipelines
│   │   ├── ml/                    # YOLO-World model management
│   │   ├── config.py              # Environment configuration loader
│   │   └── main.py                # FastAPI entry point
│   ├── requirements.txt           # Python packages
│   └── .env                       # Local environment variables
└── frontend/                      # React application
    ├── src/
    │   ├── components/            # Navbar, DragDropUpload, BoundingBoxViewer
    │   ├── pages/                 # Dashboard, History, Profile, Login, Signup
    │   ├── hooks/                 # useAuth context hook
    │   ├── services/              # api client and supabase client config
    │   ├── index.css              # Custom Tailwind styles and animations
    │   ├── App.jsx                # Router, guards, and Providers setup
    │   └── main.jsx               # Render mounting point
    ├── tailwind.config.js         # Tailwind configuration
    ├── package.json               # Node modules list
    └── .env                       # React client variables
```

---

## Getting Started

### 1. Supabase Project Setup

1. Create a new project on [Supabase](https://supabase.com).
2. Navigate to **SQL Editor** in your Supabase dashboard and run the scripts in order:
   * **First**: Run the SQL inside `supabase/schema.sql` (Creates public tables, hooks the user signup triggers, and sets up live analytics).
   * **Second**: Run the SQL inside `supabase/storage-policies.sql` (Creates the `object-detection` storage bucket and enables authenticated folder uploads).
   * **Third**: Run the SQL inside `supabase/auth-policies.sql` (Secures database tables using Row Level Security policies).

### 2. Backend Setup (FastAPI)

1. Open your terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Set up a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the `.env` template and fill in your Supabase credentials:
   * `SUPABASE_URL`: Project URL (Settings -> API)
   * `SUPABASE_KEY`: Project Anon Public Key (Settings -> API)
   * `SUPABASE_SERVICE_ROLE_KEY`: Service Role Key (Settings -> API -> `service_role` secret key. Needed by the backend to bypass RLS to upload user files).
   * `SUPABASE_JWT_SECRET`: JWT Secret (Settings -> API -> JWT Secret. Needed to verify tokens locally).
   * `DATABASE_URL`: Transaction connection string (Settings -> Database -> Connection string -> Connection Pooler -> Transaction mode).
5. Start the backend:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   *The YOLO-World model will be downloaded automatically (first time) and loaded into memory on startup.*

### 3. Frontend Setup (React)

1. Open a new terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Copy the `.env` template and fill in:
   * `VITE_SUPABASE_URL`: Your Supabase Project URL.
   * `VITE_SUPABASE_ANON_KEY`: Your Supabase public anon key.
   * `VITE_API_URL`: `http://localhost:8000` (FastAPI development URL).
4. Run the Vite development server:
   ```bash
   npm run dev
   ```
5. Open `http://localhost:5173` in your browser.

---

## Best Practices & Security

1. **Authentication**: All endpoints (except login/signup) require a valid Supabase JWT Bearer token in the `Authorization` header. The backend validates this token locally via the project's `SUPABASE_JWT_SECRET` (extremely fast, no API round-trips) or queries Supabase Auth as a fallback.
2. **Data Isolation**: Database Row-Level Security (RLS) is enabled on all tables. Users can only select or delete records where `user_id = auth.uid()`.
3. **Storage Security**: Files in Supabase Storage are structured inside `object-detection/{user_id}/`. Storage policies assert that users can only upload to and delete from folders matching their own UUID (`auth.uid()`).
4. **Local Development Fallback**: If Supabase environment variables are missing, the system will log a warning and run in a mock environment (using local disk uploads and an SQLite fallback database) for testing purposes.

---

## Troubleshooting

### Error: `Cannot find module 'dotenv'` or `ModuleNotFoundError: No module named 'dotenv'`

If you encounter this error when starting the backend (typically pointing to `app/config.py`), it means Python is executing using your global system-wide interpreter instead of the project's virtual environment where all dependencies are installed.

#### Solution A: Select the Virtual Environment Interpreter in VS Code
1. Open the Command Palette (`Ctrl + Shift + P` or `F1`).
2. Search for and select **Python: Select Interpreter**.
3. Select the python executable inside your project's virtual environment:
   `./backend/venv/Scripts/python.exe`

#### Solution B: Activate the Virtual Environment in Terminal
Ensure you run the backend commands inside the activated virtual environment:
* **PowerShell**:
  ```powershell
  cd backend
  .\venv\Scripts\Activate.ps1
  python -m uvicorn app.main:app --reload
  ```
* **Command Prompt**:
  ```cmd
  cd backend
  .\venv\Scripts\activate.bat
  python -m uvicorn app.main:app --reload
  ```
* **Direct invocation**:
  ```powershell
  cd backend
  .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
  ```
