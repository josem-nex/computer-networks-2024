import socket
import threading
import os

class FTPServer:
    def __init__(self, host = '127.0.0.5', port = 22):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = []
        self.host = host
        self.port = port
        self.directory = 'FTP_Storage'
        self.root_dir = os.path.join(os.getcwd(), self.directory)
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
        self.dataSockets = []
    
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
                print("Comando recibido: " + data.decode())
                response = self.handle_command(client_socket,data.decode())
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

    def disconnect_user(self, client_socket):
        client_socket.send(b"221 Goodbye\n")
        client_socket.close()
        self.clients.remove(client_socket)
    
    def list_files(self, data_socket, current_dir):
        try:
            data_socket = self.mode_pasv(data_socket)
            conn, addr = data_socket.accept()
            files = '\n'.join(os.listdir(os.path.join(current_dir))) + '\r\n'
            conn.sendall(files.encode())
            conn.close()
            data_socket.send(b"226 Directory send OK\n")
        except Exception as e:
            print(e)
            data_socket.send(b"550 Failed to list directory\n")
            if conn:
                conn.close()
    def mode_pasv(self, client_socket):
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind((self.host, 0))
        data_port = data_socket.getsockname()[1]
        data_socket.listen(1)
        host_bytes = self.host.split('.')
        port_bytes = [data_port // 256, data_port % 256]
        client_socket.sendall(f'227 Entering Passive Mode ({host_bytes[0]},{host_bytes[1]},{host_bytes[2]},{host_bytes[3]},{port_bytes[0]},{port_bytes[1]})\r\n'.encode())
        print(f'227 Entering Passive Mode ({host_bytes[0]},{host_bytes[1]},{host_bytes[2]},{host_bytes[3]},{port_bytes[0]},{port_bytes[1]})\r\n')
        return data_socket
    
    def handle_command(self, client_socket, command: str):
        data_socket = None
        command = command.strip().upper()
        commands = command.split(" ")
        args = commands[1:]
        command = commands[0].lower()
        print(command)
        if command == "quit" or command == "exit":
            self.disconnect_user(client_socket)
        elif command == "ls":
            if data_socket is None:
                return b"425 Use PASV first\n"
            self.list_files(data_socket, self.root_dir)
        elif command == "pasv":
            data_socket = self.mode_pasv(client_socket)
        else:
            return b"500 Comando no soportado\n"
    
    

        
if __name__ == "__main__":
    ftp_server = FTPServer()
    ftp_server.start()
    