import csv
import socket
import sys
from threading import Thread
import os  # listdir(), getcwd(), chdir(), mkdir()
import subprocess

created_threads = []
ServerFolder = os.getcwd() + "/"

class ThreadFunctions(Thread):
    def __init__(self, client_socket, client_ip, client_port):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port

    def run(self):
        os.chdir(ServerFolder)
        while True:
            request = self.client_socket.recv(1024).decode().strip()
            if not request:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
                break
            request = request.split(",")

            if request[0] == "LS":
                self.ls()
            elif request[0] == "PWD":
                self.pwd()
            elif request[0] == "CD":
                self.cd(request[1])
            elif request[0] == "MKDIR":
                self.mkdir(request[1])
            elif request[0] == "RMDIR":
                self.rmdir(request[1])
            elif request[0] == "RM":
                self.rm(request[1])

            elif request[0] == "rget" and len(request[1:]) == 1:
                self.send_file(*request[1:])

            elif request[0] == "rput" and len(request[1:]) == 2:
                self.receive_file(*request[1:])

    def ls(self):
        packet = subprocess.check_output(["ls", "-l"], universal_newlines=True)
        if packet.strip() == "":
            self.client_socket.sendall("EMPTY".encode())
        else:
            self.client_socket.sendall(packet.encode())

    def pwd(self):
        # TODO
        pass

    def cd(self, dir_path):
        try:
            if (dir_path == '..' and os.getcwd() == ServerFolder):
                self.client_socket.sendall(f"Cambio de directorio a: '{dir_path}'".encode())
            else:
                os.chdir(dir_path)
                self.client_socket.sendall(f"Cambio de directorio a: '{dir_path}'".encode())
        except FileNotFoundError:
            self.client_socket.sendall(f"Directorio '{dir_path}' no encontrado".encode())

    def mkdir(self, dir_name):
        try:
            os.mkdir(dir_name)
            self.client_socket.sendall(f"Directorio '{dir_name}' creado".encode())
        except OSError:
            self.client_socket.sendall(f"El directorio con nombre: '{dir_name}' existe".encode())

    def rmdir(self, dir_name):
        try:
            os.removedirs(dir_name)
            self.client_socket.sendall(f"Directorio '{dir_name}' removido".encode())
        except FileNotFoundError:
            self.client_socket.sendall(f"Directorio con nombre: '{dir_name}' no existe".encode())
        except OSError:
            self.client_socket.sendall(f"El directorio no está vacío".encode())

    def rm(self, file_name):
        try:
            os.remove(file_name)
            self.client_socket.sendall(f"Archivo '{file_name}' removido".encode())
        except FileNotFoundError:
            self.client_socket.sendall(f"Archivo '{file_name}' no existe".encode())
        except IsADirectoryError:
            self.client_socket.sendall(f"'{file_name}' es un directorio".encode())

    def send_file(self, file_name):
        # enviar archivo a un cliente conectado a un servidor FTP
        try:
            dataPort = self.client_socket.recv(1024).decode()

            dataConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.connect((self.client_ip, int(dataPort)))

            file_size = os.path.getsize(file_name)
            self.client_socket.sendall("> {}".format(file_size).encode('utf-8'))

            while True:
                recv_data = self.client_socket.recv(1024)
                request = recv_data.decode('utf-8').strip().split(",")

                if request[0] == "Ready":
                    print("Enviando {} al cliente {}".format(file_name, self.client_ip))

                    with open(file_name, "rb") as file:
                        dataConnection.sendfile(file)
                elif request[0] == "Received":
                    if int(request[1]) == file_size:
                        self.client_socket.sendall("Success".encode('utf-8'))
                        print("{} descargado en el cliente {}".format(file_name, self.client_ip))
                        break
                    else:
                        print("Algo salió mal al intentar descargar en el cliente {}:{}".format(self.client_ip, self.client_port))
                        break
                else:
                    print("Algo salió mal al intentar descargar en el cliente {}:{}".format(self.client_ip, self.client_port))
                    break
        except IOError:
            print("{} no existe en el servidor".format(file_name))
            self.client_socket.sendall("Failed".encode('utf-8'))

    def receive_file(self, file_name, length):
        self.client_socket.sendall("Ready".encode("utf-8"))
        print("Servidor listo para recibir: {} del cliente: {}:{}".format(file_name, self.client_ip, self.client_port))

        save_file = open("{}".format(file_name), "wb")

        amount_recieved_data = 0
        while amount_recieved_data < int(length):
            recv_data = self.client_socket.recv(1024)
            amount_recieved_data += len(recv_data)
            save_file.write(recv_data)

        save_file.close()

        self.client_socket.sendall("Received,{}".format(amount_recieved_data).encode('utf-8'))
        print("Servidor recibió el archivo de {}:{}".format(self.client_ip, self.client_port))

class FTPServer:
    def __init__(self, host = '127.0.0.5', port = 22):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_host = host
        self.server_port = port
        self.max_queued = 10
        self.allowed_users = self.load_users()
    
    def run (self):
        self.server_socket.bind((self.server_host, self.server_port))
        self.server_socket.listen(self.max_queued)

        while True:
            client_socket, client_addr = self.server_socket.accept()

            while True:
                response = client_socket.recv(1024).decode().strip().split(":")
                try:
                    if self.auth_user(response[0], response[1]):
                        client_socket.sendall("SUCCESS".encode())

                        new_client_thread = ThreadFunctions(client_socket, *client_addr)
                        new_client_thread.start()

                        created_threads.append(new_client_thread)
                        break
                    else:
                        client_socket.sendall("FAILURE".encode())
                        client_socket.close()
                        break
                except IndexError:
                    client_socket.sendall("FAILURE".encode())
                    client_socket.close()
                    break

    def auth_user(self, name=None, password=None):
        if name == None or password == None:
            return False
        for user in self.allowed_users:
            if name == user["name"] and user["passwd"] == password:
                return True
        return False

    def load_users(self):
        try:
            register_file = open("src/users.txt.txt", "r")
        except FileNotFoundError:
            print("Ocurrió un error")
            sys.exit()

        users = []
        csv_file = csv.DictReader(register_file, delimiter=",")
        for user in csv_file:
            users.append(user)

        return users
        
if __name__ == "__main__":
    ftp_server = FTPServer()
    ftp_server.run()
    