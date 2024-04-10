import socket
import threading

class FTPServer:
    def __init__(self, host = '127.0.0.5', port = 22):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = []
        self.host = host
        self.port = port
    
    
    def start(self):
        print(f"Servidor FTP iniciado en {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Conexión desde {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
            self.clients.append(client_thread)
            
    def handle_client(self, client_socket):
        client_socket.send(b"220 Bienvenido al servidor FTP\n")
        while True:
            data = client_socket.recv(1024)
            if data:
                print(data)
                response = self.handle_command(data.decode())
                client_socket.send(response)
            else:
                client_socket.close()
                break
            
    def handle_command(self, command: str):
        command = command.strip().upper()
        if command == "QUIT":
            return b"221 Goodbye\n"
        else:
            return b"500 Comando no soportado\n"
        
if __name__ == "__main__":
    ftp_server = FTPServer()
    ftp_server.start()
    