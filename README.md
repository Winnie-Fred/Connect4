# Connect4

### A simple two-player Connect4 game in Python using PyGame and sockets. It can also be played on the terminal.

#### How to play the game
Two players take turns to drop their tokens in a grid with 6 rows and 7 columns. The first player to connect four of their tokens in a row horizontally, vertically or diagonally wins the round and earns 10 points. Note that the tokens occupy the lowest available space within the column. You can play as many rounds as you like. Points from each round will be added up at the end of the game. The overall winner of the game is the player with the most points at the end of the game.

#### Reason for the project
I chose this project to get hands-on experience with sockets and how online multiplayer games work. I have also learned a lot about threading and concurrency.

#### About the project
You can run three versions of the project. The first one runs in a single terminal session where players can take turns on the same computer. The second version also runs in the terminal but uses sockets so that players can connect and play from different computers or different terminal sessions. The other version uses pygame (and sockets) to create a nicer interface to play the game.

For the second version, the game logic is actually kept client-side. While this allows for cheating because the client cannot be trusted, preventing cheating is not really a priority of this simple project but minimizing network traffic is.

#### Status of the project and possible future features
The first version of the project is complete. 

The second version is currently in progress. In the second version, the rounds continue until one player decides to stop. Unexpected disconnection of client or server is handled on both client and server.

The game works fine for the second version but there are still some features that may be added. It only supports 1 pair of 2 clients right now but functionality may be added to allow for more than a pair at a time. Keyboard interrupts will also be handled on both server and client.

#### How to run the different versions of the project
- Clone the project and cd into the project directory.
- Create a virtual environment and activate it.
- Install the dependencies by running `pip install -r requirements.txt`
- To run the first version of the project, run `python connect4.py` to play.
- 

#### Credits and Inspiration
This project is inspired by the Connect4 project on Crio at crio.do [here](https://www.crio.do/projects/python-multiplayer-game-connect4/)
