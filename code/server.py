import socket
import threading

# Server Configuration
HOST = '127.0.0.1'
PORT = 12345

# dictionary to store connected clients: {username: client_socket}
clients = {}

def handle_client(client_socket):
    """
    Handles a single client connection.
    Receives messages, parses the target user, and forwards the message.
    """
    try:
        # Step 1: Receive the username when a connection identified.
        username = client_socket.recv(1024).decode('utf-8')
        clients[username] = client_socket
        print(f"[NEW CONNECTION] User {username} connected.")
        
        # Step 2: Listen for messages
        while True:
            message = client_socket.recv(1024).decode('utf-8')#recieving a message and decoding it.
            
            # Message format: "targetName:tessagecontent"
            if ':' in message:
                target_name, content = message.split(':', 1)
                
                # Check if the target user even exists
                if target_name in clients:
                    target_socket = clients[target_name]
                    # forwarding the message to the specific target user
                    target_socket.send(f"message from {username}: {content}".encode('utf-8'))
                else:
                    # Notify sender that user was not found (if he is not on the dictionary)
                    client_socket.send(f"[SERVER] User {target_name} not found.".encode('utf-8'))
            else:
                client_socket.send("[SERVER] Invalid format. Use 'Name:Message'".encode('utf-8'))
                
    except Exception as e:
        # if the user we are handling rn is having some kind of disconnection, with intent or without.
        disconnected_user = None
        for name, sock in clients.items():# searching the socket of the disconnected user, by going over all the usernames that are in the dictionary.
            if sock == client_socket:
                disconnected_user = name
                break
        
        if disconnected_user:
            del clients[disconnected_user]
            print(f"[DISCONNECT] User. {disconnected_user} has left the server!")
        
        client_socket.close()

def main():
    """
    Main server loop. Accepts incoming connections and starts threads.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))# giving the server ip and a port, apartment and a building
    server.listen(5) # Allow up to 5 pending connections, hadrisha legabay hamisha mishtamshim.
    print(f"[START] Server is running on {HOST}:{PORT}")# will say on which ip and port server is running

    while True:
        # Accept new connection
        client_socket, address = server.accept() # will create new socket for a new client.
        print(f"[CONNECTION] Request from {address}")# address = (client ip, client port)
        
        # Start a new thread to handle this client specifically
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    main()

