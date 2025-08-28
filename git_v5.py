import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
from datetime import datetime
import threading
import sys
import webbrowser


class GitHubHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Helper - Помощник для работы с Git")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')

        self.project_path = tk.StringVar()
        self.current_branch = tk.StringVar(value="Не определена")
        self.git_status = tk.StringVar(value="Git не найден")
        self.remote_info = tk.StringVar(value="Не подключен")
        self.user_info = tk.StringVar(value="Не настроен")

        self.setup_ui()
        self.check_git_installation()

    def setup_ui(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(left_frame, weight=3)

        right_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_frame, weight=1)

        title_label = ttk.Label(left_frame, text="🔧 GitHub Helper - Помощник для новичков",
                                font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        subtitle_label = ttk.Label(left_frame,
                                   text="Простой интерфейс для работы с Git и GitHub без командной строки",
                                   font=('Arial', 10), foreground="gray")
        subtitle_label.pack(pady=(0, 20))

        system_frame = ttk.LabelFrame(left_frame, text="🔍 1. Проверка системы и настроек", padding="15")
        system_frame.pack(fill="x", pady=(0, 15))
        git_info_frame = ttk.Frame(system_frame)
        git_info_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(git_info_frame, text="Git:", font=('Arial', 10, 'bold')).pack(anchor="w")
        git_status_frame = ttk.Frame(git_info_frame)
        git_status_frame.pack(fill="x", padx=(20, 0))
        ttk.Label(git_status_frame, textvariable=self.git_status).pack(side="left")
        ttk.Button(git_status_frame, text="Проверить Git",
                   command=self.check_git_installation).pack(side="right")
        user_info_frame = ttk.Frame(system_frame)
        user_info_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(user_info_frame, text="Пользователь Git:", font=('Arial', 10, 'bold')).pack(anchor="w")
        user_status_frame = ttk.Frame(user_info_frame)
        user_status_frame.pack(fill="x", padx=(20, 0))
        ttk.Label(user_status_frame, textvariable=self.user_info).pack(side="left")
        ttk.Button(user_status_frame, text="Настроить пользователя",
                   command=self.setup_git_user).pack(side="right", padx=(10, 0))
        help_button = ttk.Button(system_frame, text="🆘 Помощь для начинающих",
                                 command=self.show_beginner_help)
        help_button.pack(anchor="w", pady=(10, 0))

        project_frame = ttk.LabelFrame(left_frame, text="📁 2. Выбор и информация о проекте", padding="15")
        project_frame.pack(fill="x", pady=(0, 15))
        path_frame = ttk.Frame(project_frame)
        path_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(path_frame, text="Путь к проекту:").pack(anchor="w")
        entry_frame = ttk.Frame(path_frame)
        entry_frame.pack(fill="x", pady=(5, 0))
        ttk.Entry(entry_frame, textvariable=self.project_path,
                  font=('Arial', 9)).pack(side="left", fill="x", expand=True)
        ttk.Button(entry_frame, text="Выбрать папку",
                   command=self.select_project_folder).pack(side="right", padx=(10, 0))
        info_frame = ttk.Frame(project_frame)
        info_frame.pack(fill="x", pady=(10, 0))
        branch_frame = ttk.Frame(info_frame)
        branch_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(branch_frame, text="Текущая ветка:", width=20).pack(side="left")
        ttk.Label(branch_frame, textvariable=self.current_branch).pack(side="left", padx=(10, 0))
        remote_frame = ttk.Frame(info_frame)
        remote_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(remote_frame, text="Удаленный репозиторий:", width=20).pack(side="left")
        ttk.Label(remote_frame, textvariable=self.remote_info, wraplength=400).pack(side="left", padx=(10, 0))
        project_buttons_frame = ttk.Frame(project_frame)
        project_buttons_frame.pack(fill="x", pady=(15, 0))
        ttk.Button(project_buttons_frame, text="🔍 Проверить проект",
                   command=self.check_project).pack(side="left", padx=(0, 10))
        ttk.Button(project_buttons_frame, text="🆕 Создать новый репозиторий",
                   command=self.init_repository).pack(side="left", padx=(0, 10))
        ttk.Button(project_buttons_frame, text="🔗 Подключить к GitHub",
                   command=self.setup_remote_repository).pack(side="left")

        status_frame = ttk.LabelFrame(left_frame, text="📋 3. Статус файлов проекта", padding="15")
        status_frame.pack(fill="both", expand=True, pady=(0, 15))
        status_header_frame = ttk.Frame(status_frame)
        status_header_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(status_header_frame, text="🔄 Обновить статус файлов",
                   command=self.update_file_status).pack(side="left")
        ttk.Label(status_header_frame,
                  text="💡 Совет: Зеленые файлы готовы к коммиту, красные - требуют добавления",
                  foreground="gray").pack(side="right")
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
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                       command=self.file_tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.file_tree.configure(yscrollcommand=tree_scrollbar.set)

        commit_frame = ttk.LabelFrame(left_frame, text="💾 4. Сохранение изменений (коммит)", padding="15")
        commit_frame.pack(fill="x", pady=(0, 15))
        commit_info = ttk.Label(commit_frame,
                                text="ℹ️ Коммит - это сохранение снимка ваших изменений с описанием того, что вы сделали",
                                foreground="blue", font=('Arial', 9))
        commit_info.pack(anchor="w", pady=(0, 10))
        comment_frame = ttk.Frame(commit_frame)
        comment_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(comment_frame, text="Опишите ваши изменения:", font=('Arial', 10, 'bold')).pack(anchor="w")
        text_frame = ttk.Frame(comment_frame)
        text_frame.pack(fill="x", pady=(5, 0))
        self.commit_text = tk.Text(text_frame, height=3, width=50, wrap=tk.WORD)
        self.commit_text.pack(side="left", fill="x", expand=True)
        comment_buttons_frame = ttk.Frame(text_frame)
        comment_buttons_frame.pack(side="right", padx=(10, 0), fill="y")
        ttk.Button(comment_buttons_frame, text="✨ Авто-комментарий",
                   command=self.auto_fill_commit_message).pack(fill="x", pady=(0, 5))
        ttk.Button(comment_buttons_frame, text="🗑️ Очистить",
                   command=lambda: self.commit_text.delete(1.0, tk.END)).pack(fill="x")
        examples_label = ttk.Label(comment_frame,
                                   text="💡 Примеры: 'Добавил новую функцию входа', 'Исправил ошибку в калькуляторе', 'Обновил документацию'",
                                   foreground="gray", font=('Arial', 8))
        examples_label.pack(anchor="w", pady=(5, 0))
        commit_buttons_frame = ttk.Frame(commit_frame)
        commit_buttons_frame.pack(fill="x", pady=(15, 0))
        ttk.Button(commit_buttons_frame, text="💾 Сохранить выбранный файл",
                   command=self.commit_selected_file).pack(side="left", padx=(0, 10))
        ttk.Button(commit_buttons_frame, text="💾 Сохранить все изменения",
                   command=self.commit_all_changes).pack(side="left", padx=(0, 10))
        ttk.Button(commit_buttons_frame, text="🚀 Отправить на GitHub",
                   command=self.push_to_github).pack(side="left")

        console_frame = ttk.LabelFrame(right_frame, text="📺 5. Журнал операций и подсказки", padding="15")
        console_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.console = scrolledtext.ScrolledText(console_frame, height=12,
                                                 wrap=tk.WORD, state=tk.NORMAL,
                                                 font=('Consolas', 9))
        self.console.pack(fill="both", expand=True, pady=(0, 10))
        self.console.tag_configure('command', foreground='blue', font=('Consolas', 9, 'bold'))
        self.console.tag_configure('success', foreground='green')
        self.console.tag_configure('error', foreground='red')
        self.console.tag_configure('info', foreground='orange')
        self.setup_console_bindings()
        console_buttons_frame = ttk.Frame(console_frame)
        console_buttons_frame.pack(fill="x")
        ttk.Button(console_buttons_frame, text="🗑️ Очистить журнал",
                   command=self.clear_console).pack(side="left", padx=(0, 10))
        ttk.Label(console_buttons_frame,
                  text="💡 Выделяйте текст мышью и копируйте Ctrl+C",
                  foreground="gray", font=('Arial', 8)).pack(side="left", padx=(10, 0))
        self.log_message("🎉 Добро пожаловать в GitHub Helper!", 'info')
        self.log_message("Этот инструмент поможет вам работать с Git и GitHub без командной строки.", 'info')
        self.log_message("Начните с проверки системы и выбора папки проекта.", 'info')

    def setup_console_bindings(self):
        self.context_menu = tk.Menu(self.console, tearoff=0)
        self.context_menu.add_command(label="📋 Копировать", command=self.copy_selection_menu)
        self.context_menu.add_command(label="✅ Выделить всё", command=self.select_all_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Очистить журнал", command=self.clear_console)
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
        success, output = self.run_git_command("git --version", False)
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
        info_text = ("Git нужно знать ваше имя и email для подписи коммитов.\n"
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

        ttk.Button(buttons_frame, text="💾 Сохранить",
                   command=save_user).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена",
                   command=setup_window.destroy).pack(side="right", padx=(0, 10))
        name_entry.focus()

    def show_beginner_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("🆘 Справка для начинающих")
        help_window.geometry("600x500")
        help_window.transient(self.root)
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
        close_button = ttk.Button(help_window, text="✅ Понятно",
                                  command=help_window.destroy)
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
                self.log_message(f"Подключен к: {remote_url}", 'success')
            else:
                self.remote_info.set("❌ Не настроен")
                self.log_message("Удаленный репозиторий не настроен", 'error')
        else:
            self.remote_info.set("❌ Не подключен")
            self.log_message("Удаленный репозиторий не подключен", 'error')
            self.log_message("💡 РЕШЕНИЕ: Нажмите 'Подключить к GitHub'", 'info')

    def push_to_github(self):
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return

        success_remote, output_remote = self.run_git_command("git remote -v", False)
        if not success_remote or not output_remote.strip():
            self.log_message("❌ Удаленный репозиторий не подключен. Открытие окна подключения...", 'error')
            self.setup_remote_repository()
            return

        self.log_message("🚀 ОТПРАВКА НА GITHUB", 'info')
        self.log_message("Отправляем изменения на удаленный репозиторий...", 'info')

        threading.Thread(target=self._run_push).start()

    def _run_push(self):
        success, output = self.run_git_command(
            "git push -u origin " + self.current_branch.get().replace("✅ ", "").strip())
        if success:
            self.log_message("✅ Изменения успешно отправлены на GitHub!", 'success')
        else:
            self.log_message(f"❌ Не удалось отправить изменения:\n{output}", 'error')

    def setup_remote_repository(self):
        if not self.project_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return
        setup_window = tk.Toplevel(self.root)
        setup_window.title("🔗 Подключение к GitHub")
        setup_window.geometry("500x400")
        setup_window.transient(self.root)
        setup_window.grab_set()
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill="both", expand=True)
        ttk.Label(main_frame, text="🔗 Подключение к GitHub",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        info_text = ("Чтобы отправлять код на GitHub, нужно подключить локальный\n"
                     "репозиторий к удаленному репозиторию на GitHub.")
        ttk.Label(main_frame, text=info_text, wraplength=450,
                  justify="left", foreground="gray").pack(pady=(0, 20))
        instruction_frame = ttk.LabelFrame(main_frame, text="📝 Инструкция", padding="10")
        instruction_frame.pack(fill="x", pady=(0, 20))
        instruction_text = ("1. Перейдите на GitHub.com\n"
                            "2. Создайте новый репозиторий (New repository)\n"
                            "3. Скопируйте URL репозитория\n"
                            "4. Вставьте URL в поле ниже")
        ttk.Label(instruction_frame, text=instruction_text,
                  justify="left").pack(anchor="w")
        ttk.Button(instruction_frame, text="🌐 Открыть GitHub.com",
                   command=lambda: webbrowser.open("https://github.com/new")).pack(pady=(10, 0))
        ttk.Label(main_frame, text="URL репозитория GitHub:",
                  font=('Arial', 10, 'bold')).pack(anchor="w")
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=(5, 10))
        url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        url_entry.pack(fill="x")
        url_entry.insert(0, "https://github.com/username/repository.git")
        ttk.Label(main_frame,
                  text="💡 Пример: https://github.com/username/my-project.git",
                  foreground="gray", font=('Arial', 9)).pack(anchor="w", pady=(0, 20))
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        def connect_repository():
            url = url_entry.get().strip()
            if not url or url == "https://github.com/username/repository.git":
                messagebox.showwarning("Предупреждение", "Введите корректный URL репозитория!")
                return
            self.log_message(f"🔗 Подключаем к репозиторию: {url}", 'info')
            self.run_git_command("git remote remove origin", False)
            success, output = self.run_git_command(f'git remote add origin "{url}"')
            if success:
                self.log_message("✅ Удаленный репозиторий успешно подключен!", 'success')
                self.check_remote_repository()
                setup_window.destroy()
                messagebox.showinfo("Успех", "Репозиторий успешно подключен к GitHub!")
            else:
                messagebox.showerror("Ошибка", f"Не удалось подключить репозиторий:\n{output}")

        ttk.Button(buttons_frame, text="🔗 Подключить",
                   command=connect_repository).pack(side="right")
        ttk.Button(buttons_frame, text="❌ Отмена",
                   command=setup_window.destroy).pack(side="right", padx=(0, 10))
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
            self.log_message("Делаем первый коммит...", 'info')
            self.run_git_command("git add .")
            self.run_git_command('git commit -m "Initial commit"')
            self.log_message("✅ Проект готов к работе!", 'success')
            self.check_project()
        else:
            self.log_message(f"❌ Не удалось инициализировать репозиторий: {output}", 'error')

    def update_file_status(self):
        if not self.project_path.get() or "Не Git репозиторий" in self.current_branch.get():
            self.log_message("⚠️ Сначала выберите валидный Git репозиторий!", 'info')
            return
        self.log_message("🔄 Обновляем статус файлов...", 'info')
        self.file_tree.delete(*self.file_tree.get_children())
        success, output = self.run_git_command("git status --porcelain", False)
        if success:
            lines = output.strip().split('\n')
            if not lines or not output.strip():
                self.log_message("✅ Все файлы чистые. Нет изменений для коммита.", 'success')
            else:
                for line in lines:
                    line = line.strip()
                    status = line[0:2].strip()
                    file_name = line[2:].strip()
                    if status == "??":
                        self.file_tree.insert('', 'end', text=file_name, values=('Untracked', 'Новый файл'), tags=('untracked',))
                    elif status == "A":
                        self.file_tree.insert('', 'end', text=file_name, values=('Added', 'Добавлен'), tags=('added',))
                    elif status == "M":
                        self.file_tree.insert('', 'end', text=file_name, values=('Modified', 'Изменен'), tags=('modified',))
                    elif status == "D":
                        self.file_tree.insert('', 'end', text=file_name, values=('Deleted', 'Удален'), tags=('deleted',))
                    elif status == "R":
                        self.file_tree.insert('', 'end', text=file_name, values=('Renamed', 'Переименован'), tags=('renamed',))
                    elif status == "C":
                        self.file_tree.insert('', 'end', text=file_name, values=('Copied', 'Скопирован'), tags=('copied',))
            self.file_tree.tag_configure('untracked', foreground='red')
            self.file_tree.tag_configure('added', foreground='green')
            self.file_tree.tag_configure('modified', foreground='blue')
            self.file_tree.tag_configure('deleted', foreground='purple')
            self.file_tree.tag_configure('renamed', foreground='orange')
            self.file_tree.tag_configure('copied', foreground='brown')
            self.log_message("✅ Статус файлов обновлен.", 'success')
        else:
            self.log_message(f"❌ Не удалось получить статус файлов: {output}", 'error')

    def auto_fill_commit_message(self):
        self.log_message("✨ Создаем авто-комментарий...", 'info')
        commit_message = ""
        success, output = self.run_git_command("git status --porcelain", False)
        if success and output.strip():
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                status = line[0:2].strip()
                file_name = line[2:].strip()
                if status == "??":
                    commit_message += f"Add {file_name}\n"
                elif status == "A":
                    commit_message += f"Add {file_name}\n"
                elif status == "M":
                    commit_message += f"Update {file_name}\n"
                elif status == "D":
                    commit_message += f"Remove {file_name}\n"
            self.commit_text.delete(1.0, tk.END)
            self.commit_text.insert(tk.END, commit_message.strip())
            self.log_message("✅ Авто-комментарий создан.", 'success')
        else:
            self.log_message("❌ Нет изменений для авто-комментария.", 'error')
            self.commit_text.delete(1.0, tk.END)
            self.commit_text.insert(tk.END, "No changes to commit")

    def commit_selected_file(self):
        if not self.project_path.get() or "Не Git репозиторий" in self.current_branch.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return
        selected_item = self.file_tree.focus()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Сначала выберите файл из списка!")
            return
        file_name = self.file_tree.item(selected_item, 'text')
        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание коммита!")
            return
        self.log_message("💾 СОХРАНЕНИЕ ВЫБРАННОГО ФАЙЛА", 'info')
        success_add, _ = self.run_git_command(f'git add "{file_name}"')
        if success_add:
            success_commit, _ = self.run_git_command(f'git commit -m "{commit_message}"')
            if success_commit:
                self.log_message("✅ Файл успешно сохранен (скоммичен)!", 'success')
                self.update_file_status()
            else:
                self.log_message("❌ Не удалось сделать коммит для файла.", 'error')
        else:
            self.log_message("❌ Не удалось добавить файл в staging area.", 'error')

    def commit_all_changes(self):
        if not self.project_path.get() or "Не Git репозиторий" in self.current_branch.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите папку проекта!")
            return
        commit_message = self.commit_text.get(1.0, tk.END).strip()
        if not commit_message:
            messagebox.showwarning("Предупреждение", "Введите описание коммита!")
            return
        self.log_message("💾 СОХРАНЕНИЕ ВСЕХ ИЗМЕНЕНИЙ", 'info')
        success_add, _ = self.run_git_command("git add .")
        if success_add:
            success_commit, _ = self.run_git_command(f'git commit -m "{commit_message}"')
            if success_commit:
                self.log_message("✅ Все изменения успешно сохранены (скоммичены)!", 'success')
                self.update_file_status()
            else:
                self.log_message("❌ Не удалось сделать коммит.", 'error')
        else:
            self.log_message("❌ Не удалось добавить файлы в staging area.", 'error')


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    app = GitHubHelper(root)
    root.mainloop()