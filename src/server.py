import socket
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
            self.client_socket.sendall(
                f"File '{file_name}' successfully removed.".encode())
        except FileNotFoundError:
            self.client_socket.sendall(
                f"File named '{file_name}' doesn't exists.".encode())
        except IsADirectoryError:
            self.client_socket.sendall(
                f"'{file_name}' is a directory.".encode())
        # except OSError:
        #     self.client_socket.sendall(f"directory is not empty".encode())

    def send_file(self, file_name):
        """
        Sends requested file to client if it exits on the server.

        Params:
            file_name (str): name of file to find and transfer
        """

        try:
            dataPort = self.client_socket.recv(1024).decode()
            print("[Control] Data port is {}".format(dataPort))

            # Connect to the data connection
            dataConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dataConnection.connect((self.client_ip, int(dataPort)))

            file_size = os.path.getsize(file_name)
            self.client_socket.sendall(
                "Exists,{}".format(file_size).encode('utf-8'))

            while True:
                recv_data = self.client_socket.recv(1024)
                request = recv_data.decode('utf-8').strip().split(",")

                if request[0] == "Ready":
                    print("Sending file {} to client {}".format(
                        file_name, self.client_ip))

                    with open(file_name, "rb") as file:
                        dataConnection.sendfile(file)
                elif request[0] == "Received":
                    if int(request[1]) == file_size:
                        self.client_socket.sendall("Success".encode('utf-8'))
                        print("{} successfully downloaded to client {}".format(
                            file_name, self.client_ip))
                        break
                    else:
                        print("Something went wrong trying to download to client {}:{}. Try again".format(
                            self.client_ip, self.client_port))
                        break
                else:
                    print("Something went wrong trying to download to client {}:{}. Try again".format(
                        self.client_ip, self.client_port))
                    break
        except IOError:
            print("File {} does not exist on server".format(file_name))
            self.client_socket.sendall("Failed".encode('utf-8'))

    def receive_file(self, file_name, length):
        """
        Reads a file that is sent from the client.

        Params:
            file_name (str): name of file to be transfered
            length (str): byte length of the file to be transfered from client
        """
        self.client_socket.sendall("Ready".encode("utf-8"))
        print("Server ready to accept file: {} from client: {}:{}".format(
            file_name, self.client_ip, self.client_port))

        save_file = open("{}".format(file_name), "wb")

        amount_recieved_data = 0
        while amount_recieved_data < int(length):
            recv_data = self.client_socket.recv(1024)
            amount_recieved_data += len(recv_data)
            save_file.write(recv_data)

        save_file.close()

        self.client_socket.sendall("Received,{}".format(
            amount_recieved_data).encode('utf-8'))
        print("Server done receiving from client {}:{}. File Saved.".format(
            self.client_ip, self.client_port))

class FTPServer:
    def __init__(self, host = '127.0.0.5', port = 22):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = []
        self.host = host
        self.port = port
        self.max_queued = 10
    
    def run (self):
        self.server_socket.bind(('', self.port))
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
        for thread in created_threads:
            thread.join()
    
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
    