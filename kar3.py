import tkinter as tk
from tkinter import filedialog, messagebox
import os
from dotenv import load_dotenv
import requests
import base64
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('karaoke_client.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('karaoke_client')


class AudioProcessorGUI:
    def __init__(self, root):
        # Загружаем переменные окружения
        load_dotenv()
        self.root = root
        self.root.title("Караоке процессор")
        self.root.geometry("400x400")

        # Загружаем конфигурацию из .env
        self.output_dir = os.getenv('OUTPUT_DIRECTORY')
        self.api_url = os.getenv('API_URL')

        logger.info(f"Инициализация с выходной директорией: {self.output_dir}")
        logger.info(f"API URL: {self.api_url}")

        # Проверяем наличие необходимых директорий
        self.check_directories()

        # Настраиваем интерфейс
        self.setup_gui()

        # Флаг обработки
        self.processing = False

    def check_directories(self):
        """Проверяет наличие необходимых директорий"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info("Директории проверены и созданы")
        except Exception as e:
            logger.error(f"Ошибка при создании директорий: {e}")
            messagebox.showerror(
                "Ошибка",
                "Не удалось создать необходимые директории"
            )

    def setup_gui(self):
        """Настройка графического интерфейса"""
        # Основная рамка
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')

        # Кнопка загрузки
        self.upload_btn = tk.Button(
            self.main_frame,
            text="Загрузить аудио файл",
            command=self.upload_file,
            width=20,
            height=2
        )
        self.upload_btn.pack(pady=10)

        # Статус
        self.status_label = tk.Label(
            self.main_frame,
            text="Ожидание загрузки файла",
            wraplength=350
        )
        self.status_label.pack(pady=10)

        # Прогресс обработки
        self.progress_label = tk.Label(
            self.main_frame,
            text="",
            wraplength=350
        )
        self.progress_label.pack(pady=5)

        # Ссылки на файлы
        self.links_frame = tk.Frame(self.main_frame)
        self.links_frame.pack(pady=10)

        # Кнопка настроек
        self.settings_btn = tk.Button(
            self.main_frame,
            text="Настройки",
            command=self.show_settings,
            width=15
        )
        self.settings_btn.pack(side="bottom", pady=10)

    def upload_file(self):
        """Обработчик загрузки файла"""
        try:
            file_path = filedialog.askopenfilename(
                title="Выберите аудио файл",
                filetypes=[("Аудио файлы", "*.mp3;*.wav")]
            )
            if file_path:
                logger.info(f"Выбран файл: {file_path}")
                self.process_file(file_path)
            else:
                logger.info("Выбор файла отменён")
        except Exception as e:
            logger.error(f"Ошибка при выборе файла: {e}")
            self.show_error("Ошибка при выборе файла")

    def process_file(self, file_path):
        """Обработка файла и отправка на сервер"""
        self.processing = True
        self.update_gui_state("Ждите, идёт создание минусовки...")

        try:
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50 MB
                raise ValueError("Файл слишком большой (максимум 50 MB)")

            # Отправляем файл
            with open(file_path, 'rb') as audio_file:
                files = {'audio': (os.path.basename(file_path), audio_file)}
                logger.info(f"Отправка файла на сервер: {file_path}")

                response = requests.post(
                    self.api_url,
                    files=files,
                    timeout=120  # Увеличенный таймаут
                )

            if response.status_code == 200:
                data = response.json()
                if 'audio' in data and 'lyrics' in data:
                    self.handle_server_response(data, file_path)
                else:
                    raise ValueError("Неверный формат ответа от сервера")
            else:
                raise requests.exceptions.RequestException(
                    f"Ошибка сервера: {response.status_code}"
                )

        except requests.exceptions.Timeout:
            logger.error("Превышено время ожидания ответа от сервера")
            self.show_error("Превышено время ожидания ответа от сервера")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сетевого запроса: {e}")
            self.show_error(f"Ошибка связи с сервером: {str(e)}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            self.show_error(f"Неожиданная ошибка: {str(e)}")
        finally:
            self.processing = False
            self.update_gui_state()

    def handle_server_response(self, data, original_file):
        """Обработка ответа от сервера"""
        try:
            # Декодируем данные
            mp3_data = base64.b64decode(data['audio'])
            txt_data = base64.b64decode(data['lyrics'])

            # Сохраняем файлы
            file_name = Path(original_file).stem
            output_path = Path(self.output_dir) / file_name
            output_path.mkdir(parents=True, exist_ok=True)

            # Сохраняем MP3
            mp3_path = output_path / f"{file_name}_processed.mp3"
            with open(mp3_path, 'wb') as f:
                f.write(mp3_data)
            logger.info(f"MP3 файл сохранен: {mp3_path}")

            # Сохраняем текст
            txt_path = output_path / f"{file_name}_lyrics.txt"
            with open(txt_path, 'wb') as f:
                f.write(txt_data)
            logger.info(f"TXT файл сохранен: {txt_path}")

            # Обновляем интерфейс с ссылками
            self.show_links(mp3_path, txt_path)

        except Exception as e:
            logger.error(f"Ошибка при сохранении файлов: {e}")
            self.show_error("Ошибка при сохранении файлов")

    def show_links(self, mp3_path, txt_path):
        """Отображение ссылок на обработанные файлы"""
        for widget in self.links_frame.winfo_children():
            widget.destroy()

        mp3_link = tk.Label(
            self.links_frame, text="Текст песни", fg="blue", cursor="hand2"
        )
        mp3_link.pack(pady=5)
        mp3_link.bind("<Button-1>", lambda e: os.startfile(txt_path))

        txt_link = tk.Label(
            self.links_frame, text="Аудиофайл", fg="blue", cursor="hand2"
        )
        txt_link.pack(pady=5)
        txt_link.bind("<Button-1>", lambda e: os.startfile(mp3_path))

    def show_error(self, message):
        """Показ сообщения об ошибке"""
        logger.error(message)
        self.status_label.config(text="Ошибка")
        self.progress_label.config(text=message, fg="red")
        messagebox.showerror("Ошибка", message)

    def update_gui_state(self, progress_message=None):
        """Обновление состояния интерфейса"""
        if self.processing:
            self.upload_btn.config(state='disabled')
            if progress_message:
                self.progress_label.config(text=progress_message)
        else:
            self.upload_btn.config(state='normal')

    def show_settings(self):
        """Показать настройки из .env"""
        settings = f"OUTPUT_DIRECTORY: {self.output_dir}\nAPI_URL: {self.api_url}"
        messagebox.showinfo("Настройки", settings)


if __name__ == "__main__":
    try:
        logger.info("Запуск приложения")
        root = tk.Tk()
        app = AudioProcessorGUI(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {e}")
