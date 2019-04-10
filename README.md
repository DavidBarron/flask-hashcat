# hashcat-flask

### Description
Simple Flask app that wraps hashcat commnd line util to perform various simple password attacks on a set of MD5 password hashes. Instructions below pertinent to OSX app install.

### Installing Dependencies
```
brew install hashcat
brew install redis
```


### Before first run of app (or python script only to clear database at any point)
```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
python3 db_init.py
deactivate
```
Also, download rockyou.txt from link and place file in /word_lists: https://wiki.skullsecurity.org/Passwords


### Running app
Start redis server

```
redis-server
```
In separate window, start worker to listen to redis queue
```
. venv/bin/activate
python3 hashcat_worker.py
```
Finally, in another window start the Flask app

```
. venv/bin/activate
flask run
```

### Other helpful commands
Clearing .potfile (assuming similar installation w/ Homebrew)
```
cp /dev/null ~/.hashcat/hashcat.potfile
```
Flushing redis
```
redis-cli flushall
```
Shutting down redis
```
redis-cli shutdown
```
