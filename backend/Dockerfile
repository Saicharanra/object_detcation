FROM python:3.11-slim

WORKDIR /app

# System libs required by opencv-python-headless, plus git (needed below to
# install the CLIP text encoder that YOLO-World's set_classes() requires for
# open-vocabulary text search — without it Ultralytics tries to auto-install
# CLIP via git on every single request and fails since git isn't present).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch first so ultralytics' transitive torch requirement
# is already satisfied by the lightweight CPU wheel (avoids pulling the much
# larger CUDA build, which is wasted weight on a CPU-only host).
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir git+https://github.com/ultralytics/CLIP.git

COPY app ./app
COPY yolo11n.pt yolov8s-worldv2.pt ./

RUN mkdir -p uploads

# Render (and most PaaS Docker runners) inject the port to listen on via $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
