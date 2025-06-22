import tkinter as tk
from tkinter import messagebox, ttk
import threading
import irc.client
import pyttsx3
import asyncio
from edge_tts import Communicate
from playsound import playsound
import os
import tempfile
import json
import random

# Фоновой asyncio-loop для edge-tts
class AsyncioThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        t = threading.Thread(target=self.loop.run_forever, daemon=True)
        t.start()

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

async def speak_neural(text: str, voice: str = "ru-RU-DariyaNeural"):
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.close()
        communicate = Communicate(text, voice)
        await communicate.save(tmp.name)
        return tmp.name
    except Exception as e:
        print("TTS Error:", e)
        return None

class TwitchTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitch TTS")
        self.engine = pyttsx3.init()
        self.asyncio_thread = AsyncioThread()

        # Интерфейс
        tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1)

        tk.Label(root, text="Channel:").grid(row=1, column=0, sticky="e")
        self.channel_entry = tk.Entry(root)
        self.channel_entry.grid(row=1, column=1)

        tk.Label(root, text="Access Token с сайта \n twitchtokengenerator.com:").grid(row=2, column=0, sticky="e")
        self.token_entry = tk.Entry(root, show="*")
        self.token_entry.grid(row=2, column=1)

        self.load_config()

        self.tts_mode = tk.IntVar(value=0)
        tk.Label(root, text="Тип озвучивания:").grid(row=3, column=0, sticky="e")
        frame_mode = tk.Frame(root)
        frame_mode.grid(row=3, column=1, sticky="w")
        tk.Radiobutton(frame_mode, text="Только за баллы канала", variable=self.tts_mode, value=0).pack(anchor="w")
        tk.Radiobutton(frame_mode, text="Все сообщения", variable=self.tts_mode, value=1).pack(anchor="w")

        tk.Label(root, text="Голос TTS:").grid(row=4, column=0, sticky="e")
        self.voice_var = tk.StringVar(value="ru-RU-SvetlanaNeural")
        self.voices = [
            "ru-RU-SvetlanaNeural",
            "ru-RU-DmitryNeural",
        ]
        self.voice_combo = ttk.Combobox(root, textvariable=self.voice_var, values=self.voices, state="readonly")
        self.voice_combo.grid(row=4, column=1)

        self.random_voice_var = tk.BooleanVar()
        self.random_voice_check = tk.Checkbutton(root, text="Рандомный голос", variable=self.random_voice_var)
        self.random_voice_check.grid(row=5, column=1, sticky="w")

        self.status_label = tk.Label(root, text="Статус: отключено", fg="red")
        self.status_label.grid(row=6, columnspan=2, pady=10)

        self.connect_button = tk.Button(root, text="Подключиться", command=self.connect_to_twitch)
        self.connect_button.grid(row=7, columnspan=2, pady=10)

        self.client = None
        self.connection = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.username_entry.insert(0, data.get("username", ""))
                self.channel_entry.insert(0, data.get("channel", ""))
                self.token_entry.insert(0, data.get("token", ""))
        except FileNotFoundError:
            pass

    def save_config(self):
        data = {
            "username": self.username_entry.get(),
            "channel": self.channel_entry.get(),
            "token": self.token_entry.get()
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def connect_to_twitch(self):
        username = self.username_entry.get().lower()
        channel = self.channel_entry.get().lower()
        token = 'oauth:' + self.token_entry.get().strip()

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

            def on_connect(conn, event):
                conn.join(f"#{channel}")
                self.status_label.config(text="Статус: подключено", fg="green")

            def on_disconnect(conn, event):
                self.status_label.config(text="Статус: отключено", fg="red")

            def on_pubmsg(conn, event):
                msg = event.arguments[0]
                tags = getattr(event, 'tags', [])
                has_cp = any(t.get('key') == 'custom-reward-id' and t.get('value') for t in tags)

                mode = self.tts_mode.get()
                if mode == 0 and not has_cp:
                    return

                original_msg = msg
                voice = self.voice_var.get()

                if self.random_voice_var.get():
                    voice = random.choice(self.voices)

                msg_lower = msg.lower()
                if msg_lower.startswith("!м ") or msg_lower.startswith("!m "):
                    male_voices = [v for v in self.voices if "dmitry" in v.lower()]
                    if male_voices:
                        voice = random.choice(male_voices)
                    msg = msg[3:].strip()
                elif msg_lower.startswith("!ж ") or msg_lower.startswith("!f "):
                    female_voices = [v for v in self.voices if "svetlana" in v.lower()]
                    if female_voices:
                        voice = random.choice(female_voices)
                    msg = msg[3:].strip()

                future = self.asyncio_thread.run(speak_neural(msg, voice))
                def done_callback(f):
                    path = f.result()
                    if path:
                        playsound(path)
                        os.remove(path)
                    else:
                        self.engine.say(msg)
                        self.engine.runAndWait()
                future.add_done_callback(done_callback)
                print(f"[TTS] {event.source.nick}: {original_msg} -> [{voice}] {msg}")

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
