#! /usr/bin/python

# import the necessary packages
from picamera2 import Picamera2
import face_recognition
import pickle
import cv2
import time
import os

# Initialize 'currentname' to trigger only when a new person is identified
currentname = "unknown"
# Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"
# Use this xml file for face detection with Haar cascades
#https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
cascade = "haarcascade_frontalface_default.xml"

# Load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
detector = cv2.CascadeClassifier(cascade)

# Initialize the Raspberry Pi camera using Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
time.sleep(2.0)  # Allow the camera to warm up

# Start the frame per second (FPS) counter
start_time = time.time()

# Loop over frames from the video stream
while True:
    # Capture the frame from the Raspberry Pi camera
    frame = picam2.capture_array()

    # Convert the frame to grayscale for face detection and RGB for face recognition
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect faces in the grayscale frame
    rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
                                      minNeighbors=5, minSize=(30, 30),
                                      flags=cv2.CASCADE_SCALE_IMAGE)

    # Convert bounding boxes from (x, y, w, h) to (top, right, bottom, left)
    boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
    
    # Compute the facial embeddings for each face bounding box
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []

    # Loop over the facial embeddings
    for encoding in encodings:
        # Attempt to match each face in the input image to our known encodings
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"  # Default to "Unknown" if no match is found

        # Check if a match was found
        if True in matches:
            # Get the indices of all matched faces and count each match
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            
        # Count the number of times each face was matched
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # Determine the recognized face with the most matches
            name = max(counts, key=counts.get)

            # If a new person is identified, print their name
            if currentname != name:
                currentname = name
                print(currentname)

        # Add the name to the list of recognized names
        names.append(name)
        
        # Loop over the recognized faces and draw rectangles around them
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # Draw the predicted face's name on the image
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 0, 0), 2)

    # Display the frame to the screen
    cv2.imshow("Facial Recognition", frame)

    # Exit the loop if 'q' is pressed
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Cleanup
cv2.destroyAllWindows()
picam2.stop()
