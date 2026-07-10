import cv2
import numpy as np

def get_color_palette(num_classes=80):
    """
    Generates a color palette with unique colors for each class ID using HSV space.
    """
    np.random.seed(42)
    colors = []
    for i in range(num_classes):
        hue = int(360 * i / num_classes)
        saturation = int(90 + np.random.rand() * 10)
        value = int(200 + np.random.rand() * 55)
        
        hsv_color = np.uint8([[[hue // 2, saturation, value]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        colors.append(tuple(int(c) for c in bgr_color))
    return colors

def draw_bounding_box(image, label, confidence, box, color):
    """
    Draws a bounding box and a label with a solid background banner for high readability.
    """
    xmin, ymin, xmax, ymax = map(int, box)
    
    cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
    text = f"{label} {confidence:.2f}"
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    text_offset_y = 5
    text_ymin = ymin - text_h - text_offset_y - baseline
    
    if text_ymin < 0:
        text_ymin = ymin + text_h + text_offset_y
        cv2.rectangle(image, (xmin, ymin), (xmin + text_w + 10, text_ymin + baseline + 5), color, -1)
        cv2.putText(image, text, (xmin + 5, text_ymin + 5), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    else:
        cv2.rectangle(image, (xmin, text_ymin), (xmin + text_w + 10, ymin), color, -1)
        cv2.putText(image, text, (xmin + 5, ymin - baseline - 2), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    return image
