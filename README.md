# Connect4

### A simple two-player Connect4 game in Python using PyGame and sockets. It can also be played on the terminal.

#### How to play the game
Two players take turns to drop their tokens in a grid with 6 rows and 7 columns. The first player to connect four of their tokens in a row horizontally, vertically or diagonally wins the round and earns 10 points. Note that the tokens occupy the lowest available space within the column. You can play as many rounds as you like. Points from each round will be added up at the end of the game. The overall winner of the game is the player with the most points at the end of the game.

#### Reason for the project
I chose this project to get hands-on experience with sockets and how online multiplayer games work.

#### About the project
You can run three versions of the project. The first one runs in a single terminal session where players can take turns on the same computer. The second version also runs in the terminal but uses sockets so that players can connect and play from different computers or different terminal sessions. The other version uses pygame (and sockets) to create a nicer interface to play the game.

#### How to run the different versions of the project
- Clone the project and cd into the project directory.
- Install the dependencies by running `pip install -r requirements.txt`
-


#### Credits and Inspiration
This project is inspired by the Connect4 project on Crio at crio.do [here](https://www.crio.do/projects/python-multiplayer-game-connect4/)
