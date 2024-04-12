import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 8849
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
MID_ROAD = SCREEN_WIDTH // 2
LANE_WIDTH = 100
X1 = player_car_x = MID_ROAD - LANE_WIDTH // 2
X2 = MID_ROAD + LANE_WIDTH // 2


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

    def broadcast(self, message):
        with self.lock:
            for number, conn in self.players.items():
                try:
                    conn.sendall((message + "\n").encode())
                    print(f"Sent to {conn.getpeername()}: {message}")
                except Exception as e:
                    print(f"Failed to send to {number}: {e}")

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
                        self.ready_acks = 0

                if message.get("action") == "update_position":
                    self.broadcast_to_others(player_number, json.dumps(message))

                elif message.get("action") in ["start", "finish"]:
                    self.handle_game_state_changes(message, player_number)

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
                },
            }
            conn.sendall((json.dumps(message) + "\n").encode())

    def start(self):
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
