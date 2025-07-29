# Maze Game – Sophia Project

A simple Python maze game built using PySimpleGUI and the `keyboard` module. Designed for the Sophia Introduction to Python course.

##  Requirements

- Python 3.10 or later
- `PySimpleGUI`
- `keyboard`

##  Installation

1. Download or clone the repository:

   ```bash
   git clone https://github.com/Edwin-A-B-White/Maze_Game.git
   cd Maze_Game
   ```

2. (Optional) Create a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   >  Note: If `PySimpleGUI` has trouble installing or gives and error on game launch, try:
   > ```bash
   > pip install --upgrade --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
   > ```

4. Run the game:

   ```bash
   python maze_game.py
   ```

##  Controls

- Use arrow keys or WASD to move
- Hold Shift to sprint
- Escape or click X to quit

##  Tested On

- Python 3.10.11
- Windows 11
