import os
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
import shutil

def main():
    base_dir = "dataset"
    csv_path = os.path.join(base_dir, "train_solution_bounding_boxes (1).csv")
    img_dir = os.path.join(base_dir, "training_images")
    
    # YOLO format directories
    yolo_dir = "yolo_dataset"
    for split in ['train', 'val']:
        os.makedirs(os.path.join(yolo_dir, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(yolo_dir, 'labels', split), exist_ok=True)
        
    df = pd.read_csv(csv_path)
    
    # Get all images present in the folder, some might not have bounding boxes in the CSV
    all_images = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    # Split into train and val (80/20)
    train_imgs, val_imgs = train_test_split(all_images, test_size=0.2, random_state=42)
    
    def process_split(img_list, split_name):
        print(f"Processing {split_name} split ({len(img_list)} images)...")
        for img_name in img_list:
            src_img_path = os.path.join(img_dir, img_name)
            dst_img_path = os.path.join(yolo_dir, 'images', split_name, img_name)
            
            # Copy image
            shutil.copy(src_img_path, dst_img_path)
            
            # Create label file
            label_name = os.path.splitext(img_name)[0] + '.txt'
            dst_label_path = os.path.join(yolo_dir, 'labels', split_name, label_name)
            
            # Get boxes for this image
            boxes = df[df['image'] == img_name]
            
            if len(boxes) > 0:
                with Image.open(src_img_path) as img:
                    img_width, img_height = img.size
                    
                with open(dst_label_path, 'w') as f:
                    for _, row in boxes.iterrows():
                        xmin = row['xmin']
                        ymin = row['ymin']
                        xmax = row['xmax']
                        ymax = row['ymax']
                        
                        # YOLO format normalization
                        x_center = (xmin + xmax) / 2.0 / img_width
                        y_center = (ymin + ymax) / 2.0 / img_height
                        width = (xmax - xmin) / img_width
                        height = (ymax - ymin) / img_height
                        
                        # Class ID is 0 (assuming a single class like 'car')
                        f.write(f"0 {x_center} {y_center} {width} {height}\n")
            else:
                # Create empty label file for negative samples
                open(dst_label_path, 'a').close()
                
    process_split(train_imgs, 'train')
    process_split(val_imgs, 'val')
    print("Dataset converted to YOLO format in 'yolo_dataset' folder!")

if __name__ == "__main__":
    main()
