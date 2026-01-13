import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

# Connection Configuration
HOST = '127.0.0.1'
PORT = 12345


class ChatClient:
    """
    A small WhatsApp-inspired GUI client that communicates with the TCP server.
    """

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("PyChat Messenger")
        self.master.geometry("520x640")
        self.master.configure(bg="#f0f2f5")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.client_socket = None
        self.username = None
        self.connected = False
        self.message_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        style = ttk.Style()
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TitleLabel.TLabel", font=("Helvetica", 16, "bold"))

        main_frame = ttk.Frame(master, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        header = ttk.Label(main_frame, text="PyChat Messenger", style="TitleLabel.TLabel")
        header.grid(row=0, column=0, columnspan=2, sticky="w")

        self.chat_display = ScrolledText(main_frame, state="disabled", wrap=tk.WORD, height=20, bg="white")
        self.chat_display.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 8))
        self.chat_display.tag_configure("system", foreground="#0a7cff")
        self.chat_display.tag_configure("incoming", foreground="#1f2328")
        self.chat_display.tag_configure("outgoing", foreground="#128c7e")

        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Send to:").grid(row=2, column=0, sticky="w")
        self.target_var = tk.StringVar()
        self.target_entry = ttk.Entry(main_frame, textvariable=self.target_var)
        self.target_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.message_entry = tk.Text(main_frame, height=4, wrap=tk.WORD, bg="white", fg="#1f2328")
        self.message_entry.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.message_entry.bind("<Return>", self.handle_send_event)
        self.message_entry.bind("<Shift-Return>", self.insert_newline)

        self.send_button = ttk.Button(main_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=5, column=1, sticky="e", pady=(10, 0))

        self.master.after(50, self.prompt_username)
        self.master.after(100, self.process_incoming_messages)

    def prompt_username(self) -> None:
        """
        Prompt user for a username before connecting to the server.
        """
        while not self.username:
            username = simpledialog.askstring("Join Chat", "Choose a username:", parent=self.master)
            if username is None:
                self.master.destroy()
                return
            username = username.strip()
            if not username:
                messagebox.showinfo("Username required", "Please pick a non-empty username.")
                continue

            self.connect_to_server(username)

    def connect_to_server(self, username: str) -> None:
        """
        Open the socket connection and announce the username to the server.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(username.encode('utf-8'))
            self.username = username
            self.connected = True
            self.queue_message(f"[SERVER] Connected as {username}.", "system")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except OSError as exc:
            messagebox.showerror("Connection failed", f"Unable to connect to server:\n{exc}")
            self.master.destroy()

    def process_incoming_messages(self) -> None:
        """
        Pull messages off the queue and render them inside the chat window.
        """
        try:
            while True:
                text, tag = self.message_queue.get_nowait()
                self.chat_display.configure(state="normal")
                self.chat_display.insert(tk.END, text + "\n", tag)
                self.chat_display.configure(state="disabled")
                self.chat_display.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.process_incoming_messages)

    def queue_message(self, text: str, tag: str) -> None:
        self.message_queue.put((text, tag))

    def receive_messages(self) -> None:
        """
        Runs in a background thread, listening for new messages from the server.
        """
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.queue_message(message, "incoming")
            except OSError:
                break

        self.connected = False
        self.queue_message("[SERVER] Connection lost.", "system")

    def handle_send_event(self, event: tk.Event) -> str:
        self.send_message()
        return "break"

    def insert_newline(self, event: tk.Event) -> str:
        self.message_entry.insert(tk.INSERT, "\n")
        return "break"

    def send_message(self) -> None:
        """
        Send the composed message to the selected recipient through the server.
        """
        if not self.connected or not self.client_socket:
            messagebox.showwarning("Not connected", "You are not connected to the server.")
            return

        target = self.target_var.get().strip()
        content = self.message_entry.get("1.0", tk.END).strip()

        if not target:
            messagebox.showinfo("Missing recipient", "Please enter the username you want to message.")
            return
        if not content:
            return

        try:
            payload = f"{target}:{content}"
            self.client_socket.send(payload.encode('utf-8'))
            self.queue_message(f"You → {target}: {content}", "outgoing")
            self.message_entry.delete("1.0", tk.END)
        except OSError:
            messagebox.showerror("Send failed", "Lost connection to the server.")
            self.connected = False

    def on_close(self) -> None:
        """
        Close socket cleanly when the window is closed.
        """
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except OSError:
                pass
        self.master.destroy()


def main() -> None:
    root = tk.Tk()
    ChatClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
