import pygame
import chess
import sys

# Constants
WIDTH, HEIGHT = 800, 800
SQUARE_SIZE = WIDTH // 8
PIECE_IMAGES = {}

###################
# Load piece images
###################

def load_images():
    pieces = ['R', 'N', 'B', 'Q', 'K', 'P', 'r', 'n', 'b', 'q', 'k', 'p']
    for piece in pieces:
        PIECE_IMAGES[piece] = pygame.transform.scale(
            pygame.image.load(f"images/{piece}.png"), (SQUARE_SIZE, SQUARE_SIZE)
        )

#################
# Draw chessboard
#################

def draw_board(screen):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

##########################
# Draw pieces on the board
##########################

def draw_pieces(screen, board, dragging_piece, mouse_pos, drag):
    for row in range(8):
        for col in range(8):
            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                if drag and dragging_piece[1] == chess.square(col, 7 - row):
                    # Skip drawing the piece that is being dragged
                    continue
                screen.blit(PIECE_IMAGES[piece.symbol()], pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    if drag:
        piece, start_square = dragging_piece
        screen.blit(PIECE_IMAGES[piece.symbol()], pygame.Rect(mouse_pos[0] - SQUARE_SIZE // 2, mouse_pos[1] - SQUARE_SIZE // 2, SQUARE_SIZE, SQUARE_SIZE))

##############
# Draw text 
##############

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

####################
# Load sound effects
####################


def load_sounds():
    move_sound = pygame.mixer.Sound("sounds/move-self.mp3")
    capture_sound = pygame.mixer.Sound("sounds/capture.mp3")
    check_sound = pygame.mixer.Sound("sounds/move-check.mp3")
    castle_sound = pygame.mixer.Sound("sounds/castle.mp3")
    return move_sound, capture_sound, check_sound, castle_sound


##################
# Checkmate screen
##################

def end_game(screen, board):
    popup_width, popup_height = 400, 200
    popup_x, popup_y = (screen.get_width() - popup_width) // 2, (screen.get_height() - popup_height) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    click = False
    while True:
        screen.fill((255, 255, 255), popup_rect)
        pygame.draw.rect(screen, (0, 0, 0), popup_rect, 2)
        if board.is_checkmate():
            winner = "Black" if board.turn else "White"
            draw_text(f"Checkmate - {winner} wins!", pygame.font.Font(None, 40), (0, 0, 0), screen, popup_x + 30, popup_y + 40)
        elif board.is_stalemate():
            draw_text(f"Stalemate - It's a draw!", pygame.font.Font(None, 40), (0, 0, 0), screen, popup_x + 30, popup_y + 40)
        elif board.is_insufficient_material():
            draw_text(f"Insufficient Material - It's a draw!", pygame.font.Font(None, 40), (0, 0, 0), screen, popup_x + 30, popup_y + 40)
        elif board.is_fifty_moves():
            draw_text(f"50 Move Rule - It's a draw!", pygame.font.Font(None, 40), (0, 0, 0), screen, popup_x + 30, popup_y + 40)
        elif board.is_fivefold_repetition():
            draw_text(f"Repetition - It's a draw!", pygame.font.Font(None, 40), (0, 0, 0), screen, popup_x + 30, popup_y + 40)
        else:
            break

        mx, my = pygame.mouse.get_pos()

        button_1 = pygame.Rect(popup_x + 50, popup_y + 100, 100, 50)
        button_2 = pygame.Rect(popup_x + 250, popup_y + 100, 100, 50)

        if button_1.collidepoint((mx, my)):
            if click:
                return True  # Play again
        if button_2.collidepoint((mx, my)):
            if click:
                return False  # Go to home screen

        pygame.draw.rect(screen, (0, 200, 0), button_1)
        pygame.draw.rect(screen, (200, 0, 0), button_2)

        draw_text('Play Again', pygame.font.Font(None, 24), (255, 255, 255), screen, button_1.x + 10, button_1.y + 15)
        draw_text('Home', pygame.font.Font(None, 36), (255, 255, 255), screen, button_2.x + 20, button_2.y + 10)

        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        pygame.display.update()

#######################
# Check for legal moves
#######################

def has_legal_moves(board, square):
    for move in board.legal_moves:
        if move.from_square == square:
            return True
    return False

########################
# Play sound for move
########################

def play_sound(board, move, move_sound, capture_sound, check_sound, castle_sound):
    #capture
    #print(board)
    #print(move)
    #print(board.gives_check(move))
    temp_board = board.copy()
    temp_board.push(move)

    if temp_board.is_check():
        check_sound.play()
    elif board.is_capture(move):
        capture_sound.play()
    elif board.is_castling(move):
        castle_sound.play()
    elif temp_board.is_checkmate():
        pass #get a checkmate sound.
    else:
        move_sound.play()