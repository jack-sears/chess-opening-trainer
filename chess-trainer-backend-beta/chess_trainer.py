import chess_pgn_parser as cp
import utils
import chess
import time 
from collections import defaultdict

mistake_log = defaultdict(list)

def train_random_positions(lines, mistake):
    """Runs the CLI trainer where the player only plays their chosen color."""
    while True:
        line = cp.get_random_line(lines)
        color = line[0][3]
        position = cp.get_random_position(line, color)
        if not position:
            print("No positions available!")
            break

        board_fen, correct_move, _, color = position
        board = chess.Board(board_fen)

        print("\nCurrent Position:\n")
        utils.print_board(board, color)  # Correctly display for White/Black
        
        while True:
            # Get user input
            user_move = input("Your move (SAN format, e.g., 'Nf3'): ").strip()
            try:
                move = board.parse_san(user_move)
                if move == correct_move:
                    print("✅ Correct!")
                    board.push(move)  # Update board after correct move
                    break
                else:
                    print(f"❌ Incorrect.")
                    choice = input("Try again (R), Show solution (S), or Quit (Q)? ").strip().lower()
                    if choice == "s":
                        print(f"🔎 Solution: {correct_move}")
                        board.push(correct_move)  # Show move on board
                        break
                    elif choice == "q":
                        return  # Exit training
                    else:
                        print("🔄 Try again!")  # Loop back to ask for input again
            except ValueError:
                print("⚠️ Invalid move input!")

        cont = input("Try another? (y/n): ").strip().lower()
        if cont != "y":
            break

def train_full_line(lines, mistakes):
    """Trains the user through a randomly selected full line."""
    pgn_name, index = cp.get_weighted_line(lines)
    line = lines[pgn_name]['lines'][index]
    if not line:
        return
    print(f'Opening: {pgn_name}')
    for board_fen, correct_move, _, color in line:
        mistake = False
        board = chess.Board(board_fen)

        if board.turn != color:
            print(f"Opponent plays: {correct_move}")
            board.push(correct_move)
            continue

        print("\nCurrent Position:")
        utils.print_board(board, color)

        while True:
            user_move = input("Your move (SAN format, or 's' to see solution or 'q' to go back to menu): ").strip()
            
            if user_move.lower() == 's':
                print(f"🔎 Solution: {correct_move}")
                board.push(correct_move)
                mistake = True
                break
            elif user_move.lower() == 'q':
                return
        
            try:
                move = board.parse_san(user_move)
                if move == correct_move:
                    print("✅ Correct!")
                    board.push(move)
                    break
                else:
                    print("❌ Incorrect. Try again!")
                    mistake = True
            except ValueError:
                print("⚠️ Invalid move input!")
        if mistake:
            log_mistake(pgn_name, lines, index)
        

def log_mistake(pgn_name, lines, index):
    """Logs a mistake with a timestamp."""
    lines[pgn_name]['mistakes'][index] += 1

def get_mistakes(opening_name):
    """Returns all recorded mistakes for an opening."""
    return mistake_log.get(opening_name, [])