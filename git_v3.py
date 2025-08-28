import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import shutil
from datetime import datetime
import threading
import sys
import webbrowser


class GitHubHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Helper - Помощник для работы с Git")
        self.root.geometry("1400x1000")
        self.root.configure(bg='#f0f0f0')

        # Переменные
        self.project_path = tk.StringVar()
        self.current_branch = tk.StringVar(value="Не определена")
        self.git_status = tk.StringVar(value="Git не найден")
        self.remote_info = tk.StringVar(value="Не подключен")
        self.user_info = tk.StringVar(value="Не настроен")

        self.setup_ui()
        self.check_git_installation()

    def setup_ui(self):
        # Главный контейнер с прокруткой
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Основной контент в scrollable_frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        title_label = ttk.Label(main_frame, text="🔧 GitHub Helper - Помощник для новичков",
                                font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        # Подзаголовок с пояснением
        subtitle_label = ttk.Label(main_frame,
                                   text="Простой интерфейс для работы с Git и GitHub без командной строки",
                                   font=('Arial', 10), foreground="gray")
        subtitle_label.pack(pady=(0, 20))

        # 1. Проверка системы (расширенная)
        system_frame = ttk.LabelFrame(main_frame, text="🔍 1. Проверка системы и настроек",
                                      padding="15")
        system_frame.pack(fill="x", pady=(0, 15))

        # Git статус
        git_info_frame = ttk.Frame(system_frame)
        git_info_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(git_info_frame, text="Git:", font=('Arial', 10, 'bold')).pack(anchor="w")
        git_status_frame = ttk.Frame(git_info_frame)
        git_status_frame.pack(fill="x", padx=(20, 0))

        ttk.Label(git_status_frame, textvariable=self.git_status).pack(side="left")
        ttk.Button(git_status_frame, text="Проверить Git",
                   command=self.check_git_installation).pack(side="right")

        # Информация о пользователе Git
        user_info_frame = ttk.Frame(system_frame)
        user_info_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(user_info_frame, text="Пользователь Git:", font=('Arial', 10, 'bold')).pack(anchor="w")
        user_status_frame = ttk.Frame(user_info_frame)
        user_status_frame.pack(fill="x", padx=(20, 0))

        ttk.Label(user_status_frame, textvariable=self.user_info).pack(side="left")
        ttk.Button(user_status_frame, text="Настроить пользователя",
                   command=self.setup_git_user).pack(side="right", padx=(10, 0))

        # Кнопка помощи для начинающих
        help_button = ttk.Button(system_frame, text="🆘 Помощь для начинающих",
                                 command=self.show_beginner_help)
        help_button.pack(anchor="w", pady=(10, 0))

        # 2. Выбор проекта (расширенный)
        project_frame = ttk.LabelFrame(main_frame, text="📁 2. Выбор и информация о проекте",
                                       padding="15")
        project_frame.pack(fill="x", pady=(0, 15))

        # Выбор папки
        path_frame = ttk.Frame(project_frame)
        path_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(path_frame, text="Путь к проекту:").pack(anchor="w")
        entry_frame = ttk.Frame(path_frame)
        entry_frame.pack(fill="x", pady=(5, 0))

        ttk.Entry(entry_frame, textvariable=self.project_path,
                  font=('Arial', 9)).pack(side="left", fill="x", expand=True)
        ttk.Button(entry_frame, text="Выбрать папку",
                   command=self.select_project_folder).pack(side="right", padx=(10, 0))

        # Информация о проекте в табличном виде
        info_frame = ttk.Frame(project_frame)
        info_frame.pack(fill="x", pady=(10, 0))

        # Текущая ветка
        branch_frame = ttk.Frame(info_frame)
        branch_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(branch_frame, text="Текущая ветка:", width=20).pack(side="left")
        ttk.Label(branch_frame, textvariable=self.current_branch).pack(side="left", padx=(10, 0))

        # Удаленный репозиторий
        remote_frame = ttk.Frame(info_frame)
        remote_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(remote_frame, text="Удаленный репозиторий:", width=20).pack(side="left")
        ttk.Label(remote_frame, textvariable=self.remote_info, wraplength=400).pack(side="left", padx=(10, 0))

        # Кнопки управления проектом
        project_buttons_frame = ttk.Frame(project_frame)
        project_buttons_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(project_buttons_frame, text="🔍 Проверить проект",
                   command=self.check_project).pack(side="left", padx=(0, 10))
        ttk.Button(project_buttons_frame, text="🆕 Создать новый репозиторий",
                   command=self.init_repository).pack(side="left", padx=(0, 10))
        ttk.Button(project_buttons_frame, text="🔗 Подключить к GitHub",
                   command=self.setup_remote_repository).pack(side="left")

        # 3. Статус файлов (улучшенный)
        status_frame = ttk.LabelFrame(main_frame, text="📋 3. Статус файлов проекта",
                                      padding="15")
        status_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Кнопка обновления и информация
        status_header_frame = ttk.Frame(status_frame)
        status_header_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(status_header_frame, text="🔄 Обновить статус файлов",
                   command=self.update_file_status).pack(side="left")

        ttk.Label(status_header_frame,
                  text="💡 Совет: Зеленые файлы готовы к коммиту, красные - требуют добавления",
                  foreground="gray").pack(side="right")

        # Список файлов с улучшенным отображением
        tree_frame = ttk.Frame(status_frame)
        tree_frame.pack(fill="both", expand=True)

        self.file_tree = ttk.Treeview(tree_frame, columns=('status', 'description'), height=8)
        self.file_tree.heading('#0', text='📄 Файл')
        self.file_tree.heading('status', text='Статус')
        self.file_tree.heading('description', text='Описание')

        self.file_tree.column('#0', width=400)
        self.file_tree.column('status', width=150)
        self.file_tree.column('description', width=300)

        self.file_tree.pack(side="left", fill="both", expand=True)

        # Scrollbar для списка файлов
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                       command=self.file_tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.file_tree.configure(yscrollcommand=tree_scrollbar.set)

        # 4. Коммит (улучшенный)
        commit_frame = ttk.LabelFrame(main_frame, text="💾 4. Сохранение изменений (коммит)",
                                      padding="15")
        commit_frame.pack(fill="x", pady=(0, 15))

        # Пояснение для новичков
        commit_info = ttk.Label(commit_frame,
                                text="ℹ️ Коммит - это сохранение снимка ваших изменений с описанием того, что вы сделали",
                                foreground="blue", font=('Arial', 9))
        commit_info.pack(anchor="w", pady=(0, 10))

        # Поле для комментария
        comment_frame = ttk.Frame(commit_frame)
        comment_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(comment_frame, text="Опишите ваши изменения:", font=('Arial', 10, 'bold')).pack(anchor="w")

        text_frame = ttk.Frame(comment_frame)
        text_frame.pack(fill="x", pady=(5, 0))

        self.commit_text = tk.Text(text_frame, height=3, width=50, wrap=tk.WORD)
        self.commit_text.pack(side="left", fill="x", expand=True)

        # Кнопки для комментария
        comment_buttons_frame = ttk.Frame(text_frame)
        comment_buttons_frame.pack(side="right", padx=(10, 0), fill="y")

        ttk.Button(comment_buttons_frame, text="✨ Авто-комментарий",
                   command=self.auto_fill_commit_message).pack(fill="x", pady=(0, 5))
        ttk.Button(comment_buttons_frame, text="🗑️ Очистить",
                   command=lambda: self.commit_text.delete(1.0, tk.END)).pack(fill="x")

        # Примеры комментариев
        examples_label = ttk.Label(comment_frame,
                                   text="💡 Примеры: 'Добавил новую функцию входа', 'Исправил ошибку в калькуляторе', 'Обновил документацию'",
                                   foreground="gray", font=('Arial', 8))
        examples_label.pack(anchor="w", pady=(5, 0))

        # Кнопки коммита
        commit_buttons_frame = ttk.Frame(commit_frame)
        commit_buttons_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(commit_buttons_frame, text="💾 Сохранить выбранный файл",
                   command=self.commit_selected_file).pack(side="left", padx=(0, 10))
        ttk.Button(commit_buttons_frame, text="💾 Сохранить все изменения",
                   command=self.commit_all_changes).pack(side="left", padx=(0, 10))
        ttk.Button(commit_buttons_frame, text="🚀 Отправить на GitHub",
                   command=self.push_to_github).pack(side="left")

        # 5. Консоль (улучшенная)
        console_frame = ttk.LabelFrame(main_frame, text="📺 5. Журнал операций и подсказки",
                                       padding="15")
        console_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.console = scrolledtext.ScrolledText(console_frame, height=12,
                                                 wrap=tk.WORD, state=tk.NORMAL,
                                                 font=('Consolas', 9))
        self.console.pack(fill="both", expand=True, pady=(0, 10))

        # Настройка цветов для консоли
        self.console.tag_configure('command', foreground='blue', font=('Consolas', 9, 'bold'))
        self.console.tag_configure('success', foreground='green')
        self.console.tag_configure('error', foreground='red')
        self.console.tag_configure('info', foreground='orange')

        # Привязка событий для копирования
        self.setup_console_bindings()

        # Кнопки управления консолью
        console_buttons_frame = ttk.Frame(console_frame)
        console_buttons_frame.pack(fill="x")

        ttk.Button(console_buttons_frame, text="🗑️ Очистить журнал",
                   command=self.clear_console).pack(side="left", padx=(0, 10))

        ttk.Label(console_buttons_frame,
                  text="💡 Выделяйте текст мышью и копируйте Ctrl+C",
                  foreground="gray", font=('Arial', 8)).pack(side="left", padx=(10, 0))

        # Приветственное сообщение
        self.log_message("🎉 Добро пожаловать в GitHub Helper!", 'info')
        self.log_message("Этот инструмент поможет вам работать с Git и GitHub без командной строки.", 'info')
        self.log_message("Начните с проверки системы и выбора папки проекта.", 'info')

    def setup_console_bindings(self):
        """Настройка привязок клавиш для консоли"""
        # Контекстное меню
        self.context_menu = tk.Menu(self.console, tearoff=0)
        self.context_menu.add_command(label="📋 Копировать", command=self.copy_selection_menu)
        self.context_menu.add_command(label="✅ Выделить всё", command=self.select_all_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Очистить журнал", command=self.clear_console)

        # Привязки событий
        self.console.bind("<Button-3>", self.show_context_menu)
        self.console.bind("<Control-c>", self.copy_selection)
        self.console.bind("<Control-a>", self.select_all)
        self.console.bind("<Key>", self.on_console_key_press)

    def on_console_key_press(self, event):
        """Обработка нажатий клавиш в консоли"""
        allowed_keys = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A',
                        'Left', 'Right', 'Up', 'Down', 'Home', 'End',
                        'Prior', 'Next', 'Shift_L', 'Shift_R']
        if event.keysym not in allowed_keys:
            return "break"

    def show_context_menu(self, event):
        """Показ контекстного меню"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selection(self, event=None):
        """Копирование выделенного текста"""
        try:
            selected_text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"

    def copy_selection_menu(self):
        """Копирование из контекстного меню"""
        try:
            selected_text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            messagebox.showinfo("Информация", "Сначала выделите текст для копирования")

    def select_all(self, event=None):
        """Выделение всего текста"""
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)
        return "break"

    def select_all_menu(self):
        """Выделение всего текста из меню"""
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)

    def log_message(self, message, msg_type='normal'):
        """Добавление сообщения в консоль с цветовым кодированием"""
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
        """Очистка консоли"""
        self.console.delete(1.0, tk.END)
        self.log_message("Журнал очищен", 'info')

    def run_git_command(self, command, show_command=True):
        """Выполнение Git команды"""
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
        """Проверка установки Git"""
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
        """Проверка настройки пользователя Git"""
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
        """Настройка пользователя Git"""
        # Создаем окно для ввода данных пользователя
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Настройка пользователя Git")
        setup_window.geometry("400x300")
        setup_window.transient(self.root)
        setup_window.grab_set()

        # Центрируем окно
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))

        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(main_frame, text="🔧 Настройка пользователя Git",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Пояснение
        info_text = ("Git нужно знать ваше имя и email для подписи коммитов.\n"
                     "Эти данные будут видны в истории изменений.")
        ttk.Label(main_frame, text=info_text, wraplength=350,
                  justify="left", foreground="gray").pack(pady=(0, 20))

        # Поля ввода
        ttk.Label(main_frame, text="Ваше имя:", font=('Arial', 10, 'bold')).pack(anchor="w")
        name_entry = ttk.Entry(main_frame, font=('Arial', 11), width=30)
        name_entry.pack(fill="x", pady=(5, 15))

        ttk.Label(main_frame, text="Ваш email:", font=('Arial', 10, 'bold')).pack(anchor="w")
        email_entry = ttk.Entry(main_frame, font=('Arial', 11), width=30)
        email_entry.pack(fill="x", pady=(5, 20))

        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def save_user():
            name = name_entry.get().strip()
            email = email_entry.get().strip()

            if not name or not email:
                messagebox.showwarning("Предупреждение", "Заполните все поля!")
                return

            # Настраиваем пользователя
            success1, _ = self.run_git_command(f'git config --global user.name "{name}"')
            success2, _ = self.run_git_command(f'git config --global user.email "{email}"')

            if success1 and success2:
                self.user_info.set(f"✅ {name} ({email})")
                self.log_message(f"Пользователь настроен: {name} ({email})", 'success')
                setup_window.destroy()
                messagebox.showinfo("Успех", "Пользователь Git успешно настроен!")
            else:
                messagebox.showerror("Ошибка", "Не удалось настроить пользователя")

        ttk.Button(buttons_frame, text="💾 Сохранить",
                   command=save_user).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена",
                   command=setup_window.destroy).pack(side="right", padx=(0, 10))

        # Фокус на первое поле
        name_entry.focus()

    def show_beginner_help(self):
        """Показ справки для начинающих"""
        help_window = tk.Toplevel(self.root)
        help_window.title("🆘 Справка для начинающих")
        help_window.geometry("600x500")
        help_window.transient(self.root)

        # Создаем прокручиваемый текст
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill="both", expand=True)

        help_content = """
🆘 СПРАВКА ДЛЯ НАЧИНАЮЩИХ

🤔 ЧТО ТАКОЕ GIT И GITHUB?
Git - это программа для отслеживания изменений в ваших файлах
GitHub - это сайт для хранения ваших проектов в интернете

📚 ОСНОВНЫЕ ПОНЯТИЯ:
• Репозиторий - папка с вашим проектом под контролем Git
• Коммит - сохранение снимка изменений с описанием
• Push - отправка изменений на GitHub
• Pull - загрузка изменений с GitHub

🚀 КАК НАЧАТЬ РАБОТУ:

1️⃣ ПЕРВЫЙ ЗАПУСК:
   • Проверьте установку Git (раздел 1)
   • Настройте пользователя Git (укажите имя и email)

2️⃣ НОВЫЙ ПРОЕКТ:
   • Создайте папку для проекта
   • Выберите её в разделе 2
   • Нажмите "Создать новый репозиторий"

3️⃣ СУЩЕСТВУЮЩИЙ ПРОЕКТ:
   • Выберите папку с проектом в разделе 2
   • Нажмите "Проверить проект"

4️⃣ СОХРАНЕНИЕ ИЗМЕНЕНИЙ:
   • Измените файлы в проекте
   • Обновите статус файлов (раздел 3)
   • Напишите описание изменений (раздел 4)
   • Нажмите "Сохранить все изменения"

5️⃣ ОТПРАВКА НА GITHUB:
   • Создайте репозиторий на GitHub.com
   • Подключите его (кнопка "Подключить к GitHub")
   • Нажмите "Отправить на GitHub"

🔗 ПОЛЕЗНЫЕ ССЫЛКИ:
• Создать аккаунт GitHub: https://github.com/join
• Скачать Git: https://git-scm.com/
• Документация GitHub: https://docs.github.com/

❓ ЧАСТЫЕ ВОПРОСЫ:
Q: Что делать если Git не найден?
A: Скачайте и установите Git с официального сайта

Q: Как создать репозиторий на GitHub?
A: Зайдите на GitHub.com → нажмите "New repository"

Q: Что писать в комментарии к коммиту?
A: Кратко опишите что изменили: "Добавил кнопку входа", "Исправил ошибку"

💡 СОВЕТ: Сохраняйте изменения часто и с понятными комментариями!
        """

        help_text.insert(tk.END, help_content)
        help_text.configure(state=tk.DISABLED)

        # Кнопка закрытия
        close_button = ttk.Button(help_window, text="✅ Понятно",
                                  command=help_window.destroy)
        close_button.pack(pady=10)

    def select_project_folder(self):
        """Выбор папки проекта"""
        folder = filedialog.askdirectory(title="Выберите папку с проектом")
        if folder:
            self.project_path.set(folder)
            self.log_message(f"📁 Выбрана папка: {folder}", 'info')
            self.check_project()

    def check_project(self):
        """Проверка проекта"""
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        self.log_message("📋 ПРОВЕРКА ПРОЕКТА", 'info')
        self.log_message("Анализируем выбранную папку...", 'info')

        # Проверяем, является ли папка Git репозиторием
        success, output = self.run_git_command("git status", False)

        if success:
            self.log_message("✅ Это валидный Git репозиторий!", 'success')

            # Получаем текущую ветку
            success, branch = self.run_git_command("git branch --show-current", False)
            if success and branch:
                self.current_branch.set(f"✅ {branch}")
                self.log_message(f"Текущая ветка: {branch}", 'info')

            # Проверяем удаленный репозиторий
            self.check_remote_repository()

            self.update_file_status()
        else:
            self.current_branch.set("❌ Не Git репозиторий")
            self.remote_info.set("Не подключен")
            self.log_message("❌ Это не Git репозиторий!", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Создать новый репозиторий' для инициализации", 'info')

    def check_remote_repository(self):
        """Проверка удаленного репозитория"""
        self.log_message("Проверяем подключение к удаленному репозиторию...", 'info')

        success, output = self.run_git_command("git remote -v", False)

        if success and output.strip():
            # Парсим информацию о удаленном репозитории
            lines = output.strip().split('\n')
            origins = [line for line in lines if 'origin' in line and '(fetch)' in line]

            if origins:
                remote_url = origins[0].split('\t')[1].split(' ')[0]
                if 'github.com' in remote_url:
                    # Извлекаем имя пользователя и репозитория
                    if remote_url.startswith('https://github.com/'):
                        repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
                    elif remote_url.startswith('git@github.com:'):
                        repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                    else:
                        repo_path = remote_url

                    self.remote_info.set(f"✅ GitHub: {repo_path}")
                    self.log_message(f"Подключен к GitHub: {repo_path}", 'success')
                else:
                    self.remote_info.set(f"✅ {remote_url}")
                    self.log_message(f"Подключен к: {remote_url}", 'success')
            else:
                self.remote_info.set("❌ Не настроен")
                self.log_message("Удаленный репозиторий не настроен", 'error')
        else:
            self.remote_info.set("❌ Не подключен")
            self.log_message("Удаленный репозиторий не подключен", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Подключить к GitHub'", 'info')

    def setup_remote_repository(self):
        """Настройка подключения к удаленному репозиторию"""
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        # Создаем окно для настройки
        setup_window = tk.Toplevel(self.root)
        setup_window.title("🔗 Подключение к GitHub")
        setup_window.geometry("500x400")
        setup_window.transient(self.root)
        setup_window.grab_set()

        # Центрируем окно
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))

        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(main_frame, text="🔗 Подключение к GitHub",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Пояснение
        info_text = ("Чтобы отправлять код на GitHub, нужно подключить локальный\n"
                     "репозиторий к удаленному репозиторию на GitHub.")
        ttk.Label(main_frame, text=info_text, wraplength=450,
                  justify="left", foreground="gray").pack(pady=(0, 20))

        # Инструкция
        instruction_frame = ttk.LabelFrame(main_frame, text="📝 Инструкция", padding="10")
        instruction_frame.pack(fill="x", pady=(0, 20))

        instruction_text = ("1. Перейдите на GitHub.com\n"
                            "2. Создайте новый репозиторий (New repository)\n"
                            "3. Скопируйте URL репозитория\n"
                            "4. Вставьте URL в поле ниже")
        ttk.Label(instruction_frame, text=instruction_text,
                  justify="left").pack(anchor="w")

        # Кнопка для открытия GitHub
        ttk.Button(instruction_frame, text="🌐 Открыть GitHub.com",
                   command=lambda: webbrowser.open("https://github.com/new")).pack(pady=(10, 0))

        # Поле для URL
        ttk.Label(main_frame, text="URL репозитория GitHub:",
                  font=('Arial', 10, 'bold')).pack(anchor="w")

        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=(5, 10))

        url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        url_entry.pack(fill="x")
        url_entry.insert(0, "https://github.com/username/repository.git")

        # Пример URL
        ttk.Label(main_frame,
                  text="💡 Пример: https://github.com/username/my-project.git",
                  foreground="gray", font=('Arial', 9)).pack(anchor="w", pady=(0, 20))

        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def connect_repository():
            url = url_entry.get().strip()

            if not url or url == "https://github.com/username/repository.git":
                messagebox.showwarning("Предупреждение", "Введите корректный URL репозитория!")
                return

            # Проверяем и добавляем удаленный репозиторий
            self.log_message(f"🔗 Подключаем к репозиторию: {url}", 'info')

            # Удаляем старый origin если есть
            self.run_git_command("git remote remove origin", False)

            # Добавляем новый origin
            success, output = self.run_git_command(f'git remote add origin "{url}"')

            if success:
                self.log_message("✅ Удаленный репозиторий успешно подключен!", 'success')
                self.check_remote_repository()  # Обновляем информацию
                setup_window.destroy()
                messagebox.showinfo("Успех", "Репозиторий успешно подключен к GitHub!")
            else:
                messagebox.showerror("Ошибка", f"Не удалось подключить репозиторий:\n{output}")

        ttk.Button(buttons_frame, text="🔗 Подключить",
                   command=connect_repository).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена",
                   command=setup_window.destroy).pack(side="right", padx=(0, 10))

        # Фокус на поле URL
        url_entry.focus()
        url_entry.select_range(0, tk.END)

    def init_repository(self):
        """Инициализация Git репозитория"""
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        result = messagebox.askyesno("Подтверждение",
                                     "Создать новый Git репозиторий в выбранной папке?")
        if not result:
            return

        self.log_message("🚀 СОЗДАНИЕ НОВОГО РЕПОЗИТОРИЯ", 'info')
        self.log_message("Инициализируем Git репозиторий...", 'info')

        success, output = self.run_git_command("git init")

        if success:
            self.log_message("✅ Репозиторий успешно создан!", 'success')
            self.current_branch.set("✅ main (новый)")

            # Создаем .gitignore если его нет
            gitignore_path = os.path.join(self.project_path.get(), '.gitignore')
            if not os.path.exists(gitignore_path):
                try:
                    with open(gitignore_path, 'w', encoding='utf-8') as f:
                        gitignore_content = """# Временные файлы
*.tmp
*.temp
*~

# Системные файлы
.DS_Store
Thumbs.db
desktop.ini

# Файлы редакторов
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*.so
.env
venv/
env/

# Node.js
node_modules/
npm-debug.log*

# Java
*.class
*.jar
target/

# C#
bin/
obj/
*.exe
"""
                        f.write(gitignore_content)
                    self.log_message("📄 Создан файл .gitignore с базовыми настройками", 'success')
                except Exception as e:
                    self.log_message(f"Не удалось создать .gitignore: {e}", 'error')

            # Создаем README.md если его нет
            readme_path = os.path.join(self.project_path.get(), 'README.md')
            if not os.path.exists(readme_path):
                try:
                    project_name = os.path.basename(self.project_path.get())
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        readme_content = f"""# {project_name}

Описание проекта

## Как использовать

1. Опишите как использовать ваш проект
2. Добавьте примеры кода если нужно
3. Укажите требования к системе

## Автор

Ваше имя

## Лицензия

MIT License
"""
                        f.write(readme_content)
                    self.log_message("📄 Создан файл README.md с базовой информацией", 'success')
                except Exception as e:
                    self.log_message(f"Не удалось создать README.md: {e}", 'error')

            self.update_file_status()
            messagebox.showinfo("Успех", "Git репозиторий успешно создан!\n\n"
                                         "Созданы файлы:\n"
                                         "• .gitignore (игнорируемые файлы)\n"
                                         "• README.md (описание проекта)")

    def update_file_status(self):
        """Обновление статуса файлов"""
        if not self.project_path.get():
            return

        self.log_message("📋 ОБНОВЛЕНИЕ СТАТУСА ФАЙЛОВ", 'info')
        self.log_message("Анализируем изменения в проекте...", 'info')

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
                    status_text, description = self.decode_git_status_detailed(status_code)

                    # Добавляем в дерево с цветовым кодированием
                    item_id = self.file_tree.insert('', 'end', text=filename,
                                                    values=(status_text, description))

                    # Цветовое кодирование (работает не во всех темах)
                    if status_code.startswith('M ') or status_code.startswith('A '):
                        self.file_tree.set(item_id, 'status', f"🟢 {status_text}")
                    elif status_code == '??':
                        self.file_tree.set(item_id, 'status', f"🔴 {status_text}")
                    elif status_code.startswith(' M') or status_code.startswith(' A'):
                        self.file_tree.set(item_id, 'status', f"🟡 {status_text}")
                    else:
                        self.file_tree.set(item_id, 'status', f"⚪ {status_text}")

            self.log_message(f"📊 Найдено {len(lines)} файлов с изменениями", 'info')
        else:
            self.log_message("✅ Рабочая директория чистая - нет изменений", 'success')

    def decode_git_status_detailed(self, code):
        """Подробная расшифровка кодов статуса Git"""
        status_map = {
            'M ': ('Готов к коммиту', 'Изменения добавлены в staging area'),
            ' M': ('Изменен', 'Файл изменен, но не добавлен для коммита'),
            'A ': ('Готов к коммиту', 'Новый файл добавлен в staging area'),
            ' A': ('Добавлен', 'Новый файл, но не добавлен для коммита'),
            'D ': ('Готов к коммиту', 'Файл удален и готов к коммиту'),
            ' D': ('Удален', 'Файл удален, но изменение не добавлено'),
            '??': ('Не отслеживается', 'Новый файл, не добавленный в Git'),
            'R ': ('Переименован', 'Файл переименован и готов к коммиту'),
            'C ': ('Скопирован', 'Файл скопирован и готов к коммиту'),
            'MM': ('Частично готов', 'Есть изменения в staging и рабочей области'),
            'AM': ('Частично готов', 'Новый файл с дополнительными изменениями'),
        }

        result = status_map.get(code, (f'Неизвестно ({code})', 'Неизвестный статус файла'))
        return result[0], result[1]

    def auto_fill_commit_message(self):
        """Автоматическое заполнение комментария"""
        self.log_message("✨ Генерируем автоматический комментарий...", 'info')

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M")

        # Получаем статистику изменений
        success, output = self.run_git_command("git diff --stat", False)

        message = f"Обновление от {date_str}"

        if success and output:
            lines = output.strip().split('\n')
            # Подсчитываем файлы (исключаем итоговую строку)
            files_lines = [l for l in lines if '|' in l]
            files_changed = len(files_lines)

            if files_changed > 0:
                message = f"Обновление проекта - изменено файлов: {files_changed}"

        # Проверяем типы изменений
        success, status_output = self.run_git_command("git status --porcelain", False)
        if success and status_output:
            new_files = len([l for l in status_output.split('\n') if l.startswith('??')])
            modified_files = len([l for l in status_output.split('\n') if ' M' in l or 'M ' in l])

            details = []
            if new_files > 0:
                details.append(f"добавлено файлов: {new_files}")
            if modified_files > 0:
                details.append(f"изменено файлов: {modified_files}")

            if details:
                message = f"Обновление проекта - {', '.join(details)}"

        self.commit_text.delete(1.0, tk.END)
        self.commit_text.insert(1.0, message)

        self.log_message(f"📝 Создан комментарий: {message}", 'success')

    def commit_selected_file(self):
        """Коммит выбранного файла"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите файл для коммита!")
            return

        filename = self.file_tree.item(selection[0])['text']
        commit_message = self.commit_text.get(1.0, tk.END).strip()

        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание изменений!")
            return

        self.log_message(f"💾 СОХРАНЕНИЕ ФАЙЛА: {filename}", 'info')
        self.log_message("Добавляем файл и создаем коммит...", 'info')

        # Добавляем файл в staging area
        success, output = self.run_git_command(f'git add "{filename}"')

        if success:
            # Создаем коммит
            success, output = self.run_git_command(f'git commit -m "{commit_message}"')

            if success:
                self.log_message(f"✅ Файл {filename} успешно сохранен!", 'success')
                self.update_file_status()
                messagebox.showinfo("Успех", f"Файл {filename} успешно сохранен в Git!")
        else:
            self.log_message(f"❌ Ошибка при добавлении файла", 'error')

    def commit_all_changes(self):
        """Коммит всех изменений"""
        commit_message = self.commit_text.get(1.0, tk.END).strip()

        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание изменений!")
            return

        self.log_message("💾 СОХРАНЕНИЕ ВСЕХ ИЗМЕНЕНИЙ", 'info')
        self.log_message("Добавляем все файлы и создаем коммит...", 'info')

        # Проверяем есть ли изменения
        success, output = self.run_git_command("git status --porcelain", False)

        if not success or not output.strip():
            self.log_message("ℹ️ Нет изменений для сохранения", 'info')
            messagebox.showinfo("Информация", "Нет изменений для сохранения!")
            return

        # Добавляем все файлы
        success, output = self.run_git_command("git add .")

        if success:
            # Создаем коммит
            success, output = self.run_git_command(f'git commit -m "{commit_message}"')

            if success:
                self.log_message("✅ Все изменения успешно сохранены!", 'success')
                self.update_file_status()

                # Очищаем поле комментария
                self.commit_text.delete(1.0, tk.END)

                messagebox.showinfo("Успех", "Все изменения успешно сохранены в Git!")
            else:
                if "nothing to commit" in output.lower():
                    self.log_message("ℹ️ Нет новых изменений для сохранения", 'info')
                    messagebox.showinfo("Информация", "Нет новых изменений для сохранения!")
        else:
            self.log_message("❌ Ошибка при добавлении файлов", 'error')

    def push_to_github(self):
        """Отправка изменений в GitHub"""
        # Проверяем подключение к удаленному репозиторию
        if "Не подключен" in self.remote_info.get() or "❌" in self.remote_info.get():
            result = messagebox.askyesno("Репозиторий не подключен",
                                         "Удаленный репозиторий не подключен.\n"
                                         "Подключить к GitHub сейчас?")
            if result:
                self.setup_remote_repository()
                return
            else:
                return

        # Проверяем есть ли коммиты для отправки
        success, output = self.run_git_command("git log --oneline -1", False)
        if not success or not output.strip():
            messagebox.showwarning("Предупреждение",
                                   "Нет коммитов для отправки!\n"
                                   "Сначала сохраните изменения.")
            return

        result = messagebox.askyesno("Подтверждение",
                                     "Отправить сохраненные изменения на GitHub?\n\n"
                                     "Это сделает ваши изменения видимыми в интернете.")

        if not result:
            return

        self.log_message("🚀 ОТПРАВКА НА GITHUB", 'info')
        self.log_message("Загружаем изменения в удаленный репозиторий...", 'info')

        # Получаем текущую ветку
        success, branch = self.run_git_command("git branch --show-current", False)

        if success and branch:
            # Push в удаленный репозиторий
            success, output = self.run_git_command(f"git push origin {branch}")

            if success:
                self.log_message("✅ Изменения успешно отправлены на GitHub!", 'success')

                # Получаем URL репозитория для показа пользователю
                success_remote, remote_output = self.run_git_command("git remote get-url origin", False)
                if success_remote and remote_output:
                    repo_url = remote_output.strip().replace('.git', '')
                    if not repo_url.startswith('http'):
                        repo_url = repo_url.replace('git@github.com:', 'https://github.com/')

                    result = messagebox.askyesno("Успех",
                                                 f"Изменения успешно отправлены на GitHub!\n\n"
                                                 f"Хотите открыть репозиторий в браузере?")
                    if result:
                        webbrowser.open(repo_url)
                else:
                    messagebox.showinfo("Успех", "Изменения успешно отправлены на GitHub!")
            else:
                self.log_message(f"❌ Ошибка при отправке: {output}", 'error')

                # Подсказки для решения проблем
                if "No such remote 'origin'" in output:
                    self.log_message("💡 РЕШЕНИЕ: Подключите удаленный репозиторий", 'info')
                    messagebox.showerror("Ошибка", "Удаленный репозиторий не подключен!\n"
                                                   "Нажмите 'Подключить к GitHub'")
                elif "Permission denied" in output or "access" in output.lower():
                    self.log_message("💡 РЕШЕНИЕ: Проблема с правами доступа", 'info')
                    self.log_message("Возможные причины:", 'info')
                    self.log_message("• Неправильный пароль или токен доступа", 'info')
                    self.log_message("• Нет прав на запись в репозиторий", 'info')
                    self.log_message("• Требуется настройка SSH ключа", 'info')

                    messagebox.showerror("Ошибка доступа",
                                         "Нет прав для записи в репозиторий!\n\n"
                                         "Возможные причины:\n"
                                         "• Неправильный пароль\n"
                                         "• Нужен Personal Access Token\n"
                                         "• Нет прав на репозиторий")
                elif "nothing to push" in output:
                    self.log_message("ℹ️ Нет новых изменений для отправки", 'info')
                    messagebox.showinfo("Информация", "Нет новых изменений для отправки!")
                elif "failed to push" in output.lower():
                    self.log_message("💡 РЕШЕНИЕ: Возможно нужно сначала загрузить изменения", 'info')
                    result = messagebox.askyesno("Конфликт",
                                                 "Не удалось отправить изменения.\n"
                                                 "Возможно в удаленном репозитории есть новые изменения.\n\n"
                                                 "Попробовать принудительную отправку?\n"
                                                 "(Внимание: это может перезаписать удаленные изменения)")
                    if result:
                        success, output = self.run_git_command(f"git push origin {branch} --force")
                        if success:
                            self.log_message("✅ Принудительная отправка выполнена успешно!", 'success')
                            messagebox.showinfo("Успех", "Изменения отправлены на GitHub!")
                        else:
                            self.log_message(f"❌ Принудительная отправка не удалась: {output}", 'error')
                else:
                    self.log_message("💡 Проверьте интернет-соединение и настройки", 'info')
        else:
            self.log_message("❌ Не удалось определить текущую ветку", 'error')


def main():
    root = tk.Tk()
    app = GitHubHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()