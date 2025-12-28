# Chess Opening Trainer - Web Version

A web-based chess opening trainer with spaced repetition learning system.

## Features

- 🎯 Spaced repetition algorithm for optimal learning
- 📊 Track mastery levels and progress
- 🎨 Modern, responsive web interface
- ♟️ Interactive chess board with drag-and-drop
- 📁 Support for multiple PGN opening files
- 💾 Persistent user profiles

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have PGN files in the `../pgn/white/` and `../pgn/black/` folders

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter your username (or use "guest")
2. Select the openings you want to practice
3. Click "Start Training"
4. Practice moves by dragging pieces on the board
5. Use "Hint" to see the starting square
6. Use "Show Solution" to see the correct move
7. Complete lines to improve your mastery level

## Project Structure

```
web/
├── app.py              # Flask backend application
├── requirements.txt    # Python dependencies
├── templates/         # HTML templates
│   └── index.html
├── static/            # Static files (CSS, JS)
│   ├── style.css
│   └── app.js
└── README.md          # This file
```

## API Endpoints

- `GET /api/pgn/list` - List available PGN files
- `POST /api/training/start` - Start a training session
- `POST /api/training/next-line` - Get next line to practice
- `POST /api/training/move` - Submit a move
- `POST /api/training/hint` - Get a hint
- `POST /api/training/solution` - Get the solution

## Notes

- User profiles are saved in `../profiles/` directory
- The web version uses the same backend logic as the desktop version
- Chess piece images should be placed in `static/pieces/` or use a CDN

