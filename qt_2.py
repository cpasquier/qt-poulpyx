import sys
import time
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
matplotlib.use('Qt5Agg')
import numpy as np
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSpinBox, QHBoxLayout, QWidget, QTableWidget, \
    QTableWidgetItem, QCheckBox, QComboBox, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure


app = QApplication(sys.argv)
app.setStyle('Fusion')

class MainWindow(QMainWindow):
    def __init__(self):
        global Hwidget1, Hbox1, scroll_exist, scan_scroll, scan_scroll, ax, coord
        super().__init__()
        self.setWindowTitle("PoulPyX")
        self.setFixedSize(QSize(1600,900))   # to change later
        
        coord = []

        # Boutons OK/quitter
        button1 = QDialogButtonBox(self)
        button1.setGeometry(1360, 770, 193, 28)
        button1.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        ############## METTRE EN VERTICAL !! NB : NE MARCHE PAS AVEC VERTICAL LAYOUT #############

        # Figure
        Hwidget4 = QWidget(self)
        Hwidget4.setGeometry(10, 355, 1361, 535)
        Hbox4 = QVBoxLayout(Hwidget4)
        Hbox4.setContentsMargins(0, 0, 0, 0)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        ax = self.figure.add_subplot(111)
        #plt.gca().set_position([0.04, 0.08, 0.94, 0.9])
        plt.tight_layout()
        Hbox4.addWidget(self.canvas)	
        Hbox4.addWidget(NavigationToolbar(self.canvas, self))
        self.canvas.draw()

        # Create horizontal box for lineup selection button and scan selection
        scroll_exist=0

        Hwidget1 = QWidget(self)
        Hwidget1.setGeometry(20, 20, 261, 80)
        Hbox1 = QHBoxLayout(Hwidget1)
        Hbox1.setContentsMargins(0, 0, 0, 0)

        # Lineup selection buttons 
        lineup_button = QPushButton("Select lineup file",Hwidget1)    # select the lineup file
        Hbox1.addWidget(lineup_button)
        lineup_button.setGeometry(200, 150, 150, 50)

        # Scan selection scroll
        scan_scroll = QSpinBox(Hwidget1)    # choose scan number
        scan_scroll.setMinimum(0)    # initialize with no scan choice
        scan_scroll.setMaximum(0)
        Hbox1.addWidget(scan_scroll)

        lineup_button.clicked.connect(self.lineup_clicked)   # Opens the file selction window when button clicked 
        scan_scroll.valueChanged.connect(self.scan_changed)  # Creates a signal of scan change to change the transmission figure
        self.canvas.mpl_connect('button_press_event', self.onclick)
        #plt.show()

        # Table
        nbcol = 5  # TO CHANGE WITH NUMBER OF POINTS
        table = QTableWidget(self)
        table.setRowCount(8)
        table.setColumnCount(nbcol)
        table.setGeometry(300, 20, 1281, 322)
        table.setVerticalHeaderLabels(['Name', 'Meas. type', 'x pos.', 'z pos.', 'Flux', 
        'Measurement time (s)', 'Same as previous', 'Thickness (cm)'])
        for i in range(nbcol):
            check1 = QCheckBox()    # Check box for "same as previous"
            scroll1 = QComboBox()   # Scroll for "sample/air/lupo"
            scroll1.addItems(["Air", "Lupo/PE", "Sample"])
            table.setCellWidget(6, i, check1)
            table.setCellWidget(1, i, scroll1)

        # Temperatures and initials
        temp_label = QLabel("Temperatures", self)
        temp_label.setGeometry(30, 150, 100, 30)
        temp_text = QTextEdit(self)
        temp_text.setGeometry(125, 150, 150, 50)

        initials_label = QLabel("Initials", self)
        initials_label.setGeometry(70, 250, 100, 30)
        initials_text = QTextEdit(self)
        initials_text.setGeometry(125, 250, 150, 30)


    def lineup_clicked(self):
        global scroll_exist, scan_scroll, lineup
        lineup_sel = QFileDialog.getOpenFileName()
        lineup = lineup_sel[0] 
        lineup_file = open(lineup, 'r')
        lineup_lines = lineup_file.readlines()
        lineup_file.close()
        smax = -100
        smin = 100
        for line in lineup_lines:    # we get the number of scans
            if ("#S ") in line:
                a = line.split()
                b = int(a[1])
                if b<smin:
                    smin=b
                if b>smax:
                    smax=b
        scan_scroll.setMinimum(smin)    # update the scroll max/min number in function of numnber of scans
        scan_scroll.setMaximum(smax)
        ############ ERREUR / CRASH SI PAS LE BON FORMAT DE FICHIER --> FAIRE SECURITE CONTRE CA ##############

    def scan_changed(self):
        scan_value = scan_scroll.value()
        lineup_file = open(lineup, 'r')
        lineup_lines = lineup_file.readlines()
        lineup_file.close()
        xpos_list = []
        tr_list = []
        i=-1
        for line in lineup_lines:    # we get the number of scans
            i=i+1
            if ("#S "+str(scan_value)) in line:
                a = line.split()
                b = a[6]          #counts the number of theoretically measured points (input for ascan)
                for j in np.arange(i+14, i+14+int(b)+1, 1):
                    if ("#C") in lineup_lines[j]:      #'#C' means the end of measurement (even if aborted)
                        break      #if there are not enough points (aborted), stops before the #C line anyway
                    else:
                        c = lineup_lines[j].split()
                        xpos_list.append(float(c[0]))
                        tr_list.append(float(c[9]))

        ax.clear()
        ax.plot(xpos_list, tr_list, ls='-', marker='o', color='b', ms=4)	
        self.cursor = Cursor(ax, horizOn=True, vertOn=True, useblit=True, color = 'r', linewidth = 1)	# Tadaaaaaaah !
        self.canvas.draw()
    
    def onclick(self,event):   # saves the clicked coordinates
        x = event.xdata
        y = event.ydata
        flipper=0
        if coord:    #if coord is not an empty list
            for ctuple in coord:
                if (abs(x-ctuple[0]) < 0.5) :   #because coord is a list of tuples:[(x1,y1), (x2,y2)...]
                    flipper=flipper+1
                    coord.remove(ctuple)
                    break
                else:
                    flipper=flipper
        else:   #if coord is empty, automatically add the first point
            flipper=flipper

        if flipper==0:
            coord.append((x,y))     

        print(coord)


window = MainWindow()
window.show()

app.exec()