import pygame
import random
import json
import os

# Get the screen resolution
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Game configuration
BLOCK_SIZE = 30
PLAY_WIDTH = BLOCK_SIZE * 10  # Standard Tetris board is 10 blocks wide
PLAY_HEIGHT = BLOCK_SIZE * 20  # Standard Tetris board is 20 blocks high
WIDTH = min(SCREEN_WIDTH, PLAY_WIDTH + 400)  # Add space for UI
HEIGHT = min(SCREEN_HEIGHT, PLAY_HEIGHT + 40)  # Add some padding

# Calculate the starting position to center the game board
PLAY_X = (WIDTH - PLAY_WIDTH) // 4
PLAY_Y = (HEIGHT - PLAY_HEIGHT) // 2

ROWS = PLAY_HEIGHT // BLOCK_SIZE
COLUMNS = PLAY_WIDTH // BLOCK_SIZE
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # Cyan - I piece
    (255, 255, 0),  # Yellow - O piece
    (255, 165, 0),  # Orange - L piece
    (0, 0, 255),    # Blue - J piece
    (0, 255, 0),    # Green - S piece
    (255, 0, 0),    # Red - Z piece
    (128, 0, 128)   # Purple - T piece
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1], [1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 1], [1, 0, 0]],
    [[1, 1, 1], [0, 0, 1]]
]

class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.color = random.choice(COLORS)
        self.x = COLUMNS // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        # Even smaller fonts to match the image
        self.title_font = pygame.font.Font(None, 32)  # Title font
        self.font = pygame.font.Font(None, 28)       # Regular font
        self.small_font = pygame.font.Font(None, 20)  # Very small font for controls
        self.load_high_score()
        self.reset_game()

    def load_high_score(self):
        self.high_score = 0
        if os.path.exists('highscore.json'):
            try:
                with open('highscore.json', 'r') as f:
                    self.high_score = json.load(f)['high_score']
            except:
                pass

    def save_high_score(self):
        with open('highscore.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)

    def reset_game(self):
        self.board = [[BLACK for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.current_tetromino = self.new_tetromino()
        self.next_tetromino = self.new_tetromino()
        self.held_tetromino = None
        self.can_hold = True
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.line_clear_animation = []
        self.line_clear_timer = 0

    def new_tetromino(self):
        return Tetromino(random.choice(SHAPES))

    def get_shadow_position(self):
        shadow = Tetromino(self.current_tetromino.shape)
        shadow.x = self.current_tetromino.x
        shadow.y = self.current_tetromino.y
        
        while not self.check_collision(shadow):
            shadow.y += 1
        shadow.y -= 1
        
        return shadow

    def draw_board(self):
        # Draw game border
        pygame.draw.rect(self.screen, WHITE, (PLAY_X - 2, PLAY_Y - 2, PLAY_WIDTH + 4, PLAY_HEIGHT + 4), 2)
        
        # Draw board
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color != BLACK:
                    pygame.draw.rect(self.screen, color, 
                                   (PLAY_X + x * BLOCK_SIZE, 
                                    PLAY_Y + y * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(self.screen, GRAY, 
                               (PLAY_X + x * BLOCK_SIZE, 
                                PLAY_Y + y * BLOCK_SIZE, 
                                BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_tetromino(self, tetromino):
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, tetromino.color,
                                   (PLAY_X + (tetromino.x + x) * BLOCK_SIZE,
                                    PLAY_Y + (tetromino.y + y) * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE))

    def draw_next_tetromino(self):
        # Draw next piece below controls
        next_x = PLAY_X + PLAY_WIDTH + 20
        next_y = HEIGHT - 100
        
        # Draw "NEXT" text
        next_text = self.title_font.render("NEXT", True, WHITE)
        next_rect = next_text.get_rect(x=next_x, y=next_y)
        self.screen.blit(next_text, next_rect)
        
        # Draw next piece below the text
        offset_y = 30
        for y, row in enumerate(self.next_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_tetromino.color,
                                   (next_x + x * BLOCK_SIZE,
                                    next_y + offset_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE))

    def draw_held_piece(self):
        if self.held_tetromino:
            # Draw in left panel
            hold_x = 50
            hold_y = 50
            
            # Draw "HOLD" text with title font
            hold_text = self.title_font.render("HOLD", True, WHITE)
            self.screen.blit(hold_text, (hold_x, hold_y))
            
            # Draw held piece below the text
            offset_y = 60  # Space between text and piece
            for y, row in enumerate(self.held_tetromino.shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(self.screen, self.held_tetromino.color,
                                       (hold_x + x * BLOCK_SIZE,
                                        hold_y + offset_y + y * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE))

    def draw_game_info(self):
        # Right side info - start closer to game area
        info_x = PLAY_X + PLAY_WIDTH + 20
        info_y = 20
        spacing = 25  # Tighter spacing
        
        # Score section
        score_title = self.title_font.render("SCORE", True, WHITE)
        score_rect = score_title.get_rect(x=info_x, y=info_y)
        self.screen.blit(score_title, score_rect)
        
        score_text = self.font.render(str(self.score), True, WHITE)
        score_num_rect = score_text.get_rect(x=info_x, y=info_y + spacing)
        self.screen.blit(score_text, score_num_rect)
        
        # High score section
        high_score_y = info_y + spacing * 3
        high_score_title = self.title_font.render("HIGH SCORE", True, WHITE)
        high_score_rect = high_score_title.get_rect(x=info_x, y=high_score_y)
        self.screen.blit(high_score_title, high_score_rect)
        
        high_score_text = self.font.render(str(self.high_score), True, WHITE)
        high_score_num_rect = high_score_text.get_rect(x=info_x, y=high_score_y + spacing)
        self.screen.blit(high_score_text, high_score_num_rect)
        
        # Level and lines
        level_y = high_score_y + spacing * 3
        level_text = self.small_font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(x=info_x, y=level_y)
        self.screen.blit(level_text, level_rect)
        
        lines_text = self.small_font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        lines_rect = lines_text.get_rect(x=info_x, y=level_y + spacing)
        self.screen.blit(lines_text, lines_rect)
        
        # Controls section
        controls_y = level_y + spacing * 3
        controls_title = self.title_font.render("CONTROLS", True, WHITE)
        controls_rect = controls_title.get_rect(x=info_x, y=controls_y)
        self.screen.blit(controls_title, controls_rect)
        
        # Controls list with minimal spacing
        controls = [
            "⬅️ ➡️ Move",
            "⬆️ Rotate",
            "⬇️ Soft Drop",
            "⏬ Hard Drop"
        ]
        
        control_spacing = 20  # Minimal spacing between controls
        for i, text in enumerate(controls):
            help_text = self.small_font.render(text, True, WHITE)
            help_rect = help_text.get_rect(x=info_x, y=controls_y + spacing + i * control_spacing)
            self.screen.blit(help_text, help_rect)

    def check_collision(self, tetromino):
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    if (tetromino.y + y >= ROWS or
                        tetromino.x + x < 0 or
                        tetromino.x + x >= COLUMNS or
                        self.board[tetromino.y + y][tetromino.x + x] != BLACK):
                        return True
        return False

    def merge_tetromino(self):
        for y, row in enumerate(self.current_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.board[self.current_tetromino.y + y][self.current_tetromino.x + x] = self.current_tetromino.color

    def remove_lines(self):
        lines_to_remove = [i for i, row in enumerate(self.board) if BLACK not in row]
        for line in lines_to_remove:
            del self.board[line]
            self.board.insert(0, [BLACK for _ in range(COLUMNS)])
        return len(lines_to_remove)

    def update_score(self, lines_cleared):
        self.lines_cleared += lines_cleared
        self.score += lines_cleared * 100 * self.level
        if self.lines_cleared >= self.level * 10:
            self.level += 1

    def hold_piece(self):
        if not self.can_hold:
            return
        
        if self.held_tetromino is None:
            self.held_tetromino = Tetromino(self.current_tetromino.shape)
            self.current_tetromino = self.next_tetromino
            self.next_tetromino = self.new_tetromino()
        else:
            temp = Tetromino(self.current_tetromino.shape)
            self.current_tetromino = Tetromino(self.held_tetromino.shape)
            self.held_tetromino = temp
        
        self.can_hold = False

    def run(self):
        fall_time = 0
        fall_speed = 0.27
        
        while True:
            fall_time += self.clock.get_rawtime()
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_high_score()
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and not self.paused:
                        self.current_tetromino.x -= 1
                        if self.check_collision(self.current_tetromino):
                            self.current_tetromino.x += 1
                    if event.key == pygame.K_RIGHT and not self.paused:
                        self.current_tetromino.x += 1
                        if self.check_collision(self.current_tetromino):
                            self.current_tetromino.x -= 1
                    if event.key == pygame.K_DOWN and not self.paused:
                        self.current_tetromino.y += 1
                        if self.check_collision(self.current_tetromino):
                            self.current_tetromino.y -= 1
                    if event.key == pygame.K_UP and not self.paused:
                        self.current_tetromino.rotate()
                        if self.check_collision(self.current_tetromino):
                            for _ in range(3):
                                self.current_tetromino.rotate()
                    if event.key == pygame.K_SPACE and not self.paused:
                        while not self.check_collision(self.current_tetromino):
                            self.current_tetromino.y += 1
                            self.score += 1  # Add points for hard drop
                        self.current_tetromino.y -= 1
                        self.merge_tetromino()
                        lines_cleared = self.remove_lines()
                        self.update_score(lines_cleared)
                        self.current_tetromino = self.next_tetromino
                        self.next_tetromino = self.new_tetromino()
                        self.can_hold = True
                        if self.check_collision(self.current_tetromino):
                            if self.score > self.high_score:
                                self.high_score = self.score
                                self.save_high_score()
                            self.game_over = True
                    if event.key == pygame.K_c and not self.paused:
                        self.hold_piece()
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_r:
                        self.reset_game()

            if not self.paused and not self.game_over:
                # Increase speed with level
                current_fall_speed = fall_speed * (0.8 ** (self.level - 1))
                
                if fall_time / 1000 > current_fall_speed:
                    self.current_tetromino.y += 1
                    if self.check_collision(self.current_tetromino):
                        self.current_tetromino.y -= 1
                        self.merge_tetromino()
                        lines_cleared = self.remove_lines()
                        self.update_score(lines_cleared)
                        self.current_tetromino = self.next_tetromino
                        self.next_tetromino = self.new_tetromino()
                        self.can_hold = True
                        if self.check_collision(self.current_tetromino):
                            if self.score > self.high_score:
                                self.high_score = self.score
                                self.save_high_score()
                            self.game_over = True
                    fall_time = 0

            self.screen.fill(BLACK)
            
            # Draw shadow piece
            if not self.paused and not self.game_over:
                shadow = self.get_shadow_position()
                for y, row in enumerate(shadow.shape):
                    for x, cell in enumerate(row):
                        if cell:
                            pygame.draw.rect(self.screen, GRAY,
                                           (PLAY_X + (shadow.x + x) * BLOCK_SIZE,
                                            PLAY_Y + (shadow.y + y) * BLOCK_SIZE,
                                            BLOCK_SIZE, BLOCK_SIZE))
            
            self.draw_board()
            self.draw_tetromino(self.current_tetromino)
            self.draw_held_piece()
            self.draw_next_tetromino()
            self.draw_game_info()

            if self.paused:
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128))
                self.screen.blit(s, (0, 0))
                pause_text = self.title_font.render("PAUSED", True, WHITE)
                self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))
            elif self.game_over:
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128))
                self.screen.blit(s, (0, 0))
                game_over_text = self.title_font.render("GAME OVER", True, WHITE)
                self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
                restart_text = self.font.render("Press R to restart", True, WHITE)
                self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 40))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()