import cv2
import os
from picamera2 import Picamera2

name = 'Geetika'  # Replace with your name

# Create the directory if it doesn't exist
output_dir = f"dataset/{name}/"
os.makedirs(output_dir, exist_ok=True)

# Initialize the Raspberry Pi camera using Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

cv2.namedWindow("press space to take a photo", cv2.WINDOW_NORMAL)
cv2.resizeWindow("press space to take a photo", 500, 300)

img_counter = 0

while True:
    # Capture frame from the Raspberry Pi camera
    frame = picam2.capture_array()

    cv2.imshow("press space to take a photo", frame)

    k = cv2.waitKey(1)
    if k % 256 == 27:
        # ESC pressed
        print("Escape hit, closing...")
        break
    elif k % 256 == 32:
        # SPACE pressed, take a photo
        img_name = f"{output_dir}/image_{img_counter}.jpg"
        cv2.imwrite(img_name, frame)
        print(f"{img_name} written!")
        img_counter += 1

# Release resources and close windows
cv2.destroyAllWindows()
picam2.stop()
