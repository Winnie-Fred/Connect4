# Connect4

### A simple two-player Connect4 game in Python using Pygame and sockets. It can also be played in the terminal.

#### How to play the game
Two players take turns to drop their tokens in a grid with 6 rows and 7 columns. The first player to connect four of their tokens in a row horizontally, vertically or diagonally wins the round and earns 10 points. Note that the tokens occupy the lowest available space within the column. You can play as many rounds as you like. Points from each round will be added up at the end of the game. The overall winner of the game is the player with the most points at the end of the game.

#### Reason for the project
I chose this project to get hands-on experience with sockets and how online multiplayer games work. I have also learned a lot about threading and concurrency and about the Pygame library. I also learned how to design with Figma for this project and used it to create/edit most of the pygame version game components and UI kit.

#### About the project
You can run four versions of the project. The first one runs in a single terminal session where players can take turns on the same computer. The second version also runs in the terminal but uses sockets so that players can connect and play from different computers or different terminal sessions. The second version supports one server and only one pair of clients at a time. The third version runs in the terminal but supports one server and multiple pairs of clients at a time. In this version, a client can choose to create a game (and they can invite another client to that particular game) or they can join any game. The fourth version will be based off of the third but will use pygame (and obviously sockets) to create a nicer interface to play the game.

For the versions that use sockets, the game logic is actually kept client-side. While this allows for cheating because the client cannot be trusted, preventing cheating is not really a priority of this simple project but minimizing network traffic is.

#### Status of the project
The first version of the project is complete. 

The second and third versions are also complete. Unexpected disconnection of client or server is handled on both client and server. The server and client can both be stopped at any time with a Keyboard Interrupt.

The development of the fourth version is currently in progress.

#### How to set up the project
- Clone the project and cd into the project directory.
- Create a virtual environment.
- Activate the virtual environment.
- Make sure you are in the root of the project directory i.e connect4 and the virtual environment is activated. You will need internet access for the project installation. Install the project (and its dependencies) with this one-liner: `pip install .`. Note that this also installs the project dependencies so there is no need to do that separately.
- If you want to make changes to the code i.e. use it in development mode, what you want is an editable install. Make sure you are in the root of the project directory i.e `connect4` and the virtual environment is activated and use this command instead: `pip install -e .` or `pip install --editable .`. This will allow you to edit code and see those changes reflected in places where the project's modules are imported without re-installing each time. If you change the `pyproject.toml` file, or add to or delete from the src directory, you would have to rerun the editable install command to see those changes. 
- To install [optional dependencies](https://github.com/Winnie-Fred/Connect4/blob/d5d4db3c0a965ef12b2bd5b72821a4a0b8d8a5c5/pyproject.toml#L26) the project uses, e.g. mypy for lint, use this command: `pip install .[lint]`

#### How to run the different versions of the project
- cd into the `src` directory.
- To run the first version of the project, cd into `basic_version` and run `python connect4.py` to play.
- For the other versions of the project, you could use Wi-Fi to connect the computer or computers to one private network using a router or some other device like a mobile phone. This will work offline and you do not need internet access for this.
    - To run the second version of the project (one server and one pair of clients),
        - cd into `one_pair_of_clients_version` package.
        - Make sure to start the server first by running `python server.py` in one terminal session. 
        - Then run `python client.py` in two other terminal sessions. 
    - To run the third version of the project (one server and multiple pairs of clients)
        - cd into `multiple_pairs_of_clients_version` package.
        - Make sure to start the server first by running `python server.py` in one terminal session. 
        - Then run `python client.py` in two other terminal sessions.
    - To run the fourth (pygame) version of the project
        - cd into `pygame_version`.
        - Make sure to start the server first by running `python server.py` in one terminal session. 
        - Then run `python connect4.py` in two other terminal sessions.
    - You can run the two clients on different computers also. One or both of the clients can be run on the same computer as the server host computer. 
    - To run on one computer with localhost, make sure you are not connected to any private network.

#### Note
- If you have successfully installed the project and are having problems running the program, this may be because your firewall is blocking python.exe from running (especially if this is your first time running a program that uses sockets). If this is the case, make sure you allow python through the firewall by changing your security settings.
- To avoid troubles during installation, ensure you are using an up-to-date version of pip (preferably pip ≥ 21.3) especially if you are doing an editable install. Also make sure you have stable internet access.

#### Credits and Inspiration
This project is inspired by the Connect4 project on Crio at crio.do [here](https://www.crio.do/projects/python-multiplayer-game-connect4/)

All resources (media) used in this project that I did not create myself were gotten for free. Special thanks to these authors who I have [credited](https://github.com/Winnie-Fred/Connect4/blob/c2c27e70c7ae6c9251e205f844b6b485536b66d0/credits.md).
