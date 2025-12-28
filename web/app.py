"""
Flask web application for Chess Opening Trainer
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess_pgn_parser as cp
import user_profiles as up
import spaced_repetition as sr
import chess
import json
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Global state for current training session
training_sessions = {}

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/static/pieces/<filename>')
def serve_piece_image(filename):
    """Serve chess piece images."""
    # Pieces are in the static/pieces directory relative to this file
    pieces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pieces')
    return send_from_directory(pieces_dir, filename)

@app.route('/api/pgn/list', methods=['GET'])
def list_pgn_files():
    """List available PGN files in white and black folders."""
    pgn_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pgn')
    white_folder = os.path.join(pgn_dir, 'white')
    black_folder = os.path.join(pgn_dir, 'black')
    
    white_files = []
    black_files = []
    
    if os.path.exists(white_folder):
        white_files = [f for f in os.listdir(white_folder) if f.endswith('.pgn')]
    
    if os.path.exists(black_folder):
        black_files = [f for f in os.listdir(black_folder) if f.endswith('.pgn')]
    
    return jsonify({
        'white': white_files,
        'black': black_files
    })

@app.route('/api/training/start', methods=['POST'])
def start_training():
    """Start a new training session."""
    data = request.json
    username = data.get('username', 'guest')
    selected_files = data.get('selectedFiles', [])
    
    if not selected_files:
        return jsonify({'error': 'No PGN files selected'}), 400
    
    # Get full paths to PGN files
    pgn_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pgn')
    full_paths = []
    for file in selected_files:
        # Determine if white or black based on folder
        if os.path.exists(os.path.join(pgn_dir, 'white', file)):
            full_paths.append(os.path.join(pgn_dir, 'white', file))
        elif os.path.exists(os.path.join(pgn_dir, 'black', file)):
            full_paths.append(os.path.join(pgn_dir, 'black', file))
    
    # Load user profile and parse PGNs
    profile = up.load_user_profile(username)
    lines = cp.parse_all_pgn(full_paths)
    up.merge_training_data(lines, profile)
    
    # Generate session ID
    import uuid
    session_id = str(uuid.uuid4())
    
    # Store session data
    training_sessions[session_id] = {
        'username': username,
        'lines': lines,
        'current_line': None,
        'current_index': 0,
        'opening_name': None,
        'line_index': None,
        'board_fen': None,
        'user_color': None,
        'mistake_made': False,
        'ace': True
    }
    
    return jsonify({
        'sessionId': session_id,
        'username': username
    })

@app.route('/api/training/next-line', methods=['POST'])
def get_next_line():
    """Get the next line to practice using spaced repetition."""
    data = request.json
    session_id = data.get('sessionId')
    
    if session_id not in training_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = training_sessions[session_id]
    lines = session['lines']
    
    # Get next line using spaced repetition
    opening_name, line_index = cp.get_weighted_line(lines)
    
    if opening_name is None or line_index is None:
        return jsonify({'error': 'No lines available'}), 400
    
    line = lines[opening_name]['lines'][line_index]
    user_color = line[0][3]
    
    # Get initial board state
    initial_board = line[0][2]
    board_fen = initial_board.fen()
    
    # Update session
    session['current_line'] = line
    session['current_index'] = 0
    session['opening_name'] = opening_name
    session['line_index'] = line_index
    session['board_fen'] = board_fen
    session['user_color'] = user_color
    session['mistake_made'] = False
    session['ace'] = True
    
    # Get current position info
    position_info = get_current_position_info(session)
    
    # If the line starts with opponent's move (e.g., black opening where white moves first),
    # play it and advance to user's turn
    next_board_fen = board_fen
    if not position_info.get('isComplete') and not position_info.get('isUserTurn') and position_info.get('opponentMove'):
        # Play the opponent's initial move
        opponent_move = position_info.get('opponentMove')
        try:
            initial_board = chess.Board(board_fen)
            opp_move_obj = chess.Move.from_uci(opponent_move)
            initial_board.push(opp_move_obj)
            next_board_fen = initial_board.fen()
            # Advance index past opponent move
            session['current_index'] += 1
            position_info = get_current_position_info(session)
            # Store opponent move to play for frontend animation
            position_info['opponentMoveToPlay'] = opponent_move
        except Exception as e:
            print(f"Error processing initial opponent move: {e}")
    
    return jsonify({
        'openingName': opening_name,
        'lineIndex': line_index,
        'boardFen': next_board_fen,  # FEN after initial opponent move if applicable
        'userColor': 'white' if user_color == chess.WHITE else 'black',
        'positionInfo': position_info  # Position info for user's first turn
    })

def get_current_position_info(session):
    """Get information about the current position."""
    line = session['current_line']
    index = session['current_index']
    user_color = session['user_color']
    
    if index >= len(line):
        return {
            'isUserTurn': False,
            'isComplete': True,
            'correctMove': None
        }
    
    board_fen, correct_move, board_copy, color = line[index]
    board = chess.Board(board_fen)
    
    is_user_turn = (board.turn == user_color)
    
    return {
        'isUserTurn': is_user_turn,
        'isComplete': False,
        'correctMove': correct_move.uci() if is_user_turn else None,
        'opponentMove': correct_move.uci() if not is_user_turn else None
    }

@app.route('/api/training/move', methods=['POST'])
def submit_move():
    """Submit a move and check if it's correct."""
    data = request.json
    session_id = data.get('sessionId')
    move_uci = data.get('move')
    
    if session_id not in training_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = training_sessions[session_id]
    line = session['current_line']
    index = session['current_index']
    user_color = session['user_color']
    
    if index >= len(line):
        return jsonify({'error': 'Line already complete'}), 400
    
    board_fen, correct_move, board_copy, color = line[index]
    board = chess.Board(board_fen)
    
    # Check if it's user's turn
    if board.turn != user_color:
        # Debug logging
        print(f"Turn check: board.turn={board.turn}, user_color={user_color}, match={board.turn == user_color}")
        return jsonify({'error': f'Not your turn. Board turn: {board.turn}, User color: {user_color}'}), 400
    
    # Parse the move
    try:
        user_move = chess.Move.from_uci(move_uci)
        if user_move not in board.legal_moves:
            return jsonify({
                'correct': False,
                'error': 'Illegal move'
            }), 400
    except ValueError:
        return jsonify({'error': 'Invalid move format'}), 400
    
    # Check if move is correct
    is_correct = (user_move == correct_move)
    
    if is_correct:
        board.push(user_move)
        session['current_index'] += 1
        
        # Check if line is complete
        if session['current_index'] >= len(line):
            # Update spaced repetition metrics
            update_line_completion(session)
            # Save profile
            if session['username']:
                up.save_user_profile(session['lines'], session['username'])
        
        position_info = get_current_position_info(session)
        next_board_fen = board.fen()
        
        # If the next position is opponent's turn, we need to:
        # 1. Return the opponent move to play
        # 2. Return position info for AFTER opponent move (user's next turn)
        if not position_info.get('isComplete') and not position_info.get('isUserTurn') and position_info.get('opponentMove'):
            # Store opponent move
            opponent_move = position_info.get('opponentMove')
            # Play opponent move on board to get the FEN after opponent move
            try:
                opp_move_obj = chess.Move.from_uci(opponent_move)
                board.push(opp_move_obj)
                next_board_fen = board.fen()
                # Advance index past opponent move to get position info for user's next turn
                session['current_index'] += 1
                position_info = get_current_position_info(session)
                # But we still need to tell frontend to play the opponent move
                # So we add it back to position info
                position_info['opponentMoveToPlay'] = opponent_move
            except Exception as e:
                print(f"Error processing opponent move: {e}")
        
        return jsonify({
            'correct': True,
            'boardFen': next_board_fen,  # FEN after user move (and opponent move if applicable)
            'positionInfo': position_info,  # Position info for user's next turn (or current if no opponent move)
            'lineComplete': session['current_index'] >= len(line),
            'userColor': 'white' if user_color == chess.WHITE else 'black'
        })
    else:
        # Log mistake
        if not session['mistake_made']:
            opening_name = session['opening_name']
            line_index = session['line_index']
            lines = session['lines']
            
            lines[opening_name]['mistakes'][line_index] += 1
            if 'recent_mistakes' in lines[opening_name]:
                if line_index < len(lines[opening_name]['recent_mistakes']):
                    lines[opening_name]['recent_mistakes'][line_index] = sr.add_mistake_timestamp(
                        lines[opening_name]['recent_mistakes'][line_index]
                    )
            
            session['mistake_made'] = True
            session['ace'] = False
            if 'streaks' in lines[opening_name]:
                lines[opening_name]['streaks'][line_index] = 0
        
        return jsonify({
            'correct': False,
            'correctMove': correct_move.uci()
        })

@app.route('/api/training/hint', methods=['POST'])
def get_hint():
    """Get a hint for the current move (shows the starting square)."""
    data = request.json
    session_id = data.get('sessionId')
    
    if session_id not in training_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = training_sessions[session_id]
    line = session['current_line']
    index = session['current_index']
    
    if index >= len(line):
        return jsonify({'error': 'Line already complete'}), 400
    
    board_fen, correct_move, board_copy, color = line[index]
    
    # Log mistake
    if not session['mistake_made']:
        opening_name = session['opening_name']
        line_index = session['line_index']
        lines = session['lines']
        
        lines[opening_name]['mistakes'][line_index] += 1
        if 'recent_mistakes' in lines[opening_name]:
            if line_index < len(lines[opening_name]['recent_mistakes']):
                lines[opening_name]['recent_mistakes'][line_index] = sr.add_mistake_timestamp(
                    lines[opening_name]['recent_mistakes'][line_index]
                )
        
        session['mistake_made'] = True
        session['ace'] = False
    
    return jsonify({
        'hintSquare': chess.square_name(correct_move.from_square)
    })

@app.route('/api/training/solution', methods=['POST'])
def get_solution():
    """Get the solution for the current move."""
    data = request.json
    session_id = data.get('sessionId')
    show_only = data.get('showOnly', False)  # If True, just return the move without executing
    
    if session_id not in training_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = training_sessions[session_id]
    line = session['current_line']
    index = session['current_index']
    
    if index >= len(line):
        return jsonify({'error': 'Line already complete'}), 400
    
    board_fen, correct_move, board_copy, color = line[index]
    
    # If showOnly is True, just return the move without executing
    if show_only:
        return jsonify({
            'correctMove': correct_move.uci()
        })
    
    # Otherwise, execute the move (original behavior)
    board = chess.Board(board_fen)
    board.push(correct_move)
    
    # Log mistake
    if not session['mistake_made']:
        opening_name = session['opening_name']
        line_index = session['line_index']
        lines = session['lines']
        
        lines[opening_name]['mistakes'][line_index] += 1
        if 'recent_mistakes' in lines[opening_name]:
            if line_index < len(lines[opening_name]['recent_mistakes']):
                lines[opening_name]['recent_mistakes'][line_index] = sr.add_mistake_timestamp(
                    lines[opening_name]['recent_mistakes'][line_index]
                )
        
        session['mistake_made'] = True
        session['ace'] = False
    
    session['current_index'] += 1
    
    # Check if line is complete
    if session['current_index'] >= len(line):
        update_line_completion(session)
        if session['username']:
            up.save_user_profile(session['lines'], session['username'])
    
    position_info = get_current_position_info(session)
    
    return jsonify({
        'correctMove': correct_move.uci(),
        'boardFen': board.fen(),
        'positionInfo': position_info,
        'lineComplete': session['current_index'] >= len(line)
    })

def update_line_completion(session):
    """Update spaced repetition metrics after completing a line."""
    opening_name = session['opening_name']
    line_index = session['line_index']
    lines = session['lines']
    ace = session['ace']
    
    # Ensure all lists exist
    if 'mastery_level' not in lines[opening_name]:
        lines[opening_name]['mastery_level'] = [sr.DEFAULT_MASTERY_LEVEL] * len(lines[opening_name]['mistakes'])
    if 'easiness_factor' not in lines[opening_name]:
        lines[opening_name]['easiness_factor'] = [sr.DEFAULT_EASINESS_FACTOR] * len(lines[opening_name]['mistakes'])
    if 'last_practiced' not in lines[opening_name]:
        lines[opening_name]['last_practiced'] = [None] * len(lines[opening_name]['mistakes'])
    if 'interval_days' not in lines[opening_name]:
        lines[opening_name]['interval_days'] = [sr.DEFAULT_INTERVAL_DAYS] * len(lines[opening_name]['mistakes'])
    if 'recent_mistakes' not in lines[opening_name]:
        lines[opening_name]['recent_mistakes'] = [[] for _ in range(len(lines[opening_name]['mistakes']))]
    
    # Get current values
    mastery = lines[opening_name]['mastery_level'][line_index] if line_index < len(lines[opening_name]['mastery_level']) else sr.DEFAULT_MASTERY_LEVEL
    easiness = lines[opening_name]['easiness_factor'][line_index] if line_index < len(lines[opening_name]['easiness_factor']) else sr.DEFAULT_EASINESS_FACTOR
    streak = lines[opening_name]['streaks'][line_index] if line_index < len(lines[opening_name]['streaks']) else 0
    mistake_count = lines[opening_name]['mistakes'][line_index] if line_index < len(lines[opening_name]['mistakes']) else 0
    current_interval = lines[opening_name]['interval_days'][line_index] if line_index < len(lines[opening_name]['interval_days']) else sr.DEFAULT_INTERVAL_DAYS
    
    # Update streak
    if ace:
        lines[opening_name]['streaks'][line_index] = streak + 1
    else:
        lines[opening_name]['streaks'][line_index] = 0
    
    # Update mastery and easiness
    new_mastery, new_easiness = sr.update_mastery_after_practice(
        mastery, easiness, ace, streak, mistake_count
    )
    
    # Calculate new interval
    new_interval = sr.calculate_next_interval(
        new_mastery, new_easiness, current_interval, ace, lines[opening_name]['streaks'][line_index]
    )
    
    # Update all values
    lines[opening_name]['mastery_level'][line_index] = new_mastery
    lines[opening_name]['easiness_factor'][line_index] = new_easiness
    lines[opening_name]['interval_days'][line_index] = new_interval
    lines[opening_name]['last_practiced'][line_index] = datetime.now().isoformat()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

