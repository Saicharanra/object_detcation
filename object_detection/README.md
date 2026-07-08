# Object Detection Module

This module provides a real-time object detection implementation using a pre-trained YOLOv8 architecture (via Ultralytics). It can process static images, video files, and live camera/webcam feeds, logging detections (bounding boxes, class names, confidence scores) and saving annotated results.

## Module Structure

- [detector.py](file:///c:/Users/saich/Downloads/ObjectDetactionmodel/object_detection/detector.py): Contains the `ObjectDetector` class wrapping the YOLO model.
- [utils.py](file:///c:/Users/saich/Downloads/ObjectDetactionmodel/object_detection/utils.py): Bounding box visualization and color palette generation helpers.
- [run_detection.py](file:///c:/Users/saich/Downloads/ObjectDetactionmodel/object_detection/run_detection.py): CLI interface to run detections on different sources.
- [requirements.txt](file:///c:/Users/saich/Downloads/ObjectDetactionmodel/object_detection/requirements.txt): Module dependencies.

## Setup

All dependencies are already installed in the workspace's backend virtual environment.

To activate the virtual environment manually or run scripts:
- **Windows (PowerShell)**: `.\backend\venv\Scripts\Activate.ps1`
- **Windows (CMD)**: `.\backend\venv\Scripts\activate.bat`

## CLI Commands

You can run the model using the test script `run_detection.py`.

### 1. Detect Objects in an Image
Detects objects in a static image, prints the results in the console, displays the visual output (if GUI is available), and saves the annotated image to the output directory.
```bash
backend\venv\Scripts\python.exe object_detection\run_detection.py --source path/to/your/image.jpg
```

### 2. Detect Objects in a Video
Processes a video frame-by-frame, performs detection, and writes an output video with bounding boxes.
```bash
backend\venv\Scripts\python.exe object_detection\run_detection.py --source path/to/your/video.mp4
```

### 3. Real-Time Camera Stream / Webcam
Captures frames from your computer's webcam, processes them in real-time, prints detections to the terminal, and displays the stream in an interactive window. Press `q` to exit.
```bash
backend\venv\Scripts\python.exe object_detection\run_detection.py --source webcam
```

If you are running in a headless server or docker container with no GUI display, add the `--no-show` flag to run in console-only logging mode:
```bash
backend\venv\Scripts\python.exe object_detection\run_detection.py --source webcam --no-show
```

### 4. Customizing Parameters
- **Use a different YOLO model (e.g. YOLOv8s, YOLOv8m)**:
  ```bash
  backend\venv\Scripts\python.exe object_detection\run_detection.py --source webcam --model yolov8s.pt
  ```
- **Change confidence threshold (default: 0.25)**:
  ```bash
  backend\venv\Scripts\python.exe object_detection\run_detection.py --source webcam --conf 0.45
  ```
- **Specify a custom output folder for annotated images/videos**:
  ```bash
  backend\venv\Scripts\python.exe object_detection\run_detection.py --source path/to/image.jpg --output-dir custom_output_folder
  ```
