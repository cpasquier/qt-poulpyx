import sys
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
matplotlib.use('Qt5Agg')
import numpy as np
import os
import csv
from PyQt5.QtCore import QSize, QFileInfo 
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSpinBox, QHBoxLayout, QWidget, QTableWidget, \
    QTableWidgetItem, QComboBox, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QMessageBox, QTableView, QLineEdit
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import pandas as pd
from datetime import date
from os import listdir
from os.path import isfile, join

app = QApplication(sys.argv)
app.setStyle('Fusion')

class MainWindow(QMainWindow):
    def __init__(self):
        global file_label, q_combo, peak_text, distance_text, pixel_text, time_text, incflux_text, trflux_text, thickness_text, \
            qunit_value, k_label, ax
        super().__init__()
        self.setWindowTitle("PoulPyX")
        self.setFixedSize(QSize(800,750))  

        # Lupo file selection        
        file_button = QPushButton("Select lupo rgr file", self)
        file_button.clicked.connect(self.file_clicked)
        file_label = QLabel(self)
        file_button.setGeometry(30,30,160,30)
        file_label.setGeometry(200,30,530,30)

        # q units selection
        q_label = QLabel("q units", self)
        q_label.setGeometry(130,100,40,26)
        q_combo = QComboBox(self)
        q_combo.setGeometry(190,100,60,26)
        q_combo.addItem("A-1")
        q_combo.addItem("nm-1")
        qunit_value = "A-1"
        q_combo.activated.connect(self.combochanged)

        # Peak intensity
        peak_label = QLabel("Peak intensity (cm-1)", self)
        peak_label.setGeometry(370,100,160,20)
        peak_text = QLineEdit(self)
        peak_text.setGeometry(550,100,130,20)
        peak_text.setText("6.15")

        # Time
        time_label = QLabel("Time (s)", self)
        time_label.setGeometry(40,170,60,20)
        time_text = QLineEdit(self)
        time_text.setGeometry(100,170,90,20)

        # Pixel size
        pixel_label = QLabel("Pixel size (cm)", self)
        pixel_label.setGeometry(260,170,100,20)
        pixel_text = QLineEdit(self)
        pixel_text.setGeometry(350,170,90,20)

        # Sample to detector distance
        distance_label = QLabel("Sample-detector distance (cm)", self)
        distance_label.setGeometry(480,170,180,20)
        distance_text = QLineEdit(self)
        distance_text.setGeometry(670,170,90,20)

        # Incident flux
        incflux_label = QLabel("Incident flux", self)
        incflux_label.setGeometry(40,230,80,20)
        incflux_text = QLineEdit(self)
        incflux_text.setGeometry(120,230,90,20)

        # Transmitted flux
        trflux_label = QLabel("Transmitted flux", self)
        trflux_label.setGeometry(250,230,110,20)
        trflux_text = QLineEdit(self)
        trflux_text.setGeometry(350,230,90,20)

        # Thickness
        thickness_label = QLabel("Thickness (cm)", self)
        thickness_label.setGeometry(480,230,90,20)
        thickness_text = QLineEdit(self)
        thickness_text.setGeometry(580,230,90,20)
        thickness_text.setText("0.238")

        # Button for K calculation
        k_button = QPushButton("Calculate K",self)
        k_button.setGeometry(330,305,90,30)
        k_button.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(236,227,120, 255), stop:1 rgba(236,201,120,255))")
        k_button.clicked.connect(self.kbutton_clicked)

        # K value
        k_label = QLabel("K =",self)
        k_label.setGeometry(330,370,130,20)
        k_label.setFont(QFont('Arial', 12))

        # Figure
        Vwidget = QWidget(self)
        Vwidget.setGeometry(30,415,740,330)
        Vbox = QVBoxLayout(Vwidget)
        Vbox.setContentsMargins(0, 0, 0, 0)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        ax = self.figure.add_subplot(111)
        plt.tight_layout()
        Vbox.addWidget(self.canvas)
        Vbox.addWidget(NavigationToolbar(self.canvas, self))
        self.canvas.draw()

    def file_clicked(self):
        global lupofilepath,q,iq
        lupo_sel = QFileDialog.getOpenFileName()
        lupofilepath = lupo_sel[0]
        q,iq = np.loadtxt(lupofilepath, unpack=True, usecols=(0,1))
        file_label.setText(str(lupofilepath))
        psplit=lupofilepath.split('/')
        path=''
        for i in psplit[:-1]:
            path=path+i+'/'
        last=psplit[-1]
        fname = last.split('.')[0]
        path2=path+fname+'.rpt'
        if os.path.isfile(path2):
            rpt_file = open(path2, 'r')
            rpt_lines = rpt_file.readlines()
            rpt_file.close()
            for line in rpt_lines:
                if ("pyfai.detectordistance") in line:
                    d1 = line.split()
                    d2 = float(d1[2])
                    distance_text.setText(str(round(d2,4)))
                if ("pyfai.pixelsize") in line:
                    p1 = line.split()
                    p2 = float(p1[2])
                    pixel_text.setText(str(p2))

    def combochanged(self):
        global qunit_value
        qunit_value = str(q_combo.currentText())

    def kbutton_clicked(self):
        if (peak_text.text()!='') and (time_text.text()!='') and (pixel_text.text()!='') and (distance_text.text()!='') and \
             (incflux_text.text()!='') and (trflux_text.text()!='') and (thickness_text.text()!=''): 
            if qunit_value=="A-1":
                qpeak = 0.037
            else:
                qpeak = 0.37
            for j in np.arange(0,len(q),1):
                if q[j] < qpeak:
                    x1 = q[j]
                    x2 = q[j+1]
                    y1 = iq[j]
                    y2 = iq[j+1]
                slope = (y1-y2)/(x1-x2)
                intercept = y1 - slope*x1
                i_orig = slope*qpeak + intercept
            setdif = 10000
            goalpeakint = float(peak_text.text())  # goal peak intensity
            time_e = float(time_text.text())
            pixel_e = float(pixel_text.text())
            dist_e = float(distance_text.text())
            incfl_e = float(incflux_text.text())
            trfl_e = float(trflux_text.text())
            thick_e = float(thickness_text.text())
            denom = time_e * (pixel_e**2/dist_e**2) * (trfl_e/incfl_e) * thick_e * trfl_e
            for k in np.arange(0.1, 10000.1, 0.1):
                i_norm_test = i_orig / (denom*k)
                if abs(i_norm_test-goalpeakint)<setdif:
                    kcalc = k
                    setdif = abs(i_norm_test-goalpeakint)
            k_label.setText("K = "+str(kcalc))

            ax.plot(q,iq/(denom*kcalc),'b-',marker='o',ms=5)
            ax.plot(qpeak,goalpeakint,marker='+',color='r',ms=8, mew=2.0)
            plt.xlim(0.5*qpeak,1.5*qpeak)
            plt.ylim(goalpeakint-1.0,goalpeakint+0.5)
            self.canvas.draw()

window = MainWindow()
window.show()

app.exec()
