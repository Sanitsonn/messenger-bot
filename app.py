import apiVulcan
import random
import threading
from flask import Flask, request
from pymessenger.bot import Bot
from datetime import date, timedelta, datetime
import mysql.connector
import json
from py_librus_api import Librus

app = Flask(__name__)
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
bot = Bot(ACCESS_TOKEN)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    database="users"
)

pd = ["praca domowa","pd","pracadomowa","homework", "praca", "domowa"]

mycursor = mydb.cursor()

#We will receive messages that Facebook sends our bot at this endpoint
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']

                mycursor.execute("SELECT recipient_id FROM users")
                users=mycursor.fetchall()
                usersL = []
                for index in range(len(users)):
                    usersL.append(str(users[index][0]))
                #SPRAWDZANIE LOGOWANIA
                if(str(recipient_id) in usersL):
                    mycursor.execute("SELECT `diary` FROM `users` WHERE recipient_id="+recipient_id)
                    diary = mycursor.fetchall()
                    diaryL = []
                    for index in range(len(diary)):
                        diaryL.append(str(diary[index][0]))
                    diary = diaryL[0]
                    #LIBRUS
                    if(diary=="l"):
                        mycursor.execute("SELECT `certificate` FROM `users` WHERE recipient_id="+recipient_id)
                        clientCertificate = mycursor.fetchall()
                        clientCertificateL = []
                        for index in range(len(clientCertificate)):
                            clientCertificateL.append(str(clientCertificate[index][0]))
                        clientCertificate = clientCertificateL[0]
                        clientCertificate = clientCertificate[:-1]
                        clientCertificate = clientCertificate[2:]
                        librus = Librus()
                        try:
                            #WIADOMOSC NIE TEKSTOWA
                            if message['message'].get('attachments'):
                                send_message(recipient_id, "Błędne polecenie!\nDostępne polecenia:\n-sprawdziany\n-szczesliwy numerek\n-dni wolne\n-srednia")
                            #SPRAWDZIANY
                            elif(message['message'].get('text').lower().split()[0] == "sprawdziany"):
                                try:
                                    if("jutro" in message['message'].get('text').lower().split()):
                                        exams = librus.getHomeWork(datetime.strptime(str(date.today()), '%Y-%m-%d') + timedelta(days=1),clientCertificate)
                                        if(exams==""):
                                            send_message(recipient_id, "Brak sprawdzianów na jutro! 🎉")
                                        else:
                                            send_message(recipient_id, exams)
                                    elif("wczoraj" in message['message'].get('text').lower().split()):
                                        exams = librus.getHomeWork(datetime.strptime(str(date.today()), '%Y-%m-%d') - timedelta(days=1),clientCertificate)
                                        if(exams==""):
                                            send_message(recipient_id, "Brak sprawdzianów wczoraj! 🎉")
                                        else:
                                            send_message(recipient_id, exams)
                                    elif("dzisiaj" in message['message'].get('text').lower().split()): #or (len(message['message'].get('text').lower().split())==2):
                                        exams = librus.getHomeWork(datetime.strptime(str(date.today()), '%Y-%m-%d'),clientCertificate)
                                        if(exams==""):
                                            send_message(recipient_id, "Brak sprawdzianów dzisiaj! 🎉")
                                        else:
                                            send_message(recipient_id, exams)
                                    else:
                                        if(len(message['message'].get('text').lower().split())==2):
                                            if(librus.getHomeWork(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate)==""):
                                                send_message(recipient_id, "Brak sprawdzianów w dniu 2020-"+message['message'].get('text').lower().split()[1]+"! 🎉")
                                            else:
                                                send_message(recipient_id, librus.getHomeWork(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate))
                                        else:
                                            exams = librus.getHomeWork(datetime.strptime(str(date.today()), '%Y-%m-%d'),clientCertificate)
                                            if(exams==""):
                                                send_message(recipient_id,"Brak sprawdzianów dzisiaj! 🎉")
                                            else:
                                                send_message(recipient_id, exams)
                                except Exception as e:
                                    print(e)
                                    send_message(recipient_id, "Nieprawidłowy format daty! 🧐\nPoprawny format: miesiac-dzien")
                            #SZCZESLIWY NUMEREK
                            elif(message['message'].get('text').lower() == "szczesliwy") or (message['message'].get('text').lower() == "szczęśliwy") or (message['message'].get('text').lower() == "szczesliwy numerek") or (message['message'].get('text').lower() == "szczęśliwy numerek"):
                                try:
                                    Number = librus.get_lucky_number(clientCertificate)
                                    send_message(recipient_id, str(Number))
                                except Exception as e:
                                    print(e)
                                    send_message(recipient_id, "Wystąpił błąd przy pobieraniu szczęśliwego numerka.")
                            #DNI WOLNE
                            elif(message['message'].get('text').lower() == "dni wolne"):
                                ReturnString = ""
                                FreeDays = librus.get_school_free_days(clientCertificate)
                                for x in range(len(FreeDays)):
                                    if(x%3==0):
                                        ReturnString += "\n📋 " + FreeDays[x] + "\n" + FreeDays[x+1] + "➡️" + FreeDays[x+2] + "\n\n"
                                send_message(recipient_id, ReturnString)
                            #ŚREDNIA
                            elif (message['message'].get('text').lower().split()[0] == "srednia") or (message['message'].get('text').lower().split()[0] == "średnia"):
                                try:
                                    if(message['message'].get('text').lower().split()[1]=="niemiecki"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Język niemiecki")))
                                    elif(message['message'].get('text').lower().split()[1]=="angielski"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Język angielski")))
                                    elif(message['message'].get('text').lower().split()[1]=="polski"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Język polski")))
                                    elif(message['message'].get('text').lower().split()[1]=="wos"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Wiedza o społeczeństwie")))
                                    elif(message['message'].get('text').lower().split()[1]=="edb"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Edukacja dla bezpieczeństwa")))
                                    elif(message['message'].get('text').lower().split()[1]=="wok"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Wiedza o kulturze")))
                                    elif(message['message'].get('text').lower().split()[1]=="pp") or (message['message'].get('text').lower().split()[1]=="przedsiebiorczosc"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Podstawy przedsiębiorczości")))
                                    elif(message['message'].get('text').lower().split()[1]=="wdż"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Wychowanie do życia w rodzinie")))
                                    elif(message['message'].get('text').lower().split()[1]=="wf"):
                                        send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,"Wychowanie fizyczne")))
                                    elif(len(message['message'].get('text').lower().split())==1):
                                        send_message(recipient_id,"Błędne użycie komendy.\nPoprawne uzycie:\nśrednia (nazwa przedmiotu)")
                                    else:
                                        if(len(message['message'].get('text').lower().split())==2):
                                            send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,message['message'].get('text').split()[1].capitalize())))
                                        elif(len(message['message'].get('text').lower().split())>2):
                                            mess=str(message['message'].get('text').lower())
                                            mess = mess[8:]
                                            send_message(recipient_id, str(librus.getGradeAvg(clientCertificate,mess.capitalize())))
                                except Exception as e:
                                    print(e)
                                    send_message(recipient_id,"Błędna nazwa przedmiotu lub brak ocen")
                            #ZŁA KOMENDA
                            else:
                                send_message(recipient_id, "Błędne polecenie!\nDostępne polecenia:\n-sprawdziany\n-szczesliwy numerek\n-dni wolne\n-srednia")
                        except Exception as e:
                            mycursor.execute("DELETE FROM `users` WHERE `users`.`recipient_id` = "+recipient_id)
                            mydb.commit()
                            send_message(recipient_id, "Błąd logowania, proszę zalogować się ponownie.")
                            print(e)
                    #VULCAN
                    elif(diary=="v"):
                        mycursor.execute("SELECT `certificate` FROM `users` WHERE recipient_id="+recipient_id)
                        clientCertificate = mycursor.fetchall()
                        clientCertificateL = []
                        for index in range(len(clientCertificate)):
                            clientCertificateL.append(str(clientCertificate[index][0]))
                        clientCertificate = clientCertificateL[0]
                        clientCertificate = clientCertificate[:-1]
                        clientCertificate = clientCertificate[2:]
                        clientCertificate = clientCertificate.replace("'",'"')
                        clientCertificate = json.loads(clientCertificate)
                        #WIADOMOSC NIE TEKSTOWA
                        if message['message'].get('attachments'):
                            send_message(recipient_id, "Błędne polecenie!\nDostępne polecenia:\n-sprawdziany\n-praca domowa")
                        #PRACA DOMOWA
                        elif (message['message'].get('text').lower().split()[0] in pd):
                            try:
                                if("jutro" in message['message'].get('text').lower().split()):
                                    homework = apiVulcan.getHomework(date.today() + timedelta(days=1),clientCertificate)
                                    if(homework==""):
                                        send_message(recipient_id, "Brak pracy domowej jutro")
                                    else:
                                        send_message(recipient_id, homework)
                                elif("wczoraj" in message['message'].get('text').lower().split()):
                                    homework = apiVulcan.getHomework(date.today() - timedelta(days=1),clientCertificate)
                                    if(homework==""):
                                        send_message(recipient_id, "Brak pracy domowej wczoraj")
                                    else:
                                        send_message(recipient_id, homework)
                                elif("dzisiaj" in message['message'].get('text').lower().split()):
                                    homework = apiVulcan.getHomework(date.today(),clientCertificate)
                                    if(homework==""):
                                        send_message(recipient_id, "Brak pracy domowej na dzisiaj")
                                    else:
                                        send_message(recipient_id, homework)
                                else:
                                    if(len(message['message'].get('text').lower().split())==2):
                                        if(message['message'].get('text').lower().split()[1]=="domowa"):
                                            send_message(recipient_id, apiVulcan.getHomework(date.today(),clientCertificate))
                                        else:
                                            if(apiVulcan.getHomework(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate)==""):
                                                send_message(recipient_id, "Brak pracy domowej w dniu 2020-"+message['message'].get('text').lower().split()[1])
                                            else:
                                                send_message(recipient_id, apiVulcan.getHomework(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate))
                                    elif(len(message['message'].get('text').lower().split())==3):
                                        if(apiVulcan.getHomework(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[2], '%Y-%m-%d'),clientCertificate)==""):
                                            send_message(recipient_id, "Brak pracy domowej w dniu 2020-"+message['message'].get('text').lower().split()[2])
                                        else:
                                            send_message(recipient_id, apiVulcan.getHomework(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[2], '%Y-%m-%d'),clientCertificate))
                                    else:
                                        send_message(recipient_id, apiVulcan.getHomework(date.today(),clientCertificate))
                            except Exception as e:
                                print(e)
                                send_message(recipient_id, "Nieprawidłowy format daty!\nPoprawny format: miesiac-dzien")
                        #SPRAWDZIANY
                        elif (message['message'].get('text').lower().split()[0] == "sprawdziany"):
                            try:
                                if("jutro" in message['message'].get('text').lower().split()):
                                    exams = apiVulcan.getExams(date.today() + timedelta(days=1),clientCertificate)
                                    if(exams==""):
                                        send_message(recipient_id, "Brak sprawdzianów na jutro")
                                    else:
                                        send_message(recipient_id, exams)
                                elif("wczoraj" in message['message'].get('text').lower().split()):
                                    exams = apiVulcan.getExams(date.today() - timedelta(days=1),clientCertificate)
                                    if(exams==""):
                                        send_message(recipient_id, "Brak sprawdzianów wczoraj")
                                    else:
                                        send_message(recipient_id, exams)
                                elif("dzisiaj" in message['message'].get('text').lower().split()): #or (len(message['message'].get('text').lower().split())==2):
                                    exams = apiVulcan.getExams(date.today(),clientCertificate)
                                    if(exams==""):
                                        send_message(recipient_id, "Brak sprawdzianów dzisiaj")
                                    else:
                                        send_message(recipient_id, exams)
                                else:
                                    if(len(message['message'].get('text').lower().split())==2):
                                        if(apiVulcan.getExams(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate)==""):
                                            send_message(recipient_id, "Brak sprawdzianów w dniu 2020-"+message['message'].get('text').lower().split()[1])
                                        else:
                                            send_message(recipient_id, apiVulcan.getExams(datetime.strptime("2020-"+ message['message'].get('text').lower().split()[1], '%Y-%m-%d'),clientCertificate))
                                    else:
                                        exams = apiVulcan.getExams(date.today(),clientCertificate)
                                        if(exams==""):
                                            send_message(recipient_id,"Brak sprawdzianów dzisiaj")
                                        else:
                                            send_message(recipient_id, exams)
                            except Exception as e:
                                print(e)
                                send_message(recipient_id, "Nieprawidłowy format daty!\nPoprawny format: miesiac-dzien")
                        #SREDNIA
                        elif (message['message'].get('text').lower().split()[0] == "srednia") or (message['message'].get('text').lower().split()[0] == "średnia"):
                            try:
                                if(message['message'].get('text').lower().split()[1]=="niemiecki"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"język niemiecki")))
                                elif(message['message'].get('text').lower().split()[1]=="angielski"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"język angielski")))
                                elif(message['message'].get('text').lower().split()[1]=="polski"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"język polski")))
                                elif(message['message'].get('text').lower().split()[1]=="wos"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"wiedza o społeczeństwie")))
                                elif(message['message'].get('text').lower().split()[1]=="edb"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"edukacja dla bezpieczeństwa")))
                                elif(message['message'].get('text').lower().split()[1]=="wok"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"wiedza o kulturze")))
                                elif(message['message'].get('text').lower().split()[1]=="pp") or (message['message'].get('text').lower().split()[1]=="przedsiebiorczosc"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"podstawy przedsiębiorczości")))
                                elif(message['message'].get('text').lower().split()[1]=="wf"):
                                    send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,"wychowanie fizyczne")))
                                elif(len(message['message'].get('text').lower().split())==1):
                                    send_message(recipient_id,"Błędne użycie komendy.\nPoprawne uzycie:\nśrednia (nazwa przedmiotu)")
                                else:
                                    if(len(message['message'].get('text').lower().split())==2):
                                        send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,message['message'].get('text').lower().split()[1])))
                                    elif(len(message['message'].get('text').lower().split())>2):
                                        mess=str(message['message'].get('text').lower())
                                        mess = mess.replace("srednia","")
                                        mess = mess.replace("średnia","")
                                        mess = mess[1:]
                                        send_message(recipient_id, str(apiVulcan.getAverage(clientCertificate,mess)))
                            except:
                                send_message(recipient_id,"Błędna nazwa przedmiotu lub brak ocen")
                        #INFORMACJE O UCZNIU
                        elif(message['message'].get('text').lower() == "uczen") or (message['message'].get('text').lower() == "uczeń"):
                            info = apiVulcan.getStudentInfo(clientCertificate)
                            send_message(recipient_id, info[0] + "\nKlasa " + info[1] + "\n" + info[2] + "\n" + str(recipient_id))
                        #WIADOMOSCI
                        elif(message['message'].get('text').lower() == "wiadomosci") or (message['message'].get('text').lower() == "wiadomości"):
                            UnreadM = apiVulcan.getMessages(clientCertificate)
                            if(len(UnreadM)==0):
                                send_message(recipient_id, "Nie masz zadnych nieodczytanych wiadomości")
                            else:
                                teachers = ""
                                for x in range(len(UnreadM)):
                                    teachers += str(UnreadM[x-1]) + ", "
                                teachers = teachers[:-2]
                                send_message(recipient_id, "Masz "+str(len(UnreadM))+" nieodczytanych wiadomości od: "+teachers)
                        #PLAN LEKCJI
                        elif(message['message'].get('text').lower().split()[0] == "lekcje"):
                            #WSZYSTKIE
                            if(len(message['message'].get('text').lower().split())==1):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"pon")
                                result += "📆PONIEDZIAŁEK📆\n\n"
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                resultA = apiVulcan.getLessons(clientCertificate,"wt")
                                result += "📆 WTOREK 📆\n\n"
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                resultA = apiVulcan.getLessons(clientCertificate,"sr")
                                result += "📆 ŚRODA 📆\n\n"
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                resultA = apiVulcan.getLessons(clientCertificate,"czw")
                                result += "📆 CZWARTEK 📆\n\n"
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                resultA = apiVulcan.getLessons(clientCertificate,"pt")
                                result += "📆 PIĄTEK 📆\n\n"
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                send_message(recipient_id, result)
                            #PONIEDZIAŁEK
                            #PONIEDZIAŁEK
                            elif(message['message'].get('text').lower().split()[1] == "poniedziałek") or (message['message'].get('text').lower().split()[1] == "poniedzialek") or (message['message'].get('text').lower().split()[1] == "pon"):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"pon")
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"

                                send_message(recipient_id, result)
                            #WTOREK
                            elif(message['message'].get('text').lower().split()[1] == "wtorek") or (message['message'].get('text').lower().split()[1] == "wt"):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"wt")
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"
                                send_message(recipient_id, result)
                            #ŚRODA
                            elif(message['message'].get('text').lower().split()[1] == "środa") or (message['message'].get('text').lower().split()[1] == "sroda") or (message['message'].get('text').lower().split()[1] == "sr"):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"sr")
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"
                                send_message(recipient_id, result)
                            #CZWARTEK
                            elif(message['message'].get('text').lower().split()[1] == "czwartek") or (message['message'].get('text').lower().split()[1] == "czw"):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"czw")
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"
                                send_message(recipient_id, result)
                            #PIĄTEK
                            elif(message['message'].get('text').lower().split()[1] == "piatek") or (message['message'].get('text').lower().split()[1] == "pt") or (message['message'].get('text').lower().split()[1] == "ptk"):
                                result = ""
                                resultA = apiVulcan.getLessons(clientCertificate,"pt")
                                for x in range(len(resultA)):
                                    if(x>0 and (x+1)%3==0):
                                        result += str(resultA[x]) + "\n\n"
                                    else:
                                        result += str(resultA[x]) + "\n"
                                send_message(recipient_id, result)
                            #ZŁA KOMENDA
                            else:
                                send_message(recipient_id, "Niepoprawne użycie komendy! \nDostępne parametry: pon/poniedzialek, wt/wtorek, sr/sroda, czw/czwartek, pt/piatek")
                        #POMOC
                        elif(message['message'].get('text').lower() == "pomoc"):
                            send_message(recipient_id, "Dostępne polecenia\n\n-sprawdziany\nWyświetla sprawdziany w danym dniu\nDostępne parametry:\ndata(miesiac-dzien),jutro,wczoraj,dzisiaj\n\n-praca domowa/pd\nWyświetla prace domową w danym dniu\nDostępne parametry:\ndata(miesiac-dzien),jutro,wczoraj,dzisiaj\n\n-srednia\nWyświetla średnią ucznia z danego przedmiotu\nDostępne parametry:\n<przedmiot>\n\n-uczen\nWyświetla informacje o aktualnie zalogowanym uczniu\nDostępne parametry:\nbrak\n\n-wiadomosci\nWyświetla liczbe nieodczytanych wiadomości\nDostępne parametry:\nbrak\n\n-plan\nWyświetlna plan lekcji w danym dniu\nDostępne parametry:\npon/poniedzialek, wt/wtorek, sr/sroda, czw/czwartek, pt/piatek")
                        #ZŁA KOMENDA
                        else:
                            send_message(recipient_id, "Nie rozumiem 😕\nDostępne polecenia:\n-sprawdziany\n-praca domowa\n-srednia\n-wiadomosci\n-uczen\n-lekcje\n-pomoc")
            #NOWY UZYTKOWNIK
                else:
                    #send_message(recipient_id, "Prosimy o zalogowanie się do dziennika\nDostępne: Librus, Vulcan\nAby się zalogować do Librus Synergia napisz na czacie:\nLibrus <Twój login> <Haslo>\nAby się zalogować do Vulcana napisz na czacie:\nVulcan <token> <symbol> <pin>")
                    #VULCAN LOGOWANIE
                    if(message['message'].get('text').lower().split()[0]=="vulcan"):
                        splitM = message['message'].get('text').split()
                        if(len(splitM)<4) or (len(splitM)>4):
                            send_message(recipient_id, "Nieprawidłowy format! \nAby się zalogować napisz na czacie dane potrzebne do logowania! \nPoprawny układ: Vulcan <token> <symbol> <pin> \nOddzielone spacjami!")
                        else:
                            cert = ""
                            try:
                                cert = apiVulcan.logInVulcan(str(splitM[1]),str(splitM[2]),str(splitM[3]))
                            except Exception as e:
                                print(e)
                                send_message(recipient_id, "Logowanie się nie powiodło.")
                            if(cert!=""):
                                try:
                                    string1 = str(cert)
                                    clientCertificate = string1
                                    clientCertificate = clientCertificate.replace("'",'"')
                                    clientCertificate = json.loads(clientCertificate)
                                    insert="""INSERT INTO `users`(`recipient_id`,`certificate`,`last_gradeID`,`last_gradeDATA`, `diary`) VALUES (%s,%s,%s,%s,%s)"""
                                    diaryy = "v"
                                    mycursor.execute(insert, (recipient_id,string1,apiVulcan.getLastGrade(clientCertificate)[0],apiVulcan.getLastGrade(clientCertificate)[1],diaryy,))
                                    mydb.commit()
                                    send_message(recipient_id, "Zalogowano pomyślnie")
                                except Exception as e:
                                    print(e)
                    #LIBRUS LOGOWANIE
                    elif(message['message'].get('text').lower().split()[0]=="librus"):
                        splitM = message['message'].get('text').split()
                        if(len(splitM)<3) or (len(splitM)>3):
                            send_message(recipient_id, "Nieprawidłowy format! \nAby się zalogować napisz na czacie dane potrzebne do logowania! \nPoprawny układ: librus <Twój login> <Haslo>\nOddzielone spacjami!")
                        else:
                            cred = ""
                            librus = Librus()
                            try:
                                returnL = librus.login(message['message'].get('text').split()[1], message['message'].get('text').split()[2])
                                if returnL is False:
                                    send_message(recipient_id, "Logowanie się nie powiodło.")
                                else:
                                    string1 = str(returnL)
                                    insert="""INSERT INTO `users`(`recipient_id`,`certificate`, `diary`) VALUES (%s,%s,%s)"""
                                    diaryy = "l"
                                    mycursor.execute(insert, (recipient_id,string1,diaryy,))
                                    mydb.commit()
                                    send_message(recipient_id, "Pomyślnie zalogowano")
                            except Exception as e:
                                print(e)
                                send_message(recipient_id, "Logowanie się nie powiodło.")
                    #BŁĄD
                    else:
                        send_message(recipient_id, "Prosimy o zalogowanie się do dziennika\nDostępne: Librus, Vulcan\nAby się zalogować do Librus Synergia napisz na czacie:\nLibrus <Twój login> <Haslo>\nAby się zalogować do Vulcana napisz na czacie:\nVulcan <token> <symbol> <pin>")


    return "Message Processed"


def checkGrades():
    #threading.Timer(5.0, checkGrades).start()
    with open("lastGrade.txt", "r") as f:
        lastG = f.read()
    if(str(apiVulcan.getLastGrade("id"))==lastG):
        print("Brak nowych ocen")
    else:
        return "Nowa ocena: " + apiVulcan.getLastGrade("data")
        with open("lastGrade.txt", "w") as f:
            f.write(str(apiVulcan.getLastGrade("id")))

def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


#chooses a random message to send to the user

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

def sendMessage(recipient, data):
    bot.send_text_message(recipient, data)
    print('Wiadomosc wyslana')

#checkGrades()

if __name__ == "__main__":
    app.run()
