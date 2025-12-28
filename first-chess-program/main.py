import pygame
import chess
import utils
from game import run_chess, run_cpu_game, run_training
from utils import draw_text
import sys, os

WIDTH, HEIGHT = utils.WIDTH, utils.HEIGHT
SQUARE_SIZE = utils.SQUARE_SIZE
BACK_BUTTON_RECT = pygame.Rect(WIDTH - 110, 10, 100, 40)
# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Main function
def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")

    def main_screen():
        while True:
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True
            screen.fill((255, 255, 255))
            draw_text('Opening Trainer', pygame.font.Font(None, 74), (0, 0, 0), screen, 200, 100)

            mx, my = pygame.mouse.get_pos()

            button_1 = pygame.Rect(300, 250, 200, 50)
            button_2 = pygame.Rect(300, 350, 200, 50)
            button_3 = pygame.Rect(300, 450, 200, 50)
            button_4 = pygame.Rect(300, 550, 200, 50)

            if button_1.collidepoint((mx, my)):
                if click:
                    play_mode_selection(screen)
            if button_2.collidepoint((mx, my)):
                if click:
                    pass  # Create Lines
            if button_3.collidepoint((mx, my)):
                if click:
                    load_lines(screen)
            if button_4.collidepoint((mx, my)):
                if click:
                    pygame.quit()
                    break

            pygame.draw.rect(screen, (200, 0, 0), button_1)
            pygame.draw.rect(screen, (200, 0, 0), button_2)
            pygame.draw.rect(screen, (200, 0, 0), button_3)
            pygame.draw.rect(screen, (200, 0, 0), button_4)

            draw_text('Start Game', pygame.font.Font(None, 36), (255, 255, 255), screen, 340, 260)
            draw_text('Create Lines', pygame.font.Font(None, 36), (255, 255, 255), screen, 330, 360)
            draw_text('Load Lines', pygame.font.Font(None, 36), (255, 255, 255), screen, 340, 460)
            draw_text('Quit', pygame.font.Font(None, 36), (255, 255, 255), screen, 370, 560)


            pygame.display.update()

    def play_mode_selection(screen):
        while True:
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True
            screen.fill((255, 255, 255))
            utils.draw_text('Select Play Mode', pygame.font.Font(None, 64), (0, 0, 0), screen, 200, 100)
            mx, my = pygame.mouse.get_pos()
            button_1 = pygame.Rect(300, 250, 200, 50)
            button_2 = pygame.Rect(300, 350, 200, 50)
            #click = False
            if button_1.collidepoint((mx, my)):
                if click:
                    run_chess(screen)  # Start multiplayer game
            if button_2.collidepoint((mx, my)):
                if click:
                    run_cpu_game(screen)  # Start game against CPU
            pygame.draw.rect(screen, (200, 0, 0), button_1)
            pygame.draw.rect(screen, (200, 0, 0), button_2)
            utils.draw_text('Multiplayer', pygame.font.Font(None, 36), (255, 255, 255), screen, 330, 260)
            utils.draw_text('Engine', pygame.font.Font(None, 36), (255, 255, 255), screen, 330, 360)

            pygame.display.update()

    def load_lines(screen):
        #set up window/screen
        #screen.fill((255,255, 255))
        pygame.display.set_caption('Select a File')

        # set up fonts
        font = pygame.font.Font(None, 36)

        #list the files in the target direct
        directory = 'pgn'
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        #function to render text
        def render_text(text, pos):
            text_surface = font.render(text, True, (0, 0, 0))
            screen.blit(text_surface, pos)

        #variables to handle scrolling
        scroll_y = 0
        scroll_speed = 40
        max_scroll_y = max(0, len(files) * 40 - HEIGHT)

        #get index of file clicked
        def get_file_index(mouse_pos):
            x, y = mouse_pos
            index = (y + scroll_y) // 40
            if 0 <= index < len(files) and x < 400:
                return index
            return None
        
        #main loop
        running = True
        while running:
            screen.fill((255,255,255))

            #event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if BACK_BUTTON_RECT.collidepoint(event.pos):
                            running = False
                        else:
                            selected_index = get_file_index(event.pos)
                            if selected_index is not None:
                                selected_file = files[selected_index]
                                print(f"Selected file: {selected_file}")
                                running = False
                                run_training(selected_file)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 4:
                        scroly_y = max(scroll_y - scroll_speed, 0 )
                    elif event.button == 5:
                        scroll_y = min(scroll_y + scroll_speed, max_scroll_y)

            #draw back button
            pygame.draw.rect(screen, RED, BACK_BUTTON_RECT)
            render_text('Back', (WIDTH - BACK_BUTTON_RECT.width + 10, 15))
            #draw files
            for i, file in enumerate(files):
                render_text(file, (20, i *40 - scroll_y))

            pygame.display.update()
    main_screen()

if __name__ == "__main__":
    main()