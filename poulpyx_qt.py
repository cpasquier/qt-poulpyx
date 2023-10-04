import sys
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
matplotlib.use('Qt5Agg')
import numpy as np
import os
import csv
import pandas as pd
from PyQt5.QtCore import QSize,QRegExp
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSpinBox, QHBoxLayout, QWidget, QTableWidget, \
    QTableWidgetItem, QComboBox, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QMessageBox, QTableView, QLineEdit
from PyQt5.QtGui import QRegExpValidator
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
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
        self.setFixedSize(QSize(1680,950))

        rx1 = QRegExp("^[A-Za-z]+")    # Allows only attached letters in initials (no space, comma, number, tab...)
        rx2 = QRegExp("^[0-9]+")       # Allows only attached numbers in repetitions
        rx3 = QRegExp("^[0-9,.]+")      # Allows only attached numbers, dots and commas in temperatures
        Validator1 = QRegExpValidator(rx1, self)
        Validator2 = QRegExpValidator(rx2, self)
        Validator3 = QRegExpValidator(rx3, self)

        # Get the date of the day for file numbering
        today = date.today()
        daydate = today.strftime("%y%m%d")
        
        coord = []   # For later saving of coordinates clicked on the graph

        # Figure
        Hwidget4 = QWidget(self)
        Hwidget4.setGeometry(20,330,1470,610)
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
        Hwidget1.setGeometry(20,20,260,80)
        Hbox1 = QHBoxLayout(Hwidget1)
        Hbox1.setContentsMargins(0, 0, 0, 0)

        # Lineup selection buttons
        lineup_button = QPushButton("Select lineup file", Hwidget1)    # select the lineup file
        Hbox1.addWidget(lineup_button)
        lineup_button.setGeometry(1,25,125,30)

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
        Vwidget1.setGeometry(1505,780,160,90)
        Vbox1 = QVBoxLayout(Vwidget1)
        Vbox1.setContentsMargins(0, 0, 0, 0)

        update_button = QPushButton("Update table",self)
        update_button.setGeometry(1505,350,160,30)
        update_button.clicked.connect(self.update_clicked)

        macro_button = QPushButton("Generate macro",Vwidget1)
        Vbox1.addWidget(macro_button)
        macro_button.clicked.connect(self.macro_clicked)
        cancel_button = QPushButton("Cancel",Vwidget1)
        Vbox1.addWidget(cancel_button)
        cancel_button.clicked.connect(self.cancel_clicked)
        update_button.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(116, 222, 162, 255), stop:1 rgba(181,222,116, 255))")
        macro_button.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(236,227,120, 255), stop:1 rgba(236,201,120,255))")

        # Table
        nbcol = 1
        table = QTableWidget(self)
        table.setRowCount(7)
        table.setColumnCount(nbcol)
        table.setGeometry(300,20,1360,285)
        table.setVerticalHeaderLabels(['Name', 'Meas. type', 'x pos.', 'z pos.', 'Flux', 'Measurement time (s)', 'Thickness (cm)'])
        for i in range(nbcol):
            scroll1 = QComboBox()   # Scroll for "sample/air/lupo"
            scroll1.addItems(["Sample", "Air", "Water", "Empty campillary", "Lupo/PE"])
            table.setCellWidget(1, i, scroll1)

        # Temperatures, repetitions and initials
        initials_label = QLabel("Initials", self)
        initials_label.setGeometry(65,100,80,60)
        initials_text = QLineEdit(self)
        initials_text.setGeometry(130,110,150,40)
        initials_text.setValidator(Validator1)

        repetitions_label = QLabel("Nr. repetitions"+'\n'+'(if > 1)', self)
        repetitions_label.setGeometry(25,170,95,60)
        repetitions_text = QLineEdit(self)
        repetitions_text.setGeometry(130,180,150,40)
        repetitions_text.setValidator(Validator2)

        temp_label = QLabel("Temperatures"+'\n'+'(if oven is used)', self)
        temp_label.setGeometry(23,240,100,60)
        temp_text = QLineEdit(self)
        temp_text.setGeometry(130,250,150,40)
        temp_text.setValidator(Validator3)

    def lineup_clicked(self):
        global scan_scroll, lineup
        if os.path.isdir('/home/mar345/data/LineUp'):
            lineup_sel = QFileDialog.getOpenFileName(directory='/home/mar345/data/LineUp')   #if on SAXS bench computer, sets default lineup folder
        else:
            lineup_sel = QFileDialog.getOpenFileName()
        lineup = lineup_sel[0]
        if "_lineup" in lineup:
            lineup_file = open(lineup, 'r')
            lineup_lines = lineup_file.readlines()
            lineup_file.close()
            smax = -1000
            smin = 1000
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
        else:
            err_lineup = QMessageBox()
            err_lineup.setIcon(QMessageBox.Critical)
            err_lineup.setWindowTitle("File error")
            err_lineup.setText("Not a lineup file")
            err_lineup.setInformativeText("Please select a file ending with _lineup")
            err_lineup.exec_()

    def scan_changed(self):
        global xpos_list, tr_list, coord
        coord = []
        scan_value = scan_scroll.value()
        lineup_file = open(lineup, 'r')
        lineup_lines = lineup_file.readlines()
        lineup_file.close()
        xpos_list = []
        tr_list = []
        i=-1
        for line in lineup_lines:    # we get the number of scans
            i=i+1
            if ("#S "+str(scan_value)+'  ascan') in line:
                a = line.split()
                b = a[6]             #counts the number of theoretically measured points (input for ascan)
                for j in np.arange(i+14, i+14+int(b)+1, 1):
                    if ("#C") in lineup_lines[j]:      # '#C' means the end of measurement (even if aborted)
                        break        #if there are not enough points (aborted), stops before the #C line anyway
                    else:
                        c = lineup_lines[j].split()
                        xpos_list.append(float(c[0]))
                        tr_list.append(float(c[9]))
        ax.clear()
        ax.plot(xpos_list, tr_list, ls='-', marker='o', color='mediumblue', ms=4)
        self.cursor = Cursor(ax, horizOn=True, vertOn=True, useblit=True, color = 'r', linewidth = 1)
        self.canvas.draw()

    def onclick(self,event):   #saves the clicked coordinates
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

        tr_max = max(tr_list)
        tr_min = min(tr_list)

        # Redraw with updated points
        ax.plot(xpos_list, tr_list, ls='None', marker='o', color='mediumblue', ms=4)
        nb = 0
        for ctuple2 in coord:
            nb = nb+1
            ax.plot(ctuple2[0],ctuple2[1], marker='+', color='r', mew=2.0, ms=8)
            ax.text(ctuple2[0]-0.3,ctuple2[1]-(tr_max-tr_min)/14, str(nb), color='r', weight='bold', size=14)
        self.canvas.draw()    #redraw the figure

    def update_clicked(self):
        table.setColumnCount(len(coord))
        for i in range(len(coord)):
            scroll1 = QComboBox()   #scroll for "sample/air/lupo/ec"
            scroll1.addItems(["Sample", "Air", "Water", "Empty campillary", "Lupo/PE"])
            table.setCellWidget(1, i, scroll1)
            xval = QTableWidgetItem(str(round(coord[i][0], 1)))   #we have to switch to str for filling the cells
            fval = QTableWidgetItem(str(round(coord[i][1])))
            table.setItem(2, i, xval)
            table.setItem(4, i, fval)

    def cancel_clicked(self):
        self.close()

    def macro_clicked(self):
        global df, column_nb
        ## Checking errors
        namelist_test = []
        timelist_test = []
        err1,err2,err3,err4,err5,err6 = ('','','','','','')
        iserr=False
        init_test = initials_text.text()
        tempe_test = temp_text.text()
        tempe_test_list = tempe_test.split(',') 
        for j in range(table.columnCount()):
            type_sample_test =  table.cellWidget(1,j).currentText()
            if type_sample_test!='Air':
                try:
                    namelist_test.append(table.item(0, j).text())
                except:
                    namelist_test.append('')
                try:
                    timelist_test.append(table.item(5, j).text())
                except:
                    timelist_test.append('')
        if '' in namelist_test:
            err1 = "Sample name missing"+'\n'
            iserr=True
        if (0 in timelist_test) or ('' in timelist_test):
            err2="Measurement time missing"+'\n'
            iserr=True
        if len(namelist_test) != len(set(namelist_test)):
            err3="Several samples with same name"+'\n'
            iserr=True
        if init_test=='':
            err4="Initials missing"+'\n'
            iserr=True
        for a in timelist_test:
            if a!='':
                try:
                    float(a)
                except ValueError:
                    err5 = "Error in time entry"+'\n'
                    iserr = True
        for b in tempe_test_list:
            if b!='':
                try:
                    float(b)
                except ValueError:
                    err6 = "Error in temperature entry"+'\n'
                    iserr = True
        if iserr == True:
            err_macro = QMessageBox()
            err_macro.setIcon(QMessageBox.Critical)
            err_macro.setWindowTitle("Warning")
            err_macro.setText(err1+err2+err3+err4+err5+err6)
            err_macro.exec_()
        else:
            ## We write the macro if everything is ok
            column_nb = table.columnCount()
            df = pd.DataFrame()
            for i in range(7):
                for j in range(column_nb):
                    widget = table.cellWidget(i,j)
                    if isinstance(widget, QComboBox):
                        cell_value = widget.currentText()
                    else:
                        try:
                            cell_value = table.item(i, j).text()
                        except:
                            cell_value = ''
                    df.loc[i, j] = cell_value
                    # [0='Name', 1='Meas. type', 2='x pos.', 3='z pos.', 4='Flux', 5='Measurement time (s)', 6='Thickness (cm)']

            workdir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
            if workdir:
                temperatures = temp_text.text()
                initials = initials_text.text()
                repetitions = repetitions_text.text()

                temp_str_list = temperatures.split(',')  #split of temperatures

                path1 = str(daydate)+'_'+str(initials)
                extentlist = ["_macro.mac", "_parameters.csv", "_lupo.txt"]
                filelist= [f for f in listdir(workdir) if isfile(join(workdir, f))]

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
                flux_inc = 0
                flux_nr = 0
                templine = ''

                repetnr=1
                if repetitions!='':
                    repetnr = int(repetitions)

                macropath = os.path.join(workdir,str(a2)+"_macro.mac")
                parampath =  os.path.join(workdir,str(a2)+"_parameters.csv")

                with open(macropath, 'w') as f, open(parampath, 'w', encoding='UTF8') as h:
                    writer = csv.writer(h)
                    header = ['Name', 'Meas. type', 'x pos.', 'z pos.', 'Flux', 'Measurement time (s)', 'Thickness (cm)']
                    writer.writerow(header)
                    f.write('sc'+'\n')
                    f.write('\n')
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
                            temptest = temp_sample
                        else:
                            templine=''
                            temptest = temp_sample

                        for j in range(column_nb):
                            type_sample = df.iloc[1,j]
                            if type_sample == "Air":
                                flux_inc = flux_inc + float(df.iloc[4,j])   # sum of incident flux for later averaging
                                flux_nr = flux_nr + 1                       # number of incident flux for later averaging
                        if flux_nr!=0:
                            flux_inc_moy = flux_inc/flux_nr
                        for j in range(column_nb):
                            type_sample = df.iloc[1,j]
                            if type_sample != "Air":
                                name_sample = df.iloc[0,j]
                                x_sample = df.iloc[2,j]
                                z_tempor = df.iloc[3,j]  #string
                                flux_sample = df.iloc[4,j]
                                time_sample = df.iloc[5,j]
                                thick_sample = df.iloc[6,j]
                                z_str_list = z_tempor.split(',')   #split z_temp in a list of strings using comma sep.
                                writer.writerow([name_sample,type_sample,x_sample,z_tempor,flux_sample,time_sample,thick_sample])   #for csv
                                f.write('umv scx '+str(x_sample)+'\n')   #move to x pos.
                                for z_sample in z_str_list:
                                    if z_sample != '' and z_sample!= ztest:  #if z is the same or if z-pos field is not filled, we don't write umv saz again
                                        f.write('umv saz '+str(z_sample)+'\n')
                                    if len(z_str_list) > 1:
                                        zline ='_z'+str(z_sample)  #puts z value in file name if several
                                    else:
                                        zline = ''
                                    ztest = z_sample

                                    for r in range(repetnr):
                                        acqline = 'startacq '+str(time_sample)+' '+str(daydate)+'_'+str(initials)+'_'+str(name_sample)
                                        testpath1 = workdir+str(daydate)+'_'+str(initials)+'_'+str(name_sample)+zline+templine   #for testing if file exists
                                        testpath2 = testpath1
                                        for inc in np.arange(2,1001,1):
                                            if testpath2 in filelist:    #if there is already a file with the same name in the folder..
                                                testpath2 = testpath1+'-'+str(inc)   #we name the new file with increment
                                            else:
                                                filelist.append(testpath2)  #we store the final name of the new file
                                                break
                                        if testpath2 != testpath1:     #tests if there is a need for increment of the name in the acquisition line
                                            f.write(acqline+zline+templine+'-'+str(inc-1)+'\n')
                                            rptname = str(daydate)+'_'+str(initials)+'_'+str(name_sample)+zline+templine+'-'+str(inc-1)
                                        else:
                                            f.write(acqline+zline+templine+'\n')   #start acquisition, add z and T to file name if relevant
                                            rptname = str(daydate)+'_'+str(initials)+'_'+str(name_sample)+zline+templine
                                        # Save rpt files
                                        rptpath = os.path.join(workdir,rptname+".rpt")
                                        with open(rptpath, 'w') as rpt:
                                            rpt.write('[acquisition]'+'\n')
                                            rpt.write('filename = '+rptname+'\n')
                                            rpt.write('transmittedflux = '+str(flux_sample)+'\n')
                                            rpt.write('thickness = '+str(thick_sample)+'\n')
                                            rpt.write('time = '+str(time_sample)+'\n')
                                            rpt.write('wavelength = 0.71'+'\n')
                                            if flux_nr!=0:
                                                rpt.write('incidentflux = '+str(flux_inc_moy)+'\n')
                                            rpt.write('pixel_size = 0.015'+'\n')
                                        rpt.close()
                    if tempreg==True:     #if the temperature regulation has been activated..
                        f.write('\n'+'set_temp 20'+'\n')  #we put back the target temperature at 20°C at the end..
                        f.write('\n'+'power_off'+'\n')    #and shut down the temperature regulation at the end
                    f.write('\n'+'sc'+'\n')       #close shutter
                    f.write('\n')
                f.close()
                h.close()

window = MainWindow()
window.show()

app.exec()
