# LogRun
---
##### Script to send syslog from file to syslog server (based on IBM QRadar script logrun.pl).
---
### How to use from command line:
```
usage: logrun.py [-h] [--dest DEST] [--port PORT] [--filename FILENAME]
                 [--object OBJECT] [--sourceip SRCIP] [-v] [-t] [-b] [-l] [-p]
                 eps

positional arguments:
  eps                  messages per second

optional arguments:
  -h, --help           show this help message and exit
  --dest DEST          destination syslog host (default 127.0.0.1)
  --port PORT          destination port (default 514)
  --filename FILENAME  filename to read (default readme.syslog)
  --object OBJECT      use OBJECT for object name in syslog header
  --sourceip SRCIP     use this IP as spoofed sender (default is NOT to send
                       IP header)
  -v                   verbose, display lines read in from file
  -t                   use TCP instead of UDP for sending syslogs
  -b                   burst the same message for 20% of the delay time
  -l                   loop indefinately
  -p                   propagate the Source IP from object name in every line
                       - ^([^:]+): - starts from line begining and is closed
                       by :
```					   
### How to use as Python module:
```
>>> import logrun
>>> lr=logrun.LogRun({'dest':'syslog.loc','filename':'syslog.log', 'srcip':'127.0.0.127', 'verbose':True, 'eps':1000})
>>> lr.run()
```