from ultralytics import YOLO
import sqlite3
import sys

lost_item = sys.argv[1]

def image_identification():
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
    
    return tags

with sqlite3.connect("image_data.db") as con:
    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS Images (id INTEGER PRIMARY KEY AUTOINCREMENT, tag1 TEXT, tag2 TEXT, tag3 TEXT)")

    tags = image_identification()

    query = f"INSERT INTO Images (tag1) VALUES ('{tags[0]}')"
    cursor.execute(query)
    con.commit()
    images = cursor.execute("SELECT * FROM Images")
    for image in images:
            print(image)