import socket
import threading
import queue
import select
import sys
import getpass
import re
import os
import time

class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.local_mode = False
        self.command_queue = queue.Queue()
        ## self.ftp_socket.settimeout(10)

    def connect(self):
        self.ftp_socket.connect((self.host, self.port))
        return self.response()
    
    def transfer_mode_info(self):
        print(self.send("SYST"))

    def pasv_connect(self):
        try:
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
    
    def server_info(self, path):
        if path is None:
            response = self.send("STAT")
            response += self.response()
            print(response)
        else:
            response = self.send("STAT {path}")
            response += self.response()
            print(response)

    def default_login(self):

        self.send(f"USER anonymous\r\n")
        response = self.send(f"PASS anonymous")

        if "230" in response: 
            print("entrando como usuario anonimo")
            return response
        else:
            return ("Error de autenticación")

    def login(self):
        username = input("Ingrese el nombre de usuario: ")
        if username == "":
            return self.default_login()
        
        self.send(f"USER {username}\r\n")

        password = getpass.getpass("Ingrese la contraseña: ")
        response = self.send(f"PASS {password}\r\n")

        req = input("Requiere una cuenta específica? s- SI n- NO: ")
        if req == "s":
            account = input("Ingrese su cuenta: ")

            acct_response = self.send(f"ACCT {account}") 
            return acct_response

        elif "230" in response: 
            return response
        else:
            return ("Error de autenticación")
        
    def help_ftp(self):
        response = self.send("HELP")
        response += self.response()
        print(response)
        
    def nlst(self, path):
        data_socket = self.pasv_connect()
        try:
            if path is not None:
                self.send(f"NLST {path}")
            else:
                self.send("NLST")
                
            data_total = ""
            while True:
                data = data_socket.recv(4096).decode()
                if not data:
                    break
                data_total += data
            data_socket.close()

            print(self.response())

            for line in data_total.split("\n"):
                print(line)
            return data_total.split("\n")
        except Exception as e:
            print(f"Error al recibir datos: {e}")
            
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
                    return files
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
                return files
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
                return data_total.split("\n")
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
        if self.local_mode:
            print("Error: no se puede eliminar en modo local.")
            return
        files = self.list_files(path)
        for file in files:
            if file.startswith('d'):
                self.cwd(path)
                dirname = file.split()[-1]
                self.rm_dir(dirname)
                self.cwd("..")
            elif file.startswith('-'):
                self.cwd(path)
                filename = file.split()[-1]
                self.rm_file(filename)
                self.cwd("..")
                
        print(self.send(f"RMD {path}"))
    
    def mk_dir(self, path):
        if self.local_mode:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"Directorio {path} creado con éxito.")
            except Exception as e:
                print(f"Error al crear el directorio {path}: {e}")
            return
        else:
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
    
    def retr(self, filename):
        if self.local_mode:
            print("Error: no se puede descargar en modo local.")
            return
        response =  self.download_file(filename, filename)
        print(response)
        if "550" in response:
            print(f"Iniciando descarga del directorio {filename}...")
            self.download_dir(filename)
            
    def download_file(self, remote_path, local_path):
        data_socket = self.pasv_connect()
        try:
            response = self.send(f"RETR {remote_path}")
            print(response)
            if "550" in response:
                return response
            command = ""
            with open(local_path, 'wb') as file:
                # Iniciar un hilo para detectar el comando de stop
                stop_thread = threading.Thread(target=self.detect_stop_command)
                stop_thread.start()

                while True:
                    if not self.command_queue.empty():
                        command = self.command_queue.get()
                        if command == 'stop':
                            print("Descarga cancelada por el usuario.")
                            break
                    data = data_socket.recv(2048)
                    if not data: # Verifica si el evento está señalizado
                        break
                    file.write(data)

            # print("Descarga completada.")
            if command != 'stop':
                self.command_queue.put('download_complete')

            stop_thread.join()
            data_socket.close()
            return self.response()
        except:
            print(f"Error al descargar el archivo {remote_path}")
       
    def download_dir(self, path):
        local_path = os.path.join(os.getcwd(), path)
        os.makedirs(local_path, exist_ok=True)
        
        files = self.list_files(path)

        for file in files:
            if file.startswith('d'):
                dirname = file.split()[-1]
                self.cwd(path)
                os.chdir(path)
                self.download_dir(dirname)
                os.chdir("..")
                self.cwd("..")
            elif file.startswith('-'):
                filename = file.split()[-1]
                self.cwd(path)
                self.download_file(filename, os.path.join(local_path, filename))
                self.cwd("..")
                
    def stor(self, local_path, remote_path=None):
        if self.local_mode:
            print("Error: no se puede subir en modo local.")
            return
        
        if remote_path is None:
            remote_path = local_path

        if os.path.isfile(local_path):
            self.upload_file(local_path, remote_path)
        elif os.path.isdir(local_path):
            self.upload_dir(local_path, remote_path)
        else:
            print(f"Error: {local_path} no es un archivo o directorio válido.")

    def upload_file(self, local_path, remote_path):
        data_socket = self.pasv_connect()
        if data_socket is None:
            return
        try:
            self.send(f"STOR {remote_path}")
            with open(local_path, 'rb') as file:
                while True:
                    data = file.read(2048)
                    if not data:
                        break
                    data_socket.sendall(data)
            data_socket.close()
            print(self.response())
        except Exception as e:
            print(f"Error al subir el archivo {local_path}: {e}")
    
    def append(self, filename, data):
        data_socket = self.pasv_connect()

        self.send(f"APPE {filename}")

        data_socket.sendall(data.encode())

        data_socket.close()

        response = self.response()
        print(response)

    def upload_dir(self, local_dir, remote_dir):
        self.mk_dir(remote_dir)
        for file in os.listdir(local_dir):
            local_path = os.path.join(local_dir, file)
            remote_path = os.path.join(remote_dir, file)
            if os.path.isdir(local_path):
                self.upload_dir(local_path, remote_path)
            elif os.path.isfile(local_path):
                self.upload_file(local_path, remote_path)
            else:
                print(f"Error: {local_path} no es un archivo o directorio válido.")

    def detect_stop_command(self):
        condition = True
        while condition:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == 'download_complete':
                    print("Descarga completada.")
                    condition = False
                    break
                else:
                    self.command_queue.put(command)
            while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if line.strip().lower() == 'stop':
                    self.command_queue.put('stop')
                    condition = False
                    break
                    
    def size(self, filename):
        if self.local_mode:
            print("Error: no se puede obtener el tamaño de archivos en modo local.")
            return
        else:
            print(f"Obtener el tamaño de {filename}...")
            response = self.send(f"SIZE {filename}")
            print(response)
    def rein(self):
        print(self.send("REIN"))
    def reinLocal(self):
        self.close()
        self.ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.local_mode = False
        self.command_queue = queue.Queue()
        self.connect()
        while True:
            response = client.login()
            print(response)
            if "230" in response:
                break
            else:
                print("Intente de nuevo.")
    def mount_file_system(self, pathname):
        print(self.send(f"SMNT {pathname}"))

    def noop_loop(self):
        self.stop = False
        while True:
            response = self.send("NOOP")
            if self.stop:
                break
            print(response)
            time.sleep(10)

    def idle(self):
        noop_thread = threading.Thread(target=self.noop_loop)
        noop_thread.start()
        
        while True:
            stop = input("Presione Enter para continuar la conexion: \n")
            if stop == "": 
                self.stop = True
                noop_thread.join()
                break
    def portCnx(self, ip, port):
        h1, h2, h3, h4 = map(int, ip.split('.'))
    
        p1, p2 = divmod(port, 256)

        response = self.send(f"PORT {h1},{h2},{h3},{h4},{p1},{p2}")
        print(response)
    
    def store_unique(self):
        data_socket = self.pasv_connect()
        try:
            response = self.send("STOU")
            print(response)
            if "550" in response:
                return response
           
            data_socket.close()
            return self.response()
        except:
            print(f"Error en el comando STOU")

    def set_transfer_type(self, type_code):
        response = self.send(f"TYPE {type_code}")
        print(response)

    def site_commands(self, command, argument):
        if argument is None:
            response = self.send(f"SITE {command}")        
        else:
            response = self.send(f"SITE {command} {argument}")
        print(response)
    
                
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
        command = commands[0].lower()
        args = commands[1:]
        
        
        if command == "ls":
            if len(args) > 0:
                client.list_files(args[0])
            else:
                client.list_files(None)
        elif command == "download":
            if len(args) > 0:
                client.retr(args[0])
            else:
                print("Error: download requiere un argumento.")
        elif command == "upload":
            if len(args) > 0:
                client.stor(args[0], args[1] if len(args) > 1 else None)
            else:
                print("Error: stor requiere un argumento.")
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
        elif command == "syst":
            client.transfer_mode_info()
        elif command == "size":
            if len(args) > 0:
                client.size(args[0])
            else:
                print("Error: size requiere un argumento.")
        elif command == "quit" or command == "exit":
            client.close()
            break
        elif command == "ftp-help":
            client.help_ftp()
        elif command == "server-info":
            if len(args) > 0:
                client.server_info(args)
            else:
                client.server_info(None)
        elif command == "rein":
            client.rein()
        elif command == "rein-local":
            client.reinLocal()
        elif command == "smnt":
            if len(args) > 0:
                client.mount_file_system(args[0])
            else:
                print("Error: smnt requiere un argumento.")
        elif command == "idle":
            client.idle()
        elif command == "unique-file":
            client.store_unique()

        elif command == "stop":
            client.abort()
        elif command == "port":
            if len(args) > 0:
                client.portCnx(args[0], int(args[1]))
            else:
                print("Error: port requiere un argumento.")
        elif command == "type":
            if len(args) > 0:
                client.set_transfer_type(args[0])
            else:
                print("Error: type requiere un argumento.")
        elif command == "appe":
            if len(args) > 0:
                client.append(args[0], args[1])
            else:
                print("Error: appe requiere dos argumentos.")
        elif command == "site":
            if len(args) > 1:
                client.site_commands(args[0], args[1])
            elif len(args) > 0:
                client.site_commands(args[0], None)
            else:
                print("Error, site recibe argumentos")
        elif command == "nlst":
            if len(args) > 0:
                client.nlst(args[0])
            else:
                client.nlst(None)
        elif command == "help":
            print("Comandos disponibles para ambos modos:")
            print("ls: Listar los archivos y carpetas con descripción del directorio actual.")
            print("cd: Cambiar de directorio.")
            print("pwd: Mostrar el directorio actual.")
            print("mkdir: Crear un directorio.")
            print("clear: Limpiar la pantalla.")
            print("mode: Cambiar entre modo local y servidor.")
            print("help: Mostrar esta lista de comandos.")
            print("\n")
            
            print("Comandos disponibles para Mode server:")
            print("quit: Salir del cliente.")
            print("rmfil: Eliminar un archivo.")
            print("rmdir: Eliminar un directorio.")
            print("touch: Crear un archivo.")
            print("rename: Renombrar.")
            print("download: Descargar un archivo o directorio del servidor.")
            print("upload: Subir un archivo o directorio al servidor.")
            print("stop: Detener la descarga de un archivo.")
            print("size: Obtener el tamaño de un archivo.")
            print("syst: Ver modo de transferencia actual.")
            print("server-info: Ver información del servidor.")
            print("rein: Reiniciar la conexión con el servidor.")
            print("rein-local: Reiniciar la conexión desde el cliente.")
            print("smnt: Montar un sistema de archivos.")
            print("server-info: Mostrar estado actual del servidor")
            print("unique-file: crear archivo con nombre único en el servidor")
            print("idle: Mantener la conexión activa.")
            print("port: Establecer una conexión de datos.")
            print("type: Establecer el tipo de transferencia.")
            print("appe: Agregar datos al final de un archivo.")
            print("site: Enviar comandos específicos al servidor.")
            print("nlst: Listar archivos y directorios en el servidor.")
            
        else:
            print("Comando no válido, use help para ver la lista de comandos disponibles.")