from ultralytics import YOLO

def image_identification(lost_item):
    tags = []
    model = YOLO("yolov8s.pt")

    results = model(lost_item)

    for result in results:
        boxes = result.boxes
        names = result.names
        
        for box in boxes:
            class_id = int(box.cls)
            label = names[class_id]
            confidence = float(box.conf)
            print(f"Detected: {label} ({confidence:.2f})")
            if (confidence):
                tags += [label]
    
    tags = [tag for tag in tags if (tag != "person")]
    
    return tags[:2]
