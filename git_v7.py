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

        # Создаём прокручиваемый фрейм для левой части
        self.setup_scrollable_ui()

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
        ttk.Label(info_frame, textvariable=self.remote_info, wraplength=300).grid(row=1, column=1, sticky="w", padx=(5, 0))

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
        ttk.Label(console_frame, text="Ctrl+C — копировать", foreground="gray", font=('Arial', 8)).pack(side="left", padx=5)

        self.log_message("🎉 Добро пожаловать в GitHub Helper!", 'info')
        self.log_message("Начните с проверки системы и выбора папки проекта.", 'info')

    # Остальные методы без изменений
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
        # Без изменений
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

        info_text = ("Git нужно знать ваше имя и email для подписи коммитов. Эти данные будут видны в истории изменений.")
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
        # Без изменений
        help_window = tk.Toplevel(self.root)
        help_window.title("🆘 Справка для начинающих")
        help_window.geometry("600x500")
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill="both", expand=True)
        help_content = """
        ... (полный текст остаётся без изменений) ...
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
        success, output = self.run_git_command(f"git push -u origin {current_branch}")
        if success:
            self.log_message("✅ Изменения успешно отправлены на GitHub!", 'success')
            # Обновляем статус подключения
            self.root.after(100, self.check_remote_repository)
        else:
            self.log_message(f"❌ Не удалось отправить изменения: {output}", 'error')
            if "authentication" in output.lower() or "denied" in output.lower():
                self.log_message(
                    "💡 Проблема с аутентификацией. Возможно, нужно настроить SSH ключи или Personal Access Token",
                    'info')

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

                # Обновляем информацию в основном окне
                self.check_remote_repository()

                setup_window.destroy()
                messagebox.showinfo("Успех",
                                    "Репозиторий успешно подключен к GitHub!\n\nТеперь вы можете отправлять изменения на GitHub.")
            else:
                status_var.set("❌ Ошибка подключения")
                messagebox.showerror("Ошибка", f"Не удалось подключить репозиторий:\n\n{output}")

        def test_connection():
            url = url_entry.get().strip()
            if not url or url == example_url:
                messagebox.showwarning("Предупреждение", "Введите URL репозитория для тестирования!")
                return

            status_var.set("⏳ Тестирование...")
            setup_window.update()

            # Простая проверка формата URL
            if not (url.startswith('https://github.com/') or url.startswith('git@github.com:')):
                status_var.set("❌ Неверный формат URL")
                messagebox.showwarning("Предупреждение",
                                       "URL должен начинаться с https://github.com/ или git@github.com:")
                return

            status_var.set("✅ URL корректен")
            messagebox.showinfo("Тест", "URL выглядит корректно. Нажмите 'Подключить' для завершения.")

        ttk.Button(buttons_frame, text="🧪 Тест URL",
                   command=test_connection).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="🔗 Подключить",
                   command=connect_repository).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="❌ Отмена",
                   command=setup_window.destroy).pack(side="right")

        url_entry.focus()
        url_entry.select_range(0, tk.END)

    def init_repository(self):
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
            self.connection_status.set("❌ Репозиторий не подключен")

            # Создаем .gitignore если его нет
            gitignore_path = os.path.join(self.project_path.get(), '.gitignore')
            if not os.path.exists(gitignore_path):
                self.log_message("Создаем стандартный файл .gitignore...", 'info')
                try:
                    with open(gitignore_path, "w", encoding='utf-8') as f:
                        f.write("__pycache__/\n")
                        f.write("*.pyc\n")
                        f.write("venv/\n")
                        f.write(".vscode/\n")
                        f.write("*.log\n")
                    self.log_message("✅ .gitignore успешно создан.", 'success')
                except Exception as e:
                    self.log_message(f"❌ Не удалось создать .gitignore: {str(e)}", 'error')

            # Делаем первый коммит
            self.log_message("Делаем первый коммит...", 'info')
            self.run_git_command("git add .")
            self.run_git_command('git commit -m "Initial commit"')
            self.log_message("✅ Проект готов к работе!", 'success')
            self.check_project()
        else:
            self.log_message(f"❌ Не удалось инициализировать репозиторий: {output}", 'error')

    def update_file_status(self):
        if not self.project_path.get() or self.current_branch.get() == "❌ Не Git репозиторий":
            self.log_message("⚠️ Сначала выберите валидный Git репозиторий!", 'info')
            return

        self.log_message("🔄 Обновляем статус файлов...", 'info')
        self.file_tree.delete(*self.file_tree.get_children())

        success, output = self.run_git_command("git status --porcelain", False)
        if success:
            lines = output.strip().split('\n')
            if not lines or output.strip() == "":
                self.file_tree.insert('', 'end', text="Нет изменений для коммита",
                                      values=('✅ Чисто', 'Все файлы сохранены'), tags=('status_clean',))
                self.log_message("✅ Рабочий каталог чист, нет изменений для коммита.", 'success')
                return

            for line in lines:
                status = line[0:2].strip()
                #filename = line[3:].strip()
                parts = line.strip().split(' ', 2)
                filename = parts[2].strip() if len(parts) > 2 else parts[-1].strip()
                if status == '??':
                    self.file_tree.insert('', 'end', text=filename,
                                          values=('❌ Не отслеживается', 'Нужно добавить'), tags=('status_untracked',))
                elif status in ('M', 'A', 'D', 'R', 'C'):
                    if status == 'M':
                        description = 'Изменен'
                    elif status == 'A':
                        description = 'Добавлен'
                    elif status == 'D':
                        description = 'Удален'
                    else:
                        description = 'Изменен/Переименован'
                    self.file_tree.insert('', 'end', text=filename,
                                          values=('⚠️ Изменено', description), tags=('status_modified',))

            # Раскрашиваем строки
            self.file_tree.tag_configure('status_untracked', background='#ffcccc')  # Красный
            self.file_tree.tag_configure('status_modified', background='#ffff99')  # Желтый
            self.file_tree.tag_configure('status_clean', background='#ccffcc')  # Зеленый
            self.log_message("✅ Статус файлов обновлен.", 'success')
        else:
            self.log_message("❌ Не удалось получить статус файлов.", 'error')

    def auto_fill_commit_message(self):
        # На основе статуса файлов генерируем сообщение
        success, output = self.run_git_command("git status --porcelain", False)
        if not success or not output.strip():
            messagebox.showinfo("Информация", "Нет изменений для коммита. Автозаполнение невозможно.")
            return

        lines = output.strip().split('\n')
        messages = []
        for line in lines:
            status = line[0:2].strip()
            filename = line[3:].strip()
            if status == '??':
                messages.append(f"Добавлен новый файл: {os.path.basename(filename)}")
            elif status == 'M':
                messages.append(f"Изменён файл: {os.path.basename(filename)}")
            elif status == 'A':
                messages.append(f"Добавлен файл в индекс: {os.path.basename(filename)}")
            elif status == 'D':
                messages.append(f"Удален файл: {os.path.basename(filename)}")

        message = ", ".join(messages)
        if len(message) > 80:
            message = "Обновлены файлы: " + ", ".join([os.path.basename(l[3:].strip()) for l in lines])

        self.commit_text.delete(1.0, tk.END)
        self.commit_text.insert(tk.END, message)
        self.log_message("Авто-комментарий сгенерирован.", 'info')

    def commit_all_changes(self):
        if not self.project_path.get() or self.current_branch.get() == "❌ Не Git репозиторий":
            messagebox.showwarning("Предупреждение", "Сначала выберите валидный Git репозиторий!")
            return

        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание коммита!")
            return

        self.log_message("💾 СОХРАНЕНИЕ ВСЕХ ИЗМЕНЕНИЙ", 'info')
        self.log_message("Добавляем все файлы в индекс...", 'info')

        add_success, add_output = self.run_git_command("git add .")
        if add_success:
            self.log_message("Коммитим изменения...", 'info')
            commit_success, commit_output = self.run_git_command(f'git commit -m "{commit_message}"')
            if commit_success:
                self.log_message("✅ Все изменения успешно сохранены!", 'success')
                self.update_file_status()
                # Очищаем поле комментария после успешного коммита
                self.commit_text.delete(1.0, tk.END)
            else:
                self.log_message(f"❌ Ошибка при коммите: {commit_output}", 'error')
        else:
            self.log_message(f"❌ Ошибка при добавлении файлов: {add_output}", 'error')

    def commit_selected_file(self):
        selected_item = self.file_tree.focus()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите файл для коммита из списка!")
            return

        filename = self.file_tree.item(selected_item, 'text')
        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание коммита!")
            return

        self.log_message(f"💾 СОХРАНЕНИЕ ФАЙЛА: {filename}", 'info')
        self.log_message(f"Добавляем файл {filename} в индекс...", 'info')

        add_success, add_output = self.run_git_command(f'git add "{filename}"')
        if add_success:
            self.log_message("Коммитим изменения...", 'info')
            commit_success, commit_output = self.run_git_command(f'git commit -m "{commit_message}"')
            if commit_success:
                self.log_message(f"✅ Файл {filename} успешно сохранен!", 'success')
                self.update_file_status()
                # Очищаем поле комментария после успешного коммита
                self.commit_text.delete(1.0, tk.END)
            else:
                self.log_message(f"❌ Ошибка при коммите: {commit_output}", 'error')
        else:
            self.log_message(f"❌ Ошибка при добавлении файла: {add_output}", 'error')


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubHelper(root)
    root.mainloop()


    # # Остальные методы (check_project, check_remote_repository, push_to_github и т.д.) — без изменений
    # # Можно вставить сюда, если нужно, но они не затрагивают UI
    #
    # # Для краткости, ниже — только сигнатуры, тело остаётся как в оригинале
    # def check_project(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def check_remote_repository(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def test_remote_connection(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def push_to_github(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def _run_push(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def setup_remote_repository(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def init_repository(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def update_file_status(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def auto_fill_commit_message(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def commit_all_changes(self):
    #     # ... (оригинальное тело)
    #     pass
    #
    # def commit_selected_file(self):
    #     # ... (оригинальное тело)
    #     pass

#
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = GitHubHelper(root)
#     root.mainloop()