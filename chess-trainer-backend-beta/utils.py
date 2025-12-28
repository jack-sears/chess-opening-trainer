import chess_pgn_parser as cp
import chess_trainer as ct
import chess
import os

def print_board(board, player_color):
    """Prints the board correctly for the given player's perspective."""

    if player_color == chess.BLACK:
        flipped_board = (board.transform(chess.flip_horizontal)).transform(chess.flip_vertical)  # Correctly flip Black's view
        board_str = str(flipped_board).split("\n")
    else:
        board_str = str(board).split("\n")

    print("\n".join(board_str))

def determine_player_color(pgn_file):
    """Determines the player's color based on PGN folder location."""
    if "white" in os.path.dirname(pgn_file):
        return chess.WHITE
    elif "black" in os.path.dirname(pgn_file):
        return chess.BLACK
    else:
        print(f"⚠️ PGN file is not in 'white' or 'black' folder! {pgn_file} not added... Make sure it is in the white or black folder.")
        return None# Default fallback  


def get_user_opening_selection(pgn_directory):
    """Asks the user to select openings from the white and black PGN folders."""
    white_folder = os.path.join(pgn_directory, "white")
    black_folder = os.path.join(pgn_directory, "black")

    white_openings = [f for f in os.listdir(white_folder) if f.endswith(".pgn")]
    black_openings = [f for f in os.listdir(black_folder) if f.endswith(".pgn")]

    selected_openings = []

    print("\nSelect openings to train:")

    # Select White Openings
    if white_openings:
        print("\nWhite Openings:")
        for i, opening in enumerate(white_openings, start=1):
            print(f"{i}. {opening}")
        white_choices = input("Enter the numbers of the white openings you want (comma-separated): ").strip()
        selected_openings.extend([os.path.join(white_folder, white_openings[int(i)-1]) 
                                  for i in white_choices.split(",") if i.isdigit() and 1 <= int(i) <= len(white_openings)])

    # Select Black Openings
    if black_openings:
        print("\nBlack Openings:")
        for i, opening in enumerate(black_openings, start=1):
            print(f"{i}. {opening}")
        black_choices = input("Enter the numbers of the black openings you want (comma-separated): ").strip()
        selected_openings.extend([os.path.join(black_folder, black_openings[int(i)-1]) 
                                  for i in black_choices.split(",") if i.isdigit() and 1 <= int(i) <= len(black_openings)])

    if not selected_openings:
        print("⚠️ No openings selected. Please choose at least one.")
        return get_user_opening_selection(pgn_directory)  # Recursively ask again

    return selected_openings  # Just a list of file paths
