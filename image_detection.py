from ultralytics import YOLO
import sys

def image_identification(lost_item):
    tags = []
    model = YOLO("yolov8m.pt")
    results = model(lost_item)

    for result in results:
        boxes = result.boxes
        names = result.names
        
        for box in boxes:
            class_id = int(box.cls)
            label = names[class_id]
            confidence = float(box.conf)
            if (confidence > 0.85):
                tags += [label]
    
    tags = [tag for tag in tags if (tag != "person")]
    
    return tags[:2]

if __name__ == "__main__":
    file = sys.argv[1]
    tags = image_identification(file)
    print(tags)