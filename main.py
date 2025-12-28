from PyQt6.QtWidgets import QApplication
from chess_trainer_gui import ChessTrainerGUI  # Import the main GUI class

def main():
    app = QApplication([])  # Start PyQt app
    main_window = ChessTrainerGUI()  # Create the main trainer GUI
    main_window.show()  # Show it
    app.exec()  # Start event loop

if __name__ == "__main__":
    main()
