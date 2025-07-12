import pygame
import random

# --- 定数 ---
WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 15
BALL_RADIUS = 10
BLOCK_ROWS = 5
BLOCK_COLUMNS = 10
BLOCK_WIDTH = WIDTH // BLOCK_COLUMNS
BLOCK_HEIGHT = 30

# 色
WHITE = (245, 245, 245)     # やさしい白
BLUE = (173, 206, 255)      # 淡い水色寄りの青
RED = (255, 179, 179)       # 淡いピンク寄りの赤
GREEN = (180, 235, 180)     # パステルグリーン
BLACK = (50, 50, 50)        # 真っ黒でなく、ソフトな黒
GRAY = (210, 210, 210)      # 明るめのグレー


# --- Paddleクラス（マウス対応） ---
class Paddle:
    def __init__(self, sensitivity=1.0):
        self.rect = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 40, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.prev_mouse_x = pygame.mouse.get_pos()[0]
        self.sensitivity = sensitivity

    def move(self):
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # 左クリック時のみ
            current_mouse_x = pygame.mouse.get_pos()[0]
            dx = (current_mouse_x - self.prev_mouse_x) * self.sensitivity
            self.rect.x += dx
            self.prev_mouse_x = current_mouse_x

            # 画面端制限
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
        else:
            # 非クリック時も座標記録だけ
            self.prev_mouse_x = pygame.mouse.get_pos()[0]

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)


# --- Ballクラス ---
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.dx = 3 * random.choice([-1, 1])
        self.dy = -3

    def update(self, paddle, blocks):
        self.rect.x += self.dx
        self.rect.y += self.dy

        # 壁反射
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.dx *= -1
        if self.rect.top <= 0:
            self.dy *= -1

        # パドルとの衝突
        if self.rect.colliderect(paddle.rect):
            self.dy *= -1

        # ブロックとの衝突
        for block in blocks:
            if self.rect.colliderect(block.rect):
                blocks.remove(block)
                self.dy *= -1
                return 10  # スコア加算
        return 0

    def draw(self, screen):
        pygame.draw.ellipse(screen, WHITE, self.rect)

    def reset(self):
        self.rect.x = WIDTH // 2
        self.rect.y = HEIGHT // 2
        self.dx *= random.choice([-1, 1])
        self.dy = -4


# --- Blockクラス ---
class Block:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BLOCK_WIDTH - 2, BLOCK_HEIGHT - 2)

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, self.rect)


# --- Buttonクラス ---
class Button:
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        label = self.font.render(self.text, True, WHITE)
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# --- Gameクラス ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Block Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.running = True
        self.state = "start"  # "start", "play", "gameover"

        self.slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 0.5, 2.0, 1.0, self.font)
        self.start_button = Button("Game Start!", WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 60, self.font)

        self.retry_button = Button("Onemore!", WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 60, self.font)

        self.init_game()

        self.state = "start"  # → "start", "play", "gameover", "clear"

    def init_game(self):
        self.paddle = Paddle(sensitivity=self.slider.value)
        self.ball = Ball()
        self.blocks = [Block(col * BLOCK_WIDTH, row * BLOCK_HEIGHT + 40)
                       for row in range(BLOCK_ROWS) for col in range(BLOCK_COLUMNS)]
        self.score = 0
        self.lives = 3

    def draw_text(self, text, x, y, color):
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == "start":
                self.slider.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and self.start_button.is_clicked(event.pos):
                    self.init_game()
                    self.state = "play"

            elif self.state == "gameover": 
                if event.type == pygame.MOUSEBUTTONDOWN and self.retry_button.is_clicked(event.pos):
                    self.init_game()
                    self.state = "play"
            
            elif self.state in ("gameover", "clear"):
                if event.type == pygame.MOUSEBUTTONDOWN and self.retry_button.is_clicked(event.pos):
                    self.init_game()
                    self.state = "play"

    def update_game(self):
        self.paddle.move()
        # ボールを更新して得点加算
        score_gain = self.ball.update(self.paddle, self.blocks)
        self.score += score_gain

        # ボールが画面下に落ちたらリセット＆ライフ減少
        if self.ball.rect.bottom >= HEIGHT:
            self.lives -= 1
            self.ball.reset()

        # ライフが尽きたらゲームオーバー
        if self.lives <= 0:
            self.state = "gameover"

        # ブロックが全て消えたらクリア
        if not self.blocks:
            self.state = "clear"

    def draw_game(self):
        self.screen.fill(BLACK)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        for block in self.blocks:
            block.draw(self.screen)
        self.draw_text(f"Score: {self.score}", 10, 10, WHITE)
        self.draw_text(f"Lives: {self.lives}", WIDTH - 120, 10, WHITE)

    def draw_start_screen(self):
        self.screen.fill(BLACK)
        self.draw_text("Block Breaker", WIDTH // 2 - 80, HEIGHT // 2 - 100, WHITE)
        self.slider.draw(self.screen)
        self.start_button.draw(self.screen)

    def draw_gameover_screen(self):
        self.screen.fill(BLACK)
        self.draw_text("Game Over", WIDTH // 2 - 80, HEIGHT // 2 - 100, RED)
        self.draw_text(f"Score: {self.score}", WIDTH // 2 - 60, HEIGHT // 2 - 50, WHITE)
        self.retry_button.draw(self.screen)

    def draw_clear_screen(self):
        self.screen.fill(BLACK)
        self.draw_text("Game Clear!", WIDTH // 2 - 100, HEIGHT // 2 - 60, GREEN)
        self.draw_text(f"Score: {self.score}", WIDTH // 2 - 60, HEIGHT // 2 - 10, WHITE)
        self.retry_button.draw(self.screen)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()

            if self.state == "start":
                self.draw_start_screen()

            elif self.state == "play":
                self.update_game()
                self.draw_game()

            elif self.state == "gameover":
                 self.draw_gameover_screen()
            
            elif self.state == "clear":
                self.draw_clear_screen()

            pygame.display.flip()

        pygame.quit()


# --- Sliderクラス ---
class Slider:
    def __init__(self, x, y, width, min_value, max_value, initial_value, font):
        self.rect = pygame.Rect(x, y, width, 10)
        self.knob_radius = 8
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False
        self.font = font

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.get_knob_rect().collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value_from_mouse_x(event.pos[0])

    def set_value_from_mouse_x(self, x):
        pos_ratio = (x - self.rect.left) / self.rect.width
        pos_ratio = max(0, min(1, pos_ratio))
        self.value = self.min_value + (self.max_value - self.min_value) * pos_ratio

    def get_knob_rect(self):
        knob_x = self.rect.left + (self.value - self.min_value) / (self.max_value - self.min_value) * self.rect.width
        return pygame.Rect(knob_x - self.knob_radius, self.rect.centery - self.knob_radius, self.knob_radius * 2, self.knob_radius * 2)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.circle(screen, RED, self.get_knob_rect().center, self.knob_radius)
        value_text = self.font.render(f"Sensivity: {self.value:.2f}", True, WHITE)
        screen.blit(value_text, (self.rect.left, self.rect.top - 30))


# --- 実行 ---
if __name__ == "__main__":
    game = Game()
    game.run().rect.left, self.rect.top - 30


# --- 実行 ---
if __name__ == "__main__":
    game = Game()
    game.run()
