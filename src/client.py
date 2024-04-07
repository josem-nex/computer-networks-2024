import socket

class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.ftp_socket.connect((self.host, self.port))
        return self.response()

    def response(self):
        return self.ftp_socket.recv(1024).decode()

    def send(self, message):
        self.ftp_socket.sendall(f"{message}\r\n".encode())
        return self.response()

    def login(self, username, password):
        self.send(f"USER {username}\r\n")
        response = self.send(f"PASS {password}\r\n")
        
        return response
    def list_files(self):
        return self.send(b"LIST\r\n") 


if __name__ == "__main__":
    host = input("Ingrese la dirección del servidor FTP: ")
    port = 21

    client = FTPClient(host, port)
    try :
        print(client.connect())
    except Exception as e:
        print(f"Error al conectar con el servidor FTP: {e}")
        exit()
    
    username = input("Ingrese el nombre de usuario: ")
    password = input("Ingrese la contraseña: ")
    print(client.login(username, password))
    
    while True:
        command = input("$")
        commands = command.split(" ")
        command = commands[0]
        args = commands[1:]
        
        
        if command == "list":
            pass
        elif command == "retr":
            pass
        elif command == "stor":
            pass
        elif command == "clear":
            print("\033[H\033[J")
        elif command == "quit":
            break
        elif command == "help":
            print("Comandos disponibles:")
            print("list: Listar los archivos del servidor.")
            print("retr: Descargar un archivo del servidor.")
            print("stor: Subir un archivo al servidor.")
            print("quit: Salir del cliente.")
        else:
            print("Comando no válido, use help para ver la lista de comandos disponibles.")