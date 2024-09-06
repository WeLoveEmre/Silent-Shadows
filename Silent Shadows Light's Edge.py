import pygame
import sys
import random
import math
from collections import defaultdict

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Silent Shadows: Light's Edge")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

# Player
player1_pos = [WIDTH // 4, HEIGHT // 2]
player1_size = 20
player1_speed = 5
player1_health = 100
player1_max_health = 100

player2_pos = [WIDTH * 3 // 4, HEIGHT // 2]
player2_size = 20
player2_speed = 5
player2_health = 100
player2_max_health = 100

def draw_player1(pos):
    pygame.draw.rect(screen, BLUE, (*pos, player1_size, player1_size))

def draw_player2(pos):
    pygame.draw.rect(screen, GREEN, (*pos, player2_size, player2_size))

# Leaderboard
leaderboard = []

def update_leaderboard(score):
    leaderboard.append(score)
    leaderboard.sort(reverse=True)
    if len(leaderboard) > 10:
        leaderboard.pop()

def draw_leaderboard():
    leaderboard_text = font.render("Leaderboard", True, WHITE)
    screen.blit(leaderboard_text, (WIDTH - 200, 20))

    for i, score in enumerate(leaderboard):
        score_text = font.render(f"{i+1}. {score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 150, 50 + i * 30))

# Enemies
class Enemy:
    def __init__(self, x, y, enemy_type):
        self.pos = [x, y]
        self.type = enemy_type
        self.size = 20
        self.speed = 2 if enemy_type == "normal" else 1
        self.frozen = False
        self.freeze_time = 0
        self.animation_frame = 0
        self.animation_speed = 0.2

    def animate(self):
        self.animation_frame += self.animation_speed
        if self.animation_frame >= 4:
            self.animation_frame = 0

enemies = []

# Items
class Item:
    def __init__(self, x, y, item_type):
        self.pos = [x, y]
        self.type = item_type
        self.size = 15
        self.animation_frame = 0
        self.animation_speed = 0.1

    def animate(self):
        self.animation_frame += self.animation_speed
        if self.animation_frame >= 2:
            self.animation_frame = 0

items = []

# Flashlight
flashlight_on = False
flashlight_battery = 100
FLASHLIGHT_DRAIN_RATE = 0.05  # Reduced drain rate
BATTERY_RECHARGE_AMOUNT = 25
FLASHLIGHT_RANGE = 200
FLASHLIGHT_ANGLE = math.pi / 4  # 45 degrees
MAX_POWER_UP_DURATION = 15

# Game states
game_over = False
score = 0

# Fonts
font = pygame.font.Font(None, 36)

# Settings
difficulty = 1
spawn_rate = 0.02

# New feature: Power-ups
class PowerUp:
    def __init__(self, x, y, power_up_type):
        self.pos = [x, y]
        self.type = power_up_type
        self.size = 15
        self.duration = 10000  # 10 seconds

power_ups = []
active_power_ups = defaultdict(float)

def draw_enemy(enemy):
    if enemy.type == "normal":
        color = RED
    elif enemy.type == "light_sensitive":
        color = YELLOW
    elif enemy.type == "ghost":
        color = GRAY
    pygame.draw.rect(screen, color, (*enemy.pos, enemy.size, enemy.size))

def draw_item(item):
    color = GREEN if item.type == "battery" else WHITE
    pygame.draw.rect(screen, color, (*item.pos, item.size, item.size))

def draw_power_up(power_up):
    color = YELLOW
    pygame.draw.rect(screen, color, (*power_up.pos, power_up.size, power_up.size))

def move_enemy(enemy):
    global player1_pos, player2_pos

    if enemy.frozen:
        if pygame.time.get_ticks() - enemy.freeze_time > 3000:  # Unfreeze after 3 seconds
            enemy.frozen = False
        return

    # Calculate distances to both players
    dx1 = player1_pos[0] - enemy.pos[0]
    dy1 = player1_pos[1] - enemy.pos[1]
    dist1 = math.hypot(dx1, dy1)

    dx2 = player2_pos[0] - enemy.pos[0]
    dy2 = player2_pos[1] - enemy.pos[1]
    dist2 = math.hypot(dx2, dy2)

    # Move towards the closest player
    if dist1 < dist2:
        dx, dy, dist = dx1, dy1, dist1
    else:
        dx, dy, dist = dx2, dy2, dist2

    # Normalize the direction vector
    if dist > 0:
        dx, dy = dx / dist, dy / dist
    else:
        # If the enemy is exactly on the player, move randomly
        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
    
    # Apply enemy speed
    move_x = dx * enemy.speed
    move_y = dy * enemy.speed
    
    if enemy.type == "ghost":
        # Add some randomness to ghost movement
        move_x += random.uniform(-0.5, 0.5) * enemy.speed
        move_y += random.uniform(-0.5, 0.5) * enemy.speed
        
        # Move the ghost
        enemy.pos[0] += move_x
        enemy.pos[1] += move_y
        
        # Wrap around screen edges for ghosts
        enemy.pos[0] = enemy.pos[0] % WIDTH
        enemy.pos[1] = enemy.pos[1] % HEIGHT
    else:
        # For other enemy types, check for wall collisions
        new_x = enemy.pos[0] + move_x
        new_y = enemy.pos[1] + move_y
        
        # Check x-axis movement
        if 0 <= new_x <= WIDTH - enemy.size:
            enemy.pos[0] = new_x
        
        # Check y-axis movement
        if 0 <= new_y <= HEIGHT - enemy.size:
            enemy.pos[1] = new_y

    # Ensure non-ghost enemies stay within the screen boundaries
    if enemy.type != "ghost":
        enemy.pos[0] = max(0, min(WIDTH - enemy.size, enemy.pos[0]))
        enemy.pos[1] = max(0, min(HEIGHT - enemy.size, enemy.pos[1]))

def check_collision(pos1, size1, pos2, size2):
    return (abs(pos1[0] - pos2[0]) < (size1 + size2) // 2 and
            abs(pos1[1] - pos2[1]) < (size1 + size2) // 2)

def spawn_enemy():
    global spawn_rate
    if random.random() < spawn_rate * difficulty:
        x = random.choice([0, WIDTH])
        y = random.randint(0, HEIGHT)
        enemy_type = random.choice(["normal", "light_sensitive", "ghost"])
        enemies.append(Enemy(x, y, enemy_type))
    
    spawn_rate = max(0.005, spawn_rate - 0.00001)

def spawn_item():
    if random.random() < 0.01:  # 1% chance to spawn an item each frame
        x = random.randint(0, WIDTH - 15)
        y = random.randint(0, HEIGHT - 15)
        item_type = random.choice(["battery", "health"])
        items.append(Item(x, y, item_type))

def spawn_power_up():
    if random.random() < 0.005:  # 0.5% chance to spawn a power-up each frame
        x = random.randint(0, WIDTH - 15)
        y = random.randint(0, HEIGHT - 15)
        power_up_type = random.choice(["speed_boost", "invincibility"])
        power_ups.append(PowerUp(x, y, power_up_type))

def draw_flashlight():
    if flashlight_on:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx, dy = mouse_x - player1_pos[0], mouse_y - player1_pos[1]
        angle = math.atan2(dy, dx)
        
        points = [
            (player1_pos[0] + player1_size/2, player1_pos[1] + player1_size/2),
            (player1_pos[0] + player1_size/2 + math.cos(angle - FLASHLIGHT_ANGLE/2) * FLASHLIGHT_RANGE,
             player1_pos[1] + player1_size/2 + math.sin(angle - FLASHLIGHT_ANGLE/2) * FLASHLIGHT_RANGE),
            (player1_pos[0] + player1_size/2 + math.cos(angle + FLASHLIGHT_ANGLE/2) * FLASHLIGHT_RANGE,
             player1_pos[1] + player1_size/2 + math.sin(angle + FLASHLIGHT_ANGLE/2) * FLASHLIGHT_RANGE),
        ]
        
        light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(light_surface, (255, 255, 200, 100), points)
        screen.blit(light_surface, (0, 0))
        
        return angle, points
    return None, None

def is_in_flashlight(enemy_pos, flashlight_angle, flashlight_points):
    if not flashlight_on:
        return False
    
    dx = enemy_pos[0] - player1_pos[0]
    dy = enemy_pos[1] - player1_pos[1]
    distance = math.hypot(dx, dy)
    if distance > FLASHLIGHT_RANGE:
        return False
    
    enemy_angle = math.atan2(dy, dx)
    angle_diff = (enemy_angle - flashlight_angle + math.pi) % (2*math.pi) - math.pi
    return abs(angle_diff) < FLASHLIGHT_ANGLE/2

def show_start_screen():
    screen.fill(BLACK)
    title = font.render("Silent Shadows: Light's Edge", True, DARK_RED)
    instructions = font.render("Choose Game Mode:", True, WHITE)
    singleplayer = font.render("1. Singleplayer", True, WHITE)
    multiplayer = font.render("2. Multiplayer", True, WHITE)
    settings = font.render("Press S for settings", True, WHITE)
    controls = font.render("Press C for controls", True, WHITE)
    exit_instructions = font.render("Press ESC to exit at any time", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
    screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT // 2))
    screen.blit(singleplayer, (WIDTH // 2 - singleplayer.get_width() // 2, HEIGHT // 2 + 35))
    screen.blit(multiplayer, (WIDTH // 2 - multiplayer.get_width() // 2, HEIGHT // 2 + 65))
    screen.blit(settings, (WIDTH // 2 - settings.get_width() // 2, HEIGHT // 2 + 150))
    screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT // 2 + 200))
    screen.blit(exit_instructions, (WIDTH // 2 - exit_instructions.get_width() // 2, HEIGHT * 2 // 3))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "singleplayer"
                elif event.key == pygame.K_2:
                    return "multiplayer"
                elif event.key == pygame.K_s:
                    show_settings_menu()
                elif event.key == pygame.K_c:
                    show_controls_menu()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def show_controls_menu():
    screen.fill(BLACK)
    title = font.render("Controls", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 6))

    controls_text = [
        "Move: WASD",
        "Move (Multiplayer): ARROW KEYS",
        "Toggle Flashlight: F",
        "Pause/Quit: ESC",
        "Back to Main Menu: B"
    ]

    for i, text in enumerate(controls_text):
        control_text = font.render(text, True, WHITE)
        screen.blit(control_text, (WIDTH // 2 - control_text.get_width() // 2, HEIGHT // 3 + i * 50))

    back_text = font.render("Press B to go back", True, WHITE)
    screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT * 5 // 6))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    waiting = False
                    show_start_screen()

def show_settings_menu():
    global difficulty, player1_speed, player2_speed, FLASHLIGHT_DRAIN_RATE
    
    menu = True
    selected_option = 0
    options = ["Difficulty", "Player 1 Speed", "Player 2 Speed", "Flashlight Drain Rate", "Back", "Apply"]
    
    while menu:
        screen.fill(BLACK)
        title = font.render("Settings", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 6))
        
        for i, option in enumerate(options):
            color = YELLOW if i == selected_option else WHITE
            if option == "Difficulty":
                text = font.render(f"{option}: {difficulty}", True,color)
            elif option == "Player 1 Speed":
                text = font.render(f"{option}: {player1_speed}", True, color)
            elif option == "Player 2 Speed":
                text = font.render(f"{option}: {player2_speed}", True, color)
            elif option == "Flashlight Drain Rate":
                text = font.render(f"{option}: {FLASHLIGHT_DRAIN_RATE:.2f}", True, color)
            else:
                text = font.render(f"{option}", True, color)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3 + i * 50))
        
        instructions = font.render("Use UP/DOWN to select, LEFT/RIGHT to adjust", True, WHITE)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT * 5 // 6))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    menu = False
                    show_start_screen()
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_LEFT:
                    if selected_option == 0:
                        difficulty = max(1, difficulty - 1)
                    elif selected_option == 1:
                        player1_speed = max(1, player1_speed - 1)
                    elif selected_option == 2:
                        player2_speed = max(1, player2_speed - 1)
                    elif selected_option == 3:
                        FLASHLIGHT_DRAIN_RATE = max(0.01, FLASHLIGHT_DRAIN_RATE - 0.01)
                elif event.key == pygame.K_RIGHT:
                    if selected_option == 0:
                        difficulty = min(10, difficulty + 1)
                    elif selected_option == 1:
                        player1_speed = min(10, player1_speed + 1)
                    elif selected_option == 2:
                        player2_speed = min(10, player2_speed + 1)
                    elif selected_option == 3:
                        FLASHLIGHT_DRAIN_RATE = min(0.1, FLASHLIGHT_DRAIN_RATE + 0.01)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 4:  # Back button
                        menu = False
                        show_start_screen()
                    elif selected_option == 5:  # Apply button
                        # Apply the changes to the game
                        menu = False
                        show_start_screen()

        pygame.display.flip()
        pygame.time.Clock().tick(30)

def draw_hud(game_mode):
    health_text1 = font.render(f"Player 1 Health: {player1_health}", True, WHITE)
    screen.blit(health_text1, (10, 10))
    
    if game_mode == "multiplayer":
        health_text2 = font.render(f"Player 2 Health: {player2_health}", True, WHITE)
        screen.blit(health_text2, (10, 50))
    
    battery_text = font.render(f"Battery: {int(flashlight_battery)}%", True, WHITE)
    screen.blit(battery_text, (10, 90))
    
    if game_mode == "singleplayer":
        score_text = font.render(f"Score: {score}", True, WHITE)
    else:
        score_text = font.render(f"P1 Score: {score[0]} | P2 Score: {score[1]}", True, WHITE)
    screen.blit(score_text, (WIDTH - 370, 10))
    
    # Display active power-ups
    y_offset = 130
    for power_up_type, duration in active_power_ups.items():
        power_up_text = font.render(f"{power_up_type.capitalize()}: {int(duration)}s", True, YELLOW)
        screen.blit(power_up_text, (10, y_offset))
        y_offset += 40

def init_game(game_mode):
    global player1_pos, player2_pos, player1_health, player2_health, flashlight_battery, score, enemies, items, power_ups, active_power_ups, spawn_rate

    player1_pos = [WIDTH // 4, HEIGHT // 2]
    player1_health = player1_max_health
    flashlight_battery = 100
    enemies = []
    items = []
    power_ups = []
    active_power_ups = defaultdict(float)
    spawn_rate = 0.02

    if game_mode == "singleplayer":
        score = 0
    else:  # multiplayer
        player2_pos = [WIDTH * 3 // 4, HEIGHT // 2]
        player2_health = player2_max_health
        score = [0, 0]  # [player1_score, player2_score]

# Main game loop
while True:
    game_mode = show_start_screen()
    init_game(game_mode)
    game_over = False
    last_time = pygame.time.get_ticks()
    
    while not game_over:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time

        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over = True
                elif event.key == pygame.K_f:
                    flashlight_on = not flashlight_on
                elif event.key == pygame.K_SPACE:
                    spawn_enemy()

        keys = pygame.key.get_pressed()
        move_speed1 = player1_speed
        move_speed2 = player2_speed if game_mode == "multiplayer" else 0
        if active_power_ups["speed_boost"] > 0:
            move_speed1 *= 1.5
            move_speed2 *= 1.5

        # Player 1 movement
        if keys[pygame.K_a]: player1_pos[0] -= move_speed1
        if keys[pygame.K_d]: player1_pos[0] += move_speed1
        if keys[pygame.K_w]: player1_pos[1] -= move_speed1
        if keys[pygame.K_s]: player1_pos[1] += move_speed1

        # Player 2 movement (only in multiplayer)
        if game_mode == "multiplayer":
            if keys[pygame.K_LEFT]: player2_pos[0] -= move_speed2
            if keys[pygame.K_RIGHT]: player2_pos[0] += move_speed2
            if keys[pygame.K_UP]: player2_pos[1] -= move_speed2
            if keys[pygame.K_DOWN]: player2_pos[1] += move_speed2

        player1_pos[0] = max(0, min(WIDTH - player1_size, player1_pos[0]))
        player1_pos[1] = max(0, min(HEIGHT - player1_size, player1_pos[1]))
        if game_mode == "multiplayer":
            player2_pos[0] = max(0, min(WIDTH - player2_size, player2_pos[0]))
            player2_pos[1] = max(0, min(HEIGHT - player2_size, player2_pos[1]))

        if flashlight_on:
            flashlight_battery -= FLASHLIGHT_DRAIN_RATE
            if flashlight_battery <= 0:
                flashlight_on = False
                flashlight_battery = 0
        
        spawn_enemy()
        spawn_item()
        spawn_power_up()

        flashlight_angle, flashlight_points = None, None
        if flashlight_on:
            flashlight_angle, flashlight_points = draw_flashlight()

        for enemy in enemies[:]:
            move_enemy(enemy)
            enemy.animate()
            draw_enemy(enemy)
            
            if check_collision(player1_pos, player1_size, enemy.pos, enemy.size):
                if active_power_ups["invincibility"] > 0:
                    if enemy in enemies:
                        enemies.remove(enemy)
                    if game_mode == "singleplayer":
                        score += 10
                    else:
                        score[0] += 10
                else:
                    player1_health -= 10
                    if player1_health <= 0:
                        game_over = True
                    if enemy in enemies:
                        enemies.remove(enemy)
            
            if game_mode == "multiplayer" and check_collision(player2_pos, player2_size, enemy.pos, enemy.size):
                if active_power_ups["invincibility"] > 0:
                    if enemy in enemies:
                        enemies.remove(enemy)
                    score[1] += 10
                else:
                    player2_health -= 10
                    if player2_health <= 0:
                        game_over = True
                    if enemy in enemies:
                        enemies.remove(enemy)
            
            if flashlight_on and is_in_flashlight(enemy.pos, flashlight_angle, flashlight_points):
                if enemy.type == "light_sensitive":
                    if enemy in enemies:
                        enemies.remove(enemy)
                    if game_mode == "singleplayer":
                        score += 5
                    else:
                        score[0] += 5  # Assume player 1 controls the flashlight
                elif enemy.type == "normal":
                    enemy.frozen = True
                    enemy.freeze_time = pygame.time.get_ticks()

        for item in items[:]:
            item.animate()
            draw_item(item)
            if check_collision(player1_pos, player1_size, item.pos, item.size):
                if item.type == "battery":
                    flashlight_battery = min(100, flashlight_battery + BATTERY_RECHARGE_AMOUNT)
                elif item.type == "health":
                    player1_health = min(player1_max_health, player1_health + 20)
                items.remove(item)
                if game_mode == "singleplayer":
                    score += 1
                else:
                    score[0] += 1
            elif game_mode == "multiplayer" and check_collision(player2_pos, player2_size, item.pos, item.size):
                if item.type == "battery":
                    flashlight_battery = min(100, flashlight_battery + BATTERY_RECHARGE_AMOUNT)
                elif item.type == "health":
                    player2_health = min(player2_max_health, player2_health + 20)
                items.remove(item)
                score[1] += 1

        for power_up in power_ups[:]:
            draw_power_up(power_up)
            if check_collision(player1_pos, player1_size, power_up.pos, power_up.size) or \
               (game_mode == "multiplayer" and check_collision(player2_pos, player2_size, power_up.pos, power_up.size)):
                new_duration = min(MAX_POWER_UP_DURATION, active_power_ups[power_up.type] + power_up.duration / 1000)
                active_power_ups[power_up.type] = new_duration
                power_ups.remove(power_up)

        for power_up_type in list(active_power_ups.keys()):
            if active_power_ups[power_up_type] > 0:
                active_power_ups[power_up_type] -= dt
                if active_power_ups[power_up_type] <= 0:
                    del active_power_ups[power_up_type]

        draw_player1(player1_pos)
        if game_mode == "multiplayer":
            draw_player2(player2_pos)
        draw_hud(game_mode)
        draw_leaderboard()

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    # Game over screen
    screen.fill(BLACK)
    game_over_text = font.render("Game Over", True, RED)
    if game_mode == "singleplayer":
        final_score_text = font.render(f"Final Score: {score}", True, WHITE)
    else:
        final_score_text = font.render(f"Final Scores: Player 1: {score[0]}, Player 2: {score[1]}", True, WHITE)
    restart_text = font.render("Press R to restart or ESC to quit", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
    screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT * 2 // 3))
    pygame.display.flip()

    if game_mode == "singleplayer":
        update_leaderboard(score)
    else:
        update_leaderboard(max(score))  # Update with the higher score
    draw_leaderboard()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

# Run the game
if __name__ == "__main__":
    pygame.init()
    while True:
        main()