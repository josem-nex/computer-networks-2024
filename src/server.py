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
            dataUser = client_socket.recv(1024)
            print("Comando recibido: " + dataUser.decode())
            
            client_socket.send(b"331 Ingrese su contrasena\n")
            
            dataPass = client_socket.recv(1024)
            print("Comando recibido: " + dataPass.decode())
            if dataUser and dataPass:
                username = dataUser.decode().strip().split(" ")
                password = dataPass.decode().strip().split(" ")
                if self.login(username[1], password[1]):
                    client_socket.send(b"230 Login correcto\n")
                    break
                else:
                    client_socket.send(b"530 Login incorrecto\n")
            else:
                client_socket.close()
                break

        while True:
            data = client_socket.recv(1024)
            if data:
                print("Comando recibido: " + data)
                response = self.handle_command(data.decode())
                client_socket.send(response)
            else:
                client_socket.close()
                break
            
    def login(self, username, password):
        users = []
        with open("users.txt", "r") as file:
            data = file.readlines()
            for line in data:
                users.append(line.strip().split(" "))
        for user in users:
            if user[0] == username and user[1] == password:
                return True
        return False

    
            
        
            
    def handle_command(self, command: str):
        command = command.strip().upper()
        commands = command.split(" ")
        args = commands[1:]
        command = commands[0]
        if command == "QUIT":
            return b"221 Goodbye\n"
        else:
            return b"500 Comando no soportado\n"
        
if __name__ == "__main__":
    ftp_server = FTPServer()
    ftp_server.start()
    