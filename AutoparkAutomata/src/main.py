from __future__ import print_function
import cv2
import numpy as np
import pytesseract as tess
import string
import PySimpleGUI as sg
import io
from statistics import mode
from sys import exit as exit
from PIL import Image
import time
from threading import Thread
from imutils.video import WebcamVideoStream
import imutils
from pyfirmata import Arduino, util, STRING_DATA, SERVO
from multiprocessing import Queue, Process




def none(a):
    pass

class Vehicle:
    def __init__(self,NP,NPMode,imgResult,NumPlatePres):
        self.NumPlate = NP
        self.NumPlateMode = NPMode
        self.imgResult = imgResult
        self.NumPlatePres = NumPlatePres


class WebcamVideoStream:
    def __init__(self,src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed,self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


class Program:

    def imageProcessing(self,q):
        tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        # GUI
        # Layout

        sg.ChangeLookAndFeel("LightBlue")

        layout = [
            [sg.Text("AutoparkAutomata Kontrol ve Yönetim Paneli", size=(50, 1), justification='center',
                     font='Helvetica 15')], #AutoparkAutomata Control and Management Panel v1.0
            [sg.Text("v1.0", size=(4, 1), justification="right", font="Verdana 10 italic")],
            [sg.HSeparator()],
            [sg.Text("Giriş Plaka", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Image(filename="", key="-IMGENT-"), sg.Image(filename="", key="-IMGENTNP-")], #Entrance Number Plate pic
            [sg.Text("Çıkış Plaka", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Image(filename="", key="-IMGEXT-"), sg.Image(filename="", key="-IMGEXTNP-")],
            [sg.HSeparator()], #Exit Number Plate pic
            [sg.Text("Giriş Okn. Plaka", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-ENTREAD-"), #Ent nmpt reads
             sg.Text("Giriş Okn. Plk. Mod", size=(20, 1), justification="right", font="Verdana 10"),
             sg.Text(key="-ENTMODE-")], #Ent nmpt reads mode
            [sg.Text("Çıkış Okn. Plaka", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-EXTREAD-"), #Exit nmpt reads
             sg.Text("Çıkış Okn. Plk. Mod", size=(20, 1), justification="right", font="Verdana 10"),
             sg.Text(key="-EXTMODE-")], #Exit nmpt reads mode
            [sg.Text("Plaka Envanteri", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Listbox(values=[], enable_events=True, size=(10, 5), key="-INVENTORY-")], #Plate inventory
            [sg.Text("Boş Yer Sayısı", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-EMPTYSPACE-")], #No. of Empty Spaces Left
            [sg.HSeparator()],
            [sg.Text("Giriş Araç Bulunma Drm.", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-CARPRESENT-")], #Entrance Car Presence Stat.
            [sg.Text("Çıkış Araç Bulunma Drm.", size=(20, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-CARPRESEXT-")], #Exit Car Presence Stat.
            [sg.HSeparator()],
            [sg.Text("Çalıntı Araç Plaka Giriş", size=(20, 1), justification="right", font="Verdana 10"),
             sg.InputText(enable_events=True, key="-STOLENIN-"), #Stolen Plate Entry
             sg.ReadButton('Değer Ekle', size=(10, 1), font='Verdana 7'), #Add Value
             sg.ReadButton('Değer Çıkar', size=(10, 1), font='Verdana 7')], #Remove Value
            [sg.Text("Çalıntı Araç Plaka Liste", size=(20, 1), justification="right", font="Verdana 10"),
             sg.Listbox(values=[], enable_events=True, size=(10, 5), key="-STOLENLIST-")], #"Stolen Plates List"
            [sg.Text("Çalıntı Araç Bulunma Durumu", size=(25, 1), justification="right", font="Verdana 10"),
             sg.Text(key="-STOLENBOOL-")], #"Stolen Plate Detection Status"
            [sg.HSeparator()],
            [sg.Text("Giriş Kapısı Drm.", size=(25, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-ENTBOOL-")], #"Entrance Gate Status"
            [sg.Text("Çıkış Kapısı Drm.", size=(25, 1), justification="left", font="Verdana 10"),
             sg.Text(key="-EXTBOOL-")] #"Exit Gate Status"
        ]

        window = sg.Window('AuOKYS v1.0 Akasya', layout,icon=r'images/logo.ico')

        NPcascade = cv2.CascadeClassifier("images/turnumpt.xml")

        text = []
        cur_frame = 0
        NPMode = 0
        NPModeExt = 0
        NPNumberRet = 0
        NPNumberRetExt = 0
        NPList = []
        NPListExt = []
        NPInv = []
        StolenNPList = []
        char_whitelist = string.digits
        char_whitelist += string.ascii_lowercase
        char_whitelist += string.ascii_uppercase
        kernel = np.ones((5, 5))
        img = WebcamVideoStream(src=1).start()
        imgExt = WebcamVideoStream(src=2).start()

        dsentlast = 0
        dsextlast = 0
        invlast = 0
        exports = [0, 0, 16]

        while True:

            img1 = img.read()
            img2 = imgExt.read()
            imgCopy = img1.copy()
            img2ndCopy = img2.copy()
            imgGray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            imgHSV = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            imgGrayExt = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            imgHSVExt = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

            lower = np.array([[0], [255], [0]])
            upper = np.array([[179], [255], [255]])
            lower1 = np.array([[0], [0], [0]])
            upper1 = np.array([[179], [255], [255]])

            def applyCascadeNP(GrayIMG, PlainIMG, HSVIMG):  #Apply LBPCASCADE to frame, cover the number plate with a green rectangle
                detects = NPcascade.detectMultiScale(GrayIMG, 1.1, 4)
                for (x, y, w, h) in detects:
                    cv2.rectangle(PlainIMG, (x, y), (x + w, y + h), (0, 255, 0), 1)
                    cv2.rectangle(HSVIMG, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                    b = (y + h)
                    a = (x + w)
                    bRect = [x, y, a, b]
                    return bRect

            def applyEffectsNP(ApplyTo, mask): #Remove all parts not covered within the rectangle, cut the black space surrounding the plate
                imgTSRGray = cv2.cvtColor(ApplyTo, cv2.COLOR_BGR2GRAY)
                imgTSRGray = cv2.bitwise_and(imgTSRGray, imgTSRGray, mask=imgMask1)
                try:
                    (x, y) = np.where(mask == 255)
                    (x1, y1) = (np.min(x), np.min(y))
                    (x2, y2) = (np.max(x), np.max(y))
                    imgTSRGray = imgTSRGray[x1:x2 + 1, y1:y2 + 1]
                except:
                    pass
                return imgTSRGray

            def doOCR(ApplyTo): #Read the number plate using Tesseract OCR
                text = tess.image_to_string(ApplyTo,
                                            config="-c tessedit_char_whitelist=%s_-." % char_whitelist).upper().strip()
                print("a" + text)
                if len(text.strip().upper()) == 8:
                    if text != None:
                        if text != []:
                            try:
                                return text
                            except:
                                pass


            # NUMBER PLATE PROCESSING
            # entrance
            applyCascadeNP(imgGray, img1, imgHSV)

            imgMask = cv2.inRange(imgHSV, lower, upper)

            imgMask1 = cv2.inRange(imgHSV, lower1, upper1)

            imgTSR = cv2.bitwise_and(imgCopy, imgCopy, mask=imgMask)

            imgResult = applyEffectsNP(imgTSR, imgMask)

            NPNumber = doOCR(imgResult)

            NPNumberPresEnt = bool(NPNumber)

            imgHSVdisp = cv2.resize(imgHSV, (160, 120))

            imgResultdisp = cv2.resize(imgResult, (160, 120))

            # exit

            applyCascadeNP(imgGrayExt, img2, imgHSVExt)

            imgMaskExt = cv2.inRange(imgHSVExt, lower, upper)

            imgMask1Ext = cv2.inRange(imgHSVExt, lower1, upper1)

            imgTSRExt = cv2.bitwise_and(img2ndCopy, img2ndCopy, mask=imgMaskExt)

            imgResultExt = applyEffectsNP(imgTSRExt, imgMaskExt)

            NPNumberExt = doOCR(imgResultExt)

            NPNumberPresExt = bool(NPNumberExt)

            imgHSVdispExt = cv2.resize(imgHSVExt, (160, 120))

            imgResultdispExt = cv2.resize(imgResultExt, (160, 120))

            # ENTRANCE

            # Read the number plate 3 times, accept the mode as the ultimate value to be used in further processing

            if NPNumber != None:
                if NPNumber != []:
                    print(NPNumber)
                    NPList.append(NPNumber)
                    NPNumberRet = NPNumber

            try:
                if len(NPList) > 2:
                    NPMode = mode(NPList)
                    if NPMode != 0 or None:
                        NPList.clear()
            except:
                pass

            #EXIT

            if NPNumberExt != None:
                if NPNumberExt != []:
                    print(NPNumberExt)
                    NPListExt.append(NPNumberExt)
                    NPNumberRetExt = NPNumberExt

            try:
                if len(NPListExt) > 2:
                    NPModeExt = mode(NPListExt)
                    if NPModeExt != 0 or None:
                        NPListExt.clear()
            except:
                pass

            # inventory keeping
            if 0 in NPInv:
                NPInv.remove(0)

            if NPMode not in NPInv:
                NPInv.append(NPMode)
            if NPModeExt != [] or 0 and NPModeExt in NPInv:
                try:
                    NPInv.remove(NPModeExt)
                except:
                    pass

            vehicleEnt = Vehicle(NPNumberRet, NPMode, imgResult, NPNumberPresEnt)
            vehicleExt = Vehicle(NPNumberRetExt, NPModeExt, imgResultExt, NPNumberPresExt)
            ardnNPModeEnt = vehicleEnt.NumPlateMode
            ardnNPModeExt = vehicleExt.NumPlateMode
            ardnNPPresEnt = vehicleEnt.NumPlatePres
            ardnNPPresExt = vehicleExt.NumPlatePres

            #If the Number plate read mode is not 0 and a number plate is still being detected then a car has completed processing and is waiting for the door to open

            if ardnNPModeEnt != 0:
                if ardnNPPresEnt != False:
                    doorStatEnt = 1

                else:
                    doorStatEnt = 0

            else:
                doorStatEnt = 0


            if ardnNPModeExt != 0:
                if ardnNPPresExt != False:
                    doorStatExt = 1

                else:
                    doorStatExt = 0

            else:
                doorStatExt = 0



            event, values = window.read(timeout=0)

            #Transform OpenCV output to images to be displayed.

            try:
                EntDispImg = Image.fromarray(imgHSVdisp)  # create PIL image from frame
                bio = io.BytesIO()  # a binary memory resident stream
                EntDispImg.save(bio, format='PNG')  # save image as png to it
                EntDispImgBytes = bio.getvalue()  # this can be used by OpenCV
                window["-IMGENT-"].Update(data=EntDispImgBytes)

                EntDispImgExt = Image.fromarray(imgHSVdispExt)  # create PIL image from frame
                bio1 = io.BytesIO()  # a binary memory resident stream
                EntDispImgExt.save(bio1, format='PNG')  # save image as png to it
                EntDispImgBytesExt = bio1.getvalue()  # this can be used by OpenCV
                window["-IMGEXT-"].Update(data=EntDispImgBytesExt)

                EntDispImgNP = Image.fromarray(imgResultdisp)  # create PIL image from frame
                bio2 = io.BytesIO()  # a binary memory resident stream
                EntDispImgNP.save(bio2, format='PNG')  # save image as png to it
                EntDispImgNPBytes = bio2.getvalue()  # this can be used by OpenCV
                window["-IMGENTNP-"].Update(data=EntDispImgNPBytes)

                ExtDispImgNP = Image.fromarray(imgResultdispExt)  # create PIL image from frame
                bio3 = io.BytesIO()  # a binary memory resident stream
                ExtDispImgNP.save(bio3, format='PNG')  # save image as png to it
                ExtDispImgNPBytes = bio3.getvalue()  # this can be used by OpenCV
                window["-IMGEXTNP-"].Update(data=ExtDispImgNPBytes)

            except:
                pass

            #Update GUI spaces

            window['-ENTREAD-'].Update(vehicleEnt.NumPlate)
            window['-ENTMODE-'].Update(vehicleEnt.NumPlateMode)
            window['-EXTREAD-'].Update(vehicleExt.NumPlate)
            window['-EXTMODE-'].Update(vehicleExt.NumPlateMode)
            window['-INVENTORY-'].Update(NPInv)
            window["-EMPTYSPACE-"].Update((16 - len(NPInv)))

            if event == "Değer Ekle": #Add Value
                StolenNPList.append(values["-STOLENIN-"])
            elif event == "Değer Çıkar": #Remove Value
                StolenNPList.remove(values["-STOLENIN-"])

            window["-STOLENLIST-"].Update(StolenNPList)

            if vehicleEnt.NumPlateMode in StolenNPList:
                window["-STOLENBOOL-"].Update("Bulundu!") #Found!
            else:
                window["-STOLENBOOL-"].Update("Bulunmadı") #Not Found

            #Check if the reads have changed or not. If they have, put them on queue.

            if dsentlast != doorStatEnt:
                dsentlast = doorStatEnt
                exports[0] = doorStatEnt
                q.put(exports)

            elif dsextlast != doorStatExt:
                dsextlast = doorStatExt
                exports[1] = doorStatExt
                q.put(exports)

            elif invlast != (16 - len(NPInv)):
                invlast = (16 - len(NPInv))
                exports[2] = (16 - len(NPInv))
                q.put(exports)



            if event == sg.WINDOW_CLOSED or values is None:
                img.stop()
                imgExt.stop()
                break


    def arduinoComms(self,q):
        # ARDUINO VARS
        board = Arduino('COM7') #Arduino serial port initialize
        board.digital[9].mode = SERVO #Micro servo initialize
        board.digital[6].mode = SERVO
        while True:
            recv = q.get() #recover [entrygate car presence, exitgate car presence, free spaces] from queue
            if recv[2]:
                board.send_sysex(STRING_DATA, util.str_to_two_byte_iter("Bos Yer:")) #"Free Spaces"
                board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(str(recv[2])))

            if recv[0] == 1:
                board.digital[9].write(90) #Open gate
                time.sleep(5)
                board.digital[9].write(0) #Close gate

            elif recv[1] == 1:
                board.digital[6].write(90) #Same as given above
                time.sleep(5)
                board.digital[6].write(0)




run = Program()


if __name__ == '__main__':
    queue = Queue()
    p = Process(target=run.imageProcessing,args=(queue,))
    p1 = Process(target=run.arduinoComms,args=(queue,))
    p.start()
    p1.start()


    p.join()
    p1.join()




