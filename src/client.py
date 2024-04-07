import socket
import getpass
import re

class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.ftp_socket.connect((self.host, self.port))
        return self.response()
    
    def pasv_connect(self):
        try:
            # Enviar el comando PASV al servidor y obtener la respuesta
            response =self.send("PASV") 
            # Extraer la dirección IP y el puerto de la respuesta, expresión regular
            match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
            if match:
                ip_parts = [int(x) for x in match.groups()[:4]]
                port = (int(match.groups()[4]) << 8) + int(match.groups()[5])
                ip_address = '.'.join(str(x) for x in ip_parts)
                # Crear un nuevo socket para la conexión de datos, y conectarse al servidor
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((ip_address, port))
                # print(f"Conectado a {ip_address}:{port}")
                return data_socket
            else:
                print("Error en el modo PASV ")
                return None
        except Exception as e:
            print(f"Error al establecer la conexión PASV: {e}")
            return None
        
    def response(self):
        response = ''
        while True:
            part = self.ftp_socket.recv(1024).decode()
            response += part
            if response.endswith('\r\n') or len(part) < 1024:
                break
        return response

    def send(self, message):
        self.ftp_socket.sendall(f"{message}\r\n".encode())
        return self.response()

    def login(self):
        username = input("Ingrese el nombre de usuario: ")
        self.send(f"USER {username}\r\n")
        password = getpass.getpass("Ingrese la contraseña: ")
        response = self.send(f"PASS {password}\r\n")
         
        if "230" in response: 
            return response
        else:
            return ("Error de autenticación")
        
    def list_files(self, path):
        
        data_socket = self.pasv_connect()
        if data_socket is None:
            return
        try:
            if path is not None:
                self.send(f"LIST {path}")
            else:
                self.send("LIST")

            data_total = ""
            while True:
                data = data_socket.recv(4096).decode()
                if not data:
                    break
                data_total += data
            data_socket.close()
            
            print(self.response())
            
            for line in data_total.split("\n"):
                if line.startswith('d'):
                    print('\033[94m' + line + '\033[0m')
                elif line.startswith('-'):
                    print('\033[91m' + line + '\033[0m')  
                else:
                    print(line)
        except Exception as e:
            print(f"Error al recibir datos: {e}")
          
    def cwd(self, path):
        if path == "..":
            response = self.send("CDUP")
            print(response)
            return
        if path == ".":
            print("Ya se encuentra en el directorio actual.")
            return
        
        response = self.send(f"CWD {path}")
        print(response)
    
    def pwd(self):
        response = self.send("PWD")
        print(response)

    def close(self):
        self.send("QUIT")
        self.ftp_socket.close()


if __name__ == "__main__":
    host = input("Ingrese la dirección del servidor FTP: ")
    port = 21

    client = FTPClient(host, port)
    try :
        print(client.connect())
    except Exception as e:
        print(f"Error al conectar con el servidor FTP: {e}")
        exit()
    
    while True:
        response = client.login()
        print(response)
        if "230" in response:
            break
        else:
            print("Intente de nuevo.")
    
    while True:
        command = input('\033[92m $ \033[0m')
        commands = command.split(" ")
        command = commands[0]
        args = commands[1:]
        
        
        if command == "ls":
            if len(args) > 0:
                client.list_files(args[0])
            else:
                client.list_files(None)
        elif command == "retr":
            pass
        elif command == "stor":
            pass
        elif command == "clear":
            print("\033[H\033[J")
        elif command == "cd":
            if len(args) > 0:
                client.cwd(args[0])
            else:
                client.cwd(".")
        elif command == "pwd":
            client.pwd()
        elif command == "quit":
            client.close()
            break
        elif command == "help":
            print("Comandos disponibles:")
            print("list: Listar los archivos del servidor.")
            print("retr: Descargar un archivo del servidor.")
            print("stor: Subir un archivo al servidor.")
            print("quit: Salir del cliente.")
        else:
            print("Comando no válido, use help para ver la lista de comandos disponibles.")