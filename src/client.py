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
        # Enviar el comando PASV al servidor y obtener la respuesta
        response =self.send("PASV") 
        print(response)
        # Extraer la dirección IP y el puerto de la respuesta, expresión regular
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if match:
            ip_parts = [int(x) for x in match.groups()[:4]]
            port = (int(match.groups()[4]) << 8) + int(match.groups()[5])
            ip_address = '.'.join(str(x) for x in ip_parts)
            # Crear un nuevo socket para la conexión de datos, y conectarse al servidor
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((ip_address, port))
            print(f"Conectado a {ip_address}:{port}")
            return data_socket
        else:
            raise Exception("No se pudo extraer la dirección IP y el puerto de la respuesta PASV")



    def response(self):
        return self.ftp_socket.recv(1024).decode()

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
        
    def list_files(self):
        
        data_socket = self.pasv_connect()
        
        self.send("LIST")
        
        data_total = ""
        while True:
            data = data_socket.recv(1024).decode()
            if not data:
                break
            data_total += data
            
        data_socket.close()
        return data_total

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
        command = input("$")
        commands = command.split(" ")
        command = commands[0]
        args = commands[1:]
        
        
        if command == "list":
            print(client.list_files())
        elif command == "retr":
            pass
        elif command == "stor":
            pass
        elif command == "clear":
            print("\033[H\033[J")
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