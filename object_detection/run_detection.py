import os
import sys
import argparse
import time
import cv2
from pathlib import Path

# Add workspace directory to python path if run directly to support relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from object_detection.detector import ObjectDetector

def crop_and_save_detections(img, detections, output_dir, crop_dir, base_name=""):
    """
    Crops detected regions from the image and saves them to the crop directory.
    """
    c_dir = crop_dir if crop_dir else os.path.join(output_dir, "crops")
    os.makedirs(c_dir, exist_ok=True)

    saved_paths = []
    h, w = img.shape[:2]

    for i, det in enumerate(detections, 1):
        xmin, ymin, xmax, ymax = det['box']
        xmin_c = max(0, int(xmin))
        ymin_c = max(0, int(ymin))
        xmax_c = min(w, int(xmax))
        ymax_c = min(h, int(ymax))

        if xmax_c > xmin_c and ymax_c > ymin_c:
            crop_img = img[ymin_c:ymax_c, xmin_c:xmax_c]
            class_name = det['class_name'].replace(" ", "_")
            timestamp = int(time.time())
            out_filename = f"{class_name}_crop_{i}_{timestamp}.jpg"
            out_path = os.path.join(c_dir, out_filename)
            cv2.imwrite(out_path, crop_img)
            print(f"  -> Saved cropped {det['class_name']} to: {out_path}")
            saved_paths.append(out_path)

    return saved_paths


def run_image_detection(detector, source_path, output_dir, no_show=False, target_class=None, crop=False, crop_dir=None):
    """
    Runs object detection on a static image.
    """
    print(f"\n[IMAGE MODE] Loading image: {source_path}")
    img = cv2.imread(str(source_path))
    if img is None:
        print(f"Error: Could not load image from {source_path}", file=sys.stderr)
        return

    start_time = time.time()
    detections = detector.detect(img)
    processing_time = time.time() - start_time

    if target_class:
        target_class_lower = target_class.lower().strip()
        detections = [d for d in detections if d['class_name'].lower().strip() == target_class_lower]
        print(f"Filtered detections for target class: '{target_class}'")

    print(f"Detection completed in {processing_time:.3f} seconds.")
    print(f"Found {len(detections)} object(s):")

    for i, det in enumerate(detections, 1):
        box_str = ", ".join([f"{coord:.1f}" for coord in det['box']])
        print(f"  {i}. Label: {det['class_name']} | Confidence: {det['confidence']:.2f} | Box: [{box_str}]")

    if crop and len(detections) > 0:
        print("\nSaving cropped objects...")
        crop_and_save_detections(img, detections, output_dir, crop_dir, Path(source_path).stem)

    annotated_img = detector.annotate_frame(img, detections)

    os.makedirs(output_dir, exist_ok=True)
    out_filename = f"annotated_{Path(source_path).name}"
    out_path = os.path.join(output_dir, out_filename)
    cv2.imwrite(out_path, annotated_img)
    print(f"Saved annotated image to: {out_path}")

    if not no_show:
        try:
            cv2.imshow("Object Detection Result - Press any key to close", annotated_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error:
            print("Note: Running in a headless environment. Skipping window visualization.")


def run_video_detection(detector, source_path, output_dir, target_class=None, crop=False, crop_dir=None):
    """
    Runs object detection on a video file, saves the annotated video.
    """
    print(f"\n[VIDEO MODE] Processing video: {source_path}")
    cap = cv2.VideoCapture(str(source_path))
    if not cap.isOpened():
        print(f"Error: Could not open video from {source_path}", file=sys.stderr)
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video Info: {width}x{height} @ {fps:.2f} FPS | Total Frames: {total_frames}")

    os.makedirs(output_dir, exist_ok=True)
    out_filename = f"annotated_{Path(source_path).name}"
    out_path = os.path.join(output_dir, out_filename)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    frame_count = 0
    start_time = time.time()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            detections = detector.detect(frame)

            if target_class:
                target_class_lower = target_class.lower().strip()
                detections = [d for d in detections if d['class_name'].lower().strip() == target_class_lower]

            if crop and len(detections) > 0:
                video_name = Path(source_path).stem
                v_crop_dir = crop_dir if crop_dir else os.path.join(output_dir, "crops", video_name)
                os.makedirs(v_crop_dir, exist_ok=True)
                h_img, w_img = frame.shape[:2]
                for i, det in enumerate(detections, 1):
                    xmin, ymin, xmax, ymax = det['box']
                    xmin_c = max(0, int(xmin))
                    ymin_c = max(0, int(ymin))
                    xmax_c = min(w_img, int(xmax))
                    ymax_c = min(h_img, int(ymax))
                    if xmax_c > xmin_c and ymax_c > ymin_c:
                        crop_img = frame[ymin_c:ymax_c, xmin_c:xmax_c]
                        class_name = det['class_name'].replace(" ", "_")
                        crop_filename = f"frame_{frame_count:04d}_{class_name}_{i}.jpg"
                        cv2.imwrite(os.path.join(v_crop_dir, crop_filename), crop_img)

            annotated_frame = detector.annotate_frame(frame, detections)
            out.write(annotated_frame)

            if frame_count % 10 == 0 or frame_count == total_frames:
                pct = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                print(f"Processed frame {frame_count}/{total_frames} ({pct:.1f}%)")

    finally:
        cap.release()
        out.release()

    total_time = time.time() - start_time
    avg_fps = frame_count / total_time if total_time > 0 else 0
    print(f"\nFinished processing video. Saved to: {out_path}")
    print(f"Total time: {total_time:.2f}s | Avg speed: {avg_fps:.2f} FPS")


def run_webcam_detection(detector, camera_index, no_show=False, target_class=None, crop=False, crop_dir=None):
    """
    Opens system webcam and runs real-time YOLO-World detection.
    """
    print(f"\n[WEBCAM MODE] Initializing camera stream index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open camera with index {camera_index}", file=sys.stderr)
        return

    print("Camera stream opened successfully.")
    print("Press 'q' key in the visualization window (or Ctrl+C in terminal) to exit.")

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame from camera.", file=sys.stderr)
                break

            frame_count += 1
            start_time = time.time()
            detections = detector.detect(frame)

            if target_class:
                target_class_lower = target_class.lower().strip()
                detections = [d for d in detections if d['class_name'].lower().strip() == target_class_lower]

            latency = (time.time() - start_time) * 1000

            objects = [f"{d['class_name']} ({d['confidence']:.2f})" for d in detections]
            obj_summary = ", ".join(objects) if objects else "None"
            print(f"[Frame {frame_count:04d}] Latency: {latency:.1f}ms | Detected: {obj_summary}")

            annotated_frame = detector.annotate_frame(frame, detections)

            if crop and len(detections) > 0:
                crop_and_save_detections(frame, detections, "object_detection/output", crop_dir, "webcam")

            if not no_show:
                try:
                    cv2.imshow("YOLOv11 Real-Time Detection (Press 'q' to Quit)", annotated_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Exit signal received. Closing...")
                        break
                except cv2.error:
                    print("Visual display error: switching to terminal-only logging.")
                    no_show = True

            if no_show:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nKeyboard Interrupt received. Closing...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera stream closed.")


def main():
    parser = argparse.ArgumentParser(
        description="YOLOv11 Object Detection using OpenCV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect objects from webcam
  python run_detection.py --source webcam

  # Detect objects in an image file
  python run_detection.py --source photo.jpg

  # Use a video file
  python run_detection.py --source video.mp4

  # Use a more accurate model
  python run_detection.py --source webcam --model yolo11m.pt
        """
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to an image file, video file, 'webcam', or a webcam index integer."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11s.pt",
        help="YOLOv11 model weights. Options: yolo11n.pt (fastest), yolo11s.pt (balanced), yolo11m.pt (accurate), yolo11l.pt, yolo11x.pt (best). Default: yolo11s.pt"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.4,
        help="Confidence threshold (0.0-1.0). Default is 0.4."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="object_detection/output",
        help="Directory to save annotated outputs. Default is object_detection/output."
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Disable the cv2.imshow window. Prints console log only."
    )
    parser.add_argument(
        "--target-class",
        type=str,
        default=None,
        help="Filter detections to only show a specific class (e.g. 'person')."
    )
    parser.add_argument(
        "--crop",
        action="store_true",
        help="Save cropped images of each detected object."
    )
    parser.add_argument(
        "--crop-dir",
        type=str,
        default=None,
        help="Custom directory to save cropped objects (defaults to output-dir/crops)."
    )

    args = parser.parse_args()

    # Load detector
    detector = ObjectDetector(
        model_name=args.model,
        conf_threshold=args.conf
    )

    source = args.source
    if source.lower() == "webcam":
        run_webcam_detection(
            detector,
            camera_index=0,
            no_show=args.no_show,
            target_class=args.target_class,
            crop=args.crop,
            crop_dir=args.crop_dir
        )
    elif source.isdigit():
        run_webcam_detection(
            detector,
            camera_index=int(source),
            no_show=args.no_show,
            target_class=args.target_class,
            crop=args.crop,
            crop_dir=args.crop_dir
        )
    else:
        path = Path(source)
        if not path.exists():
            print(f"Error: Source path '{source}' does not exist.", file=sys.stderr)
            sys.exit(1)

        suffix = path.suffix.lower()
        img_suffixes = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        vid_suffixes = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}

        if suffix in img_suffixes:
            run_image_detection(
                detector,
                path,
                args.output_dir,
                no_show=args.no_show,
                target_class=args.target_class,
                crop=args.crop,
                crop_dir=args.crop_dir
            )
        elif suffix in vid_suffixes:
            run_video_detection(
                detector,
                path,
                args.output_dir,
                target_class=args.target_class,
                crop=args.crop,
                crop_dir=args.crop_dir
            )
        else:
            print(f"Unsupported file format: {suffix}. Supported images: {img_suffixes}, videos: {vid_suffixes}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
