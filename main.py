import cv2
import pyautogui
import time
import numpy as np
import keyboard
from sentdex import PressKey, ReleaseKey, W, A, S, D
import imutils
import threading

CHARACTER_POSITION = [190, 301]
CAPTURE_AREA = ((433, 400), (950, 893))

QUIT = False # We loop in-game until this is set to True.

ALLOWED_KEYS = {W, A, S, D}

# Remove the key from the list of allowed keys for a given interval.
def hold_key(key):
    global ALLOWED_KEYS

    ALLOWED_KEYS.remove(key)

    time.sleep(0.250)

    ALLOWED_KEYS.add(key)

def terminate_program():
    global QUIT
    
    QUIT = True
    
    exit(0)

# Get the center of different objects on the image.
def get_object_locations_from_image(img, object_pixels_x, object_pixels_y, min_radius):
    mask = np.zeros(img.shape, dtype=np.uint8)
    mask[object_pixels_y, object_pixels_x] = [255, 255, 255]
    mask = cv2.dilate(mask, None, iterations=2)
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    coordinates = []

    for c in cnts:
        ((x, y), radius) = cv2.minEnclosingCircle(c)

        M = cv2.moments(c)

        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        if radius > min_radius: #and center[0] > CHARACTER_POSITION[0]:
            coordinates.append((center[0], center[1]))

    return coordinates

keyboard.add_hotkey('c', terminate_program)

time.sleep(2)

while not QUIT:
    img = np.array(pyautogui.screenshot())[CAPTURE_AREA[0][1]:CAPTURE_AREA[1][1], CAPTURE_AREA[0][0]:CAPTURE_AREA[1][0], :]

    # Filter the red and yellow pixels from the image.
    red_vertex_indices = np.where((img[:, :, 0] > 150) & (img[:, :, 1] < 40) & (img[:, :, 1] > 20) & (img[:, :, 2] > 40)) 
    star_vertex_indices = np.where((img[:, :, 0] > 240) & (img[:, :, 1] > 230) & (img[:, :, 2] < 90)) 

    y_coords_apple, x_coords_apple = red_vertex_indices
    y_coords_star, x_coords_star = star_vertex_indices

    # Get the center points of the objects.
    apple_coordinates = get_object_locations_from_image(img, x_coords_apple, y_coords_apple, min_radius=20.5)
    star_coordinates = get_object_locations_from_image(img, x_coords_star, y_coords_star, min_radius=13)
    
    OBJECTS = []

    # Calculate the distance of each object relative to the character's position.
    for x_coord, y_coord in apple_coordinates + star_coordinates:
        OBJECTS.append({"location": (x_coord, y_coord), "distance_horizontal": (x_coord - CHARACTER_POSITION[0])})

    if len(OBJECTS) > 0:
        closest_objective = min(OBJECTS, key=lambda x: x["distance_horizontal"])

        x, y = closest_objective["location"]

        horizontal_distance = closest_objective["distance_horizontal"]
        vertical_distance = (y - CHARACTER_POSITION[1])

        # We only move when the object is in a given radius of our character.
        if horizontal_distance < 260 and vertical_distance > -200:
            # If the object is behind our character:
            if x < CHARACTER_POSITION[0]:
                # If there are more objects, we decide if it is safe to focus on catching the star instead of slashing forward for example.
                if len(OBJECTS) > 1:
                    temp = list(OBJECTS)
                    temp.remove(closest_objective)

                    second_closest_objective = min(temp, key=lambda x: x["distance_horizontal"])

                    condition = 3 * horizontal_distance < second_closest_objective["distance_horizontal"]
                else:
                    condition = True

                if vertical_distance < 30 and vertical_distance > - 100:
                    # If it is safe to catch the star:
                    if condition:
                        key = A
                    # We don't move if it is not safe to do so. Instead, we hold the 'A' key so that we can focus on the apples in the next iteration.
                    else:
                        threading.Thread(target=hold_key, args=(key,)).start()
                        continue
                else:
                    continue
            elif y < CHARACTER_POSITION[1] - 45:
                key = W
            elif y > CHARACTER_POSITION[1] + 45:
                key = S
            else:
                key = D

            if key in ALLOWED_KEYS:
                threading.Thread(target=hold_key, args=(key,)).start()

                PressKey(key)
                ReleaseKey(key)
