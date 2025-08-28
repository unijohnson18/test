#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания файлов рекламы с FTP сервера
Совместим с Python 3.7+
v1
"""

import os
import re
import logging
import ftplib
from datetime import datetime

try:
    from pathlib import Path
except ImportError:
    # Для случая, если pathlib недоступен (очень старые версии Python)
    import os


    class Path:
        def __init__(self, path):
            self.path = path

        def mkdir(self, parents=False, exist_ok=False):
            if not os.path.exists(self.path):
                if parents:
                    os.makedirs(self.path)
                else:
                    os.mkdir(self.path)
            elif not exist_ok and os.path.exists(self.path):
                raise FileExistsError(f"Directory '{self.path}' already exists")

from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройки из .env файла
FTP_HOST = os.getenv('FTP_HOST')
FTP_LOGIN = os.getenv('FTP_LOGIN')
FTP_PASSWORD = os.getenv('FTP_PASSWORD')
PLAYLIST_PATH = os.getenv('PLAYLIST_PATH', '/_region/Playlists/digiton/')
REKLAMA_PATH = os.getenv('REKLAMA_PATH', '/_region/REKLAMA/')
FIRST_TIME_MARK = os.getenv('FIRST_TIME_MARK', '12:47:00')
SECOND_TIME_MARK = os.getenv('SECOND_TIME_MARK', '19:47:00')
DESTINATION_FOLDER = os.getenv('DESTINATION_FOLDER', r'D:\_on-air\datcha\09_FEDERAL_RECLAMA\ФАЙЛЫ_ФР\\')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ftp_reklama.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class FTPReklamaDownloader:
    def __init__(self):
        self.ftp = None
        self.current_date = datetime.now().strftime('%Y%m%d')

    def connect_ftp(self):
        """Подключение к FTP серверу"""
        try:
            self.ftp = ftplib.FTP(FTP_HOST)
            self.ftp.login(FTP_LOGIN, FTP_PASSWORD)
            logging.info(f"Успешное подключение к FTP серверу {FTP_HOST}")
            return True
        except Exception as e:
            logging.error(f"Ошибка подключения к FTP: {e}")
            return False

    def disconnect_ftp(self):
        """Отключение от FTP сервера"""
        if self.ftp:
            try:
                self.ftp.quit()
                logging.info("Отключение от FTP сервера")
            except:
                self.ftp.close()

    def download_playlist(self):
        """Скачивание плейлиста с текущей датой"""
        playlist_filename = f"{self.current_date}.txt"
        local_playlist_path = os.path.join(os.getcwd(), playlist_filename)

        try:
            # Переход в папку плейлистов
            self.ftp.cwd(PLAYLIST_PATH)

            # Скачивание файла
            with open(local_playlist_path, 'wb') as local_file:
                self.ftp.retrbinary(f'RETR {playlist_filename}', local_file.write)

            logging.info(f"Плейлист {playlist_filename} успешно скачан")
            return local_playlist_path

        except Exception as e:
            logging.error(f"Ошибка скачивания плейлиста {playlist_filename}: {e}")
            return None

    def parse_playlist(self, playlist_path):
        """Парсинг плейлиста для извлечения файлов рекламы"""
        try:
            with open(playlist_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            try:
                with open(playlist_path, 'r', encoding='cp1251') as file:
                    lines = file.readlines()
            except:
                with open(playlist_path, 'r', encoding='latin-1') as file:
                    lines = file.readlines()

        print(f"Всего строк в плейлисте: {len(lines)}")
        logging.info(f"Всего строк в плейлисте: {len(lines)}")

        first_block_files = []
        second_block_files = []

        # Парсинг для первого блока
        print(f"\n=== ПОИСК ПЕРВОГО БЛОКА после {FIRST_TIME_MARK} ===")
        first_block_files = self._extract_reklama_block(lines, FIRST_TIME_MARK, "ПЕРВЫЙ")

        # Парсинг для второго блока
        print(f"\n=== ПОИСК ВТОРОГО БЛОКА после {SECOND_TIME_MARK} ===")
        second_block_files = self._extract_reklama_block(lines, SECOND_TIME_MARK, "ВТОРОЙ")

        print(f"\nРЕЗУЛЬТАТ ПАРСИНГА:")
        print(f"Найдено файлов для первого блока ({FIRST_TIME_MARK}): {len(first_block_files)}")
        print(f"Файлы первого блока: {first_block_files}")
        print(f"Найдено файлов для второго блока ({SECOND_TIME_MARK}): {len(second_block_files)}")
        print(f"Файлы второго блока: {second_block_files}")

        logging.info(f"Найдено файлов для первого блока ({FIRST_TIME_MARK}): {len(first_block_files)}")
        logging.info(f"Файлы первого блока: {first_block_files}")
        logging.info(f"Найдено файлов для второго блока ({SECOND_TIME_MARK}): {len(second_block_files)}")
        logging.info(f"Файлы второго блока: {second_block_files}")

        return first_block_files, second_block_files

    def _extract_reklama_block(self, lines, time_mark, block_name):
        """Извлечение блока рекламы после указанной метки времени"""
        files = []
        start_found = False
        jingles_found = False
        reklama_started = False

        print(f"\nПоиск блока {block_name} после времени {time_mark}")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Проверка на метку времени
            time_match = re.match(r'(\d{2}:\d{2}:\d{2})', line)
            if time_match:
                current_time = time_match.group(1)

                # Если достигли метки времени, начинаем поиск
                if current_time >= time_mark and not start_found:
                    start_found = True
                    print(f"Найдена стартовая метка времени: {current_time} (строка {i + 1})")

                # Если уже начали поиск
                if start_found:
                    print(f"Анализ строки {i + 1}: {current_time} - {line}")

                    # Ищем строку с JINGLES
                    if 'JINGLES\\' in line or 'JINGLES/' in line:
                        jingles_found = True
                        print(f"Найдена строка с JINGLES в строке {i + 1}: {line}")
                        continue

                    # После найденной строки с JINGLES ищем файлы REKLAMA
                    if jingles_found and ('REKLAMA\\' in line or 'REKLAMA/' in line):
                        if not reklama_started:
                            reklama_started = True
                            print(f"Начало блока REKLAMA после JINGLES в строке {i + 1}")

                        # Извлекаем имя файла (различные варианты путей)
                        filename_match = re.search(r'REKLAMA[\\\/]([^\\\/]+\.wav)', line)
                        if filename_match:
                            filename = filename_match.group(1)
                            files.append(filename)
                            print(f"Найден файл: {filename}")
                        else:
                            print(f"Не удалось извлечь имя файла из строки: {line}")

                    # Если уже нашли файлы рекламы и встретили строку без REKLAMA (конец блока)
                    elif reklama_started and ('\\' in line or '/' in line) and 'REKLAMA' not in line:
                        print(f"Конец блока REKLAMA в строке {i + 1}: {line}")
                        break

                    # Если прошло слишком много времени после метки (например, более 30 минут)
                    elif start_found:
                        time_parts = current_time.split(':')
                        mark_parts = time_mark.split(':')
                        current_minutes = int(time_parts[0]) * 60 + int(time_parts[1])
                        mark_minutes = int(mark_parts[0]) * 60 + int(mark_parts[1])

                        if current_minutes - mark_minutes > 30:  # Более 30 минут прошло
                            print(f"Прошло более 30 минут после метки времени, завершаем поиск")
                            break

        print(f"Найдено файлов в блоке {block_name}: {len(files)}")
        if not jingles_found:
            print(f"ВНИМАНИЕ: Строка с JINGLES не найдена в блоке {block_name}")
        return files

    def create_destination_folders(self):
        """Создание папок назначения"""
        first_hour = FIRST_TIME_MARK.split(':')[0] + 'h'
        second_hour = SECOND_TIME_MARK.split(':')[0] + 'h'

        first_folder = os.path.join(DESTINATION_FOLDER, self.current_date, first_hour)
        second_folder = os.path.join(DESTINATION_FOLDER, self.current_date, second_hour)

        Path(first_folder).mkdir(parents=True, exist_ok=True)
        Path(second_folder).mkdir(parents=True, exist_ok=True)

        return first_folder, second_folder

    def download_reklama_files(self, files, destination_folder):
        """Скачивание файлов рекламы"""
        downloaded_files = []

        print(f"Скачивание {len(files)} файлов в папку: {destination_folder}")

        try:
            # Переход в папку рекламы
            self.ftp.cwd(REKLAMA_PATH)
            print(f"Переход в папку рекламы: {REKLAMA_PATH}")

            for i, filename in enumerate(files, 1):
                local_file_path = os.path.join(destination_folder, filename)

                print(f"Скачивание файла {i}/{len(files)}: {filename}")

                try:
                    # Скачивание файла с замещением
                    with open(local_file_path, 'wb') as local_file:
                        self.ftp.retrbinary(f'RETR {filename}', local_file.write)

                    downloaded_files.append(filename)
                    print(f"✓ Успешно скачан: {filename}")
                    logging.info(f"Скачан файл: {filename}")

                except Exception as e:
                    print(f"✗ Ошибка скачивания файла {filename}: {e}")
                    logging.error(f"Ошибка скачивания файла {filename}: {e}")

        except Exception as e:
            print(f"Ошибка доступа к папке рекламы {REKLAMA_PATH}: {e}")
            logging.error(f"Ошибка доступа к папке рекламы: {e}")

        return downloaded_files

    def run(self):
        """Основная функция выполнения скрипта"""
        print("=== ЗАПУСК СКРИПТА СКАЧИВАНИЯ РЕКЛАМЫ ===")
        logging.info("Запуск скрипта скачивания рекламы")

        print(f"Текущая дата: {self.current_date}")
        print(f"Первая метка времени: {FIRST_TIME_MARK}")
        print(f"Вторая метка времени: {SECOND_TIME_MARK}")
        print(f"Папка назначения: {DESTINATION_FOLDER}")

        # Подключение к FTP
        if not self.connect_ftp():
            return

        try:
            # Скачивание плейлиста
            print(f"\nСкачивание плейлиста {self.current_date}.txt...")
            playlist_path = self.download_playlist()
            if not playlist_path:
                return

            # Показываем первые 100 строк плейлиста для отладки
            print(f"\n=== ПЕРВЫЕ 100 СТРОК ПЛЕЙЛИСТА ===")
            try:
                with open(playlist_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    for i, line in enumerate(lines[:100]):
                        print(f"{i + 1:3d}: {line.strip()}")
                        if 'JINGLES' in line:
                            print(f"     ^^^ JINGLES найден в строке {i + 1}")
                        if 'REKLAMA' in line:
                            print(f"     ^^^ REKLAMA найдена в строке {i + 1}")
            except:
                print("Ошибка чтения файла для предварительного просмотра")

            # Парсинг плейлиста
            print(f"\n=== ПАРСИНГ ПЛЕЙЛИСТА ===")
            first_block_files, second_block_files = self.parse_playlist(playlist_path)

            # Создание папок назначения
            first_folder, second_folder = self.create_destination_folders()
            print(f"\nПапки назначения:")
            print(f"Первый блок: {first_folder}")
            print(f"Второй блок: {second_folder}")

            # Скачивание файлов первого блока
            if first_block_files:
                print(f"\n=== СКАЧИВАНИЕ ПЕРВОГО БЛОКА ===")
                logging.info(f"Скачивание файлов первого блока в {first_folder}")
                downloaded_first = self.download_reklama_files(first_block_files, first_folder)
                print(f"Скачано файлов первого блока: {len(downloaded_first)}")
                logging.info(f"Скачано файлов первого блока: {len(downloaded_first)}")
            else:
                print("Нет файлов для скачивания в первом блоке")

            # Скачивание файлов второго блока
            if second_block_files:
                print(f"\n=== СКАЧИВАНИЕ ВТОРОГО БЛОКА ===")
                logging.info(f"Скачивание файлов второго блока в {second_folder}")
                downloaded_second = self.download_reklama_files(second_block_files, second_folder)
                print(f"Скачано файлов второго блока: {len(downloaded_second)}")
                logging.info(f"Скачано файлов второго блока: {len(downloaded_second)}")
            else:
                print("Нет файлов для скачивания во втором блоке")

            # Удаление временного файла плейлиста
            try:
                os.remove(playlist_path)
                print(f"\nВременный файл плейлиста удален: {playlist_path}")
            except:
                print(f"Не удалось удалить временный файл: {playlist_path}")

            print("\n=== СКРИПТ ЗАВЕРШЕН УСПЕШНО ===")
            logging.info("Скрипт завершен успешно")

        except Exception as e:
            print(f"\nОБЩАЯ ОШИБКА: {e}")
            logging.error(f"Общая ошибка выполнения скрипта: {e}")

        finally:
            # Отключение от FTP
            self.disconnect_ftp()


def main():
    """Главная функция"""
    # Проверка обязательных переменных окружения
    if not all([FTP_HOST, FTP_LOGIN, FTP_PASSWORD]):
        logging.error("Не все обязательные переменные окружения установлены в .env файле")
        logging.error("Требуются: FTP_HOST, FTP_LOGIN, FTP_PASSWORD")
        return

    downloader = FTPReklamaDownloader()
    downloader.run()


if __name__ == "__main__":
    main()