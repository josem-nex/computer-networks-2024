import socket
import getpass
import re
import os

class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.local_mode = False

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
        if self.local_mode:
            if path is not None:
                if os.path.isdir(path):
                    files = os.listdir(path)
                    for file in files:
                        full_path = os.path.join(path, file)
                        if os.path.isdir(full_path):
                            print('\033[94m' + file + '\033[0m')
                        else:
                            print('\033[91m' + file + '\033[0m')
                else:
                    print("Error: el directorio no existe.")
            else:
                files = os.listdir()
                for file in files:
                    full_path = os.path.join(os.getcwd(), file)
                    if os.path.isdir(full_path):
                        print('\033[94m' + file + '\033[0m')
                    else:
                        print('\033[91m' + file + '\033[0m')
            return
        else:
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
        if self.local_mode:
            try:
                os.chdir(path)
                print(f"Directorio cambiado a {path}")
            except Exception as e:
                print(f"Error al cambiar de directorio: {e}")
            return
        else:
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
        if self.local_mode:
            print(os.getcwd())
            return
        else:
            response = self.send("PWD")
            print(response)

    def close(self):
        self.send("QUIT")
        self.ftp_socket.close()

    def rm_dir(self, path):
        print(self.send(f"RMD {path}"))
    
    def mk_dir(self, path):
        print(self.send(f"MKD {path}"))
    
    def rm_file(self, path):
        print(self.send(f"DELE {path}"))
    
    def rename(self, from_name, to_name):
        response = self.send(f"RNFR {from_name}")
        print(response)
        response = self.send(f"RNTO {to_name}")
        print(response)
    
    def touch(self, filename):
        data_socket = self.pasv_connect()
        try:
            
            response = self.send(f"STOR {filename}") 
            print(response)
            data_socket.sendall(f"{''}\r\n".encode())
            print(f"Creando archivo {filename}...")
            
            data_socket.close()
            response = self.response()
            print(response)
            
            
            if response.startswith('2'):
                print(f'Archivo {filename} creado con éxito.')
            else:
                print(f'Error al crear el archivo {filename}.')
        except:
            print(f"Error al crear el archivo {filename}.")
      
    def toggle_local_mode(self, mode):
        if mode == "local":
            self.local_mode = True
            print("Modo local activado.")
        elif mode == "server":
            self.local_mode = False
            print("Modo servidor activado.")
        else:
            print("Error: modo no válido. Escriba 'local' o 'server'.")
    

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
        elif command == "rmfil":
            if len(args) > 0:
                client.rm_file(args[0])
            else:
                print("Error: rmfil requiere un argumento.")
        elif command == "rmdir":
            if len(args) > 0:
                client.rm_dir(args[0])
            else:
                print("Error: rmdir requiere un argumento.")
        elif command == "mkdir":
            if len(args) > 0:
                client.mk_dir(args[0])
            else:
                print("Error: mkdir requiere un argumento.")
        elif command == "touch":
            if len(args) > 0:
                client.touch(args[0])
            else:
                print("Error: touch requiere un argumento.")
        elif command == "rename":
            if len(args) > 1:
                client.rename(args[0], args[1])
            else:
                print("Error: rename requiere dos argumentos.")
        elif command == "mode":
            if len(args) > 0:
                client.toggle_local_mode(args[0])
            else:
                print("Error mode requiere un argumento: 'local' o 'server'.")
        elif command == "quit" or command == "exit":
            client.close()
            break
        elif command == "help":
            print("Comandos disponibles para Mode server:")
            print("list: Listar los archivos del servidor.")
            print("retr: Descargar un archivo del servidor.")
            print("stor: Subir un archivo al servidor.")
            print("quit: Salir del cliente.")
            print("clear: Limpiar la pantalla.")
            print("cd: Cambiar de directorio.")
            print("pwd: Mostrar el directorio actual.")
            print("rmfil: Eliminar un archivo.")
            print("rmdir: Eliminar un directorio.")
            print("mkdir: Crear un directorio.")
            print("touch: Crear un archivo.")
            print("rename: Renombrar.")
            print("mode: Cambiar entre modo local y servidor.")
            print("help: Mostrar esta lista de comandos.")
            print("\n")
            print("Comandos disponibles para Mode local:")
            print("ls: Listar los archivos del directorio actual.")
            print("cd: Cambiar de directorio.")
            print("pwd: Mostrar el directorio actual.")
            
        else:
            print("Comando no válido, use help para ver la lista de comandos disponibles.")