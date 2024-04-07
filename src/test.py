import socket
import sys

def ftp_client():
    # Establecer la dirección y el puerto del servidor FTP
    host = input("Ingrese la dirección del servidor FTP: ")
    port = 21

    # Crear el socket FTP
    ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ftp_socket.connect((host, port))

    # Recibir y mostrar el mensaje de bienvenida del servidor
    print(ftp_socket.recv(1024).decode())

    # Autenticarse en el servidor FTP
    username = input("Ingrese el nombre de usuario: ")
    ftp_socket.sendall(f"USER {username}\r\n".encode())
    print(ftp_socket.recv(1024).decode())

    password = input("Ingrese la contraseña: ")
    ftp_socket.sendall(f"PASS {password}\r\n".encode())
    print(ftp_socket.recv(1024).decode())

    

    while True:
        # Leer el comando del usuario
        command = input("Ingrese un comando (LIST, RETR, STOR, QUIT): ")

        if command == "LIST":
            # Enviar el comando LIST al servidor
            ftp_socket.sendall(b"LIST\r\n")

            # Recibir y mostrar la lista de archivos del servidor
            file_list = ftp_socket.recv(4096).decode()
            print(file_list)
            
        elif command == "RETR":
            # Leer el nombre del archivo a descargar
            filename = input("Ingrese el nombre del archivo a descargar: ")

            # Enviar el comando RETR al servidor
            ftp_socket.sendall(f"RETR {filename}\r\n".encode())

            # Recibir y guardar el archivo en el cliente
            file_data = b""
            while True:
                data = ftp_socket.recv(1024)
                if not data:
                    break
                file_data += data

            with open(filename, "wb") as file:
                file.write(file_data)

            print(f"Archivo {filename} descargado correctamente.")

        elif command == "STOR":
            # Leer el nombre del archivo a subir
            filename = input("Ingrese el nombre del archivo a subir: ")

            # Enviar el comando STOR al servidor
            ftp_socket.sendall(f"STOR {filename}\r\n".encode())

            # Leer el archivo y enviarlo al servidor
            with open(filename, "rb") as file:
                ftp_socket.sendall(file.read())

            print(f"Archivo {filename} subido correctamente.")

        elif command == "QUIT":
            # Enviar el comando QUIT al servidor
            ftp_socket.sendall(b"QUIT\r\n")

            # Recibir y mostrar la respuesta del servidor
            print(ftp_socket.recv(1024).decode())

            # Cerrar la conexión
            ftp_socket.close()
            break

        else:
            print("Comando inválido.")

if __name__ == "__main__":
    ftp_client()