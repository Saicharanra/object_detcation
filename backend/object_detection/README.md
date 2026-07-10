# Standalone Real-Time Object Detection Module (Backend Relocated)

This sub-module provides a real-time object detection implementation using a pre-trained YOLOv8 architecture, complete with Supabase storage and database integration.

## CLI Commands

You can run this script using the backend virtual environment:

### 1. Detect Objects in an Image (with Supabase upload)
```bash
backend\venv\Scripts\python.exe backend\object_detection\run_detection.py --source backend\venv\Lib\site-packages\ultralytics\assets\bus.jpg --supabase
```

### 2. Live Webcam Stream (with Manual snapshot upload on 's' key)
```bash
backend\venv\Scripts\python.exe backend\object_detection\run_detection.py --source webcam --supabase
```
- Press **`s`** to capture and upload a snapshot.
- Press **`q`** to quit.

### 3. Headless Webcam Stream (with Periodic Auto-save)
If running on a remote headless server, disable the GUI pop-up window and auto-save a snapshot to Supabase every 5 seconds:
```bash
backend\venv\Scripts\python.exe backend\object_detection\run_detection.py --source webcam --supabase --no-show --save-interval 5
```
