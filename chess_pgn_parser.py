import chess
import chess.pgn
import random
import utils
import os
import spaced_repetition as sr

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
            "streaks": [0] * len(lines),
            "mastery_level": [0.0] * len(lines),
            "easiness_factor": [2.5] * len(lines),
            "last_practiced": [None] * len(lines),
            "interval_days": [1.0] * len(lines),
            "recent_mistakes": [[] for _ in range(len(lines))]
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
    """
    Selects a line using spaced repetition algorithm.
    Prioritizes lines based on:
    - Time since last practice (overdue lines)
    - Mastery level (lower mastery = higher priority)
    - Recent mistakes (more recent = higher priority)
    """
    if not lines:
        print("No lines found!")
        return None, None

    # Calculate priority scores for all lines
    line_priorities = []
    
    for pgn_file, data in lines.items():
        mistakes = data.get("mistakes", [])
        streaks = data.get("streaks", [])
        mastery_levels = data.get("mastery_level", [])
        easiness_factors = data.get("easiness_factor", [])
        last_practiced_list = data.get("last_practiced", [])
        interval_days_list = data.get("interval_days", [])
        recent_mistakes_list = data.get("recent_mistakes", [])
        
        for idx in range(len(data["lines"])):
            # Get values for this line, with defaults
            mastery = mastery_levels[idx] if idx < len(mastery_levels) else sr.DEFAULT_MASTERY_LEVEL
            easiness = easiness_factors[idx] if idx < len(easiness_factors) else sr.DEFAULT_EASINESS_FACTOR
            last_practiced = last_practiced_list[idx] if idx < len(last_practiced_list) else None
            interval = interval_days_list[idx] if idx < len(interval_days_list) else sr.DEFAULT_INTERVAL_DAYS
            recent_mistakes = recent_mistakes_list[idx] if idx < len(recent_mistakes_list) else []
            
            # Apply time-based decay to mastery
            mastery = sr.decay_mastery_over_time(mastery, last_practiced)
            
            # Calculate priority score
            priority = sr.calculate_priority_score(
                mastery_level=mastery,
                easiness_factor=easiness,
                last_practiced=last_practiced,
                interval_days=interval,
                recent_mistakes=recent_mistakes
            )
            
            line_priorities.append((pgn_file, idx, priority))
    
    if not line_priorities:
        return None, None
    
    # Use weighted random selection based on priority scores
    # Convert priorities to weights (exponential to emphasize differences)
    total_weight = 0.0
    weighted_choices = []
    
    for pgn_file, idx, priority in line_priorities:
        # Use exponential weighting to make high-priority lines much more likely
        weight = priority ** 2  # Square the priority for stronger emphasis
        weighted_choices.append((pgn_file, idx, weight))
        total_weight += weight
    
    if total_weight == 0:
        # Fallback: select randomly
        pgn_file, idx, _ = random.choice(line_priorities)
        return pgn_file, idx
    
    # Weighted random selection
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    for pgn_file, idx, weight in weighted_choices:
        cumulative += weight
        if r <= cumulative:
            return pgn_file, idx
    
    # Fallback (shouldn't reach here)
    pgn_file, idx, _ = line_priorities[0]
    return pgn_file, idx



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
