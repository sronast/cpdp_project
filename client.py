import random
import pygame
import socket
import threading

# Set up pygame
pygame.init()

# Set up the screen
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racing Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)
ROAD_COLOR = (100, 100, 100)  # Road color
RED = (255, 0, 0)

LANE_WIDTH = 100
ROAD_WIDTH = 400  # Adjust this value as needed
LANE_COUNT = 4
EDGE_WIDTH = 5  # Width of the black edges on the sides of the road


# Car settings
CAR_WIDTH, CAR_HEIGHT = 100, 160
car_img = pygame.image.load("./asset/car_black_small_5.png")
car_img = pygame.transform.scale(car_img, (CAR_WIDTH, CAR_HEIGHT))
car_x = SCREEN_WIDTH // 2 - CAR_WIDTH // 2
car_y = SCREEN_HEIGHT - CAR_HEIGHT

car_img_1 = pygame.image.load("./asset/car_red_small_5.png")
car_img_1 = pygame.transform.scale(car_img, (CAR_WIDTH, CAR_HEIGHT))

car_ent = pygame.image.load("./asset/car_blue_small_5.png")
car_ent = pygame.transform.scale(car_ent, (CAR_WIDTH, CAR_HEIGHT))

rock_img = pygame.image.load("./asset/rock3.png")
rock_img = pygame.transform.scale(rock_img, (CAR_WIDTH, CAR_HEIGHT))


left_pressed = False
right_pressed = False
up_pressed = False
down_pressed = False


# Connect to server
HOST = "127.0.0.1"
PORT = 8848
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
player_num = client_socket.recv(1024).decode()
print(player_num)
last_obstacle_spawn_time = pygame.time.get_ticks()


def receive_data():
    while True:
        try:
            data = client_socket.recv(1024)
            if data:
                # Update game state based on received data
                pass
        except Exception as e:
            print("Error receiving data:", e)
            break


# Start receiving data in a separate thread
threading.Thread(target=receive_data, daemon=True).start()

def generate_obstacle_positions(screen_width, screen_height, obstacle_count, obstacle_width):
    obstacle_positions = []
    for _ in range(obstacle_count):
        x = random.randint(0, screen_width - obstacle_width)
        y = random.randint(-screen_height, 0)  # Ensure obstacles start off-screen
        obstacle_positions.append((x, y))
    return obstacle_positions

car_x = (SCREEN_WIDTH - CAR_WIDTH) // 2
car_y = SCREEN_HEIGHT - CAR_HEIGHT
game_over = False
# Game loop
entities = []
speed = 4
clock = pygame.time.Clock()
running = True
obstacle_count = 0
obstacles = []
start_time = pygame.time.get_ticks()
MAX_OBSTACLES = 3
last_spawn_time = start_time



def spawn_obstacle():
    obstacle_x = random.randint(
        (SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH,
        (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH - CAR_WIDTH,
    )
    obstacle_y = 0
    obstacles.append({"x": obstacle_x, "y": obstacle_y})
    
def handle_road_and_lines():
    # Draw road
    pygame.draw.rect(
        screen,
        ROAD_COLOR,
        ((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, ROAD_WIDTH, SCREEN_HEIGHT),
    )
    # Draw black edges on the sides of the road
    pygame.draw.rect(
        screen,
        BLACK,
        ((SCREEN_WIDTH - ROAD_WIDTH) // 2 - EDGE_WIDTH, 0, EDGE_WIDTH, SCREEN_HEIGHT),
    )
    pygame.draw.rect(
        screen,
        BLACK,
        (SCREEN_WIDTH // 2 + ROAD_WIDTH // 2, 0, EDGE_WIDTH, SCREEN_HEIGHT),
    )

    # Draw white edge lines
    pygame.draw.rect(
        screen, WHITE, ((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, EDGE_WIDTH, SCREEN_HEIGHT)
    )
    pygame.draw.rect(
        screen,
        WHITE,
        (
            SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 - EDGE_WIDTH,
            0,
            EDGE_WIDTH,
            SCREEN_HEIGHT,
        ),
    )

def draw_bg():
    # Clear the screen
    screen.fill(WHITE)

    # Draw green sides of the road
    pygame.draw.rect(
        screen, GREEN, (0, 0, (SCREEN_WIDTH - ROAD_WIDTH) // 2, SCREEN_HEIGHT)
    )
    pygame.draw.rect(
        screen,
        GREEN,
        (
            SCREEN_WIDTH // 2 + ROAD_WIDTH // 2,
            0,
            (SCREEN_WIDTH - ROAD_WIDTH) // 2,
            SCREEN_HEIGHT,
        ),
    )

def handle_keypress():
    global left_pressed, right_pressed, up_pressed, down_pressed
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            left_pressed = True
        elif event.key == pygame.K_RIGHT:
            right_pressed = True
        elif event.key == pygame.K_UP:
            up_pressed = True
        elif event.key == pygame.K_DOWN:
            down_pressed = True

    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_LEFT:
            left_pressed = False
        elif event.key == pygame.K_RIGHT:
            right_pressed = False
        elif event.key == pygame.K_UP:
            up_pressed = False
        elif event.key == pygame.K_DOWN:
            down_pressed = False
            
def handle_entities():
    global game_over, obstacle_count, last_spawn_time, last_obstacle_spawn_time
    for entity in entities:
        if entity["type"] == "car":
            screen.blit(car_ent, (entity["x"], entity["y"]))  # Use car_ent image
        elif entity["type"] == "obstacle":
            screen.blit(rock_img, (entity["x"], entity["y"]))
            entity["y"] += speed  # Adjust speed as needed

            # Check for collisions with player's car
            if pygame.Rect(entity["x"], entity["y"], CAR_WIDTH, CAR_HEIGHT).colliderect(pygame.Rect(car_x, car_y, CAR_WIDTH, CAR_HEIGHT)):
                game_over = True
                break

            # Remove entities that have moved off-screen
            if entity["y"] > SCREEN_HEIGHT:
                entities.remove(entity)
                obstacle_count -= 1

    if not game_over:
        # Spawning obstacles
        if len(entities) < MAX_OBSTACLES:
            if pygame.time.get_ticks() - last_obstacle_spawn_time > random.randint(2000, 3000):
                obstacle_x = random.randint((SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH, (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH - CAR_WIDTH)
                obstacle_y = 0
                entities.append({"x": obstacle_x, "y": obstacle_y, "type": "obstacle"})
                obstacle_count += 1
                last_obstacle_spawn_time = pygame.time.get_ticks()

def update_car_movement():
    global car_x, car_y
    if left_pressed and car_x > (SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH:
        car_x -= 5
    if right_pressed and car_x < (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH - CAR_WIDTH:
        car_x += 5
    if up_pressed and car_y > 0:
        car_y -= 5
    if down_pressed and car_y < SCREEN_HEIGHT - CAR_HEIGHT:
        car_y += 5

def handle_dashed_lines():
    dash_length = 50
    gap_length = 30
    dash_count = 100
    line_x = SCREEN_WIDTH // 2
    start_y = EDGE_WIDTH  # Start from the top

    current_time = pygame.time.get_ticks()
    time_offset = (current_time // speed) % (dash_length + gap_length)  # Adjust speed as needed
    
    for i in range(dash_count):
        y1 = start_y + i * (dash_length + gap_length) + time_offset
        y2 = y1 + dash_length
        pygame.draw.line(screen, WHITE, (line_x, y1), (line_x, y2), 5)

def handle_game_over():
    font = pygame.font.SysFont(None, 48)
    game_over_text = font.render("Game Over", True, RED)
    game_over_rect = game_over_text.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    )
    pygame.draw.rect(screen, WHITE, game_over_rect.inflate(20, 20))
    screen.blit(game_over_text, game_over_rect)

# Main game loop
clock = pygame.time.Clock()
running = True
entities = []
speed = 4
game_over = False
obstacle_count = 0
last_spawn_time = pygame.time.get_ticks()
MAX_OBSTACLES = 3

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        handle_keypress()
        update_car_movement()
        handle_entities()

    draw_bg()
    handle_road_and_lines()
    handle_dashed_lines()
    screen.blit(car_img, (car_x, car_y))

    if game_over:
        handle_game_over()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client_socket.close()