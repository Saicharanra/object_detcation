import os
import sys
import argparse
import shutil
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Add workspace directory to python path if run directly to support relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

def setup_mock_dataset(dataset_root_path):
    """
    Creates a minimal mock dataset (images and labels) for testing the training flow.
    """
    print(f"\n[Mock Dataset] Setting up mock dataset in: {dataset_root_path}")
    dataset_root = Path(dataset_root_path)
    
    # Create directory structure
    for split in ['train', 'val']:
        (dataset_root / 'images' / split).mkdir(parents=True, exist_ok=True)
        (dataset_root / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
    # Generate mock images and label files
    # Class ID: 0 (custom_object), bbox center_x, center_y, width, height (normalized 0-1)
    mock_label_content = "0 0.5 0.5 0.3 0.3\n"
    
    for split in ['train', 'val']:
        for i in range(2):
            img_name = f"mock_{split}_{i}.jpg"
            label_name = f"mock_{split}_{i}.txt"
            
            img_path = dataset_root / 'images' / split / img_name
            label_path = dataset_root / 'labels' / split / label_name
            
            # Create a 640x640 RGB image (solid color with a square drawn on it)
            img = np.zeros((640, 640, 3), dtype=np.uint8)
            img[:, :] = [50 + i * 50, 100, 150] # RGB background
            # Draw a mock object square in the center
            cv2.rectangle(img, (224, 224), (416, 416), (0, 255, 0), -1)
            cv2.imwrite(str(img_path), img)
            
            # Create corresponding label file
            with open(label_path, 'w') as f:
                f.write(mock_label_content)
                
    print("[Mock Dataset] Mock dataset successfully created.")

def main():
    parser = argparse.ArgumentParser(description="YOLOv8 Custom Model Training Pipeline")
    parser.add_argument(
        "--data", 
        type=str, 
        default="object_detection/dataset_template.yaml", 
        help="Path to dataset configuration YAML file. Default is object_detection/dataset_template.yaml."
    )
    parser.add_argument(
        "--epochs", 
        type=int, 
        default=50, 
        help="Number of training epochs. Default is 50."
    )
    parser.add_argument(
        "--imgsz", 
        type=int, 
        default=640, 
        help="Training image size (square size in pixels). Default is 640."
    )
    parser.add_argument(
        "--batch", 
        type=int, 
        default=16, 
        help="Batch size (use -1 for automatic batch sizing). Default is 16."
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="yolov8n.pt", 
        help="Base model weights to start training from (e.g., yolov8n.pt, yolov8s.pt). Default is yolov8n.pt."
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="cpu", 
        help="Execution device for training (e.g., cpu, cuda, 0, 1). Default is cpu."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=str(Path(__file__).resolve().parent / "models"), 
        help="Directory to save training results and weights. Default is the 'models' folder inside the script directory."
    )
    parser.add_argument(
        "--setup-mock-data", 
        action="store_true", 
        help="If set, generates a minimal mock dataset in the path configured in the YAML file to test training."
    )
    
    args = parser.parse_args()
    
    # 1. Parse dataset YAML to verify configurations
    yaml_path = Path(args.data)
    if not yaml_path.exists():
        # Try relative to the script directory (e.g., if running from within object_detection folder)
        alt_path = Path(__file__).resolve().parent / yaml_path.name
        if alt_path.exists():
            yaml_path = alt_path
        elif yaml_path.parts and yaml_path.parts[0] == "object_detection":
            # Strip object_detection prefix if user is already inside it
            alt_path = Path(*yaml_path.parts[1:])
            if alt_path.exists():
                yaml_path = alt_path
        
        # If still not found, print error
        if not yaml_path.exists():
            print(f"Error: Dataset configuration file not found at: {yaml_path}", file=sys.stderr)
            sys.exit(1)
        
    print(f"Loading dataset configuration: {yaml_path.resolve()}")
    
    # Simple YAML parsing to extract 'path' variable
    dataset_path = "./dataset"
    try:
        with open(yaml_path, 'r') as f:
            for line in f:
                if line.strip().startswith("path:"):
                    dataset_path = line.split("path:")[-1].strip()
                    # Resolve comments or quotes
                    dataset_path = dataset_path.split("#")[0].strip().replace("'", "").replace('"', '')
                    break
        
        # If dataset_path is relative, resolve it relative to the directory containing the YAML file
        dataset_path_obj = Path(dataset_path)
        if not dataset_path_obj.is_absolute():
            dataset_path_obj = (yaml_path.parent / dataset_path_obj).resolve()
            dataset_path = str(dataset_path_obj)
            
    except Exception as e:
        print(f"Warning: Could not parse dataset path from configuration: {str(e)}. Defaulting to './dataset'")

    # 2. Setup mock data if requested
    if args.setup_mock_data:
        setup_mock_dataset(dataset_path)
    else:
        # Verify the training dataset directories exist
        img_train_dir = Path(dataset_path) / "images" / "train"
        if not img_train_dir.exists() or not any(img_train_dir.iterdir()):
            print(f"\n[Warning] Training images directory '{img_train_dir}' is missing or empty.")
            print(f"Please place your training dataset in '{dataset_path}' in YOLO format,")
            print(f"or run with '--setup-mock-data' to generate a mock dataset automatically for testing.")
            sys.exit(1)

    # 3. Load base model
    print(f"\nInitializing YOLO model from base weights: {args.model}...")
    model = YOLO(args.model)

    # Ensure output models directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. Start training
    print(f"\nStarting YOLOv8 training run...")
    print(f"  Dataset config: {yaml_path}")
    print(f"  Epochs:         {args.epochs}")
    print(f"  Image Size:     {args.imgsz}")
    print(f"  Batch Size:     {args.batch}")
    print(f"  Device:         {args.device}")
    print(f"  Output Dir:     {output_dir.resolve()}")
    
    # Create a temporary resolved yaml file to avoid CWD path issues in YOLOv8
    temp_yaml_path = yaml_path.parent / "temp_dataset_resolved.yaml"
    try:
        with open(yaml_path, 'r') as f:
            yaml_lines = f.readlines()
        
        with open(temp_yaml_path, 'w') as f:
            for line in yaml_lines:
                if line.strip().startswith("path:"):
                    # Use forward slashes for paths inside YOLO YAML files to avoid Windows escape character errors
                    abs_path_str = str(Path(dataset_path).resolve()).replace('\\', '/')
                    f.write(f"path: {abs_path_str}\n")
                else:
                    f.write(line)
        print(f"Created temporary resolved configuration for training: {temp_yaml_path.resolve()}")
    except Exception as e:
        print(f"Warning: Failed to create temp resolved dataset config: {str(e)}. Falling back to default.")
        temp_yaml_path = yaml_path

    try:
        results = model.train(
            data=str(temp_yaml_path),
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            project=str(output_dir.resolve()),
            name="custom_train",
            exist_ok=True
        )
        
        print("\nTraining completed successfully!")
        
        # 5. Locate and extract best model weights
        best_weights_src = output_dir / "custom_train" / "weights" / "best.pt"
        best_weights_dst = output_dir / "custom_yolov8.pt"
        
        if best_weights_src.exists():
            shutil.copy(best_weights_src, best_weights_dst)
            print(f"\n[Success] Custom model weights saved to: {best_weights_dst.resolve()}")
            print(f"You can now run predictions using the custom model:")
            print(f"  python object_detection/run_detection.py --source webcam --model {best_weights_dst}")
        else:
            print(f"\n[Warning] Training finished, but best weights file could not be found at: {best_weights_src}")
            
    except Exception as train_err:
        print(f"\nError during training execution: {str(train_err)}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary YAML file
        if temp_yaml_path != yaml_path and temp_yaml_path.exists():
            try:
                temp_yaml_path.unlink()
            except Exception:
                pass

if __name__ == "__main__":
    main()
