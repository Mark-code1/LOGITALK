import base64
import io
import threading
import os
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog
from PIL import Image

set_appearance_mode("dark")

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        
        self.username = self.ask_username() or "Анонім"
        self.geometry('650x550')
        self.title(f"Чат — {self.username}")
        self.configure(fg_color="#121212")

        # --- ГЛАВНЫЙ КОНТЕЙНЕР ---
        self.chat_container = CTkFrame(self, fg_color="transparent")
        self.chat_container.place(x=0, y=0, relwidth=1, relheight=1)

        self.chat_field = CTkScrollableFrame(self.chat_container, fg_color="transparent")
        self.chat_field.pack(pady=(10, 110), padx=(55, 10), fill="both", expand=True)

        # --- ПАНЕЛЬ ЭМОДЗИ ---
        self.emoji_frame = CTkFrame(self, fg_color="#1e1e1e", height=35, corner_radius=10)
        self.emoji_frame.place(relx=0.5, rely=0.82, anchor="center", relwidth=0.7)
        emojis = ["😀", "😂", "😎", "🔥", "👍", "❤️", "🚀", "💀"]
        for emo in emojis:
            btn = CTkButton(self.emoji_frame, text=emo, width=35, fg_color="transparent", 
                            command=lambda e=emo: self.message_entry.insert(END, e))
            btn.pack(side="left", padx=2)

        # --- ПОЛЕ ВВОДА ---
        self.input_frame = CTkFrame(self, fg_color="#1e1e1e", height=60, corner_radius=15)
        self.input_frame.place(relx=0.5, rely=0.92, anchor="center", relwidth=0.85)

        self.message_entry = CTkEntry(self.input_frame, placeholder_text="Напишіть щось...", 
                                      fg_color="transparent", border_width=0)
        self.message_entry.place(relx=0.02, rely=0.5, relwidth=0.75, anchor="w")
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = CTkButton(self.input_frame, text="▲", width=40, fg_color="#ffffff", 
                                  text_color="black", corner_radius=10, command=self.send_message)
        self.send_btn.place(relx=0.98, rely=0.5, anchor="e")

        self.img_btn = CTkButton(self.input_frame, text="📂", width=40, fg_color="#333", 
                                 corner_radius=10, command=self.open_image)
        self.img_btn.place(relx=0.88, rely=0.5, anchor="e")

        # --- БОКОВОЕ МЕНЮ ---
        self.is_show_menu = False
        self.menu_frame = CTkFrame(self, width=45, fg_color="#1e1e1e", corner_radius=0)
        self.menu_frame.place(x=0, y=0, relheight=1)
        
        self.btn = CTkButton(self.menu_frame, text='☰', command=self.toggle_show_menu, 
                             width=45, fg_color="transparent", hover_color="#333333")
        self.btn.pack(pady=15)

        self.menu_content = CTkFrame(self.menu_frame, fg_color="transparent")
        self.name_entry = CTkEntry(self.menu_content, placeholder_text="Новий нік...")
        self.name_entry.pack(pady=10, padx=10)
        CTkButton(self.menu_content, text="Зберегти", fg_color="#333", command=self.change_name).pack(pady=5)

        self.connect_server()

    def ask_username(self):
        dialog = CTkInputDialog(text="Введіть ваш нік:", title="Вхід")
        return dialog.get_input()

    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        target = 180 if self.is_show_menu else 45
        self.animate_menu(target)
        if self.is_show_menu:
            self.menu_content.pack(fill="both", expand=True)
            self.btn.configure(text="✕")
            self.menu_frame.lift()
        else:
            self.menu_content.pack_forget()
            self.btn.configure(text="☰")

    def animate_menu(self, target):
        curr = self.menu_frame.winfo_width()
        if curr != target:
            step = 15 if curr < target else -15
            self.menu_frame.configure(width=curr + step)
            self.after(10, lambda: self.animate_menu(target))

    def change_name(self):
        new = self.name_entry.get().strip()
        if new:
            self.username = new
            self.title(f"Чат — {self.username}")
            self.add_message("Система", f"Нік змінено на: {new}", side="w")

    def connect_server(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except:
            self.add_message("Система", "Сервер офлайн", side="w")

    def add_message(self, author, message, img=None, raw_bytes=None, side=None):
        if not side:
            side = "e" if author == self.username else "w"
        
        color = "#333333" if side == "e" else "#222222"
        anchor = "e" if side == "e" else "w"
        
        outer = CTkFrame(self.chat_field, fg_color="transparent")
        outer.pack(fill="x", pady=5)

        msg_frame = CTkFrame(outer, fg_color=color, corner_radius=15)
        msg_frame.pack(padx=10, anchor=anchor)

        # Если есть картинка, делаем её кнопкой для сохранения
        if img:
            btn_img = CTkButton(msg_frame, text=f"{author}: {message}", image=img, 
                                compound="top", fg_color="transparent", hover_color="#444",
                                command=lambda b=raw_bytes: self.download_image(b))
            btn_img.pack(padx=10, pady=8)
        else:
            lbl = CTkLabel(msg_frame, text=f"{author}: {message}", wraplength=280)
            lbl.pack(padx=12, pady=8)
        
        self.chat_field._parent_canvas.yview_moveto(1.0)

    def download_image(self, b):
        if not b: return
        path = filedialog.asksaveasfilename(defaultextension=".png", 
                                             filetypes=[("Image", "*.png"), ("All files", "*.*")])
        if path:
            with open(path, "wb") as f:
                f.write(b)

    def send_message(self):
        text = self.message_entry.get().strip()
        if text:
            try:
                data = f"TEXT@{self.username}@{text}\n"
                self.sock.sendall(data.encode('utf-8'))
                self.add_message(self.username, text, side="e")
                self.message_entry.delete(0, END)
            except: pass

    def open_image(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, "rb") as f:
                raw = f.read()
                b64 = base64.b64encode(raw).decode()
            data = f"IMAGE@{self.username}@{os.path.basename(path)}@{b64}\n"
            self.sock.sendall(data.encode('utf-8'))
            img = CTkImage(Image.open(path), size=(200, 150))
            self.add_message(self.username, "надіслав фото (клікніть щоб зберегти)", img, raw_bytes=raw, side="e")

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(1024*800)
                if not chunk: break
                buffer += chunk.decode('utf-8', errors='ignore')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line: self.handle_line(line)
            except: break

    def handle_line(self, line):
        try:
            parts = line.split("@", 3)
            if len(parts) < 3: return
            m_type, author, content = parts[0], parts[1], parts[2]
            
            if author != self.username:
                if m_type == "TEXT":
                    self.add_message(author, content, side="w")
                elif m_type == "IMAGE":
                    img_data = base64.b64decode(parts[3])
                    img = CTkImage(Image.open(io.BytesIO(img_data)), size=(200, 150))
                    self.add_message(author, "надіслав фото (клікніть щоб зберегти)", img, raw_bytes=img_data, side="w")
        except: pass

if __name__ == "__main__":
    MainWindow().mainloop()
