# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 21:29:58 2017

@author: Dwiki
"""

##Contador de personas
##Federico Mejia
import numpy as np
import cv2
import Person
import time
import sqlite3
import MySQLdb
# import firebase
# import serial

# koneksi dengan sqlite
def insertSQLite(masuk, keluar):
    konek = sqlite3.connect("count.db")
    query = "INSERT INTO hitung(Masuk, Keluar, tanggal, waktu) Values("+str(masuk)+","+str(keluar)+","+str(time.strftime("%Y-%m-%d"))+","+time.strftime("%H:%M:%S")+")"
    konek.execute(query)
    #mySql
    konek.commit()
    konek.close()

def insertMySql(masuk, keluar):
    konek = MySQLdb.connect(db="count", user="root")
    x = konek.cursor()
    query = "INSERT INTO hitung(masuk, keluar, tanggal, waktu) Values("+str(masuk)+","+str(keluar)+",""NOW()"",""NOW()"")"
    x.execute(query)
    konek.commit()
    konek.close()


# fb = firebase.FirebaseApplication('https://count-4dd03.firebaseio.com/')

#inisialisassi komunikasi dengan arduino
# arduinoKirim = serial.Serial('COM3', 9600)

# def tampilArduino():
#     arduinData = arduinoKirim.readline().decode('ascii')
#     PIR, suhu = arduinData.split(',')
#     print "PIR: ", PIR, "\t\tSuhu : ", suhu
#
# def ambilArduino(num):
#     arduinData = arduinoKirim.readline().decode('ascii')
#     PIR, suhu = arduinData.split(',')
#     try:
#         if num == 0:
#             return PIR
#         elif num == 1:
#             return suhu
#     except:
#         return "Salah akses"

#Contadores de entrada y salida
cnt_up   = 0
cnt_down = 0

# Fuente de video
# cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture('sip.mp4')

#Properti video
##cap.set(3,160) #Width
##cap.set(4,120) #Height

#Cetak properti pengambilan ke konsol
for i in range(19): #range asli 19
    print i, cap.get(i)

w = cap.get(3) #nilai asli 3
h = cap.get(4) #nilai asli 4
frameArea = 2*(h*w) #nilai asli h*w
areaTH = frameArea/250 #konstanta 250
print 'Area Threshold', areaTH

#Jalur masuk / keluar
line_up = int(2*(h/6)) #nilai asli int(2*(h/5))
line_down   = int(3*(h/5)) #nilai asli int(3*(h/5))

up_limit =   int(1*(h/7)) #nilai asli int(1*(h/5))
down_limit = int(4*(h/5)) #nilai asli int(4*(h/5))

print "Red line y:",str(line_down)
print "Blue line y:", str(line_up)
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down]
pt2 =  [w, line_down]
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up]
pt4 =  [w, line_up]
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit]
pt6 =  [w, up_limit]
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit]
pt8 =  [w, down_limit]
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

#Substractor de fondo
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = True)

#Elementos estructurantes para filtros morfoogicos
kernelOp = np.ones((3,3),np.uint8)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((11,11),np.uint8)

#Variables
font = cv2.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1

while(cap.isOpened()):
##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    #Lee una imagen de la fuente de video
    ret, frame = cap.read()
##    frame = image.array

    for i in persons:
        i.age_one() #age every person one frame
    #########################
    #   PRE-PROCESAMIENTO   #
    #########################
    
    #Aplica substraccion de fondo
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    #Binariazcion para eliminar sombras (color gris)
    try:
        ret,imBin= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
        ret,imBin2 = cv2.threshold(fgmask2,200,255,cv2.THRESH_BINARY)
        #Opening (erode->dilate) para quitar ruido.
        mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
        mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)
        #Closing (dilate -> erode) para juntar regiones blancas.
        mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
    except:
        print('EOF')
        print 'UP:',cnt_up
        print 'DOWN:',cnt_down
        break
    #################
    #   CONTORNOS   #
    #################
    
    # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind.
    _, contours0, hierarchy = cv2.findContours(mask2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours0:
        area = cv2.contourArea(cnt)
        if area > areaTH:
            #################
            #   TRACKING    #
            #################
            
            #Falta agregar condiciones para multipersonas, salidas y entradas de pantalla.
            
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv2.boundingRect(cnt)

            new = True
            if cy in range(up_limit,down_limit):
                for i in persons:
                    if abs(cx-i.getX()) <= w and abs(cy-i.getY()) <= h:
                        # el objeto esta cerca de uno que ya se detecto antes
                        new = False
                        i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                        if i.going_UP(line_down,line_up) == True:
                            cnt_up += 1
                            print "Masuk: ", cnt_up, "\t|\tTotal di ruangan: ", cnt_up-cnt_down, "\t|\tPada tanggal :", time.strftime("%Y-%m-%d"), "\t|\tPada Jam :", time.strftime("%H:%M:%S")
                            # tampilArduino()
                            # insertSQLite(cnt_up, cnt_down)
                            insertMySql(cnt_up, cnt_down)
                        elif i.going_DOWN(line_down,line_up) == True:
                            cnt_down += 1
                            print "Masuk: ", cnt_up, "\t|\tTotal di ruangan: ", cnt_up-cnt_down, "\t|\tPada tanggal :", time.strftime("%Y-%m-%d"), "\t|\tPada Jam :", time.strftime("%H:%M:%S")
                            # tampilArduino()
                            # insertSQLite(cnt_up, cnt_down)
                            insertMySql(cnt_up, cnt_down)
                        break
                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        #sacar i de la lista persons
                        index = persons.index(i)
                        persons.pop(index)
                        del i     #liberar la memoria de i
                if new == True:
                    p = Person.MyPerson(pid,cx,cy, max_p_age)
                    persons.append(p)
                    pid += 1     
            #################
            #   DIBUJOS     #
            #################
            cv2.circle(frame,(cx,cy), 5, (0,0,255), -1)
            img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            
    #END for cnt in contours0
            
    #########################
    # DIBUJAR TRAYECTORIAS  #
    #########################
    for i in persons:
        cv2.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv2.LINE_AA)

    #################
    #   IMAGANES    #
    #################
    str_up = 'UP: '+ str(cnt_up)
    str_down = 'DOWN: '+ str(cnt_down)
    frame = cv2.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
    frame = cv2.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
    frame = cv2.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
    frame = cv2.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
    cv2.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv2.LINE_AA)
    cv2.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame, str_down ,(10,90),font,0.5,(255,0,0),1,cv2.LINE_AA)

    cv2.imshow('Frame',frame)
    #cv2.imshow('Mask',mask)

        #firebase upload
    # fb.put('user', 'masuk', cnt_up)
    # fb.put('user', 'keluar', cnt_down)
    # fb.put('user', 'total', cnt_up-cnt_down)
    # fb.put('user', 'hari', time.strftime('%A'))
    # fb.put('user', 'tanggal', time.strftime('%d'))
    # fb.put('user', 'bulan', time.strftime('%B'))
    # fb.put('user', 'tahun', time.strftime('%Y'))
    # fb.put('user', 'jam', time.strftime('%H'))
    # fb.put('user', 'menit', time.strftime('%M'))
    # fb.put('user', 'detik', time.strftime('%S'))
    # fb.put('user', 'suhu', ambilArduino(0))
    # fb.put('user', 'PIR', ambilArduino(1))

    #preisonar ESC para salir
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
#END while(cap.isOpened())

    #firebase upload
# fb.put('user', 'masuk', cnt_up)
# fb.put('user', 'keluar', cnt_down)
# fb.put('user', 'total', cnt_up-cnt_down)
# fb.put('user', 'hari', time.strftime('%A'))
# fb.put('user', 'tanggal', time.strftime('%d'))
# fb.put('user', 'bulan', time.strftime('%B'))
# fb.put('user', 'tahun', time.strftime('%Y'))
# fb.put('user', 'jam', time.strftime('%H'))
# fb.put('user', 'menit', time.strftime('%M'))
# fb.put('user', 'detik', time.strftime('%S'))
# fb.put('user', 'suhu', ambilArduino(0))
# fb.put('user', 'PIR', ambilArduino(1))

#################
#   LIMPIEZA    #
#################
cap.release()
cv2.destroyAllWindows()
