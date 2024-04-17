import random
import socket
import threading
import json
import time

HOST = "127.0.0.1"
PORT = 8848
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
MID_ROAD = SCREEN_WIDTH // 2
LANE_WIDTH = 100
X1 = player_car_x = MID_ROAD - LANE_WIDTH // 2
X2 = MID_ROAD + LANE_WIDTH // 2
ROAD_WIDTH = 400
EDGE_WIDTH = 5


class RaceServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)
        print("Server is listening for connections...")
        self.players = {}
        self.game_state = "waiting"  # can be 'waiting', 'ready', 'started', 'finished'
        self.lock = threading.RLock()
        self.start_received = 0
        self.player_score_dict = {}
        self.ready_acks = 0
        self.last_spawn_time = time.time()
        self.spawn_interval = 2.0
        self.running = True
        self.obstacles = []
        self.winner = 0

    def run(self):
        while self.running:
            self.update_game()
            time.sleep(0.1)

    def update_game(self):
        current_time = time.time()
        if (
            current_time - self.last_spawn_time >= self.spawn_interval
            and self.game_state == "started"
        ):
            self.spawn_obstacle()
            self.last_spawn_time = current_time
            self.adjust_difficulty()

    def adjust_difficulty(self):
        # Decrease spawn interval over time to increase difficulty
        if self.spawn_interval > 0.5:  # Prevent it from going too low
            self.spawn_interval *= 0.99  # Spawn faster by 5%

    def broadcast(self, message):
        with self.lock:
            for number, conn in self.players.items():
                try:
                    conn.sendall((message + "\n").encode())
                    print(f"Sent to {conn.getpeername()}: {message}")
                except Exception as e:
                    print(f"Failed to send to {number}: {e}")

    def spawn_obstacle(self):
        obstacle_x = random.randint(
            SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + EDGE_WIDTH,
            SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 - EDGE_WIDTH,
        )
        obstacle_y = -100  # Start just above the view
        obstacle = {"x": obstacle_x, "y": obstacle_y}
        # self.obstacles.append(obstacle)
        # self.broadcast(json.dumps({"action": "spawn_obstacle", "obstacle": obstacle}))

    def handle_client(self, conn, player_number):
        try:
            with self.lock:
                self.players[player_number] = conn
                if len(self.players) == 2:
                    self.game_state = "ready"
                    # self.broadcast(json.dumps({"action": "ready"}))
                    self.broadcast_setup_info()

            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)

                if message.get("action") == "ready_ack":
                    self.ready_acks += 1
                    print(f"Received ready acknowledgment from player {player_number}")
                    if self.ready_acks == 2:
                        print("2 acknowledgment received. Sending start signal")
                        self.broadcast(json.dumps({"action": "start"}))
                        self.game_state = "started"
                        self.ready_acks = 0

                if message.get("action") == "update_position":
                    self.broadcast_to_others(player_number, json.dumps(message))

                elif message.get("action") in ["start", "finish"]:
                    self.handle_game_state_changes(message, player_number)

                elif message.get("action") == "game_over":
                    msg = (
                        json.dumps({"action": "game_won", "loser": player_number})
                        + "\n"
                    )
                    if message.get("winner"):
                        # winner is only present if game is over
                        if self.winner == 0:
                            # the one sending the msg first is the winner

                            msg = json.dumps(
                                {"action": "game_won", "winner": player_number}
                            )
                            msg_to_loser = json.dumps(
                                {"action": "game_over", "winner": player_number}
                            )
                            self.broadcast_to_others(player_number, msg_to_loser)
                            self.broadcast(msg)
                            self.game_state = "finished"
                        else:
                            pass
                    else:
                        over_message = (
                            json.dumps({"action": "finished", "loser": player_number})
                            + "\n"
                        )
                        self.broadcast_to_others(player_number, msg)
                        self.broadcast(over_message)
                        self.game_state = "finished"

        except Exception as e:
            print("Error handling client:", e)
        finally:
            self.cleanup_player(player_number, conn)

    def broadcast_to_others(self, sender_id, message):
        with self.lock:
            for player_id, conn in self.players.items():
                if player_id != sender_id:
                    try:
                        conn.sendall((message + "\n").encode())
                    except Exception as ex:
                        print(f"Failed to send message to player {player_id}: {ex}")

    def handle_game_state_changes(self, message, player_number):
        action = message.get("action")
        if action == "start":
            # Handle start
            pass
        elif action == "finish":
            # Handle finish
            self.broadcast(json.dumps({"action": "finish", "winner": player_number}))

    def cleanup_player(self, player_number, conn):
        with self.lock:
            if player_number in self.players:
                del self.players[player_number]
                self.broadcast(
                    json.dumps({"action": "disconnect", "player": player_number})
                )
                if self.game_state != "finished":
                    self.game_state = "waiting"
        conn.close()

    def broadcast_setup_info(self):
        seed = random.randint(0, 999999999)
        setup_info = {
            1: {
                "position": (X1, SCREEN_HEIGHT - 180),
                "color": "black",
            },  # Left side start
            2: {
                "position": (X2, SCREEN_HEIGHT - 180),
                "color": "blue",
            },  # Right side start
        }
        for player_id, conn in self.players.items():
            message = {
                "action": "ready",
                "setup": {
                    "player_number": player_id,
                    "your_color": setup_info[player_id]["color"],
                    "opponent_color": setup_info[3 - player_id][
                        "color"
                    ],  # Gets the other player's color
                    "start_position": setup_info[player_id]["position"],
                    "opponent_start_position": setup_info[3 - player_id]["position"],
                    "seed": seed,
                },
            }
            conn.sendall((json.dumps(message) + "\n").encode())

    def start(self):
        threading.Thread(
            target=self.run
        ).start()  # Start the game logic in a separate thread
        while True:
            conn, addr = self.server_socket.accept()
            player_number = len(self.players) + 1
            print(f"Player {player_number} connected.")
            conn.send(f"{player_number}".encode())
            threading.Thread(
                target=self.handle_client, args=(conn, player_number)
            ).start()


if __name__ == "__main__":
    race_server = RaceServer()
    race_server.start()
