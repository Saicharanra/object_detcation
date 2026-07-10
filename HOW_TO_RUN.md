# How to Run the Object Detection Project

This folder contains the complete consolidated project, including:
1. **Frontend**: React application built with Vite and Tailwind.
2. **Backend**: FastAPI web server with YOLO-World open-vocabulary object detection.
3. **Supabase Database & Storage Settings**: Setup scripts under `/supabase`.
4. **CLI tool**: Command-line interface under `/object_detection` to run detection directly.

---

## 1. Run the Full Web Application (UI + API)

To run the full web application, you need to open two separate terminal windows:

### Terminal 1: Backend Server (FastAPI)
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
3. Run the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   *(The server will run on `http://localhost:8000`)*

---

### Terminal 2: Frontend Server (React)
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Run the Vite development server:
   ```bash
   npm run dev
   ```
   *(The React UI will run on `http://localhost:5173`)*
3. Open `http://localhost:5173` in your browser.
4. Upload any image, and under the **Objects Detected** list in the sidebar, click the **Download icon** next to any detected item to instantly crop and download it!

---

## 2. Run the CLI Tool (Terminal-only)

You can run object detection and crop objects directly from the terminal without launching the web server.

1. Navigate to the `object_detection` folder:
   ```bash
   cd object_detection
   ```
2. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
3. Run detection locally or from Supabase:

   * **Option A: Crop objects from a local image** (e.g. crop all `person` objects from `bus.jpg`):
     ```bash
     python run_detection.py --source output/annotated_bus.jpg --target-class person --crop --no-show
     ```

   * **Option B: Crop objects from the latest Supabase image** (e.g. crop all `cup` objects):
     ```bash
     python run_detection.py --source supabase --target-class cup --crop --no-show
     ```

   *(All cropped files will be saved in `object_detection/output/crops/`)*
