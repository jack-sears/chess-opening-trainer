from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QComboBox, QLineEdit, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsRectItem
)
from PyQt6.QtGui import QPixmap, QColor, QTransform, QPen
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import chess_pgn_parser as cp
import chess_trainer as ct
import user_profiles as up
import utils
import os
import chess
import chess.pgn
import chess.svg
import spaced_repetition as sr
from datetime import datetime

class ChessTrainerGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.username = None
        self.profile = {}
        self.white_files = []
        self.black_files = []
        self.pgn_directory = "pgn"

        self.init_ui()

    def init_ui(self):
        """Setup UI layout and buttons."""
        layout = QVBoxLayout()

        # Username Input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        self.enter_button = QPushButton("Enter")
        self.enter_button.clicked.connect(self.set_username)

        self.change_username_button = QPushButton("Change Username")
        self.change_username_button.clicked.connect(self.change_username)
        self.change_username_button.setDisabled(True)  # Disabled until a username is set

        layout.addWidget(self.username_input)
        layout.addWidget(self.enter_button)
        layout.addWidget(self.change_username_button)

        # PGN Selection Buttons
        self.white_label = QLabel("White Openings: None")
        self.white_button = QPushButton("Select White PGNs")
        self.white_button.clicked.connect(lambda: self.select_pgn_files("white"))

        self.black_label = QLabel("Black Openings: None")
        self.black_button = QPushButton("Select Black PGNs")
        self.black_button.clicked.connect(lambda: self.select_pgn_files("black"))

        layout.addWidget(self.white_button)
        layout.addWidget(self.white_label)
        layout.addWidget(self.black_button)
        layout.addWidget(self.black_label)

        # Training Mode Selection
        self.mode_label = QLabel("Select Training Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Full Line", "Random Position"])
        self.start_button = QPushButton("Start Training")
        self.start_button.clicked.connect(self.start_training)

        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.start_button)

        self.setLayout(layout)
        self.setWindowTitle("Chess Opening Trainer")

    def set_username(self):
        """Locks in the username when 'Enter' is clicked."""
        username = self.username_input.text().strip()
        if username:
            self.username = username
            self.username_input.setDisabled(True)  # Lock input field
            self.enter_button.setDisabled(True)  # Disable enter button
            self.change_username_button.setDisabled(False)  # Enable change username button
            self.enter_button.setText(f"User: {self.username}")  # Update button text

    def change_username(self):
        """Allows the user to change the username."""
        self.username = None
        self.profile = {}
        self.username_input.setDisabled(False)  # Unlock input field
        self.enter_button.setDisabled(False)  # Enable enter button
        self.change_username_button.setDisabled(True)  # Disable change button
        self.username_input.clear()  # Clear input field
        self.enter_button.setText("Enter")  # Reset button text

    def select_pgn_files(self, color):
        """Open file dialog to select PGNs for White/Black."""
        folder = os.path.join(self.pgn_directory, color)
        files, _ = QFileDialog.getOpenFileNames(self, f"Select {color.capitalize()} PGN Files", folder, "PGN Files (*.pgn)")

        if files:
            if color == "white":
                self.white_files = files
                self.white_label.setText(f"White Openings: {len(files)} files selected")
            else:
                self.black_files = files
                self.black_label.setText(f"Black Openings: {len(files)} files selected")

    def start_training(self):
        """Start the selected training mode."""
        
        selected_openings = self.white_files + self.black_files
        if not selected_openings:
            self.mode_label.setText("Select PGN files before training!")
            return
        
        self.profile = up.load_user_profile(self.username)
        lines = cp.parse_all_pgn(selected_openings)
        up.merge_training_data(lines, self.profile)

        mode = self.mode_combo.currentText()
        if mode == "Full Line":
            self.train_full_line_gui = ChessBoard(lines, self.username)#TrainFullLineGUI(lines, self.profile)
            self.train_full_line_gui.show()
        elif mode == "Random Position":
            ct.train_random_positions(lines, self.profile)
            


        # Save progress after training
        #print("Saving user profile...")
        #up.save_user_profile(lines, self.username)
        self.mode_label.setText("Training Complete!")

class ChessBoard(QGraphicsView):
    def __init__(self, lines, username):
        super().__init__()

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.lines = lines
        self.opening_name = ''
        self.index = None
        self.user_color = None
        self.current_index = 0
        self.mistake = False
        self.ace = True
        self.username = username

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.board_size = 8
        self.square_size = 80  # Adjust based on image size
        self.piece_images = {}  # Dictionary to store loaded images

        self.line = None
        self.mistakes = None
        self.streaks = None
        self.mastery_levels = None
        self.easiness_factors = None
        self.last_practiced_list = None
        self.interval_days_list = None
        self.recent_mistakes_list = None

        self.board = None

        self.load_piece_images()
        self.draw_board()
        self.load_new_line()

        self.arrow = None
        self.hint = None

        self.setup_pieces()

        self.setFixedSize(self.board_size * self.square_size + 300, self.board_size * self.square_size + 50)

        self.solution_button = QPushButton("Show Solution", self)
        self.solution_button.setGeometry(self.board_size * self.square_size + 165, 25, 120, 40)
        self.solution_button.clicked.connect(self.show_solution)

        self.hint_button = QPushButton("Hint", self)
        self.hint_button.setGeometry(self.board_size * self.square_size + 165, 75, 120, 40)
        self.hint_button.clicked.connect(self.show_hint)

        self.play_next_move()

    def load_piece_images(self):
        """Load chess piece images into a dictionary."""
        piece_names = ['P', 'p', 'R', 'r', 'N', 'n', 'B', 'b', 'Q', 'q', 'K', 'k']
        for piece in piece_names:
            self.piece_images[piece] = QPixmap(f"images/{piece}.png").scaled(self.square_size, self.square_size, Qt.AspectRatioMode.KeepAspectRatio)

    def draw_board(self):
        """Draw the chessboard squares."""
        colors = [QColor(240, 217, 181), QColor(181, 136, 99)]  # Light and dark squares

        for row in range(self.board_size):
            for col in range(self.board_size):
                square = QGraphicsRectItem(col * self.square_size, row * self.square_size, self.square_size, self.square_size)
                square.setBrush(colors[(row + col) % 2])
                self.scene.addItem(square)

    def setup_pieces(self):
        """Set up pieces based on the current board's FEN."""
        self.scene.clear()  # Clear existing pieces and board
        self.draw_board()  # Redraw board squares

        self.piece_items = {}  # Track piece items for updates

        for rank in range(8):
            for file in range(8):
                square = chess.square(file, rank)  # Convert to chess index
                #print(square)
                piece = self.board.piece_at(square)
                if piece:
                    self.add_piece(piece.symbol(), square)  # Place piece

    def add_piece(self, piece_symbol, square):
        """Place a piece on the board using PieceItem class."""
        pixmap = QPixmap(f"images/{piece_symbol}.png").scaled(self.square_size, self.square_size)
        piece = PieceItem(pixmap, square, self.square_size, self.lines, self)
        self.scene.addItem(piece)

    def load_new_line(self):
        self.opening_name, self.index = cp.get_weighted_line(self.lines)
        #print(self.opening_name, self.index)
        self.line = self.lines[self.opening_name]['lines'][self.index]
        self.mistakes = self.lines[self.opening_name]['mistakes']
        self.streaks = self.lines[self.opening_name]['streaks']
        self.mastery_levels = self.lines[self.opening_name].get('mastery_level', [])
        self.easiness_factors = self.lines[self.opening_name].get('easiness_factor', [])
        self.last_practiced_list = self.lines[self.opening_name].get('last_practiced', [])
        self.interval_days_list = self.lines[self.opening_name].get('interval_days', [])
        self.recent_mistakes_list = self.lines[self.opening_name].get('recent_mistakes', [])

        self.user_color = self.line[0][3]
        self.board = chess.Board(self.line[0][2].fen())
        self.setup_pieces()
        #self.play_next_move()
        

    def play_next_move(self):
        """Handles the next move in the sequence."""
        if self.current_index >= len(self.line):  # If all moves are done
            self.update_line_completion()
            self.ace = True
            if self.username != None:
                print("Saving user profile...")
                up.save_user_profile(self.lines, self.username)
            self.load_new_line()  # Load a new line
            self.setup_pieces()
            self.current_index = 0
            self.play_next_move()
            return

        _, correct_move, _, _ = self.line[self.current_index]  # Get current move
        #print(self.board.turn, self.user_color)
        
        if self.board.turn == self.user_color:
            pass
        else:
            self.board.push(correct_move)  # Auto-play opponent move
            self.current_index += 1
            self.setup_pieces()

        if self.current_index >= len(self.line):  # If all moves are done
            self.update_line_completion()
            self.ace = True
            if self.username != None:
                print("Saving user profile...")
                up.save_user_profile(self.lines, self.username)
            self.load_new_line()  # Load a new line
            self.setup_pieces()
            self.current_index = 0
            self.play_next_move()
            
            
    def show_solution(self):
        """Show the solution for the current move."""
        if self.arrow:
            return
        
        if self.current_index >= len(self.line):
            return
        
        correct_move = self.line[self.current_index][1]
        start_square = correct_move.from_square
        end_square = correct_move.to_square

        start_x, start_y = utils.chess_square_to_gui(start_square, self.user_color)
        end_x, end_y = utils.chess_square_to_gui(end_square, self.user_color)

        self.arrow = self.scene.addLine(start_x * self.square_size + self.square_size // 2, start_y * self.square_size + self.square_size // 2,
                                        end_x * self.square_size + self.square_size // 2, end_y * self.square_size + self.square_size // 2,
                                        QPen(QColor(255, 0, 0), 5))
        
        if self.mistake == False:
            self.mistakes[self.index] += 1
            # Add mistake timestamp
            if self.recent_mistakes_list and self.index < len(self.recent_mistakes_list):
                self.recent_mistakes_list[self.index] = sr.add_mistake_timestamp(
                    self.recent_mistakes_list[self.index]
                )
                # Update in lines dictionary
                self.lines[self.opening_name]['recent_mistakes'] = self.recent_mistakes_list
            self.mistake = True
            self.ace = False

        
    def remove_solution(self):
        """Remove the solution arrow from the board."""
        if self.arrow:
            self.scene.removeItem(self.arrow)
            self.arrow = None

    def show_hint(self):
        """Show a hint for the current move."""
        if self.hint:
            return
        
        if self.current_index >= len(self.line):
            return
        
        correct_move = self.line[self.current_index][1]
        start_square = correct_move.from_square

        start_x, start_y = utils.chess_square_to_gui(start_square, self.user_color)

        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and item.rect().x() == start_x * self.square_size and item.rect().y() == start_y * self.square_size:
                item.setBrush(QColor(255,255,0,150))
                self.hint = item

        if self.mistake == False:
            self.mistakes[self.index] += 1
            # Add mistake timestamp
            if self.recent_mistakes_list and self.index < len(self.recent_mistakes_list):
                self.recent_mistakes_list[self.index] = sr.add_mistake_timestamp(
                    self.recent_mistakes_list[self.index]
                )
                # Update in lines dictionary
                self.lines[self.opening_name]['recent_mistakes'] = self.recent_mistakes_list
            self.mistake = True
            self.ace = False

    def remove_hint(self):
        """Remove the hint from the board."""
        if self.hint:
            # Get square coordinates
            square_x = self.hint.rect().x() // self.square_size
            square_y = self.hint.rect().y() // self.square_size
            # Determine original color based on (file + rank) % 2
            original_color = QColor(240, 217, 181) if (square_x + square_y) % 2 == 0 else QColor(181, 136, 99)
            self.hint.setBrush(original_color)
            self.hint = None

    def update_line_completion(self):
        """Update spaced repetition metrics after completing a line."""
        if self.index is None or self.index >= len(self.mistakes):
            return
        
        # Ensure all lists are properly initialized
        if not self.mastery_levels:
            self.mastery_levels = [sr.DEFAULT_MASTERY_LEVEL] * len(self.mistakes)
        if not self.easiness_factors:
            self.easiness_factors = [sr.DEFAULT_EASINESS_FACTOR] * len(self.mistakes)
        if not self.last_practiced_list:
            self.last_practiced_list = [None] * len(self.mistakes)
        if not self.interval_days_list:
            self.interval_days_list = [sr.DEFAULT_INTERVAL_DAYS] * len(self.mistakes)
        if not self.recent_mistakes_list:
            self.recent_mistakes_list = [[] for _ in range(len(self.mistakes))]
        
        # Get current values
        mastery = self.mastery_levels[self.index] if self.index < len(self.mastery_levels) else sr.DEFAULT_MASTERY_LEVEL
        easiness = self.easiness_factors[self.index] if self.index < len(self.easiness_factors) else sr.DEFAULT_EASINESS_FACTOR
        streak = self.streaks[self.index] if self.index < len(self.streaks) else 0
        mistake_count = self.mistakes[self.index] if self.index < len(self.mistakes) else 0
        current_interval = self.interval_days_list[self.index] if self.index < len(self.interval_days_list) else sr.DEFAULT_INTERVAL_DAYS
        
        # Update streak
        if self.ace:
            self.streaks[self.index] = streak + 1
        else:
            self.streaks[self.index] = 0
        
        # Update mastery and easiness
        was_correct = self.ace
        new_mastery, new_easiness = sr.update_mastery_after_practice(
            mastery, easiness, was_correct, streak, mistake_count
        )
        
        # Calculate new interval
        new_interval = sr.calculate_next_interval(
            new_mastery, new_easiness, current_interval, was_correct, self.streaks[self.index]
        )
        
        # Update all values
        if self.index < len(self.mastery_levels):
            self.mastery_levels[self.index] = new_mastery
        else:
            self.mastery_levels.extend([sr.DEFAULT_MASTERY_LEVEL] * (self.index - len(self.mastery_levels) + 1))
            self.mastery_levels[self.index] = new_mastery
        
        if self.index < len(self.easiness_factors):
            self.easiness_factors[self.index] = new_easiness
        else:
            self.easiness_factors.extend([sr.DEFAULT_EASINESS_FACTOR] * (self.index - len(self.easiness_factors) + 1))
            self.easiness_factors[self.index] = new_easiness
        
        if self.index < len(self.interval_days_list):
            self.interval_days_list[self.index] = new_interval
        else:
            self.interval_days_list.extend([sr.DEFAULT_INTERVAL_DAYS] * (self.index - len(self.interval_days_list) + 1))
            self.interval_days_list[self.index] = new_interval
        
        # Update last practiced timestamp
        current_time = datetime.now()
        if self.index < len(self.last_practiced_list):
            self.last_practiced_list[self.index] = current_time.isoformat()
        else:
            self.last_practiced_list.extend([None] * (self.index - len(self.last_practiced_list) + 1))
            self.last_practiced_list[self.index] = current_time.isoformat()
        
        # Update the lines dictionary
        self.lines[self.opening_name]['mastery_level'] = self.mastery_levels
        self.lines[self.opening_name]['easiness_factor'] = self.easiness_factors
        self.lines[self.opening_name]['last_practiced'] = self.last_practiced_list
        self.lines[self.opening_name]['interval_days'] = self.interval_days_list
        self.lines[self.opening_name]['recent_mistakes'] = self.recent_mistakes_list
        
        print(f"Line {self.index} completed. Mastery: {new_mastery:.2f}, Interval: {new_interval:.1f} days")

    def update_board(board):
        pass

class PieceItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, square, square_size, lines, chessboard):
        super().__init__(pixmap)
        self.chessboard = chessboard
        self.color = self.chessboard.user_color
        self.lines = lines # Reference to lines
        self.move = 0
        self.cur_board = self.lines
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable)  # Make it draggable
        self.setZValue(1)  # Ensure pieces are above the board
        self.square_size = square_size
        self.start_pos = self.pos()  # Store original position
        self.square = square # Convert to chess square
        self.gui_square = utils.chess_square_to_gui(square, self.color)
        self.setPos(self.gui_square[0] * square_size, self.gui_square[1] * square_size)

    def mousePressEvent(self, event):
        """Detect when a piece is clicked."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setZValue(2)  # Bring piece to front
            self.start_pos = self.pos()

            start_x = round(self.x() / self.square_size)
            start_y = round(self.y() / self.square_size)

            
            self.start_square = utils.gui_to_chess_square(start_x, start_y, self.color)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Drop piece onto a valid square and check legality."""
        new_x = round(self.x() / self.square_size)
        new_y = round(self.y() / self.square_size)
        #print(chess.Square(new_x, new_y))
        #print(new_x, new_y)
        new_square = utils.gui_to_chess_square(new_x, new_y, self.color)  # Convert to chess square

        move = chess.Move(self.start_square, new_square)
        #print(move)
        #print(self.chessboard.line[self.chessboard.current_index][1])
        if move in self.chessboard.board.legal_moves:
            if move == self.chessboard.line[self.chessboard.current_index][1]:
                #Remove the piece if captured
                if self.chessboard.board.is_capture(move):
                    for item in self.chessboard.scene.items():
                        if isinstance(item, PieceItem) and item.gui_square == (new_x, new_y):
                            self.chessboard.scene.removeItem(item)
                elif self.chessboard.board.is_castling(move):
                    self.handle_castling(move)

                self.chessboard.board.push(move)  # Apply move to chess.Board
                self.setPos(new_x * self.square_size, new_y * self.square_size)  # Move piece
                self.gui_square = (new_x, new_y)
                self.square = new_square
                self.chessboard.current_index += 1
                self.chessboard.mistake = False

                self.chessboard.remove_solution()
                self.chessboard.remove_hint()
                
                QTimer.singleShot(25, self.chessboard.play_next_move)

            else:
                #move is incorrect deal with a mistake
                if self.chessboard.mistake == False:
                    self.chessboard.mistakes[self.chessboard.index] += 1
                    # Add mistake timestamp
                    if self.chessboard.recent_mistakes_list and self.chessboard.index < len(self.chessboard.recent_mistakes_list):
                        self.chessboard.recent_mistakes_list[self.chessboard.index] = sr.add_mistake_timestamp(
                            self.chessboard.recent_mistakes_list[self.chessboard.index]
                        )
                        # Update in lines dictionary
                        self.chessboard.lines[self.chessboard.opening_name]['recent_mistakes'] = self.chessboard.recent_mistakes_list
                    self.chessboard.mistake = True
                    self.chessboard.ace = False
                    self.chessboard.streaks[self.chessboard.index] = 0
                self.setPos(self.start_pos)
        else:
            self.setPos(self.start_pos)  # Snap back to original position if move is illegal

        self.setZValue(1)  # Send back to normal layer
        super().mouseReleaseEvent(event)

    def handle_castling(self, move):
        """Moves both the king and the rook on screen when castling."""
        board = self.chessboard.board

        # Get the castling rook's move
        rook_start_square = None
        rook_end_square = None

        if board.is_kingside_castling(move):
            rook_start_square = move.to_square + 1  # Right of king
            rook_end_square = move.to_square - 1  # Next to new king position
        elif board.is_queenside_castling(move):
            rook_start_square = move.to_square - 2  # Left of king
            rook_end_square = move.to_square + 1  # Next to new king position

        if rook_start_square is not None:
            # Convert squares to GUI coordinates
            rook_gui_pos = utils.chess_square_to_gui(rook_start_square, self.chessboard.user_color)
            new_rook_gui_pos = utils.chess_square_to_gui(rook_end_square, self.chessboard.user_color)

            # Find the rook piece on the board and move it
            for item in self.chessboard.scene.items():
                if isinstance(item, PieceItem) and item.square == rook_start_square:
                    item.setPos(new_rook_gui_pos[0]*self.square_size, new_rook_gui_pos[1] * self.square_size)
                    item.square = rook_end_square  # Update the rook's stored position
                    item.gui_square = new_rook_gui_pos
                    break