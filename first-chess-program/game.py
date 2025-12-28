import chess
import pygame
import utils
import sys

WIDTH, HEIGHT = utils.WIDTH, utils.HEIGHT
SQUARE_SIZE = utils.SQUARE_SIZE

def run_chess(screen):
    board = chess.Board()
    move_stack = []
    move_index = 0
    utils.load_images()
    move_sound, capture_sound, check_sound, castle_sound = utils.load_sounds()

    running = True
    dragging_piece = None
    mouse_x, mouse_y = 0, 0
    drag = False
    second_click = False

    def draw_cur_board():
        #print(board)
        temp_board = chess.Board()
        for move in move_stack[:move_index]:
            temp_board.push(move)
        utils.draw_board(screen)
        utils.draw_pieces(screen, temp_board, dragging_piece, (mouse_x, mouse_y), drag)

    while running:
        for event in pygame.event.get():
            #print(f"Selected square: {selected_square}")
            #print(f"dragging_piece: {dragging_piece}")
            #print(f"click_move: {click_move}")
            #print(f"drag: {drag}")
            #print(f"second_click: {second_click}")
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:  # Go backwards through the moves
                    if move_index > 0:
                        move_index -= 1
                elif event.key == pygame.K_RIGHT:  # Go forwards through the moves
                    if move_index < len(move_stack):
                        move_index += 1


            # MOUSE DOWN ############################################################
            elif event.type == pygame.MOUSEBUTTONDOWN:
                col, row = event.pos[0] // SQUARE_SIZE, event.pos[1] // SQUARE_SIZE
                square = chess.square(col, 7 - row)
                #checks to see if we are on most recent position...
                if move_index != len(move_stack):
                    move_index = len(move_stack)
                elif board.piece_at(square) and not second_click: #first click and a piece IS being selected
                    if utils.has_legal_moves(board, square):
                        second_click = False
                        dragging_piece = (board.piece_at(square), square)
                        drag = False
                    else: #piece is INVALID to move
                        dragging_piece = None
                        drag = False
                        second_click = False
                elif not board.piece_at(square) and not second_click: #first click and a piece IS NOT being selected
                    dragging_piece = None
                    drag = False
                    second_click = False
                elif second_click: #Second Click POTENTIAL CAPTURE
                    move = chess.Move(dragging_piece[1], square)
                    if move in board.legal_moves: #if the move is LEGAL
                        utils.play_sound(board, move, move_sound, capture_sound, check_sound, castle_sound)
                        board.push(move)
                        move_stack.append(move)
                        move_index += 1
                        if board.is_game_over():
                            utils.end_game(screen, board)
                            board = chess.Board()
                            move_stack = []
                            move_index = 0
                            draw_cur_board()
                            dragging_piece = None
                        drag = False


                #print("MOUSE DOWN")
                #print(f"Selected square: {selected_square}")
                #print(f"dragging_piece: {dragging_piece}")
                #print(f"click_move: {click_move}")
                #print(f"drag: {drag}")
                #print(f"second_click: {second_click}")

            # MOUSE UP #############################################
            elif event.type == pygame.MOUSEBUTTONUP:
                col, row = event.pos[0] // SQUARE_SIZE, event.pos[1] // SQUARE_SIZE
                square = chess.square(col, 7 - row)
                if drag: #if a piece is being dropped
                    if 0 <= col < 8 and 0 <= row < 8:
                        move = chess.Move(dragging_piece[1], square)
                        if move in board.legal_moves: #if the move is LEGAL
                            utils.play_sound(board, move, move_sound, capture_sound, check_sound, castle_sound)
                            board.push(move)
                            move_stack.append(move)
                            move_index += 1
                            if board.is_game_over():
                                utils.end_game(screen, board)
                                board = chess.Board()
                                move_stack = []
                                move_index = 0
                    draw_cur_board() #MAYBE I think board must be drawn to see peice move.
                    dragging_piece = None
                    second_click = False
                    drag = False
                    square = None
                    move = None
                    #print("MOUSE UP")
                    #print(f"Selected square: {selected_square}")
                    #print(f"dragging_piece: {dragging_piece}")
                    #print(f"click_move: {click_move}")
                    #print(f"drag: {drag}")
                    #print(f"second_click: {second_click}")
                else: #if click is released but not a drag
                    if not second_click:
                        if utils.has_legal_moves(board, square): #first click release on a valid piece
                            second_click = True
                            drag = False
                        else: #first click release on an invalid piece
                            dragging_piece = None
                            second_click = False
                            drag = False
                            square = None
                            move = None
                    elif second_click: #second click release
                        dragging_piece = None
                        second_click = False
                        drag = False
                        square = None
                        move = None
            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                mouse_x, mouse_y = event.pos
                # Update dragging piece position
                if dragging_piece:
                    drag = True
                second_click = False
                #print("MOUSE MOTION")
                #print(f"Selected square: {selected_square}")
                #print(f"dragging_piece: {dragging_piece}")
                #print(f"click_move: {click_move}")
                #print(f"drag: {drag}")
                #print(f"second_click: {second_click}")

        draw_cur_board()
        #utils.draw_pieces(screen, board, dragging_piece, (mouse_x, mouse_y))
        pygame.display.flip()

    return

def run_cpu_game():

    return

def run_training(pgn):

    return