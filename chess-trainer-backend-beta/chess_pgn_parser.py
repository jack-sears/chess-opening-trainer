import chess
import chess.pgn
import random
import utils
import os

def parse_all_pgn(pgn_files):
    """Extracts all lines from multiple PGN files, including player color."""
    all_lines = {}

    for pgn_file in pgn_files:
        color = utils.determine_player_color(pgn_file)
        if color == None:
            continue
        lines = extract_all_lines(pgn_file, color)

        opening_name = os.path.splitext(os.path.basename(pgn_file))[0]
        
        all_lines[opening_name] = {
            "lines": lines,
            "mistakes": [0] * len(lines),
            "streaks": [0] * len(lines)
        }
    return all_lines

def extract_all_lines(filename, color):
    """Extracts every possible line from a PGN file."""
    with open(filename) as pgn:
        game = chess.pgn.read_game(pgn)
        #NEED TO ERROR CHECK HERE
    
    lines = []
    def traverse(node, board, line):
        if not node.variations:
            lines.append(line[:])  # Store completed line
            return
        for variation in node.variations:
            # Save the board state BEFORE pushing the move
            line.append((board.fen(), variation.move, board.copy(), color))
            board.push(variation.move)
            
            traverse(variation, board, line)
            
            board.pop()  # Undo the move after recursion
            line.pop()   # Remove last move to backtrack
    
    board = game.board()
    traverse(game, board, [])
    return lines

def get_random_line(lines):
    """Selects a random full line."""
    if not lines:
        print("No lines found!")
        return None
    random_pgn = random.choice(list(lines.keys()))
    pgn_data = lines[random_pgn]
    if not pgn_data['lines']:
        return None
    
    return random.choice(pgn_data[lines])

def get_random_position(positions, color):
    """Selects a random position where it's the given color's turn to move."""
    filtered_positions = [pos for pos in positions if pos[2].turn == color]  # pos[2] is the board

    if not filtered_positions:
        print(f"No positions found where {color} is to move!")
        return None

    return random.choice(filtered_positions)

import random

def get_weighted_line(lines):
    """Selects a random full line, prioritizing lines with more mistakes."""
    if not lines:
        print("No lines found!")
        return None

    # Create a weighted list of (pgn_file, line_index) based on mistake counts
    weighted_lines = []

    for pgn_file, data in lines.items():
        mistakes = data["mistakes"] # Get mistakes for this opening
        streaks = data["streaks"]
        for idx, mistake_count in enumerate(data["mistakes"]):
            # Streak decay: If 3+ correct in a row, mistakes decay twice as fast
            if streaks[idx] >= 3:
                mistakes[idx] = max(0, int(mistakes[idx] - mistakes[idx]/2))  # Faster decay

            # Regular decay: If 1-2 correct in a row, normal decay
            elif streaks[idx] > 0:
                mistakes[idx] = max(0, int(mistakes[idx] - mistakes[idx]/4))

            # Cap mistake weight to prevent one line from dominating forever
            weight = min(10, max(1, mistakes[idx]))  
            weighted_lines.extend([(pgn_file, idx)] * weight)

    if not weighted_lines:
        return None, None  # No lines available

    # Pick a (pgn_file, line_index) based on weight
    pgn_file, line_index = random.choice(weighted_lines)

    return pgn_file, line_index



'''
# Example usage
pgn_file = "pgn/alapin-sicilian-black.pgn"  # Change this to your PGN file
positions = load_pgn(pgn_file)

if positions:
    random_pos = get_random_position(positions)
    print("Random Position FEN:", random_pos[0])
    print("Expected Move:", random_pos[1])
    print("\nBoard Position:\n")
    random_pos[2].turn = chess.BLACK
    print(random_pos[2])  # Prints the board in ASCII format using python-chess's __str__()

else:
    print("No positions found in PGN!")
'''
