# Connect4

### A simple two-player Connect4 game in Python using PyGame and sockets. It can also be played in the terminal.

#### How to play the game
Two players take turns to drop their tokens in a grid with 6 rows and 7 columns. The first player to connect four of their tokens in a row horizontally, vertically or diagonally wins the round and earns 10 points. Note that the tokens occupy the lowest available space within the column. You can play as many rounds as you like. Points from each round will be added up at the end of the game. The overall winner of the game is the player with the most points at the end of the game.

#### Reason for the project
I chose this project to get hands-on experience with sockets and how online multiplayer games work. I have also learned a lot about threading and concurrency.

#### About the project
You can run four versions of the project. The first one runs in a single terminal session where players can take turns on the same computer. The second version also runs in the terminal but uses sockets so that players can connect and play from different computers or different terminal sessions. The seond version supports one server and only one pair of two clients at a time. The third version will run in the terminal but support one server and multiple pairs of two clients at a time. In this version, a client can choose to create a game (and they can invite another client to that particular game) or they can join any game. The fourth version will be based off of the third but will use pygame (and obviously sockets) to create a nicer interface to play the game.

For the versions that use sockets, the game logic is actually kept client-side. While this allows for cheating because the client cannot be trusted, preventing cheating is not really a priority of this simple project but minimizing network traffic is.

#### Status of the project and possible future features
The first version of the project is complete. 

The second version is also complete. Unexpected disconnection of client or server is handled on both client and server. The server and client can now both be stopped at any time with a Keyboard Interrupt.

The third version is currently in progress. No work has begun on the fourth version.

#### How to run the different versions of the project
- Clone the project and cd into the project directory.
- Create a virtual environment
- Activate the virtual environment.
- Install the dependencies by running `pip install -r requirements.txt`
- To run the first version of the project, run `python connect4.py` to play.
- To run the second version of the project (one server and one pair of two clients), you could use Wi-Fi to connect the computer or computers to one private network using a router or some other device like a mobile phone. This will work offline and you do not need internet access for this. 
  - Make sure to start the server first by running `python server.py` in one terminal session. 
  - Then run `python client.py` in two other terminal sessions. You can run the two clients on different computers also. One or both of the clients can be run on the same computer as the server host computer. 
  - If the IP address found by server.py or client.py is not the one you wish to use, you can find it and copy and paste it yourself. More information on finding your internal IP address [here](#finding-your-internal-ipv4-address).
  - To run the second version on one computer with localhost, make sure you are not connected to any private network. Press Enter when prompted for an IP address as it will use the localhost IP by default.

#### Finding your internal IPv4 address
To check your internal (private or local) IP address for [Windows](https://www.sas.upenn.edu/~jasonrw/HowTo-FindIP.htm#:~:text=From%20the%20desktop%2C%20navigate%20through%3B%20Logo%20%3E%20type%20%22cmd,by%20Windows%20will%20be%20displayed.), open cmd and type in the command `ipconfig` or `ipconfig /all`. For [Linux](https://constellix.com/news/what-is-my-ip-address#:~:text=Finding%20My%20IP%20for%20Linux%20Users&text=In%20the%20terminal%20enter%20one,is%20connected%20to%20the%20network.), enter `ip addr` in the terminal. For [Mac](https://www.macworld.com/article/673075/how-to-find-your-macs-ip-address.html), enter `ipconfig getifaddr en0` in the terminal.

#### Credits and Inspiration
This project is inspired by the Connect4 project on Crio at crio.do [here](https://www.crio.do/projects/python-multiplayer-game-connect4/)
