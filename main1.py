#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания файлов рекламы с FTP сервера
Совместим с Python 3.8+
"""

import os
import re
import logging
import ftplib
from datetime import datetime
from pathlib import Path
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

        first_block_files = []
        second_block_files = []

        # Парсинг для первого блока
        first_block_files = self._extract_reklama_block(lines, FIRST_TIME_MARK)

        # Парсинг для второго блока
        second_block_files = self._extract_reklama_block(lines, SECOND_TIME_MARK)

        logging.info(f"Найдено файлов для первого блока ({FIRST_TIME_MARK}): {len(first_block_files)}")
        logging.info(f"Найдено файлов для второго блока ({SECOND_TIME_MARK}): {len(second_block_files)}")

        return first_block_files, second_block_files

    def _extract_reklama_block(self, lines, time_mark):
        """Извлечение блока рекламы после указанной метки времени"""
        files = []
        start_found = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Проверка на метку времени
            time_match = re.match(r'(\d{2}:\d{2}:\d{2})', line)
            if time_match:
                current_time = time_match.group(1)

                # Если достигли метки времени, начинаем сбор
                if current_time >= time_mark and not start_found:
                    start_found = True

                # Если уже начали сбор, проверяем на REKLAMA
                if start_found:
                    if 'REKLAMA\\' in line:
                        # Извлекаем имя файла
                        filename_match = re.search(r'REKLAMA\\([^\\]+\.wav)', line)
                        if filename_match:
                            filename = filename_match.group(1)
                            files.append(filename)
                    elif files:  # Если файлы уже найдены и путь больше не содержит REKLAMA
                        # Проверяем, что это не просто строка без пути
                        if '\\' in line and 'REKLAMA\\' not in line:
                            break

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

        try:
            # Переход в папку рекламы
            self.ftp.cwd(REKLAMA_PATH)

            for filename in files:
                local_file_path = os.path.join(destination_folder, filename)

                try:
                    # Скачивание файла с замещением
                    with open(local_file_path, 'wb') as local_file:
                        self.ftp.retrbinary(f'RETR {filename}', local_file.write)

                    downloaded_files.append(filename)
                    logging.info(f"Скачан файл: {filename}")

                except Exception as e:
                    logging.error(f"Ошибка скачивания файла {filename}: {e}")

        except Exception as e:
            logging.error(f"Ошибка доступа к папке рекламы: {e}")

        return downloaded_files

    def run(self):
        """Основная функция выполнения скрипта"""
        logging.info("Запуск скрипта скачивания рекламы")

        # Подключение к FTP
        if not self.connect_ftp():
            return

        try:
            # Скачивание плейлиста
            playlist_path = self.download_playlist()
            if not playlist_path:
                return

            # Парсинг плейлиста
            first_block_files, second_block_files = self.parse_playlist(playlist_path)

            # Создание папок назначения
            first_folder, second_folder = self.create_destination_folders()

            # Скачивание файлов первого блока
            if first_block_files:
                logging.info(f"Скачивание файлов первого блока в {first_folder}")
                downloaded_first = self.download_reklama_files(first_block_files, first_folder)
                logging.info(f"Скачано файлов первого блока: {len(downloaded_first)}")

            # Скачивание файлов второго блока
            if second_block_files:
                logging.info(f"Скачивание файлов второго блока в {second_folder}")
                downloaded_second = self.download_reklama_files(second_block_files, second_folder)
                logging.info(f"Скачано файлов второго блока: {len(downloaded_second)}")

            # Удаление временного файла плейлиста
            try:
                os.remove(playlist_path)
            except:
                pass

            logging.info("Скрипт завершен успешно")

        except Exception as e:
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