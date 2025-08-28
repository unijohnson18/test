import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import shutil
from datetime import datetime
import threading
import sys


class GitHubHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Helper - Помощник для работы с Git")
        self.root.geometry("1200x900")
        self.root.configure(bg='#f0f0f0')

        # Переменные
        self.project_path = tk.StringVar()
        self.current_branch = tk.StringVar(value="Не определена")
        self.git_status = tk.StringVar(value="Git не найден")

        self.setup_ui()
        self.check_git_installation()

    def setup_ui(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Заголовок
        title_label = ttk.Label(main_frame, text="GitHub Helper",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 1. Проверка системы
        system_frame = ttk.LabelFrame(main_frame, text="1. Проверка системы",
                                      padding="10")
        system_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E),
                          pady=(0, 10))
        system_frame.columnconfigure(1, weight=1)

        ttk.Label(system_frame, text="Статус Git:").grid(row=0, column=0,
                                                         sticky=tk.W)
        ttk.Label(system_frame, textvariable=self.git_status).grid(row=0, column=1,
                                                                   sticky=tk.W, padx=(10, 0))
        ttk.Button(system_frame, text="Проверить Git",
                   command=self.check_git_installation).grid(row=0, column=2,
                                                             padx=(10, 0))

        # 2. Выбор проекта
        project_frame = ttk.LabelFrame(main_frame, text="2. Выбор проекта",
                                       padding="10")
        project_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E),
                           pady=(0, 10))
        project_frame.columnconfigure(1, weight=1)

        ttk.Label(project_frame, text="Путь к проекту:").grid(row=0, column=0,
                                                              sticky=tk.W)
        ttk.Entry(project_frame, textvariable=self.project_path,
                  width=50).grid(row=0, column=1, sticky=(tk.W, tk.E),
                                 padx=(10, 10))
        ttk.Button(project_frame, text="Выбрать папку",
                   command=self.select_project_folder).grid(row=0, column=2)

        # Информация о проекте
        info_frame = ttk.Frame(project_frame)
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E),
                        pady=(10, 0))
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(info_frame, text="Текущая ветка:").grid(row=0, column=0,
                                                          sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.current_branch).grid(row=0, column=1,
                                                                     sticky=tk.W, padx=(10, 0))
        ttk.Button(info_frame, text="Проверить проект",
                   command=self.check_project).grid(row=0, column=2, padx=(10, 0))

        # 3. Статус файлов
        status_frame = ttk.LabelFrame(main_frame, text="3. Статус файлов проекта",
                                      padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S),
                          pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=1)

        # Кнопка обновления статуса
        ttk.Button(status_frame, text="Обновить статус файлов",
                   command=self.update_file_status).grid(row=0, column=0,
                                                         sticky=tk.W, pady=(0, 10))

        # Список файлов с изменениями
        self.file_tree = ttk.Treeview(status_frame, columns=('status',), height=8)
        self.file_tree.heading('#0', text='Файл')
        self.file_tree.heading('status', text='Статус')
        self.file_tree.column('#0', width=600)
        self.file_tree.column('status', width=150)
        self.file_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar для списка файлов
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL,
                                  command=self.file_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        # 4. Коммит
        commit_frame = ttk.LabelFrame(main_frame, text="4. Коммит изменений",
                                      padding="10")
        commit_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E),
                          pady=(0, 10))
        commit_frame.columnconfigure(1, weight=1)

        # Комментарий к коммиту
        ttk.Label(commit_frame, text="Комментарий:").grid(row=0, column=0,
                                                          sticky=tk.NW, pady=(5, 0))

        self.commit_text = tk.Text(commit_frame, height=3, width=50)
        self.commit_text.grid(row=0, column=1, sticky=(tk.W, tk.E),
                              padx=(10, 10), pady=(0, 10))

        # Автозаполнение комментария
        auto_frame = ttk.Frame(commit_frame)
        auto_frame.grid(row=0, column=2, sticky=tk.N, pady=(5, 0))

        ttk.Button(auto_frame, text="Авто-комментарий",
                   command=self.auto_fill_commit_message).pack(pady=(0, 5))
        ttk.Button(auto_frame, text="Очистить",
                   command=lambda: self.commit_text.delete(1.0, tk.END)).pack()

        # Кнопки коммита
        button_frame = ttk.Frame(commit_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        ttk.Button(button_frame, text="Коммит выбранного файла",
                   command=self.commit_selected_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Коммит всех изменений",
                   command=self.commit_all_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Push в GitHub",
                   command=self.push_to_github).pack(side=tk.LEFT)

        # 5. Консоль вывода
        console_frame = ttk.LabelFrame(main_frame, text="5. Вывод команд и объяснения",
                                       padding="10")
        console_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S),
                           pady=(0, 10))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = scrolledtext.ScrolledText(console_frame, height=10,
                                                 wrap=tk.WORD, state=tk.NORMAL)
        self.console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Делаем консоль только для чтения, но с возможностью копирования
        self.console.bind("<Key>",
                          lambda e: "break" if e.keysym not in ['Control_L', 'Control_R', 'c', 'C', 'a', 'A'] else None)

        # Кнопки управления консолью
        console_buttons_frame = ttk.Frame(console_frame)
        console_buttons_frame.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))

        ttk.Button(console_buttons_frame, text="Очистить консоль",
                   command=self.clear_console).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(console_buttons_frame, text="Копировать всё",
                   command=self.copy_all_console).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(console_buttons_frame, text="Выделить всё",
                   command=self.select_all_console).pack(side=tk.LEFT)

        # Настройка веса для растягивания
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def log_message(self, message, is_command=False):
        """Добавление сообщения в консоль"""
        if is_command:
            self.console.insert(tk.END, f"\n🔧 КОМАНДА: {message}\n", 'command')
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.insert(tk.END, f"[{timestamp}] {message}\n")

        self.console.see(tk.END)
        self.root.update_idletasks()

    def clear_console(self):
        """Очистка консоли"""
        self.console.delete(1.0, tk.END)

    def copy_all_console(self):
        """Копирование всего содержимого консоли в буфер обмена"""
        content = self.console.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Копирование", "Содержимое консоли скопировано в буфер обмена!")

    def select_all_console(self):
        """Выделение всего текста в консоли"""
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)

    def run_git_command(self, command, show_command=True):
        """Выполнение Git команды"""
        if show_command:
            self.log_message(command, is_command=True)

        try:
            if self.project_path.get():
                os.chdir(self.project_path.get())

            result = subprocess.run(command, shell=True, capture_output=True,
                                    text=True, encoding='utf-8')

            if result.returncode == 0:
                if result.stdout.strip():
                    self.log_message(f"✅ Успешно: {result.stdout.strip()}")
                return True, result.stdout.strip()
            else:
                self.log_message(f"❌ Ошибка: {result.stderr.strip()}")
                return False, result.stderr.strip()

        except Exception as e:
            self.log_message(f"❌ Исключение: {str(e)}")
            return False, str(e)

    def check_git_installation(self):
        """Проверка установки Git"""
        self.log_message("📋 ПРОВЕРКА СИСТЕМЫ")
        self.log_message("Объяснение: Проверяем, установлен ли Git в системе")

        success, output = self.run_git_command("git --version")

        if success:
            self.git_status.set(f"✅ {output}")
            self.log_message("Git найден и готов к работе!")
        else:
            self.git_status.set("❌ Git не найден")
            self.log_message("⚠️ Git не найден! Установите Git с https://git-scm.com/")

    def select_project_folder(self):
        """Выбор папки проекта"""
        folder = filedialog.askdirectory(title="Выберите папку с проектом")
        if folder:
            self.project_path.set(folder)
            self.log_message(f"📁 Выбрана папка: {folder}")
            self.check_project()

    def check_project(self):
        """Проверка проекта"""
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        self.log_message("📋 ПРОВЕРКА ПРОЕКТА")
        self.log_message("Объяснение: Проверяем, является ли папка Git-репозиторием")

        # Проверяем, является ли папка Git репозиторием
        success, output = self.run_git_command("git status")

        if success:
            self.log_message("✅ Это валидный Git репозиторий!")

            # Получаем текущую ветку
            success, branch = self.run_git_command("git branch --show-current", False)
            if success and branch:
                self.current_branch.set(f"✅ {branch}")
                self.log_message(f"Текущая ветка: {branch}")

            self.update_file_status()
        else:
            self.current_branch.set("❌ Не Git репозиторий")
            self.log_message("❌ Это не Git репозиторий!")

            # Предлагаем инициализировать
            result = messagebox.askyesno("Инициализация",
                                         "Это не Git репозиторий. Хотите инициализировать?")
            if result:
                self.init_repository()

    def init_repository(self):
        """Инициализация Git репозитория"""
        self.log_message("🚀 ИНИЦИАЛИЗАЦИЯ РЕПОЗИТОРИЯ")
        self.log_message("Объяснение: Создаем новый Git репозиторий в выбранной папке")

        success, output = self.run_git_command("git init")

        if success:
            self.log_message("✅ Репозиторий успешно инициализирован!")
            self.current_branch.set("✅ main (новый)")

            # Создаем .gitignore если его нет
            gitignore_path = os.path.join(self.project_path.get(), '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write("# Игнорируемые файлы\n__pycache__/\n*.pyc\n.env\n.vscode/\n")
                self.log_message("📄 Создан файл .gitignore с базовыми настройками")

            self.update_file_status()

    def update_file_status(self):
        """Обновление статуса файлов"""
        if not self.project_path.get():
            return

        self.log_message("📋 ОБНОВЛЕНИЕ СТАТУСА ФАЙЛОВ")
        self.log_message("Объяснение: Проверяем какие файлы изменены, добавлены или удалены")

        # Очищаем дерево
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        success, output = self.run_git_command("git status --porcelain", False)

        if success and output:
            lines = output.strip().split('\n')
            for line in lines:
                if len(line) >= 3:
                    status_code = line[:2]
                    filename = line[3:]

                    # Расшифровка статуса
                    status_text = self.decode_git_status(status_code)

                    self.file_tree.insert('', 'end', text=filename,
                                          values=(status_text,))

            self.log_message(f"📊 Найдено {len(lines)} файлов с изменениями")
        else:
            self.log_message("✅ Нет изменений в рабочей директории")

    def decode_git_status(self, code):
        """Расшифровка кодов статуса Git"""
        status_map = {
            'M ': 'Изменен (staged)',
            ' M': 'Изменен',
            'A ': 'Добавлен (staged)',
            ' A': 'Добавлен',
            'D ': 'Удален (staged)',
            ' D': 'Удален',
            '??': 'Не отслеживается',
            'R ': 'Переименован',
            'C ': 'Скопирован',
            'U ': 'Конфликт',
        }
        return status_map.get(code, f'Неизвестно ({code})')

    def auto_fill_commit_message(self):
        """Автоматическое заполнение комментария"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M")

        # Получаем статистику изменений
        success, output = self.run_git_command("git diff --stat", False)

        if success and output:
            lines = output.strip().split('\n')
            files_changed = len([l for l in lines if '|' in l])
            message = f"Обновление от {date_str} - изменено файлов: {files_changed}"
        else:
            message = f"Автоматический коммит от {date_str}"

        self.commit_text.delete(1.0, tk.END)
        self.commit_text.insert(1.0, message)

        self.log_message(f"📝 Автоматически заполнен комментарий: {message}")

    def commit_selected_file(self):
        """Коммит выбранного файла"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите файл для коммита!")
            return

        filename = self.file_tree.item(selection[0])['text']
        commit_message = self.commit_text.get(1.0, tk.END).strip()

        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите комментарий к коммиту!")
            return

        self.log_message(f"📤 КОММИТ ФАЙЛА: {filename}")
        self.log_message("Объяснение: Добавляем файл в staging area и создаем коммит")

        # Добавляем файл
        success, output = self.run_git_command(f'git add "{filename}"')

        if success:
            # Создаем коммит
            success, output = self.run_git_command(f'git commit -m "{commit_message}"')

            if success:
                self.log_message(f"✅ Файл {filename} успешно закоммичен!")
                self.update_file_status()
                messagebox.showinfo("Успех", f"Файл {filename} успешно закоммичен!")
            else:
                self.log_message(f"❌ Ошибка при коммите: {output}")

    def commit_all_changes(self):
        """Коммит всех изменений"""
        commit_message = self.commit_text.get(1.0, tk.END).strip()

        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите комментарий к коммиту!")
            return

        self.log_message("📤 КОММИТ ВСЕХ ИЗМЕНЕНИЙ")
        self.log_message("Объяснение: Добавляем все измененные файлы и создаем коммит")

        # Добавляем все файлы
        success, output = self.run_git_command("git add .")

        if success:
            # Создаем коммит
            success, output = self.run_git_command(f'git commit -m "{commit_message}"')

            if success:
                self.log_message("✅ Все изменения успешно закоммичены!")
                self.update_file_status()
                messagebox.showinfo("Успех", "Все изменения успешно закоммичены!")
            else:
                self.log_message(f"❌ Ошибка при коммите: {output}")

    def push_to_github(self):
        """Отправка изменений в GitHub"""
        result = messagebox.askyesno("Подтверждение",
                                     "Отправить изменения в удаленный репозиторий GitHub?")

        if not result:
            return

        self.log_message("🚀 ОТПРАВКА В GITHUB")
        self.log_message("Объяснение: Отправляем локальные коммиты в удаленный репозиторий")

        # Получаем текущую ветку
        success, branch = self.run_git_command("git branch --show-current", False)

        if success and branch:
            # Push в удаленный репозиторий
            success, output = self.run_git_command(f"git push origin {branch}")

            if success:
                self.log_message("✅ Изменения успешно отправлены в GitHub!")
                messagebox.showinfo("Успех", "Изменения успешно отправлены в GitHub!")
            else:
                self.log_message(f"❌ Ошибка при отправке: {output}")
                if "No such remote 'origin'" in output:
                    self.log_message("💡 Подсказка: Добавьте удаленный репозиторий командой:")
                    self.log_message("git remote add origin https://github.com/username/repository.git")


def main():
    root = tk.Tk()
    app = GitHubHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()