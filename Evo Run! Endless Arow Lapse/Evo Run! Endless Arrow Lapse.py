import pygame
import random
import sys
import os
from PIL import Image, ImageSequence
import math

pygame.init()

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Evo Run! Endless Arrow Lapse")
CLOCK = pygame.time.Clock()
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
YELLOW = (255, 251, 0)

BAR_Y = HEIGHT // 2
BOX_SIZE = 40

FONT = pygame.font.SysFont(None, 36)
BIG_FONT = pygame.font.SysFont(None, 64)

# ---------------- RAINBOW COLOR ----------------
def rainbow(t):
    return (
        int(128 + 127 * math.sin(t)),
        int(128 + 127 * math.sin(t + 2)),
        int(128 + 127 * math.sin(t + 4))
    )

# ---------------- GIF LOADER ----------------
def load_gif(path, max_height):
    frames = []
    durations = []
    img = Image.open(path)
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert("RGBA")
        w, h = frame.size
        scale = min(max_height / h, 1.0)
        frame = frame.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        surface = pygame.image.fromstring(frame.tobytes(), frame.size, "RGBA").convert_alpha()
        frames.append(surface)
        durations.append(frame.info.get("duration", 100))
    return frames, durations

# ---------------- PATHS ----------------
try:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

GIF_FOLDER = os.path.join(SCRIPT_DIR, "gifs")

NORMAL_GIFS = [
    "Eevee dancing.gif",
    "Umbreon dancing.gif",
    "Sylveon dancing.gif",
    "Glaceon dancing.gif",
    "Groovy Espeon.gif",
    "Jolteon dancing.gif"
]

GAME_OVER_GIFS = [
    "Espeon amused.gif",
    "Sylveon sad.gif",
    "Flareon firebreath.gif"
]

RANK_GIFS = {
    "C": "Rank C.gif",
    "B": "Rank B.gif",
    "A": "Rank A.gif",
    "S": "Rank S.gif"
}

NORMAL_GIF_FILES = [
    os.path.join(GIF_FOLDER, name)
    for name in NORMAL_GIFS
    if os.path.exists(os.path.join(GIF_FOLDER, name))
]

def load_random_game_over_gif():
    valid = [
        os.path.join(GIF_FOLDER, name)
        for name in GAME_OVER_GIFS
        if os.path.exists(os.path.join(GIF_FOLDER, name))
    ]
    if valid:
        return load_gif(random.choice(valid), BAR_Y - 30)
    return [], []

def load_rank_gif(rank, max_height):
    path = os.path.join(GIF_FOLDER, RANK_GIFS.get(rank, ""))
    if os.path.exists(path):
        return load_gif(path, max_height)
    return [], []

# ---------------- BUTTON ----------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, color):
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=8)
        txt = FONT.render(self.text, True, WHITE)
        SCREEN.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

# ---------------- ARROW BOX ----------------
class ArrowBox:
    def __init__(self, arrow):
        self.arrow = arrow
        self.y = BAR_Y
        self.x = {
            "left": WIDTH * 0.25 - BOX_SIZE // 2,
            "right": WIDTH * 0.75 - BOX_SIZE // 2,
            "up": WIDTH // 2 - BOX_SIZE // 2,
            "down": WIDTH // 2 - BOX_SIZE // 2
        }[arrow]
        self.rect = pygame.Rect(self.x, self.y, BOX_SIZE, BOX_SIZE)

    def update(self, speed):
        self.y += speed
        self.rect.y = self.y

    def draw(self, color):
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=6)
        cx, cy = self.rect.center
        s = 10
        shapes = {
            "up": [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)],
            "down": [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)],
            "left": [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)],
            "right": [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
        }
        pygame.draw.polygon(SCREEN, WHITE, shapes[self.arrow])

# ---------------- GAME STATE ----------------
def reset_game():
    return {
        "boxes": [],
        "queue": [],
        "spawn_timer": 0,
        "speed": 2.5,
        "start_time": pygame.time.get_ticks(),
        "game_over": False,
        "early_fail": False,
        "rank": None,
        "time_text": "",
        "gif_frames": [],
        "gif_durations": [],
        "gif_index": 0,
        "gif_timer": 0
    }

game_started = False
game = reset_game()

start_button = Button((WIDTH // 2 - 75, BAR_Y + 100, 150, 50), "Start")
play_again_button = Button((WIDTH // 2 - 100, HEIGHT - 70, 200, 50), "Play Again")

# ---------------- GAME OVER TRIGGER ----------------
def trigger_game_over():
    game["game_over"] = True
    elapsed = (pygame.time.get_ticks() - game["start_time"]) / 1000

    # Boundary testing thresholds
    if elapsed >= 180:
        rank = "S"
    elif elapsed >= 120:
        rank = "A"
    elif elapsed >= 60:
        rank = "B"
    elif elapsed >= 30:
        rank = "C"
    else:
        rank = None

    if rank:
        game["rank"] = rank
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        game["time_text"] = f"{minutes}:{seconds:02d}"
        game["gif_frames"], game["gif_durations"] = load_rank_gif(rank, BAR_Y - 30)
        game["gif_index"] = game["gif_timer"] = 0
    else:
        game["early_fail"] = True
        game["gif_frames"], game["gif_durations"] = load_random_game_over_gif()
        game["gif_index"] = game["gif_timer"] = 0

# ---------------- MAIN LOOP ----------------
while True:
    dt = CLOCK.tick(FPS)
    t = pygame.time.get_ticks() / 500

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if not game_started and start_button.clicked(event):
            game_started = True
            game = reset_game()
            game["gif_frames"], game["gif_durations"] = load_gif(random.choice(NORMAL_GIF_FILES), BAR_Y - 30)
            game["gif_index"] = game["gif_timer"] = 0

        elif game["game_over"] and play_again_button.clicked(event):
            game = reset_game()
            game["gif_frames"], game["gif_durations"] = load_gif(random.choice(NORMAL_GIF_FILES), BAR_Y - 30)
            game["gif_index"] = game["gif_timer"] = 0

        elif not game["game_over"] and event.type == pygame.KEYDOWN and game["queue"]:
            key_map = {
                pygame.K_LEFT: "left",
                pygame.K_RIGHT: "right",
                pygame.K_UP: "up",
                pygame.K_DOWN: "down"
            }
            if event.key in key_map:
                if key_map[event.key] == game["queue"][0]:
                    game["queue"].pop(0)
                    game["boxes"].pop(0)
                else:
                    trigger_game_over()

    # ---------------- DRAW ----------------
    SCREEN.fill(BLACK)
    pygame.draw.rect(SCREEN, rainbow(t), (0, BAR_Y - 4, WIDTH, 8))

    if not game_started:
        SCREEN.blit(BIG_FONT.render("Evo Run!", True, rainbow(t)), (WIDTH // 2 - 100, BAR_Y // 2 - 40))
        SCREEN.blit(FONT.render("Endless Arrow Lapse", True, rainbow(t)), (WIDTH // 2 - 130, BAR_Y // 2 + 20))
        start_button.draw(rainbow(t))

    elif not game["game_over"]:
        # Draw GIF
        if game["gif_frames"]:
            game["gif_timer"] += dt
            if game["gif_timer"] >= game["gif_durations"][game["gif_index"]]:
                game["gif_timer"] = 0
                game["gif_index"] = (game["gif_index"] + 1) % len(game["gif_frames"])
            SCREEN.blit(game["gif_frames"][game["gif_index"]],
                        game["gif_frames"][game["gif_index"]].get_rect(center=(WIDTH // 2, BAR_Y // 2)))

        # Timer at top-right
        elapsed_ms = pygame.time.get_ticks() - game["start_time"]
        elapsed = elapsed_ms / 1000
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed_ms % 1000) / 10)
        timer_surface = FONT.render(f"{minutes}:{seconds:02d}:{milliseconds:02d}", True, rainbow(t))
        SCREEN.blit(timer_surface, timer_surface.get_rect(topright=(WIDTH - 20, 20)))

        # Spawn arrows
        game["spawn_timer"] += 1
        if game["spawn_timer"] >= 35:
            arrow = random.choice(["left", "right", "up", "down"])
            game["boxes"].append(ArrowBox(arrow))
            game["queue"].append(arrow)
            game["spawn_timer"] = 0
            game["speed"] += 0.05

        for box in game["boxes"]:
            box.update(game["speed"])
            box.draw(rainbow(t))
            if box.y > HEIGHT:
                trigger_game_over()

    else:
        pygame.draw.rect(SCREEN, RED, (0, BAR_Y, WIDTH, BAR_Y))
        SCREEN.blit(BIG_FONT.render("GAME OVER", True, BLACK), (WIDTH // 2 - 140, BAR_Y + BAR_Y // 2 - 40))

        # Draw GIF
        if game["gif_frames"]:
            game["gif_timer"] += dt
            if game["gif_timer"] >= game["gif_durations"][game["gif_index"]]:
                game["gif_timer"] = 0
                game["gif_index"] = (game["gif_index"] + 1) % len(game["gif_frames"])
            SCREEN.blit(game["gif_frames"][game["gif_index"]],
                        game["gif_frames"][game["gif_index"]].get_rect(center=(WIDTH // 2, BAR_Y // 2)))

        # Draw pass/fail text
        if game["early_fail"]:
            fail_text = BIG_FONT.render("You failed", True, RED)
            SCREEN.blit(fail_text, fail_text.get_rect(center=(WIDTH // 2, BAR_Y // 2 - 100)))
        elif game["rank"]:
            pass_text = FONT.render(f"You passed with rank {game['rank']} at {game['time_text']}!", True, YELLOW)
            SCREEN.blit(pass_text, pass_text.get_rect(center=(WIDTH // 2, BAR_Y // 2 - 100)))

        play_again_button.draw(rainbow(t))

    pygame.display.flip()
