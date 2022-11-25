import sys
import time
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
matplotlib.use('Qt5Agg')
import numpy as np
import os
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSpinBox, QHBoxLayout, QWidget, QTableWidget, \
    QTableWidgetItem, QCheckBox, QComboBox, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import pandas as pd
from datetime import date
from os import listdir
from os.path import isfile, join

app = QApplication(sys.argv)
app.setStyle('Fusion')

class MainWindow(QMainWindow):
    def __init__(self):
        global Hwidget1, Hbox1, scan_scroll, scan_scroll, ax, coord, table, nbcol, daydate, initials_text, temp_text, repetitions_text
        super().__init__()
        self.setWindowTitle("PoulPyX")
        self.setFixedSize(QSize(1600,900))   #### TO CHANGE LATER ACCORDING TO SCREEN 
        
        # Get the date of the day for file numbering
        today = date.today()
        daydate = today.strftime("%y%m%d")
        
        coord = []   # For later saving of coordinates clicked on the graph

        # Figure
        Hwidget4 = QWidget(self)
        Hwidget4.setGeometry(10, 355, 1361, 535)
        Hbox4 = QVBoxLayout(Hwidget4)
        Hbox4.setContentsMargins(0, 0, 0, 0)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        ax = self.figure.add_subplot(111)
        plt.tight_layout()
        Hbox4.addWidget(self.canvas)	
        Hbox4.addWidget(NavigationToolbar(self.canvas, self))
        self.canvas.draw()

        # Create horizontal box for lineup selection button and scan selection
        Hwidget1 = QWidget(self)
        Hwidget1.setGeometry(20, 20, 261, 80)
        Hbox1 = QHBoxLayout(Hwidget1)
        Hbox1.setContentsMargins(0, 0, 0, 0)

        # Lineup selection buttons 
        lineup_button = QPushButton("Select lineup file", Hwidget1)    # select the lineup file
        Hbox1.addWidget(lineup_button)
        lineup_button.setGeometry(200, 150, 150, 50)

        # Scan selection scroll
        scan_scroll = QSpinBox(Hwidget1)    # choose scan number
        scan_scroll.setMinimum(0)           # initialize with no scan choice
        scan_scroll.setMaximum(0)
        Hbox1.addWidget(scan_scroll)

        lineup_button.clicked.connect(self.lineup_clicked)   # Opens the file selction window when button clicked 
        scan_scroll.valueChanged.connect(self.scan_changed)  # Creates a signal of scan change to change the transmission figure

        # Cursor for the figure / clickable
        self.canvas.mpl_connect('button_press_event', self.onclick)

        # Button to refresh the table, button ok, button cancel
        Vwidget1 = QWidget(self)
        Vwidget1.setGeometry(1410, 790, 160, 91)
        Vbox1 = QVBoxLayout(Vwidget1)
        Vbox1.setContentsMargins(0, 0, 0, 0)

        update_button = QPushButton("Update table",self)
        update_button.setGeometry(1400, 370, 158, 28)
        update_button.clicked.connect(self.update_clicked)

        macro_button = QPushButton("Generate macro",Vwidget1)
        Vbox1.addWidget(macro_button)
        macro_button.clicked.connect(self.macro_clicked)
        cancel_button = QPushButton("Cancel",Vwidget1)
        Vbox1.addWidget(cancel_button)
        #### ADD CANCEL OPTION #######

        # Table
        nbcol = 1  
        table = QTableWidget(self)
        table.setRowCount(8)
        table.setColumnCount(nbcol)
        table.setGeometry(300, 20, 1281, 322)
        table.setVerticalHeaderLabels(['Name', 'Meas. type', 'x pos.', 'z pos.', 'Flux', 
        'Measurement time (s)', 'Same as previous', 'Thickness (cm)'])
        for i in range(nbcol):
            check1 = QCheckBox()    # Check box for "same as previous"
            scroll1 = QComboBox()   # Scroll for "sample/air/lupo"
            scroll1.addItems(["Sample", "Air", "Water", "Empty campillary", "Lupo/PE"])
            table.setCellWidget(6, i, check1)
            table.setCellWidget(1, i, scroll1)

        # Temperatures, repetitions and initials
        repetitions_label = QLabel("Nr. repetitions", self)
        repetitions_label.setGeometry(20, 130, 85, 60)
        repetitions_text = QTextEdit(self)
        repetitions_text.setGeometry(120,140, 150, 40)

        temp_label = QLabel("Temperatures", self)
        temp_label.setGeometry(20, 190, 85, 60)
        temp_text = QTextEdit(self)
        temp_text.setGeometry(120, 200, 150, 40)

        initials_label = QLabel("Initials", self)
        initials_label.setGeometry(20, 250, 80, 60)
        initials_text = QTextEdit(self)
        initials_text.setGeometry(120,260, 150, 40)


    def lineup_clicked(self):
        global scan_scroll, lineup
        lineup_sel = QFileDialog.getOpenFileName()
        lineup = lineup_sel[0] 
        if "_lineup" in lineup:
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
                    if ("#C") in lineup_lines[j]:      # '#C' means the end of measurement (even if aborted)
                        break      #if there are not enough points (aborted), stops before the #C line anyway
                    else:
                        c = lineup_lines[j].split()
                        xpos_list.append(float(c[0]))
                        tr_list.append(float(c[9]))

        ax.clear()
        ax.plot(xpos_list, tr_list, ls='-', marker='o', color='b', ms=4)	
        self.cursor = Cursor(ax, horizOn=True, vertOn=True, useblit=True, color = 'r', linewidth = 1)	# Tadaaaaaaah !
        self.canvas.draw()      ##### CHANGEMENT DE TYPE DE TRACE QD CLICK : A CORRIGER ##########
    
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

        # Clear all markers and text (necessary for unclicking procedure)
        for aline in ax.lines:
            aline.set_marker(None)
        for txt in ax.texts:
            txt.set_visible(False)

        # Redraw with updated points
        nb = 0
        for ctuple2 in coord:
            nb = nb+1
            ax.plot(ctuple2[0],ctuple2[1], marker='+', color='r', mew=2.0, ms=8)
            #ax.text(ctuple2[0]-0.4,ctuple2[1]-(tr_max-tr_min)/12, str(nb), color='r', weight='bold')   ### VOIR OU PLACER TEXTE CHIFFRE ####
        self.canvas.draw()    #redraw the figure
        #plt.savefig(figpath, bbox_inches='tight',dpi=100)

    def update_clicked(self):
        table.setColumnCount(len(coord))
        for i in range(len(coord)):
            check1 = QCheckBox()    #check box for "same as previous"
            scroll1 = QComboBox()   #scroll for "sample/air/lupo/ec"
            scroll1.addItems(["Sample", "Air", "Water", "Empty campillary", "Lupo/PE"])
            table.setCellWidget(1, i, scroll1)
            xval = QTableWidgetItem(str(round(coord[i][0], 1)))   #we have to switch to str for filling the cells
            fval = QTableWidgetItem(str(round(coord[i][1])))
            table.setItem(2, i, xval)
            table.setItem(4, i, fval)
            table.setCellWidget(6, i, check1)

    def macro_clicked(self):
        column_nb = table.columnCount()
        df = pd.DataFrame()
        for i in [0,1,2,3,4,5,7]:
            for j in range(column_nb):
                widget = table.cellWidget(i,j)
                if isinstance(widget, QComboBox):
                    cell_value = widget.currentText()
                else:
                    try:
                        cell_value = table.item(i, j).text()
                    except:
                        cell_value = "0" 
                df.loc[i, j] = cell_value
                # [0='Name', 1='Meas. type', 2='x pos.', 3='z pos.', 4='Flux', 5='Measurement time (s)', 7='Thickness (cm)']

        workdir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        temperatures = temp_text.toPlainText()
        initials = initials_text.toPlainText()
        repetitions = repetitions_text.toPlainText()

        temp_str_list = temperatures.split(',')  #split des températures

        path1 = str(daydate)+'_'+str(initials)
        extentlist = ["_macro.mac", "_parameters.csv", "_lupo.txt"]
        filelist= [f for f in listdir(workdir) if isfile(join(workdir, f))]   ## Note : workdir remplace pfx

        a2 = path1   #incrementation of names of macro, parameters, lupo files if necessary
        for inc in np.arange(2,1001,1):
            if any((str(a2)+i) in filelist for i in extentlist):
                a2 = path1+'-'+str(inc)
            else:
                break

        # Create macro
        ztest = ''
        temptest = ''
        heat = False
        cool = False
        tempreg = False  #checks if the temperature regulation has been used
        tr_vac = ''
        templine = ''

        macropath = os.path.join(workdir,str(a2)+"_macro.mac")    ## Note : macropath remplace runpath
        parampath =  os.path.join(workdir,str(a2)+"_parameters.csv")
        lupopath =  os.path.join(workdir,str(a2)+"_lupo.txt")

        with open(macropath, 'w') as f:
            f.write('sc'+'\n')
            f.write('\n')
            if temp_str_list!='':
                for temp_sample in temp_str_list:
                    if temp_sample!='' and temp_sample!=temptest:  #if temp is the same or if temp field is not filled, we don't write set_temp again
                        tempreg = True
                        if 40 >= float(temp_sample) >= 10:    #loops for conditions on turning on/off heating and cooling
                            if heat==False:
                                f.write('heat_on'+'\n')
                                heat=True
                            if cool==False:
                                f.write('cool_on'+'\n')
                                cool=True
                        if float(temp_sample) > 40:
                            if heat==False:
                                f.write('heat_on'+'\n')
                                heat=True
                            if cool==True:
                                f.write('cool_off'+'\n')
                                cool = False
                        if float(temp_sample) < 10:
                            if heat==True:
                                f.write('heat_off'+'\n')
                                heat=False
                            if cool==False:
                                f.write('cool_on'+'\n')
                                cool = True
                        sleep_time = 900     #standard 15 min for equilibration
                        f.write('set_temp '+str(temp_sample)+'\n')
                        f.write('sleep('+str(sleep_time)+')'+'\n')

                    templine = '_T'+str(temp_sample)
                    temptest = temp_sample     ##### SHIFTED

                    ######## FINISH MACRO


window = MainWindow()
window.show()

app.exec()
