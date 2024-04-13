import random
import pygame
import socket
import threading
import json

# Pygame setup
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Multiplayer Racing Game")

# Colors and Fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)
ROAD_COLOR = (100, 100, 100)
RED = (255, 0, 0)
FONT = pygame.font.SysFont(None, 36)

# Game constants and variables
LANE_WIDTH = 100
ROAD_WIDTH = 400
EDGE_WIDTH = 5
MAX_OBSTACLES = 3
MID_ROAD = SCREEN_WIDTH // 2
speed = 4
distance_traveled = 0
score = 0
RACE_DISTANCE = 100000
WAITING_FOR_PLAYERS = 0
COUNTDOWN = 1
GAME_RUNNING = 2
game_won = False
game_state = WAITING_FOR_PLAYERS  # 0: Waiting, 1: Countdown, 2: Running
countdown_timer = 3
last_countdown_update = pygame.time.get_ticks()
last_obstacle_spawn_time = pygame.time.get_ticks()


# Network setup
HOST = "127.0.0.1"
PORT = 8849
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
player_num = client_socket.recv(1024).decode()
print(f"Connected as {player_num}")


def send_to_server(data):
    """Helper function to send data to the server in JSON format."""
    try:
        json_data = json.dumps(data)
        client_socket.sendall(json_data.encode("utf-8"))
    except Exception as e:
        print(f"Failed to send data to the server: {e}")


# Car class
class Car(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (100, 160))
            self.rect = self.image.get_rect(center=(x, y))
        except Exception as ex:
            print(f"Failed to load image {image_path}: {ex}")
        self.speed = 5
        self.player_number = 0

    def update_position(self, left, right, up, down):
        moved = False
        original_position = self.rect.copy()

        # Calculate new proposed positions
        new_x = self.rect.x
        new_y = self.rect.y

        if left:
            new_x -= self.speed
        if right:
            new_x += self.speed
        if up:
            new_y -= self.speed
        if down:
            new_y += self.speed

        # Check horizontal boundaries
        if (
            new_x >= (SCREEN_WIDTH - ROAD_WIDTH) // 2 + EDGE_WIDTH
            and new_x + self.rect.width <= (SCREEN_WIDTH + ROAD_WIDTH) // 2 - EDGE_WIDTH
        ):
            self.rect.x = new_x
            moved = True

        # Check vertical boundaries (if needed)
        if new_y >= 0 and new_y + self.rect.height <= SCREEN_HEIGHT:
            self.rect.y = new_y
            moved = True

        if self.rect.colliderect(opponent_car_sprite.rect):
            self.rect = original_position

        # If the car moved, send the updated position to the server
        if moved and self.rect != original_position:
            d = {
                "action": "update_position",
                "x": self.rect.x,
                "y": self.rect.y,
                "player": self.player_number,
            }
            send_to_server(d)


# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (100, 160))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed  # This might be updated dynamically based on game difficulty

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > SCREEN_HEIGHT:
            self.kill()


# Sprites setup
player_x = player_car_x = MID_ROAD - LANE_WIDTH // 2
car_sprite = Car("./asset/car_black_small_5.png", player_x, SCREEN_HEIGHT - 180)
car_sprite.player_number = player_num
opponent_car_x = MID_ROAD + LANE_WIDTH // 2
opponent_car_sprite = Car(
    "./asset/car_blue_small_5.png", opponent_car_x, SCREEN_HEIGHT - 180
)
obstacles = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()


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


def spawn_obstacle():
    global last_obstacle_spawn_time
    if pygame.time.get_ticks() - last_obstacle_spawn_time > 2000:
        obstacle_x = random.randint(
            SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + EDGE_WIDTH,
            SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 - EDGE_WIDTH,
        )
        obstacle = Obstacle("./asset/rock3.png", obstacle_x, -100)
        obstacles.add(obstacle)
        all_sprites.add(obstacle)
        last_obstacle_spawn_time = pygame.time.get_ticks()


def handle_setup(d):
    global car_sprite, opponent_car_sprite, all_sprites
    if d["action"] == "ready":
        data = d["setup"]
        # Initialize your car
        car_color = data["your_color"]
        car_start_pos = data["start_position"]
        car_sprite = Car(f"./asset/car_{car_color}_small_5.png", *car_start_pos)

        # Initialize opponent's car
        opponent_color = data["opponent_color"]
        opponent_start_pos = data["opponent_start_position"]
        opponent_car_sprite = Car(
            f"./asset/car_{opponent_color}_small_5.png", *opponent_start_pos
        )

        all_sprites.add(car_sprite, opponent_car_sprite)
        print("added to all sprites")


def receive_data():
    buffer = ""
    while True:
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break
            buffer += data  # Append new data to the buffer

            while (
                "\n" in buffer
            ):  # Check if there are any complete messages with \n delimiter
                message, buffer = buffer.split("\n", 1)  # Split on the first \n found
                if message:
                    json_data = json.loads(message)  # Parse the complete JSON message
                    handle_message(json_data)  # Function to handle the parsed message

        except Exception as e:
            print("Error receiving data:", e)
            break


def handle_message(json_data):
    global game_state, countdown_timer, opponent_car_sprite, all_sprites
    print("Data received:", json_data)
    if json_data["action"] == "ready":
        handle_setup(json_data)
        send_to_server({"action": "ready_ack"})
        game_state = COUNTDOWN
    elif json_data["action"] == "start":
        print("received start signal from server")
        game_state = GAME_RUNNING
    elif json_data["action"] == "update_position":
        x = json_data["x"]
        y = json_data["y"]
        # if json_data["player"] != player_number:
        opponent_car_sprite.rect.x = x
        opponent_car_sprite.rect.y = y
    # elif json_data["action"] == "setup":
    #     handle_setup(json_data)


threading.Thread(target=receive_data, daemon=True).start()


def draw_waiting_screen():
    screen.fill(BLACK)
    wait_text = FONT.render("Waiting for other player to join game...", True, WHITE)
    screen.blit(
        wait_text, (SCREEN_WIDTH // 2 - wait_text.get_width() // 2, SCREEN_HEIGHT // 2)
    )
    pygame.display.flip()


def draw_countdown():
    global countdown_timer, last_countdown_update, game_state
    current_time = pygame.time.get_ticks()

    if current_time - last_countdown_update > 1000:
        countdown_timer -= 1
        last_countdown_update = current_time
        if countdown_timer <= 0:
            countdown_timer = 0  # Prevent it from going below zero
            print(f"Current game state is {game_state}")
            # if game_state != GAME_RUNNING:
            #     send_to_server({"action": "start"})
            #     game_state = GAME_RUNNING  # Ensure this change is made once

    screen.fill(BLACK)
    countdown_text = FONT.render(f"Game starting in {countdown_timer}...", True, WHITE)
    screen.blit(
        countdown_text,
        (SCREEN_WIDTH // 2 - countdown_text.get_width() // 2, SCREEN_HEIGHT // 2),
    )
    pygame.display.flip()


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


def game_loop():
    global score, distance_traveled, game_won
    screen.fill(GREEN)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            client_socket.close()
            exit()

    keys = pygame.key.get_pressed()
    handle_road_and_lines()
    handle_dashed_lines()
    car_sprite.update_position(
        keys[pygame.K_LEFT],
        keys[pygame.K_RIGHT],
        keys[pygame.K_UP],
        keys[pygame.K_DOWN],
    )

    spawn_obstacle()

    # Update and draw all sprites
    all_sprites.update()
    all_sprites.draw(screen)

    # Handle collisions
    if pygame.sprite.spritecollide(
        car_sprite, obstacles, True, pygame.sprite.collide_mask
    ):
        game_won = False  # Set game over state or conditions
        send_to_server({"action": "game_over", "result": "lose"})

    # Scoring and distance tracking
    distance_traveled += speed
    score = int(distance_traveled * 0.1)
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    # Check win condition
    if distance_traveled >= RACE_DISTANCE:
        game_won = True
        send_to_server({"action": "finish", "winner": player_num})
        pygame.quit()
        client_socket.close()

    pygame.display.flip()


# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    if game_state == WAITING_FOR_PLAYERS:
        draw_waiting_screen()
    elif game_state == COUNTDOWN:
        draw_countdown()
    elif game_state == GAME_RUNNING:
        game_loop()

    clock.tick(60)

pygame.quit()
client_socket.close()
