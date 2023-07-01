import sys
import mss
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QVBoxLayout, QGridLayout, QFrame
from PyQt5.QtGui import QPainter, QColor, QScreen, QPen, QIcon
from PyQt5.QtCore import pyqtSlot, QTimer
import cv2
import numpy as np

class Overlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.pen = QtGui.QPen(QtGui.QColor(0,255,0,255))                
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setGeometry(0, 0, 1000, 1000)
        self.move(0, 0)
        self.initUI()

        # y coordinate of center of top row in inventory
        self.inventory_top = 314
        # x coordinate of center of right column in inventory
        self.inventory_right = 621

        # y coordinate of center of bot row in inventory
        self.inventory_bot = 707
        # x coordinate of center of left most column in inventory
        self.inventory_left = 72

        # x coordinate of center of left most stash tab icon in inventory
        self.stash_left = 244
        # x coordinate of center of right most stash tab icon in inventory
        self.stash_right = 448


        # coordinates of edge border of four sets of stash tabs
        self.stash_border_top = 144
        self.stash_border_left = 219
        self.stash_border_bot = 193
        self.stash_border_right = 485
        
        self.stash_x_step = (self.stash_right - self.stash_left) //  3

        self.stash_rect_width = 60
        self.stash_rect_height  = 60

        self.inventory_rect_width = 50
        self.inventory_rect_height = 80

        self.inventory_x_step = (self.inventory_right - self.inventory_left) / 9
        self.inventory_y_step = (self.inventory_bot - self.inventory_top) / 4

        self.index_list = []
        self.inventory_list = []
        self.stash_active = 0
        self.stash_index_found = [0,0,0,0]


    def initUI(self):
        container = QFrame()
        container.setFixedSize(200, 200)  # Set fixed size for the container

        self.x_input = QLineEdit()
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_inventory_highlights)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_highlights)
        self.x_input.returnPressed.connect(self.update_button.click)

        layout = QVBoxLayout(container)
        layout.addWidget(self.x_input)
        layout.addWidget(self.update_button)
        layout.addWidget(self.clear_button)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(container)
        main_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)  
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_widget)
        self.timer.start(500)  # Update every 0.5 seconds

    """
        List of inventory OCR strings (250 strings)
    """
    def set_inventory_list(self, inventory_list):
        self.inventory_list = inventory_list
        print(self.inventory_list)

    """
        Captures four stash tabs and determines which one is active by detecting red pixels 
    """
    def updateActiveStashTab(self):
        stash_image = ''
        with mss.mss() as sct:
            monitor = {'top': self.stash_border_top, 'left': self.stash_border_left, 'width': self.stash_border_right - self.stash_border_left, 'height': self.stash_border_bot - self.stash_border_top}
            stash_image = np.array(sct.grab(monitor))

        stash_ind_image = []
        for i in range(0,4):
            stash_ind_image.append(stash_image[:, 0+i*self.stash_x_step:50+i*self.stash_x_step])

            img_hsv = cv2.cvtColor(stash_ind_image[i], cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(img_hsv, (0,200,150), (1,255,255))
            mask = mask1

            if cv2.countNonZero(mask) > 5:
                self.stash_active = i

    """
        Draws green rectangles around items that are in the index_list
    """
    def paintEvent(self, event):

        self.updateActiveStashTab()
        painter = QPainter(self)
        pen = QPen(QColor(0,255,0,255))
        pen.setWidth(4)  # Set the thickness of the border here
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))

        # Highlight stash tabs that are in the list 
        for i in range(0,len(self.stash_index_found)):
            if self.stash_index_found[i] == 1:
                painter.drawRect(self.stash_border_left + self.stash_x_step * i, self.stash_border_top, self.stash_rect_width, self.stash_rect_height)

        # Highlight inventory items that are in the current stash tab that are in the list
        for index in self.index_list:
            if int(index / 50) != self.stash_active:
                continue
            inventory_index = index % 50
            inventory_index_x = inventory_index % 10
            inventory_index_y = int(inventory_index / 10)

            box_x = int(self.inventory_right - self.inventory_x_step * inventory_index_x)
            box_y = int(self.inventory_top + self.inventory_y_step * inventory_index_y) 

            painter.drawRect(box_x - int(self.inventory_rect_width / 2), box_y - int(self.inventory_rect_height / 2), self.inventory_rect_width, self.inventory_rect_height)
        
    def update_widget(self):
        self.update()

    def clear_highlights(self):
        self.index_list = []
        self.stash_index_found = [0,0,0,0]

    def update_inventory_highlights(self):
        self.stash_index_found = [0,0,0,0]
        query = self.x_input.text()
        self.index_list = []
        for i in range(0,len(self.inventory_list)):
            if query in self.inventory_list[i]:
                self.stash_index_found[int(i/50)] = 1
                self.index_list.append(i)
        self.update()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv) 

    widget = Overlay()
    widget.show()
    sys.exit(app.exec_())