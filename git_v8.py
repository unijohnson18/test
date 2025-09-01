# git_v8.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import shutil
from datetime import datetime
import threading
import sys
import webbrowser
import json


class GitHubHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Helper - Помощник для работы с Git")
        # Устанавливаем начальный размер, но разрешаем изменение
        self.root.geometry("1400x900")  # Уменьшено с 1400x700
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(1200, 800)  # Минимальный размер

        # Переменные
        self.project_path = tk.StringVar()
        self.current_branch = tk.StringVar(value="Не определена")
        self.git_status = tk.StringVar(value="Git не найден")
        self.remote_info = tk.StringVar(value="Не подключен")
        self.user_info = tk.StringVar(value="Не настроен")
        self.connection_status = tk.StringVar(value="❌ Репозиторий не подключен")

        # Загружаем команды Git из JSON
        self.git_commands = self.load_git_commands()

        # Создаём прокручиваемый фрейм для левой части
        self.setup_scrollable_ui()

    def load_git_commands(self):
        """Загружает список команд Git из JSON файла или создает его если не существует"""
        commands_file = "git_commands.json"
        default_commands = {
            "Основные команды": {
                "git status": "Показать статус репозитория (измененные файлы)",
                "git log --oneline -10": "Показать последние 10 коммитов",
                "git branch": "Показать все ветки",
                "git branch --show-current": "Показать текущую ветку",
                "git remote -v": "Показать удаленные репозитории"
            },
            "Работа с файлами": {
                "git add .": "Добавить все измененные файлы в индекс",
                "git add [filename]": "Добавить конкретный файл в индекс",
                "git reset HEAD [filename]": "Убрать файл из индекса",
                "git checkout -- [filename]": "Отменить изменения в файле",
                "git rm [filename]": "Удалить файл из репозитория"
            },
            "Коммиты": {
                "git commit -m \"[message]\"": "Создать коммит с сообщением",
                "git commit --amend": "Изменить последний коммит",
                "git reset --soft HEAD~1": "Отменить последний коммит (оставить изменения)",
                "git reset --hard HEAD~1": "Отменить последний коммит (удалить изменения)"
            },
            "Ветки": {
                "git checkout -b [branch_name]": "Создать и переключиться на новую ветку",
                "git checkout [branch_name]": "Переключиться на ветку",
                "git merge [branch_name]": "Слить ветку в текущую",
                "git branch -d [branch_name]": "Удалить ветку"
            },
            "Удаленный репозиторий": {
                "git fetch": "Загрузить изменения с удаленного репозитория",
                "git pull": "Загрузить и применить изменения",
                "git push": "Отправить изменения на удаленный репозиторий",
                "git push --force-with-lease": "Принудительная отправка (безопасная)",
                "git push -u origin [branch]": "Отправить ветку на удаленный репозиторий"
            },
            "Информация": {
                "git diff": "Показать изменения в файлах",
                "git diff --staged": "Показать изменения в индексе",
                "git show": "Показать детали последнего коммита",
                "git config --list": "Показать настройки Git"
            }
        }

        try:
            if os.path.exists(commands_file):
                with open(commands_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Создаем файл с командами по умолчанию
                with open(commands_file, 'w', encoding='utf-8') as f:
                    json.dump(default_commands, f, ensure_ascii=False, indent=2)
                return default_commands
        except Exception as e:
            print(f"Ошибка загрузки команд: {e}")
            return default_commands

    def setup_scrollable_ui(self):
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # PanedWindow для разделения на левую (прокручиваемую) и правую части
        main_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)

        # ЛЕВАЯ ЧАСТЬ — с прокруткой
        left_frame_outer = ttk.Frame(main_pane)
        main_pane.add(left_frame_outer, weight=3)

        # Canvas + Scrollbar для прокрутки
        canvas = tk.Canvas(left_frame_outer, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(left_frame_outer, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Правая часть — консоль и подсказки (без прокрутки)
        right_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_frame, weight=1)

        # Теперь размещаем UI в scrollable_frame
        self.setup_ui_content(self.scrollable_frame, right_frame)

    def setup_ui_content(self, left_frame, right_frame):
        # --- Содержимое ЛЕВОЙ ЧАСТИ ---
        # Заголовок
        title_label = ttk.Label(left_frame, text="🔧 GitHub Helper - Помощник для новичков",
                                font=('Arial', 16, 'bold'))  # Уменьшено с 18
        title_label.pack(pady=(0, 10))

        subtitle_label = ttk.Label(left_frame,
                                   text="Простой интерфейс для работы с Git и GitHub без командной строки",
                                   font=('Arial', 9), foreground="gray")
        subtitle_label.pack(pady=(0, 15))

        # 1. Проверка системы
        system_frame = ttk.LabelFrame(left_frame, text="🔍 1. Проверка системы и настроек", padding="10")
        system_frame.pack(fill="x", pady=(0, 10))

        # Git статус
        ttk.Label(system_frame, text="Git:", font=('Arial', 9, 'bold')).pack(anchor="w")
        git_status_frame = ttk.Frame(system_frame)
        git_status_frame.pack(fill="x", padx=(20, 0), pady=(0, 5))
        ttk.Label(git_status_frame, textvariable=self.git_status).pack(side="left")
        ttk.Button(git_status_frame, text="Проверить Git",
                   command=self.check_git_installation).pack(side="right")

        # Пользователь
        ttk.Label(system_frame, text="Пользователь Git:", font=('Arial', 9, 'bold')).pack(anchor="w", pady=(5, 0))
        user_status_frame = ttk.Frame(system_frame)
        user_status_frame.pack(fill="x", padx=(20, 0), pady=(0, 5))
        ttk.Label(user_status_frame, textvariable=self.user_info).pack(side="left")
        ttk.Button(user_status_frame, text="Настроить",
                   command=self.setup_git_user).pack(side="right", padx=(5, 0))

        ttk.Button(system_frame, text="🆘 Помощь для начинающих",
                   command=self.show_beginner_help).pack(anchor="w", pady=(5, 0))

        # 2. Выбор проекта
        project_frame = ttk.LabelFrame(left_frame, text="📁 2. Выбор и информация о проекте", padding="10")
        project_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(project_frame, text="Путь к проекту:").pack(anchor="w")
        entry_frame = ttk.Frame(project_frame)
        entry_frame.pack(fill="x", pady=(2, 5))
        ttk.Entry(entry_frame, textvariable=self.project_path,
                  font=('Arial', 9)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(entry_frame, text="Выбрать",
                   command=self.select_project_folder).pack(side="right")

        # Информация о проекте
        info_frame = ttk.Frame(project_frame)
        info_frame.pack(fill="x", pady=(5, 0))

        ttk.Label(info_frame, text="Текущая ветка:", width=18).grid(row=0, column=0, sticky="w", pady=1)
        ttk.Label(info_frame, textvariable=self.current_branch).grid(row=0, column=1, sticky="w", padx=(5, 0))

        ttk.Label(info_frame, text="Удалённый репозиторий:", width=18).grid(row=1, column=0, sticky="w", pady=1)
        ttk.Label(info_frame, textvariable=self.remote_info, wraplength=300).grid(row=1, column=1, sticky="w",
                                                                                  padx=(5, 0))

        ttk.Label(info_frame, text="Статус подключения:", width=18).grid(row=2, column=0, sticky="w", pady=1)
        self.connection_label = ttk.Label(info_frame, textvariable=self.connection_status)
        self.connection_label.grid(row=2, column=1, sticky="w", padx=(5, 0))

        # Кнопки
        btn_frame = ttk.Frame(project_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="🔍 Проверить", command=self.check_project).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="🆕 Создать", command=self.init_repository).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="🔗 Подключить", command=self.setup_remote_repository).pack(side="left")

        # 3. Статус файлов
        status_frame = ttk.LabelFrame(left_frame, text="📋 3. Статус файлов проекта", padding="10")
        status_frame.pack(fill="both", expand=True, pady=(0, 10))

        header = ttk.Frame(status_frame)
        header.pack(fill="x", pady=(0, 5))
        ttk.Button(header, text="🔄 Обновить", command=self.update_file_status).pack(side="left")
        ttk.Label(header, text="💡 Совет: зелёные — готовы, красные — не отслеживаются",
                  foreground="gray", font=('Arial', 8)).pack(side="right")

        tree_frame = ttk.Frame(status_frame)
        tree_frame.pack(fill="both", expand=True)

        self.file_tree = ttk.Treeview(tree_frame, columns=('status', 'description'), height=5)
        self.file_tree.heading('#0', text='Файл')
        self.file_tree.heading('status', text='Статус')
        self.file_tree.heading('description', text='Описание')
        self.file_tree.column('#0', width=300)
        self.file_tree.column('status', width=100)
        self.file_tree.column('description', width=200)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        self.file_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # 4. Коммит
        commit_frame = ttk.LabelFrame(left_frame, text="💾 4. Сохранение изменений", padding="10")
        commit_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(commit_frame,
                  text="Коммит — сохранение изменений с описанием",
                  foreground="blue", font=('Arial', 9)).pack(anchor="w", pady=(0, 5))

        ttk.Label(commit_frame, text="Опишите изменения:", font=('Arial', 9, 'bold')).pack(anchor="w")

        comment_frame = ttk.Frame(commit_frame)
        comment_frame.pack(fill="x", pady=(2, 5))

        self.commit_text = tk.Text(comment_frame, height=2, width=40, wrap=tk.WORD, font=('Arial', 9))
        self.commit_text.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btns = ttk.Frame(comment_frame)
        btns.pack(side="right", fill="y")
        ttk.Button(btns, text="✨", width=6, command=self.auto_fill_commit_message).pack(pady=(0, 2))
        ttk.Button(btns, text="🗑️", width=6, command=lambda: self.commit_text.delete(1.0, tk.END)).pack()

        ttk.Label(commit_frame,
                  text="💡 Пример: 'Исправил ошибку', 'Добавил форму'",
                  foreground="gray", font=('Arial', 8)).pack(anchor="w")

        commit_btns = ttk.Frame(commit_frame)
        commit_btns.pack(fill="x", pady=(10, 0))
        ttk.Button(commit_btns, text="💾 Текущий", command=self.commit_selected_file).pack(side="left", padx=(0, 5))
        ttk.Button(commit_btns, text="💾 Все", command=self.commit_all_changes).pack(side="left", padx=(0, 5))
        ttk.Button(commit_btns, text="🚀 Отправить", command=self.push_to_github).pack(side="left")

        # 5. НОВАЯ СЕКЦИЯ: Ручное управление командами
        manual_frame = ttk.LabelFrame(left_frame, text="⌨️ 5. Ручное управление командами Git", padding="10")
        manual_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(manual_frame,
                  text="Выполнение команд Git напрямую для опытных пользователей",
                  foreground="blue", font=('Arial', 9)).pack(anchor="w", pady=(0, 10))

        # Выбор из готовых команд
        preset_frame = ttk.LabelFrame(manual_frame, text="📚 Готовые команды", padding="10")
        preset_frame.pack(fill="x", pady=(0, 10))

        # Выпадающий список категорий
        ttk.Label(preset_frame, text="Категория:").pack(anchor="w")
        self.command_category = ttk.Combobox(preset_frame, values=list(self.git_commands.keys()), state="readonly")
        self.command_category.pack(fill="x", pady=(2, 5))
        self.command_category.bind("<<ComboboxSelected>>", self.update_command_list)

        # Выпадающий список команд
        ttk.Label(preset_frame, text="Команда:").pack(anchor="w")
        self.command_preset = ttk.Combobox(preset_frame, state="readonly")
        self.command_preset.pack(fill="x", pady=(2, 5))
        self.command_preset.bind("<<ComboboxSelected>>", self.update_command_description)

        # Описание команды
        ttk.Label(preset_frame, text="Описание:").pack(anchor="w")
        self.command_description = ttk.Label(preset_frame, text="", foreground="gray",
                                             font=('Arial', 9), wraplength=400)
        self.command_description.pack(anchor="w", pady=(2, 5))

        # Кнопка выполнения готовой команды
        ttk.Button(preset_frame, text="▶️ Выполнить выбранную команду",
                   command=self.execute_preset_command).pack(anchor="w", pady=(5, 0))

        # Поле для ручного ввода
        manual_input_frame = ttk.LabelFrame(manual_frame, text="✏️ Ручной ввод команды", padding="10")
        manual_input_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(manual_input_frame, text="Введите команду Git:").pack(anchor="w")

        input_frame = ttk.Frame(manual_input_frame)
        input_frame.pack(fill="x", pady=(2, 5))

        self.manual_command = ttk.Entry(input_frame, font=('Consolas', 9))
        self.manual_command.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.manual_command.bind('<Return>', lambda e: self.execute_manual_command())

        ttk.Button(input_frame, text="▶️ Выполнить",
                   command=self.execute_manual_command).pack(side="right")

        ttk.Label(manual_input_frame,
                  text="💡 Пример: git log --graph --oneline",
                  foreground="gray", font=('Arial', 8)).pack(anchor="w")

        # Кнопки быстрого доступа
        quick_buttons_frame = ttk.LabelFrame(manual_frame, text="⚡ Быстрые команды", padding="10")
        quick_buttons_frame.pack(fill="x")

        quick_btn_row1 = ttk.Frame(quick_buttons_frame)
        quick_btn_row1.pack(fill="x", pady=(0, 5))

        ttk.Button(quick_btn_row1, text="📊 Status",
                   command=lambda: self.execute_command("git status")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row1, text="📋 Log",
                   command=lambda: self.execute_command("git log --oneline -10")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row1, text="🌿 Branches",
                   command=lambda: self.execute_command("git branch")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row1, text="🔄 Fetch",
                   command=lambda: self.execute_command("git fetch")).pack(side="left")

        quick_btn_row2 = ttk.Frame(quick_buttons_frame)
        quick_btn_row2.pack(fill="x")

        ttk.Button(quick_btn_row2, text="📥 Pull",
                   command=lambda: self.execute_command("git pull")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row2, text="📤 Push",
                   command=lambda: self.execute_command("git push")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row2, text="🔍 Diff",
                   command=lambda: self.execute_command("git diff")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_btn_row2, text="ℹ️ Config",
                   command=lambda: self.execute_command("git config --list")).pack(side="left")

        # --- ПРАВАЯ ЧАСТЬ: Консоль и подсказки ---
        console_frame = ttk.LabelFrame(right_frame, text="📺 Журнал операций", padding="10")
        console_frame.pack(fill="both", expand=True)

        self.console = scrolledtext.ScrolledText(console_frame, height=24,
                                                 wrap=tk.WORD, state=tk.NORMAL,
                                                 font=('Consolas', 9))
        self.console.pack(fill="both", expand=True, pady=(0, 10))

        self.console.tag_configure('command', foreground='blue', font=('Consolas', 9, 'bold'))
        self.console.tag_configure('success', foreground='green')
        self.console.tag_configure('error', foreground='red')
        self.console.tag_configure('info', foreground='orange')

        self.setup_console_bindings()

        ttk.Button(console_frame, text="🗑️ Очистить", command=self.clear_console).pack(side="left")
        ttk.Label(console_frame, text="Ctrl+C — копировать", foreground="gray", font=('Arial', 8)).pack(side="left",
                                                                                                        padx=5)

        self.log_message("🎉 Добро пожаловать в GitHub Helper!", 'info')
        self.log_message("Начните с проверки системы и выбора папки проекта.", 'info')

    def update_command_list(self, event=None):
        """Обновляет список команд при выборе категории"""
        category = self.command_category.get()
        if category and category in self.git_commands:
            commands = list(self.git_commands[category].keys())
            self.command_preset.config(values=commands)
            self.command_preset.set("")
            self.command_description.config(text="")

    def update_command_description(self, event=None):
        """Обновляет описание команды при выборе команды"""
        category = self.command_category.get()
        command = self.command_preset.get()
        if category and command and category in self.git_commands:
            if command in self.git_commands[category]:
                description = self.git_commands[category][command]
                self.command_description.config(text=description)

    def execute_preset_command(self):
        """Выполняет выбранную из списка команду"""
        command = self.command_preset.get()
        if not command:
            messagebox.showwarning("Предупреждение", "Выберите команду для выполнения!")
            return

        # Проверяем шаблоны в команде
        if "[filename]" in command or "[message]" in command or "[branch" in command:
            self.show_command_template_dialog(command)
        else:
            self.execute_command(command)

    def show_command_template_dialog(self, command_template):
        """Показывает диалог для заполнения шаблона команды"""
        template_window = tk.Toplevel(self.root)
        template_window.title("📝 Заполнение параметров команды")
        template_window.geometry("500x400")
        template_window.transient(self.root)
        template_window.grab_set()

        main_frame = ttk.Frame(template_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="📝 Заполните параметры для команды",
                  font=('Arial', 12, 'bold')).pack(pady=(0, 15))

        ttk.Label(main_frame, text=f"Команда: {command_template}",
                  font=('Consolas', 10), background='#f0f0f0').pack(pady=(0, 15))

        # Словарь для хранения значений параметров
        params = {}
        entries = {}

        # Определяем какие параметры нужно заполнить
        if "[filename]" in command_template:
            ttk.Label(main_frame, text="Имя файла:", font=('Arial', 10, 'bold')).pack(anchor="w")
            entries['filename'] = ttk.Entry(main_frame, font=('Arial', 10), width=40)
            entries['filename'].pack(fill="x", pady=(2, 10))

        if "[message]" in command_template:
            ttk.Label(main_frame, text="Сообщение коммита:", font=('Arial', 10, 'bold')).pack(anchor="w")
            entries['message'] = ttk.Entry(main_frame, font=('Arial', 10), width=40)
            entries['message'].pack(fill="x", pady=(2, 10))

        if "[branch_name]" in command_template or "[branch]" in command_template:
            ttk.Label(main_frame, text="Имя ветки:", font=('Arial', 10, 'bold')).pack(anchor="w")
            entries['branch'] = ttk.Entry(main_frame, font=('Arial', 10), width=40)
            entries['branch'].pack(fill="x", pady=(2, 10))

        # Результирующая команда
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.pack(fill="x", pady=(10, 15))

        result_var = tk.StringVar(value=command_template)
        result_label = ttk.Label(result_frame, textvariable=result_var,
                                 font=('Consolas', 9), background='white')
        result_label.pack(fill="x")

        def update_result(*args):
            """Обновляет превью команды в реальном времени"""
            result = command_template
            for key, entry in entries.items():
                if key == 'filename':
                    result = result.replace("[filename]", entry.get() or "[filename]")
                elif key == 'message':
                    result = result.replace("[message]", entry.get() or "[message]")
                elif key == 'branch':
                    result = result.replace("[branch_name]", entry.get() or "[branch_name]")
                    result = result.replace("[branch]", entry.get() or "[branch]")
            result_var.set(result)

        # Привязываем обновление к изменениям в полях
        for entry in entries.values():
            entry.bind('<KeyRelease>', update_result)

        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def execute_filled_command():
            final_command = result_var.get()

            # Проверяем что все параметры заполнены
            if "[" in final_command and "]" in final_command:
                messagebox.showwarning("Предупреждение", "Заполните все параметры команды!")
                return

            template_window.destroy()
            self.execute_command(final_command)

        ttk.Button(buttons_frame, text="▶️ Выполнить", command=execute_filled_command).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена", command=template_window.destroy).pack(side="right", padx=(0, 10))

        # Фокус на первое поле
        if entries:
            list(entries.values())[0].focus()

    def execute_manual_command(self):
        """Выполняет команду, введенную вручную"""
        command = self.manual_command.get().strip()
        if not command:
            messagebox.showwarning("Предупреждение", "Введите команду для выполнения!")
            return

        # Проверяем что команда начинается с git
        if not command.startswith('git'):
            result = messagebox.askyesno("Предупреждение",
                                         f"Команда не начинается с 'git': {command}\n\nВыполнить её всё равно?")
            if not result:
                return

        self.execute_command(command)
        # Очищаем поле после выполнения
        self.manual_command.delete(0, tk.END)

    def execute_command(self, command):
        """Универсальный метод для выполнения любой git команды"""
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        self.log_message(f"⌨️ РУЧНАЯ КОМАНДА: {command}", 'info')

        # Специальная обработка для команд push
        if command.startswith('git push') and not '--force' in command:
            self._handle_push_with_conflict_detection(command)
        else:
            success, output = self.run_git_command(command)
            if success:
                self.log_message("✅ Команда выполнена успешно.", 'success')
                # Обновляем информацию о проекте после выполнения команды
                self.update_project_info_after_command(command)
            else:
                self.log_message("❌ Команда завершилась с ошибкой.", 'error')

    def _handle_push_with_conflict_detection(self, push_command):
        """Обрабатывает команду push с обнаружением конфликтов"""
        self.log_message("🔍 Проверяем возможные конфликты перед отправкой...", 'info')

        # Сначала выполняем fetch для получения актуальной информации
        fetch_success, _ = self.run_git_command("git fetch", False)
        if not fetch_success:
            self.log_message("⚠️ Не удалось получить обновления с сервера", 'error')

        # Проверяем статус
        status_success, status_output = self.run_git_command("git status", False)
        if status_success and ("behind" in status_output or "diverged" in status_output):
            self.log_message("⚠️ Обнаружены конфликты! Удаленная ветка содержит новые изменения.", 'error')
            self._show_conflict_resolution_dialog(push_command)
            return

        # Если конфликтов нет, выполняем обычный push
        success, output = self.run_git_command(push_command)
        if not success and ("rejected" in output or "non-fast-forward" in output):
            self.log_message("❌ Push отклонен из-за конфликтов", 'error')
            self._show_conflict_resolution_dialog(push_command)
        elif success:
            self.log_message("✅ Изменения успешно отправлены!", 'success')

    def _show_conflict_resolution_dialog(self, original_push_command):
        """Показывает диалог разрешения конфликтов"""
        conflict_window = tk.Toplevel(self.root)
        conflict_window.title("⚠️ Обнаружен конфликт")
        conflict_window.geometry("600x400")
        conflict_window.transient(self.root)
        conflict_window.grab_set()

        main_frame = ttk.Frame(conflict_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="⚠️ Конфликт при отправке изменений",
                  font=('Arial', 14, 'bold'), foreground='red').pack(pady=(0, 15))

        info_text = ("Удаленная ветка содержит изменения, которых нет у вас локально.\n"
                     "Выберите один из способов решения:")
        ttk.Label(main_frame, text=info_text, wraplength=500).pack(pady=(0, 20))

        # Опции решения
        options_frame = ttk.LabelFrame(main_frame, text="Варианты решения", padding="15")
        options_frame.pack(fill="x", pady=(0, 20))

        def safe_pull():
            conflict_window.destroy()
            self.log_message("📥 Выполняем безопасное обновление...", 'info')
            current_branch = self.current_branch.get().replace("✅ ", "").strip()
            success, output = self.run_git_command(f"git pull origin {current_branch}")
            if success:
                self.log_message("✅ Обновление завершено. Попробуйте отправить изменения снова.", 'success')
            else:
                self.log_message(f"❌ Ошибка при обновлении: {output}", 'error')

        def force_push():
            result = messagebox.askyesno("Подтверждение",
                                         "⚠️ ВНИМАНИЕ!\n\nПринудительная отправка может перезаписать чужие изменения!\n\nПродолжить?")
            if result:
                conflict_window.destroy()
                force_command = original_push_command.replace("git push", "git push --force-with-lease")
                self.log_message("🚨 Выполняем принудительную отправку...", 'info')
                success, output = self.run_git_command(force_command)
                if success:
                    self.log_message("✅ Принудительная отправка выполнена успешно!", 'success')
                else:
                    self.log_message(f"❌ Ошибка принудительной отправки: {output}", 'error')

        ttk.Button(options_frame, text="📥 Безопасно: сначала загрузить изменения (git pull)",
                   command=safe_pull, width=50).pack(pady=(0, 10))

        ttk.Button(options_frame, text="🚨 Принудительно: перезаписать удаленную ветку (--force-with-lease)",
                   command=force_push, width=50).pack(pady=(0, 10))

        ttk.Button(options_frame, text="❌ Отмена",
                   command=conflict_window.destroy, width=50).pack()

    def update_project_info_after_command(self, command):
        """Обновляет информацию о проекте после выполнения команды"""
        # Обновляем информацию для команд, которые могут изменить состояние
        update_commands = ['checkout', 'branch', 'commit', 'pull', 'push', 'merge', 'remote']

        if any(cmd in command for cmd in update_commands):
            # Небольшая задержка для корректного обновления
            self.root.after(500, self._delayed_project_update)

    def _delayed_project_update(self):
        """Отложенное обновление информации о проекте"""
        self.check_project()

    # Остальные методы остаются без изменений
    def setup_console_bindings(self):
        self.context_menu = tk.Menu(self.console, tearoff=0)
        self.context_menu.add_command(label="📋 Копировать", command=self.copy_selection_menu)
        self.context_menu.add_command(label="✅ Выделить всё", command=self.select_all_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Очистить", command=self.clear_console)
        self.console.bind("<Button-3>", self.show_context_menu)
        self.console.bind("<Control-c>", self.copy_selection)
        self.console.bind("<Control-a>", self.select_all)
        self.console.bind("<Key>", self.on_console_key_press)

    def on_console_key_press(self, event):
        allowed_keys = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A',
                        'Left', 'Right', 'Up', 'Down', 'Home', 'End',
                        'Prior', 'Next', 'Shift_L', 'Shift_R']
        if event.keysym not in allowed_keys:
            return "break"

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selection(self, event=None):
        try:
            selected_text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"

    def copy_selection_menu(self):
        try:
            selected_text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            messagebox.showinfo("Информация", "Сначала выделите текст для копирования")

    def select_all(self, event=None):
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)
        return "break"

    def select_all_menu(self):
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)

    def log_message(self, message, msg_type='normal'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if msg_type == 'command':
            self.console.insert(tk.END, f"\n🔧 КОМАНДА: {message}\n", 'command')
        elif msg_type == 'success':
            self.console.insert(tk.END, f"[{timestamp}] ✅ {message}\n", 'success')
        elif msg_type == 'error':
            self.console.insert(tk.END, f"[{timestamp}] ❌ {message}\n", 'error')
        elif msg_type == 'info':
            self.console.insert(tk.END, f"[{timestamp}] ℹ️ {message}\n", 'info')
        else:
            self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.root.update_idletasks()

    def clear_console(self):
        self.console.delete(1.0, tk.END)
        self.log_message("Журнал очищен", 'info')

    def run_git_command(self, command, show_command=True):
        if show_command:
            self.log_message(command, 'command')
        try:
            if self.project_path.get():
                os.chdir(self.project_path.get())
            result = subprocess.run(command, shell=True, capture_output=True,
                                    text=True, encoding='utf-8')
            if result.returncode == 0:
                if result.stdout.strip():
                    self.log_message(result.stdout.strip(), 'success')
                return True, result.stdout.strip()
            else:
                error_msg = result.stderr.strip()
                if not error_msg:
                    error_msg = "Команда выполнена, но нет изменений"
                self.log_message(error_msg, 'error')
                return False, error_msg
        except Exception as e:
            self.log_message(f"Исключение: {str(e)}", 'error')
            return False, str(e)

    def check_git_installation(self):
        self.log_message("🔍 ПРОВЕРКА СИСТЕМЫ", 'info')
        self.log_message("Проверяем, установлен ли Git в системе...", 'info')
        success, output = self.run_git_command("git --version")
        if success:
            self.git_status.set(f"✅ {output}")
            self.log_message("Git найден и готов к работе!", 'success')
            self.check_git_user()
        else:
            self.git_status.set("❌ Git не найден")
            self.log_message("Git не найден! Необходима установка.", 'error')
            self.log_message("💡 РЕШЕНИЕ: Скачайте Git с https://git-scm.com/", 'info')

    def check_git_user(self):
        self.log_message("Проверяем настройки пользователя Git...", 'info')
        success_name, name = self.run_git_command("git config --global user.name", False)
        success_email, email = self.run_git_command("git config --global user.email", False)
        if success_name and success_email and name and email:
            self.user_info.set(f"✅ {name} ({email})")
            self.log_message(f"Пользователь настроен: {name} ({email})", 'success')
        else:
            self.user_info.set("❌ Не настроен")
            self.log_message("Пользователь Git не настроен", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Настроить пользователя'", 'info')

    def setup_git_user(self):
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Настройка пользователя Git")
        setup_window.geometry("400x300")
        setup_window.transient(self.root)
        setup_window.grab_set()
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="🔧 Настройка пользователя Git",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        info_text = ("Git нужно знать ваше имя и email для подписи коммитов. "
                     "Эти данные будут видны в истории изменений.")
        ttk.Label(main_frame, text=info_text, wraplength=350,
                  justify="left", foreground="gray").pack(pady=(0, 20))

        ttk.Label(main_frame, text="Ваше имя:", font=('Arial', 10, 'bold')).pack(anchor="w")
        name_entry = ttk.Entry(main_frame, font=('Arial', 11), width=30)
        name_entry.pack(fill="x", pady=(5, 15))

        ttk.Label(main_frame, text="Ваш email:", font=('Arial', 10, 'bold')).pack(anchor="w")
        email_entry = ttk.Entry(main_frame, font=('Arial', 11), width=30)
        email_entry.pack(fill="x", pady=(5, 20))

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def save_user():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            if not name or not email:
                messagebox.showwarning("Предупреждение", "Заполните все поля!")
                return
            success1, _ = self.run_git_command(f'git config --global user.name "{name}"')
            success2, _ = self.run_git_command(f'git config --global user.email "{email}"')
            if success1 and success2:
                self.user_info.set(f"✅ {name} ({email})")
                self.log_message(f"Пользователь настроен: {name} ({email})", 'success')
                setup_window.destroy()
                messagebox.showinfo("Успех", "Пользователь Git успешно настроен!")
            else:
                messagebox.showerror("Ошибка", "Не удалось настроить пользователя")

        ttk.Button(buttons_frame, text="💾 Сохранить", command=save_user).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена", command=setup_window.destroy).pack(side="right", padx=(0, 10))
        name_entry.focus()

    def show_beginner_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("🆘 Справка для начинающих")
        help_window.geometry("600x500")
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill="both", expand=True)

        help_content = """
🆘 СПРАВКА ДЛЯ НАЧИНАЮЩИХ

📚 ЧТО ТАКОЕ GIT И GITHUB?
Git — это система контроля версий. Она помогает:
• Сохранять историю изменений ваших файлов
• Работать в команде над одним проектом
• Откатывать изменения при необходимости
• Создавать разные версии (ветки) проекта

GitHub — это облачный сервис для хранения Git-репозиториев.

🔄 ОСНОВНОЙ РАБОЧИЙ ПРОЦЕСС:
1. Изменяете файлы в проекте
2. Добавляете их в "индекс" (git add)
3. Создаете "коммит" — сохранение с описанием (git commit)
4. Отправляете на GitHub (git push)

⚙️ НАЧАЛЬНАЯ НАСТРОЙКА:
1. Установите Git с официального сайта
2. Настройте пользователя (имя и email)
3. Создайте аккаунт на GitHub.com
4. Инициализируйте репозиторий в папке проекта
5. Подключите к удаленному репозиторию на GitHub

🛠️ НОВЫЕ ВОЗМОЖНОСТИ:
• Выпадающий список готовых команд с описаниями
• Ручной ввод любых Git команд
• Быстрые кнопки для частых операций
• Автоматическое обнаружение конфликтов при push

💡 ПОЛЕЗНЫЕ СОВЕТЫ:
• Делайте коммиты часто и с осмысленными комментариями
• Всегда проверяйте статус перед коммитом
• Используйте git pull перед git push
• Создавайте ветки для экспериментов

❓ ЕСЛИ ЧТО-ТО ПОШЛО НE ТАК:
• git status — покажет текущее состояние
• git log — покажет историю коммитов  
• git reset — отменит изменения
• В крайнем случае — создайте резервную копию и начните заново
        """

        help_text.insert(tk.END, help_content)
        help_text.configure(state=tk.DISABLED)
        close_button = ttk.Button(help_window, text="✅ Понятно", command=help_window.destroy)
        close_button.pack(pady=10)

    def select_project_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с проектом")
        if folder:
            self.project_path.set(folder)
            self.log_message(f"📁 Выбрана папка: {folder}", 'info')
            self.check_project()

    def check_project(self):
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        self.log_message("📋 ПРОВЕРКА ПРОЕКТА", 'info')
        self.log_message("Анализируем выбранную папку...", 'info')

        success, output = self.run_git_command("git status", False)
        if success:
            self.log_message("✅ Это валидный Git репозиторий!", 'success')

            success, branch = self.run_git_command("git branch --show-current", False)
            if success and branch:
                self.current_branch.set(f"✅ {branch}")
                self.log_message(f"Текущая ветка: {branch}", 'info')

            self.check_remote_repository()
            self.update_file_status()
        else:
            self.current_branch.set("❌ Не Git репозиторий")
            self.remote_info.set("Не подключен")
            self.connection_status.set("❌ Репозиторий не найден")
            self.log_message("❌ Это не Git репозиторий!", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Создать новый репозиторий' для инициализации", 'info')

    def check_remote_repository(self):
        self.log_message("Проверяем подключение к удаленному репозиторию...", 'info')
        success, output = self.run_git_command("git remote -v", False)
        if success and output.strip():
            lines = output.strip().split('\n')
            origins = [line for line in lines if 'origin' in line and '(fetch)' in line]
            if origins:
                remote_url = origins[0].split('\t')[1].split(' ')[0]
                self.remote_info.set(f"✅ {remote_url}")
                self.connection_status.set("✅ Репозиторий подключен")
                self.log_message(f"Подключен к: {remote_url}", 'success')

                # Проверяем возможность связи с удаленным репозиторием
                self.test_remote_connection()
            else:
                self.remote_info.set("❌ Не настроен")
                self.connection_status.set("❌ Репозиторий не подключен")
                self.log_message("Удаленный репозиторий не настроен", 'error')
        else:
            self.remote_info.set("❌ Не подключен")
            self.connection_status.set("❌ Репозиторий не подключен")
            self.log_message("Удаленный репозиторий не подключен", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Подключить к GitHub'", 'info')

    def test_remote_connection(self):
        """Проверяем связь с удаленным репозиторием"""
        self.log_message("Тестируем соединение с GitHub...", 'info')
        success, output = self.run_git_command("git ls-remote --heads origin", False)
        if success:
            self.connection_status.set("✅ Соединение установлено")
            self.log_message("✅ Связь с удаленным репозиторием работает!", 'success')
        else:
            self.connection_status.set("⚠️ Проблемы с соединением")
            self.log_message("⚠️ Проблемы с доступом к удаленному репозиторию", 'error')
            if "authentication" in output.lower() or "denied" in output.lower():
                self.log_message("💡 Возможна проблема с аутентификацией. Проверьте настройки SSH/Token", 'info')

    def push_to_github(self):
        # Проверяем, что проект выбран
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        # Проверяем статус подключения
        if "не подключен" in self.connection_status.get().lower() or "не найден" in self.connection_status.get().lower():
            self.log_message("❌ Удаленный репозиторий не подключен. Открываем окно подключения...", 'error')
            self.setup_remote_repository()
            return

        self.log_message("🚀 ОТПРАВКА НА GITHUB", 'info')
        self.log_message("Отправляем изменения на удаленный репозиторий...", 'info')

        # Запускаем push в отдельном потоке, чтобы не блокировать интерфейс
        threading.Thread(target=self._run_push).start()

    def _run_push(self):
        current_branch = self.current_branch.get().replace("✅ ", "").strip()
        command = f"git push -u origin {current_branch}"
        self._handle_push_with_conflict_detection(command)


    def setup_remote_repository(self):
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        setup_window = tk.Toplevel(self.root)
        setup_window.title("🔗 Подключение к GitHub")
        setup_window.geometry("650x600")
        setup_window.transient(self.root)
        setup_window.grab_set()
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))

        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(main_frame, text="🔗 Подключение к GitHub",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Информация
        info_text = ("Чтобы отправлять код на GitHub, нужно подключить локальный\n"
                     "репозиторий к удаленному репозиторию на GitHub.")
        ttk.Label(main_frame, text=info_text, wraplength=500,
                  justify="left", foreground="gray").pack(pady=(0, 20))

        # Инструкция
        instruction_frame = ttk.LabelFrame(main_frame, text="📝 Инструкция", padding="15")
        instruction_frame.pack(fill="x", pady=(0, 20))

        instruction_text = ("1. Перейдите на GitHub.com\n"
                            "2. Создайте новый репозиторий (New repository)\n"
                            "3. Скопируйте URL репозитория\n"
                            "4. Вставьте URL в поле ниже\n"
                            "5. Нажмите 'Подключить'")
        ttk.Label(instruction_frame, text=instruction_text,
                  justify="left").pack(anchor="w", pady=(0, 10))

        ttk.Button(instruction_frame, text="🌐 Открыть GitHub.com",
                   command=lambda: webbrowser.open("https://github.com/new")).pack(anchor="w")

        # Поле ввода URL
        ttk.Label(main_frame, text="URL репозитория GitHub:",
                  font=('Arial', 10, 'bold')).pack(anchor="w")
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=(5, 10))
        url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        url_entry.pack(fill="x")

        # Предзаполняем поле примером
        example_url = "https://github.com/username/repository.git"
        url_entry.insert(0, example_url)

        ttk.Label(main_frame,
                  text="💡 Пример: https://github.com/unijohnson18/test_reclama.git",
                  foreground="gray", font=('Arial', 9)).pack(anchor="w", pady=(0, 15))

        # Статус подключения в окне
        status_frame = ttk.LabelFrame(main_frame, text="🔍 Статус", padding="10")
        status_frame.pack(fill="x", pady=(0, 20))

        status_var = tk.StringVar(value="Ожидание подключения...")
        status_label = ttk.Label(status_frame, textvariable=status_var, foreground="orange")
        status_label.pack(anchor="w")

        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def connect_repository():
            url = url_entry.get().strip()
            if not url or url == example_url:
                messagebox.showwarning("Предупреждение", "Введите корректный URL репозитория!")
                return

            status_var.set("⏳ Подключение...")
            setup_window.update()

            self.log_message(f"🔗 Подключаем к репозиторию: {url}", 'info')

            # Удаляем старое подключение если есть
            self.run_git_command("git remote remove origin", False)

            # Добавляем новое подключение
            success, output = self.run_git_command(f'git remote add origin "{url}"')
            if success:
                status_var.set("✅ Успешно подключено!")
                self.log_message("✅ Удаленный репозиторий успешно подключен!", 'success')

                # Обновляем информацию о подключении
                self.remote_info.set(f"✅ {url}")
                self.connection_status.set("✅ Репозиторий подключен")

                # Предлагаем отправить первый коммит
                self.root.after(2000, lambda: self._suggest_first_push(setup_window))
            else:
                status_var.set("❌ Ошибка подключения")
                self.log_message(f"❌ Ошибка подключения: {output}", 'error')
                self.log_message("💡 Проверьте корректность URL и доступ к репозиторию", 'info')

        def _suggest_first_push(parent_window):
            result = messagebox.askyesno("Отправка изменений",
                                         "Репозиторий подключен! Отправить изменения на GitHub сейчас?",
                                         parent=parent_window)
            if result:
                parent_window.destroy()
                self.push_to_github()
            else:
                parent_window.destroy()

        ttk.Button(buttons_frame, text="🔗 Подключить", command=connect_repository).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена", command=setup_window.destroy).pack(side="right", padx=(0, 10))
        url_entry.focus()

    def init_repository(self):
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        # Проверяем, есть ли уже репозиторий
        if os.path.exists(os.path.join(self.project_path.get(), ".git")):
            messagebox.showinfo("Информация", "В этой папке уже есть Git репозиторий!")
            return

        # Подтверждение
        result = messagebox.askyesno("Подтверждение",
                                     f"Создать новый Git репозиторий в папке:\n{self.project_path.get()}?")
        if not result:
            return

        self.log_message("🆕 СОЗДАНИЕ РЕПОЗИТОРИЯ", 'info')
        self.log_message("Инициализируем новый Git репозиторий...", 'info')

        success, output = self.run_git_command("git init")
        if success:
            self.log_message("✅ Репозиторий создан успешно!", 'success')

            # Создаем начальный коммит если есть файлы
            self.log_message("Создаем первоначальный коммит...", 'info')
            self.run_git_command("git add .")

            commit_success, _ = self.run_git_command('git commit -m "Initial commit"')
            if commit_success:
                self.log_message("✅ Начальный коммит создан!", 'success')

            # Обновляем информацию о проекте
            self.check_project()

            messagebox.showinfo("Успех", "Git репозиторий создан!\n\nТеперь вы можете подключить его к GitHub.")
        else:
            self.log_message("❌ Ошибка создания репозитория", 'error')
            messagebox.showerror("Ошибка", "Не удалось создать репозиторий!")

    def update_file_status(self):
        if not self.project_path.get():
            return

        # Очищаем дерево
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.log_message("🔄 Обновляем статус файлов...", 'info')
        success, output = self.run_git_command("git status --porcelain", False)

        if success:
            if output.strip():
                for line in output.strip().split('\n'):
                    if len(line) >= 3:
                        status_code = line[:2]
                        filename = line[3:]

                        status_text, status_color = self._get_status_info(status_code)
                        description = self._get_status_description(status_code)

                        item = self.file_tree.insert('', 'end', text=filename,
                                                     values=(status_text, description))

                        # Применяем цвета
                        self.file_tree.set(item, 'status', status_text)
                        if status_color == 'green':
                            self.file_tree.item(item, tags=('staged',))
                        elif status_color == 'red':
                            self.file_tree.item(item, tags=('modified',))
                        elif status_color == 'blue':
                            self.file_tree.item(item, tags=('untracked',))

                # Настраиваем цвета
                self.file_tree.tag_configure('staged', foreground='green')
                self.file_tree.tag_configure('modified', foreground='red')
                self.file_tree.tag_configure('untracked', foreground='blue')

                self.log_message(f"Найдено изменений: {len(output.strip().split())}", 'info')
            else:
                # Нет изменений
                self.file_tree.insert('', 'end', text="📁 Все файлы актуальны",
                                      values=("✅ Чисто", "Нет изменений"))
                self.log_message("✅ Рабочая область чистая - нет изменений", 'success')
        else:
            self.log_message("❌ Ошибка получения статуса файлов", 'error')

    def _get_status_info(self, status_code):
        """Возвращает текст статуса и цвет для кода статуса git"""
        status_map = {
            'M ': ('📝 Изменен', 'green'),  # Modified and staged
            ' M': ('📝 Изменен', 'red'),  # Modified not staged
            'A ': ('➕ Добавлен', 'green'),  # Added to staging
            'D ': ('🗑️ Удален', 'green'),  # Deleted from staging
            ' D': ('🗑️ Удален', 'red'),  # Deleted not staged
            'R ': ('📛 Переименован', 'green'),  # Renamed
            'C ': ('📋 Скопирован', 'green'),  # Copied
            '??': ('❓ Новый', 'blue'),  # Untracked
            'MM': ('📝 Смешанный', 'red'),  # Modified in both index and worktree
        }
        return status_map.get(status_code, (f'❓ {status_code}', 'gray'))

    def _get_status_description(self, status_code):
        """Возвращает описание статуса файла"""
        descriptions = {
            'M ': 'В индексе, готов к коммиту',
            ' M': 'Изменен, нужно добавить в индекс',
            'A ': 'Добавлен в индекс, готов к коммиту',
            'D ': 'Удален из индекса',
            ' D': 'Удален, изменения не в индексе',
            'R ': 'Переименован, в индексе',
            'C ': 'Скопирован, в индексе',
            '??': 'Новый файл, не отслеживается',
            'MM': 'Изменен и в индексе и в рабочей области',
        }
        return descriptions.get(status_code, 'Неизвестный статус')

    def commit_selected_file(self):
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите файл для коммита!")
            return

        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание изменений!")
            return

        filename = self.file_tree.item(selection[0])['text']
        if filename == "📁 Все файлы актуальны":
            messagebox.showinfo("Информация", "Нет файлов для коммита!")
            return

        self.log_message("💾 КОММИТ ФАЙЛА", 'info')
        self.log_message(f"Добавляем файл в индекс: {filename}", 'info')

        # Добавляем файл в индекс
        add_success, _ = self.run_git_command(f'git add "{filename}"')
        if add_success:
            # Создаем коммит
            commit_success, _ = self.run_git_command(f'git commit -m "{commit_message}"')
            if commit_success:
                self.log_message(f"✅ Файл {filename} успешно сохранен!", 'success')
                self.commit_text.delete(1.0, tk.END)
                self.update_file_status()
            else:
                self.log_message("❌ Ошибка создания коммита", 'error')
        else:
            self.log_message("❌ Ошибка добавления файла в индекс", 'error')

    def commit_all_changes(self):
        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание изменений!")
            return

        self.log_message("💾 КОММИТ ВСЕХ ИЗМЕНЕНИЙ", 'info')
        self.log_message("Добавляем все измененные файлы в индекс...", 'info')

        # Добавляем все файлы
        add_success, _ = self.run_git_command("git add .")
        if add_success:
            # Создаем коммит
            commit_success, output = self.run_git_command(f'git commit -m "{commit_message}"')
            if commit_success:
                self.log_message("✅ Все изменения успешно сохранены!", 'success')
                self.commit_text.delete(1.0, tk.END)
                self.update_file_status()
            else:
                if "nothing to commit" in output:
                    self.log_message("ℹ️ Нет изменений для коммита", 'info')
                else:
                    self.log_message("❌ Ошибка создания коммита", 'error')
        else:
            self.log_message("❌ Ошибка добавления файлов в индекс", 'error')

    def auto_fill_commit_message(self):
        """Автоматически заполняет сообщение коммита на основе изменений"""
        self.log_message("✨ Генерируем автоматическое сообщение коммита...", 'info')

        success, output = self.run_git_command("git diff --staged --name-status", False)
        if success and output.strip():
            # Анализируем изменения
            changes = output.strip().split('\n')
            added_files = [line[2:] for line in changes if line.startswith('A')]
            modified_files = [line[2:] for line in changes if line.startswith('M')]
            deleted_files = [line[2:] for line in changes if line.startswith('D')]

            message_parts = []
            if added_files:
                message_parts.append(f"Добавлено файлов: {len(added_files)}")
            if modified_files:
                message_parts.append(f"Изменено файлов: {len(modified_files)}")
            if deleted_files:
                message_parts.append(f"Удалено файлов: {len(deleted_files)}")

            if message_parts:
                auto_message = ", ".join(message_parts)
            else:
                auto_message = "Обновление проекта"
        else:
            # Если нет staged изменений, проверяем обычные изменения
            success, output = self.run_git_command("git status --porcelain", False)
            if success and output.strip():
                lines = output.strip().split('\n')
                auto_message = f"Обновление: изменено файлов ({len(lines)})"
            else:
                auto_message = "Обновление проекта"

        self.commit_text.delete(1.0, tk.END)
        self.commit_text.insert(1.0, auto_message)
        self.log_message(f"✨ Сгенерировано сообщение: {auto_message}", 'info')


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubHelper(root)
    root.mainloop()