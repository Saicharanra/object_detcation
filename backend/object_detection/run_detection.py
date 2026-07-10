import os
import sys
import argparse
import time
import cv2
from pathlib import Path

# Add backend directory to python path if run directly to support relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from object_detection.detector import ObjectDetector

def run_image_detection(detector, source_path, output_dir, use_supabase=False, user_id=None):
    """
    Runs object detection on a static image, prints results, and saves/shows annotated image.
    Optionally uploads results and logs detections to Supabase.
    """
    print(f"\n[IMAGE MODE] Loading image: {source_path}")
    img = cv2.imread(str(source_path))
    if img is None:
        print(f"Error: Could not load image from {source_path}", file=sys.stderr)
        return
        
    start_time = time.time()
    detections = detector.detect(img)
    processing_time = time.time() - start_time
    
    print(f"Detection completed in {processing_time:.3f} seconds.")
    print(f"Found {len(detections)} object(s):")
    
    for i, det in enumerate(detections, 1):
        box_str = ", ".join([f"{coord:.1f}" for coord in det['box']])
        print(f"  {i}. Label: {det['class_name']} | Confidence: {det['confidence']:.2f} | Box: [{box_str}]")
        
    # Annotate and save locally
    annotated_img = detector.annotate_frame(img, detections)
    
    os.makedirs(output_dir, exist_ok=True)
    out_filename = f"annotated_{Path(source_path).name}"
    out_path = os.path.join(output_dir, out_filename)
    cv2.imwrite(out_path, annotated_img)
    print(f"Saved annotated image to: {out_path}")
    
    # Upload to Supabase if enabled
    if use_supabase and user_id:
        print("\n[Supabase] Uploading image and detections to Supabase...")
        try:
            from object_detection.supabase_helper import save_to_supabase
            res = save_to_supabase(
                user_id=user_id,
                original_filename=Path(source_path).name,
                local_orig_path=str(source_path),
                local_annot_path=out_path,
                detections=detections,
                processing_time=processing_time
            )
            print(f"[Supabase] Upload successful!")
            print(f"  Image ID: {res['image_id']}")
            print(f"  Original URL: {res['image_url']}")
            print(f"  Annotated URL: {res['annotated_image_url']}\n")
        except Exception as e:
            print(f"[Supabase] Error uploading to Supabase: {str(e)}", file=sys.stderr)

    # Try to show image
    try:
        cv2.imshow("Object Detection Result - Press any key to close", annotated_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error:
        print("Note: Running in a headless environment. Skipping window visualization.")

def run_video_detection(detector, source_path, output_dir, use_supabase=False, user_id=None):
    """
    Runs object detection on a video file, prints progress, and saves the annotated video.
    If Supabase is enabled, uploads the final annotated video to Supabase Storage.
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
    
    # Setup video writer
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
            # Run detection
            detections = detector.detect(frame)
            
            # Annotate
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
    print(f"Total processing time: {total_time:.2f} seconds | Average processing speed: {avg_fps:.2f} FPS")
    
    # Upload to Supabase if enabled
    if use_supabase and user_id:
        print("\n[Supabase] Uploading video to Supabase Storage...")
        try:
            from object_detection.supabase_helper import save_to_supabase
            res = save_to_supabase(
                user_id=user_id,
                original_filename=Path(source_path).name,
                local_orig_path=str(source_path),
                local_annot_path=out_path,
                detections=[],
                processing_time=total_time
            )
            print(f"[Supabase] Video upload successful!")
            print(f"  Video ID: {res['image_id']}")
            print(f"  Original Video URL: {res['image_url']}")
            print(f"  Annotated Video URL: {res['annotated_image_url']}\n")
        except Exception as e:
            print(f"[Supabase] Error uploading video: {str(e)}", file=sys.stderr)

def run_webcam_detection(detector, camera_index, no_show=False, use_supabase=False, user_id=None, save_interval=None):
    """
    Opens the default system webcam, runs real-time detection, logs to console, and displays window.
    Optionally uploads snapshot images to Supabase on key press or at fixed intervals.
    """
    print(f"\n[WEBCAM MODE] Initializing camera stream index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open camera with index {camera_index}", file=sys.stderr)
        return
        
    print("Camera stream opened successfully.")
    print("Press 'q' key in the visualization window (or Ctrl+C in terminal) to exit.")
    if use_supabase:
        print("Press 's' key in the visualization window to capture and upload a snapshot to Supabase.")
        if save_interval:
            print(f"Auto-saving snapshot to Supabase every {save_interval} seconds.")
    
    frame_count = 0
    feedback_frames = 0
    last_save_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame from camera.", file=sys.stderr)
                break
                
            frame_count += 1
            start_time = time.time()
            detections = detector.detect(frame)
            latency = (time.time() - start_time) * 1000  # ms
            
            # Form clean summary log
            objects = [f"{d['class_name']} ({d['confidence']:.2f})" for d in detections]
            obj_summary = ", ".join(objects) if objects else "None"
            print(f"[Frame {frame_count:04d}] Latency: {latency:.1f}ms | Detected: {obj_summary}")
            
            # Annotate frame
            annotated_frame = detector.annotate_frame(frame, detections)
            
            # Check for auto-save interval
            should_save = False
            current_time = time.time()
            if use_supabase and save_interval and (current_time - last_save_time >= save_interval):
                should_save = True
                last_save_time = current_time
                print(f"\n[Supabase] Auto-saving snapshot (interval: {save_interval}s)...")
            
            # Show interactive window features
            if not no_show:
                # Add on-screen hints
                if use_supabase:
                    cv2.putText(
                        annotated_frame, 
                        "Supabase: Enabled | Press 's' to Save Snapshot", 
                        (10, annotated_frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (255, 0, 0), 
                        1, 
                        cv2.LINE_AA
                    )
                
                # Snapshot upload visual feedback
                if feedback_frames > 0:
                    cv2.putText(
                        annotated_frame, 
                        "SNAPSHOT UPLOADED!", 
                        (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 0), 
                        2, 
                        cv2.LINE_AA
                    )
                    feedback_frames -= 1
                    
                try:
                    cv2.imshow("Real-Time Object Detection (Press 'q' to Quit)", annotated_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Exit signal received. Closing...")
                        break
                    elif key == ord('s') and use_supabase:
                        should_save = True
                        print("\n[Supabase] Snapshot triggered manually via 's' key...")
                except cv2.error:
                    print("Visual display error: Heading to terminal-only logging (disabling window).")
                    no_show = True
            
            # Handle upload if triggered
            if should_save:
                # Save temp files locally to upload
                temp_dir = Path(__file__).resolve().parent / "output" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                temp_orig = temp_dir / "snapshot_orig.jpg"
                temp_annot = temp_dir / "snapshot_annot.jpg"
                
                cv2.imwrite(str(temp_orig), frame)
                cv2.imwrite(str(temp_annot), annotated_frame)
                
                try:
                    from object_detection.supabase_helper import save_to_supabase
                    res = save_to_supabase(
                        user_id=user_id,
                        original_filename=f"webcam_snapshot_{int(time.time())}.jpg",
                        local_orig_path=str(temp_orig),
                        local_annot_path=str(temp_annot),
                        detections=detections,
                        processing_time=latency / 1000.0
                    )
                    print(f"[Supabase] Snapshot uploaded successfully!")
                    print(f"  Image ID: {res['image_id']}")
                    print(f"  Original URL: {res['image_url']}")
                    print(f"  Annotated URL: {res['annotated_image_url']}\n")
                    feedback_frames = 30
                except Exception as upload_err:
                    print(f"[Supabase] Error uploading snapshot: {str(upload_err)}", file=sys.stderr)
                finally:
                    # Clean up temp files
                    if temp_orig.exists():
                        temp_orig.unlink()
                    if temp_annot.exists():
                        temp_annot.unlink()
            
            if no_show:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt received. Closing...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera stream closed.")

def main():
    parser = argparse.ArgumentParser(description="YOLOv8 Real-Time Object Detection with Supabase Logging")
    parser.add_argument(
        "--source", 
        type=str, 
        required=True, 
        help="Path to an image file, video file, or 'webcam' for real-time camera feed."
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="yolov8n.pt", 
        help="YOLOv8 pre-trained model (e.g. yolov8n.pt, yolov8s.pt). Default is yolov8n.pt."
    )
    parser.add_argument(
        "--conf", 
        type=float, 
        default=0.25, 
        help="Confidence threshold for predictions. Default is 0.25."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=str(Path(__file__).resolve().parent / "output"), 
        help="Directory to save annotated outputs. Default is backend/object_detection/output."
    )
    parser.add_argument(
        "--no-show", 
        action="store_true", 
        help="For webcam stream: disables displaying the cv2.imshow visualization window. Prints console log only."
    )
    parser.add_argument(
        "--supabase", 
        action="store_true", 
        help="Enables uploading detection images and database logs to Supabase."
    )
    parser.add_argument(
        "--user-id", 
        type=str, 
        default="b35baf1f-33f4-4515-bfba-ea8d881f5187", 
        help="Supabase User UUID to associate database entries with. Defaults to saicharan's user ID."
    )
    parser.add_argument(
        "--save-interval", 
        type=float, 
        default=None, 
        help="For webcam: automatic snapshot upload interval in seconds. Only active if --supabase is specified."
    )
    
    args = parser.parse_args()
    
    # Load detector
    detector = ObjectDetector(model_name=args.model, conf_threshold=args.conf)
    
    # Run based on source
    source = args.source
    if source.lower() == "webcam":
        run_webcam_detection(
            detector, 
            camera_index=0, 
            no_show=args.no_show, 
            use_supabase=args.supabase, 
            user_id=args.user_id,
            save_interval=args.save_interval
        )
    elif source.isdigit():
        run_webcam_detection(
            detector, 
            camera_index=int(source), 
            no_show=args.no_show, 
            use_supabase=args.supabase, 
            user_id=args.user_id,
            save_interval=args.save_interval
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
                use_supabase=args.supabase, 
                user_id=args.user_id
            )
        elif suffix in vid_suffixes:
            run_video_detection(
                detector, 
                path, 
                args.output_dir, 
                use_supabase=args.supabase, 
                user_id=args.user_id
            )
        else:
            print(f"Unsupported file format: {suffix}. Supported images: {img_suffixes}, videos: {vid_suffixes}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
