import pickle
from tqdm import tqdm
import sys
import getopt
import time                                                                                              
import pyautogui
from PIL import Image
import cv2
import pytesseract
import numpy as np
import mss
from tesserocr import PyTessBaseAPI, RIL
from time import perf_counter
from Overlay import Overlay
from PyQt5 import QtCore, QtGui, QtWidgets


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

global inventory_all_list
inventory_all_list = [''] * 200

def update_inventory():
    global inventory_all_list

    time.sleep(1)

    # Coordinates for 1920 x 1080 main monitor

    # y coordinate of center of top row in inventory
    inventory_top = 314
    # x coordinate of center of right column in inventory
    inventory_right = 621

    # y coordinate of center of bot row in inventory
    inventory_bot = 707
    # x coordinate of center of left most column in inventory
    inventory_left = 72

    # y coordinate of center stash icon in inventory
    stash_top = 165
    # x coordinate of center of left most stash tab icon in inventory
    stash_left = 244
    # x coordinate of center of right most stash tab icon in inventory
    stash_right = 448

    # coordinates of top left of item description that pops up during hover
    item_descrip_left_x = 70
    item_descrip_top_y = 100

    # width and height of item description
    item_descrip_width = 350
    item_descrip_height = 720

    inventory_x_step = (inventory_right - inventory_left) / 9
    inventory_y_step = (inventory_bot - inventory_top) / 4
    stash_x_step = (stash_right - stash_left) //  3

    api = PyTessBaseAPI()
    image_list = []

    count = 0

    # Grab images of all items in inventory for OCR
    # For each stash tab
    for k in range(0,4):
        pyautogui.click(stash_left + k * stash_x_step, stash_top)
        time.sleep(0.05)

        # For 5 rows of inventory
        for j in range(0,5):

            # For each column in inventory (start right to left)
            for i in range(0,10):
                time.sleep(0.1)
                pyautogui.middleClick(inventory_right - i * inventory_x_step , inventory_top + j * inventory_y_step)


                image = ''
                with mss.mss() as sct:

                    monitor = {'top': item_descrip_top_y, 'left': item_descrip_left_x + int(inventory_right - i *inventory_x_step), 'width': item_descrip_width, 'height': item_descrip_height}
                    image = np.array(sct.grab(monitor))

                image = Image.fromarray(image) 
                gray = cv2.cvtColor(np.float32(image).astype('uint8'), cv2.COLOR_BGR2GRAY)
                sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpen = cv2.filter2D(gray, -1, sharpen_kernel)
                new_image = Image.fromarray(cv2.threshold(sharpen, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1])
                #new_image.show()

                image_list.append(new_image)

                continue

    # Process OCR
    for n in tqdm(range(0,len(image_list))):
        api.SetImage(image_list[n])
        api.SetVariable("tessedit_do_invert", "0")
        item_text = api.GetUTF8Text()
        inventory_all_list[count] = item_text
        count = count + 1

    print(inventory_all_list)

    # Write current inventory to file if want to reload 
    with open('inventory_list.txt', 'wb') as f:
        pickle.dump(inventory_all_list, f)

if __name__ == '__main__':

    try:
        opts, args = getopt.getopt(sys.argv[1:], "rw")
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        sys.exit(2)

    
    for o, a in opts:
        if o in ("-w"):
            update_inventory()
        elif o in ("-r"):
            with open('inventory_list.txt', 'rb') as f:
                inventory_all_list = pickle.load(f)

    app = QtWidgets.QApplication(sys.argv) 
    widget = Overlay()
    widget.set_inventory_list(inventory_all_list)
    widget.show()
    app.exec_()