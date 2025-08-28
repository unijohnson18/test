import tkinter as tk
from tkinter import filedialog, messagebox
import os
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# from dotenv import load_load_dotenv
from dotenv import load_dotenv
import webbrowser
from pathlib import Path
import time
import base64


class AudioProcessorGUI:
    def __init__(self, root):
        load_dotenv()
        self.root = root
        self.root.title("Audio Processor")
        self.root.geometry("600x400")

        # Config
        self.watch_dir = os.getenv('WATCH_DIRECTORY')
        self.output_dir = os.getenv('OUTPUT_DIRECTORY')
        self.api_url = os.getenv('API_URL')

        # GUI elements
        self.setup_gui()

        # Processing flag
        self.processing = False

    def setup_gui(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')

        # Upload button
        self.upload_btn = tk.Button(self.main_frame, text="Загрузить аудио файл",
                                    command=self.upload_file)
        self.upload_btn.pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.main_frame, text="Ожидание загрузки файла")
        self.status_label.pack(pady=10)

        # Links frame
        self.links_frame = tk.Frame(self.main_frame)
        self.links_frame.pack(pady=20)

        # New song button
        self.new_song_btn = tk.Button(self.main_frame, text="Новая песня",
                                      command=self.reset_gui, state='disabled')
        self.new_song_btn.pack(pady=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3;*.wav")]
        )
        if file_path:
            self.process_file(file_path)

    #2

    def process_file(self, file_path):
        self.processing = True
        self.update_gui_state()
        self.status_label.config(text="Ждите - идёт обработка")

        try:
            files = {'audio': open(file_path, 'rb')}
            response = requests.post(
                self.api_url,
                files=files,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if 'audio' in data and 'lyrics' in data:
                    mp3_data = base64.b64decode(data['audio'])
                    txt_data = base64.b64decode(data['lyrics'])
                    self.save_processed_files(mp3_data, txt_data, file_path)
                else:
                    self.status_label.config(text="Ошибка обработки файла")
        except Exception as e:
            print(f"Error: {str(e)}")
            self.status_label.config(text="Ошибка обработки")
        finally:
            self.processing = False
            self.update_gui_state()


    def save_processed_files(self, data, original_file):
        # Create output directory
        file_name = Path(original_file).stem
        output_path = Path(self.output_dir) / file_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Save files and create links
        mp3_path = output_path / "processed.mp3"
        txt_path = output_path / "lyrics.txt"

        with open(mp3_path, 'wb') as f:
            f.write(data['audio'])
        with open(txt_path, 'wb') as f:
            f.write(data['lyrics'])

        self.create_file_links(mp3_path, txt_path)
        self.processing = False
        self.update_gui_state()

    def create_file_links(self, mp3_path, txt_path):
        # Clear previous links
        for widget in self.links_frame.winfo_children():
            widget.destroy()

        # Create new links
        mp3_link = tk.Label(self.links_frame, text="Открыть минусовку",
                            fg="blue", cursor="hand2")
        mp3_link.pack(pady=5)
        mp3_link.bind("<Button-1>", lambda e: webbrowser.open(mp3_path))

        txt_link = tk.Label(self.links_frame, text="Открыть текст песни",
                            fg="blue", cursor="hand2")
        txt_link.pack(pady=5)
        txt_link.bind("<Button-1>", lambda e: webbrowser.open(txt_path))

    def update_gui_state(self):
        if self.processing:
            self.upload_btn.config(state='disabled')
            self.new_song_btn.config(state='disabled')
        else:
            self.upload_btn.config(state='normal')
            self.new_song_btn.config(state='normal')
            self.status_label.config(text="Обработка завершена")

    def reset_gui(self):
        # Clear links
        for widget in self.links_frame.winfo_children():
            widget.destroy()

        self.status_label.config(text="Ожидание загрузки файла")
        self.processing = False
        self.update_gui_state()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioProcessorGUI(root)
    root.mainloop()