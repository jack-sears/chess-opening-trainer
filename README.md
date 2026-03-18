# Chess Opening Trainer (Desktop GUI)

A desktop chess opening trainer built with PyQt6 and `python-chess`, focused on practicing lines with spaced repetition.

> Note: the `web` version has its own documentation in `web/README.md`.

## Features

- PyQt6 GUI with draggable pieces
- Train from your own PGN files
- Supports White and Black repertoires
- Hint and show-solution tools during training
- Progress tracking with spaced-repetition fields
- Per-user saved training profiles

## Requirements

- Python 3.10+ (recommended)
- Dependencies in `requirements.txt`

## Setup

From the `chess` folder:

pip install -r requirements.txt
python main.py

## How to use

- Enter a username and click Enter.
- Click Select White PGNs and/or Select Black PGNs.
- Choose training mode
- Click Start Training
Drag a piece to make your move  
Use Hint to highlight the starting square  
Use Show Solution to display the correct move  

## Notes
pgn/white/ and pgn/black/: suggested locations for opening files. Can use lichess or chess.com to create your own pgn.  
profiles/: user progress JSON files are saved here automatically  
images/: chess piece images used by the GUI  