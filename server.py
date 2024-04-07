import socket
import threading

HOST = '127.0.0.1'
PORT = 8848

class RaceServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)
        print("Server is listening for connections...")
        self.players = []
        self.lock = threading.Lock()

    def handle_client(self, conn, player):
        with self.lock:
            self.players.append(conn)
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                with self.lock:
                    for player_conn in self.players:
                        if player_conn != conn:
                            player_conn.sendall(data)
            except Exception as e:
                print("Error handling client:", e)
                break
        with self.lock:
            self.players.remove(conn)
        conn.close()

    def start(self):
        while True:
            conn, addr = self.server_socket.accept()
            print(f"Player {len(self.players) + 1} connected.")
            conn.send(f"You are Player {len(self.players) + 1}".encode())
            threading.Thread(target=self.handle_client, args=(conn, len(self.players) + 1)).start()

if __name__ == "__main__":
    race_server = RaceServer()
    race_server.start()
