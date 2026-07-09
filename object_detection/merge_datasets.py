import os
import json
import shutil

def process_split(split, coco_dataset_dir, yolo_dataset_dir):
    split_dir = os.path.join(coco_dataset_dir, split)
    json_path = os.path.join(split_dir, "_annotations.coco.json")
    
    if not os.path.exists(json_path):
        print(f"No json found in {split_dir}")
        return

    print(f"Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    yolo_split = "train" if split == "train" else "val"
    yolo_images_dir = os.path.join(yolo_dataset_dir, "images", yolo_split)
    yolo_labels_dir = os.path.join(yolo_dataset_dir, "labels", yolo_split)
    
    # Create image lookup dict
    images_dict = {img['id']: img for img in data.get('images', [])}
    
    # Collect annotations by image
    from collections import defaultdict
    ann_by_img = defaultdict(list)
    
    car_category_id = 10
    
    for ann in data.get('annotations', []):
        cat_id = ann.get('category_id')
        bbox = ann.get('bbox')
        
        # Only keep 'car' category and skip invalid boxes
        if cat_id == car_category_id and bbox is not None and len(bbox) == 4 and all(x is not None for x in bbox):
            ann_by_img[ann['image_id']].append(bbox)
            
    print(f"Found {len(ann_by_img)} images containing cars in {split}.")
    
    for img_id, bboxes in ann_by_img.items():
        img_info = images_dict.get(img_id)
        if not img_info:
            continue
            
        file_name = img_info['file_name']
        img_w = img_info['width']
        img_h = img_info['height']
        
        # Normalize and prepare YOLO format lines
        yolo_lines = []
        for bbox in bboxes:
            xmin, ymin, w, h = bbox
            x_center = (xmin + w / 2.0) / img_w
            y_center = (ymin + h / 2.0) / img_h
            norm_w = w / img_w
            norm_h = h / img_h
            
            # constrain between 0 and 1
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            norm_w = max(0.0, min(1.0, norm_w))
            norm_h = max(0.0, min(1.0, norm_h))
            
            yolo_lines.append(f"0 {x_center} {y_center} {norm_w} {norm_h}\n")
            
        if yolo_lines:
            # Write label file
            label_name = os.path.splitext(file_name)[0] + '.txt'
            dst_label_path = os.path.join(yolo_labels_dir, label_name)
            with open(dst_label_path, 'w') as f:
                f.writelines(yolo_lines)
                
            # Copy image
            src_img_path = os.path.join(split_dir, file_name)
            dst_img_path = os.path.join(yolo_images_dir, file_name)
            if os.path.exists(src_img_path):
                shutil.copy(src_img_path, dst_img_path)

def main():
    base_dir = r"C:\Users\saini\OneDrive\Documents\GitHub\object_detcation\object_detection"
    coco_dataset_dir = os.path.join(base_dir, "dataset", "Senior-Design-VIAD-4")
    yolo_dataset_dir = os.path.join(base_dir, "yolo_dataset")
    
    process_split("train", coco_dataset_dir, yolo_dataset_dir)
    process_split("test", coco_dataset_dir, yolo_dataset_dir)
    print("Custom merge completed!")

if __name__ == "__main__":
    main()
