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


class Car(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += speed


# Game loop variables
entities = pygame.sprite.Group()  # Group to hold all sprites
car_sprite = Car(car_ent, SCREEN_WIDTH // 2, SCREEN_HEIGHT - CAR_HEIGHT)
entities.add(car_sprite)
speed = 4
clock = pygame.time.Clock()
running = True
obstacle_count = 0
start_time = pygame.time.get_ticks()
MAX_OBSTACLES = 3
last_spawn_time = start_time


def spawn_obstacle():
    global speed, MAX_OBSTACLES, last_spawn_time

    # Increase obstacle speed gradually
    if speed < 8:  # Maximum speed limit
        speed += 0.1

    # Increase obstacle frequency gradually
    MAX_OBSTACLES += 0.01

    # Randomly spawn obstacles
    obstacle_x = random.randint(
        (SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH,
        (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH - CAR_WIDTH,
    )
    obstacle_y = 0
    obstacle = Obstacle(rock_img, obstacle_x, obstacle_y)
    entities.add(obstacle)

    # Update last obstacle spawn time
    last_spawn_time = pygame.time.get_ticks()


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
    global left_pressed, right_pressed, up_pressed, down_pressed, game_over
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                left_pressed = True
            elif event.key == pygame.K_RIGHT:
                right_pressed = True
            elif event.key == pygame.K_UP:
                up_pressed = True
            elif event.key == pygame.K_DOWN:
                down_pressed = True
            # elif event.key == pygame.K_SPACE and game_over:
            #     restart_game()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                left_pressed = False
            elif event.key == pygame.K_RIGHT:
                right_pressed = False
            elif event.key == pygame.K_UP:
                up_pressed = False
            elif event.key == pygame.K_DOWN:
                down_pressed = False


def handle_entities(screen_to_draw):
    global game_over, last_spawn_time
    for entity in entities.sprites():
        if isinstance(entity, Car):
            screen_to_draw.blit(entity.image, entity.rect)
        elif isinstance(entity, Obstacle):
            screen_to_draw.blit(entity.image, entity.rect)
            entity.update()  # Adjust speed as needed

            # Check for collisions with player's car
            if pygame.sprite.collide_mask(entity, car_sprite):
                game_over = True

            # Remove entities that have moved off-screen
            if entity.rect.y > SCREEN_HEIGHT:
                entity.kill()

    if not game_over:
        # Spawning obstacles
        if len(entities.sprites()) < MAX_OBSTACLES:
            current_time = pygame.time.get_ticks()
            if current_time - last_spawn_time > random.randint(2000, 3000):
                spawn_obstacle()
                last_spawn_time = current_time


def update_car_movement():
    global car_x, car_y
    if (
        left_pressed
        and car_sprite.rect.left > (SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH
    ):
        car_sprite.rect.x -= 5
    if (
        right_pressed
        and car_sprite.rect.right < (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH
    ):
        car_sprite.rect.x += 5
    if up_pressed and car_sprite.rect.top > 0:
        car_sprite.rect.y -= 5
    if down_pressed and car_sprite.rect.bottom < SCREEN_HEIGHT:
        car_sprite.rect.y += 5


def handle_dashed_lines():
    dash_length = 50
    gap_length = 30
    dash_count = 100
    line_x = SCREEN_WIDTH // 2
    start_y = EDGE_WIDTH  # Start from the top

    current_time = pygame.time.get_ticks()
    time_offset = (current_time // speed) % (
        dash_length + gap_length
    )  # Adjust speed as needed

    for i in range(dash_count):
        y1 = start_y + i * (dash_length + gap_length) + time_offset
        y2 = y1 + dash_length
        pygame.draw.line(screen, WHITE, (line_x, y1), (line_x, y2), 5)


def handle_game_over():
    font = pygame.font.SysFont(None, 48)
    game_over_text = font.render("Game Over", True, RED)
    restart_text = font.render("Press Space to restart the game", True, BLACK)

    game_over_rect = game_over_text.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
    )
    restart_rect = restart_text.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)
    )

    pygame.draw.rect(screen, WHITE, game_over_rect.inflate(20, 20))
    screen.blit(game_over_text, game_over_rect)
    # screen.blit(restart_text, restart_rect)


def restart_game():
    global game_over
    game_over = False
    entities.empty()  # Clear all sprites
    car_sprite = Car(
        car_ent, SCREEN_WIDTH // 2, SCREEN_HEIGHT - CAR_HEIGHT
    )  # Create a new car sprite
    entities.add(car_sprite)  # Add the car sprite back to the entities group


# Main game loop
clock = pygame.time.Clock()
running = True
game_over = False

while running:
    handle_keypress()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # elif event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_SPACE and game_over:
        #         restart_game()

    if not game_over:
        update_car_movement()
        draw_bg()
        handle_road_and_lines()
        handle_dashed_lines()
        handle_entities(screen)
        entities.update()

    if game_over:
        handle_game_over()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client_socket.close()
