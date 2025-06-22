import tkinter as tk
from tkinter import messagebox
import threading
import irc.client
import pyttsx3

class TwitchTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitch TTS")
        self.engine = pyttsx3.init()

        # Интерфейс
        tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1)

        tk.Label(root, text="Channel:").grid(row=1, column=0, sticky="e")
        self.channel_entry = tk.Entry(root)
        self.channel_entry.grid(row=1, column=1)

        tk.Label(root, text="Access Token (oauth):").grid(row=2, column=0, sticky="e")
        self.token_entry = tk.Entry(root, show="*")
        self.token_entry.grid(row=2, column=1)

        # Переключатель типа сообщений
        self.tts_mode = tk.IntVar(value=0)  # 0 - только за баллы, 1 - все сообщения
        tk.Label(root, text="Тип озвучивания:").grid(row=3, column=0, sticky="e")
        frame = tk.Frame(root)
        frame.grid(row=3, column=1, sticky="w")
        tk.Radiobutton(frame, text="Только за баллы канала", variable=self.tts_mode, value=0).pack(anchor="w")
        tk.Radiobutton(frame, text="Все обычные сообщения", variable=self.tts_mode, value=1).pack(anchor="w")

        self.status_label = tk.Label(root, text="Статус: отключено", fg="red")
        self.status_label.grid(row=4, columnspan=2, pady=10)

        self.connect_button = tk.Button(root, text="Подключиться", command=self.connect_to_twitch)
        self.connect_button.grid(row=5, columnspan=2, pady=10)

        self.client = None
        self.connection = None

    def connect_to_twitch(self):
        username = self.username_entry.get().lower()
        channel = self.channel_entry.get().lower()
        token = 'oauth:' + self.token_entry.get()

        if not username or not channel or not token:
            messagebox.showwarning("Ошибка", "Пожалуйста, заполните все поля")
            return

        self.status_label.config(text="Статус: подключение...", fg="orange")

        threading.Thread(target=self._run_irc, args=(username, channel, token), daemon=True).start()

    def _run_irc(self, username, channel, token):
        try:
            self.client = irc.client.Reactor()
            self.connection = self.client.server().connect(
                "irc.chat.twitch.tv", 6667, username, password=token
            )

            def on_connect(connection, event):
                connection.join(f"#{channel}")
                self.status_label.config(text="Статус: подключено", fg="green")

            def on_disconnect(connection, event):
                self.status_label.config(text="Статус: отключено", fg="red")

            def on_pubmsg(connection, event):
                message = event.arguments[0]
                tags = getattr(event, 'tags', {})

                # Проверяем наличие Channel Points тега
                has_cp = False
                for tag in tags:
                    if tag.get('key') == 'custom-reward-id' and tag.get('value'):
                        has_cp = True
                        break

                # Решаем, озвучивать ли сообщение
                mode = self.tts_mode.get()
                if mode == 0 and not has_cp:
                    return  # озвучиваем только за баллы
                # mode == 1 - озвучиваем все сообщения

                print(f"[TTS] {event.source.nick}: {message}")
                self.engine.say(message)
                self.engine.runAndWait()

            self.connection.add_global_handler("welcome", on_connect)
            self.connection.add_global_handler("disconnect", on_disconnect)
            self.connection.add_global_handler("pubmsg", on_pubmsg)

            self.client.process_forever()
        except Exception as e:
            print("Ошибка подключения:", e)
            self.status_label.config(text="Статус: ошибка подключения", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = TwitchTTSApp(root)
    root.mainloop()
