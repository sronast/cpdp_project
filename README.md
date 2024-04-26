# cpdp_project

Before running the game, we have to install all the dependencies. The game depends on `pygame` module so we have to install it. Also the game runs in a virtual environment so we have to install the virtual environment. To do all those run the following command:
```bash
pip install virtualenv #install virtual env
# cd into the root directory and do..
virtualenv env #create a new virtual environment
source env/bin/activate
## Now the virtual environment has been activated
# Now install the packages required
pip install -r requirements.txt # this will install all the required dependency
```

Now to finally run the program, enter the following:
```bash
python server.py # this will start the server in port 8848
python client.py # this will start one client
# On another terminal you can do
python client.py # this will start a new client and the game will start
```
