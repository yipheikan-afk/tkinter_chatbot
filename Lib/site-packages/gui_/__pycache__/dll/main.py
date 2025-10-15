import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import random
import string
import io
import sqlite3
import hashlib
import datetime
import time
import os


DATABASE_NAME = 'hospital_db.db' 


def connect_db():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def create_tables():
    """Создает необходимые таблицы в базе данных, если они еще не существуют."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            date_of_birth TEXT,
            passport_series TEXT,
            passport_number TEXT,
            phone TEXT,
            email TEXT,
            insurance_policy_number TEXT,
            insurance_policy_type TEXT,
            insurance_company TEXT,
            is_archived INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_lab_technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            is_archived INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accountants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            last_login_datetime TEXT,
            is_archived INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administrators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_archived INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL, -- patient, lab_technician, research_lab_technician, accountant, administrator
            is_archived INTEGER DEFAULT 0,
            last_login_datetime TEXT -- For accountants, others can be null
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients_details (
            user_id INTEGER PRIMARY KEY,
            date_of_birth TEXT,
            passport_series TEXT,
            passport_number TEXT,
            phone TEXT,
            email TEXT,
            insurance_policy_number TEXT,
            insurance_policy_type TEXT,
            insurance_company TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost REAL NOT NULL,
            code TEXT UNIQUE NOT NULL,
            completion_time_days INTEGER,
            avg_deviation REAL,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            creation_date TEXT NOT NULL,
            order_status TEXT NOT NULL,
            completion_time_days INTEGER, -- Может быть рассчитан по услугам
            is_archived INTEGER DEFAULT 0,
            FOREIGN KEY (patient_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            service_status TEXT NOT NULL,
            result TEXT, 
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accountant_id INTEGER NOT NULL,
            insurance_company TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            amount REAL NOT NULL,
            order_id INTEGER,
            FOREIGN KEY (accountant_id) REFERENCES users(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_login TEXT NOT NULL,
            role TEXT NOT NULL,
            login_datetime TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM administrators WHERE login = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO administrators (login, password) VALUES (?, ?)", ('admin', '12345'))

    cursor.execute("SELECT COUNT(*) FROM lab_technicians WHERE login = 'lab_tech1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO lab_technicians (login, password, full_name) VALUES (?, ?, ?)", 
                       ('lab_tech1', hash_password('password123'), 'Иванов Иван Иванович'))
                       
    cursor.execute("SELECT COUNT(*) FROM research_lab_technicians WHERE login = 'res_tech1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO research_lab_technicians (login, password, full_name) VALUES (?, ?, ?)", 
                       ('res_tech1', hash_password('password123'), 'Петров Петр Петрович'))

    cursor.execute("SELECT COUNT(*) FROM accountants WHERE login = 'accountant1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO accountants (login, password, full_name) VALUES (?, ?, ?)", 
                       ('accountant1', hash_password('password123'), 'Сидорова Анна Сергеевна'))
    
    cursor.execute("SELECT COUNT(*) FROM patients WHERE login = 'patient1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO patients (login, password, full_name, date_of_birth, passport_series, passport_number, phone, email, insurance_policy_number, insurance_policy_type, insurance_company) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       ('patient1', hash_password('patientpass'), 'Смирнов Дмитрий Сергеевич', '1990-01-15', '1234', '567890', '89123456789', 'patient@example.com', 'ABC123456', 'ОМС', 'ТООСтраховка'))
    
    cursor.execute("SELECT COUNT(*) FROM patients WHERE login = 'patient2'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO patients (login, password, full_name, date_of_birth, passport_series, passport_number, phone, email, insurance_policy_number, insurance_policy_type, insurance_company) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       ('patient2', hash_password('patientpass2'), 'Кузнецов Олег Игоревич', '1985-05-20', '5678', '123456', '89001112233', 'oleg@example.com', 'XYZ987654', 'ДМС', 'ДБСТРАХ'))
    
    cursor.execute("PRAGMA table_info(order_services)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'result' not in columns:
        cursor.execute("ALTER TABLE order_services ADD COLUMN result TEXT")

    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    if 'last_login_datetime' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login_datetime TEXT")

    conn.commit()
    conn.close()

def insert_initial_data():
    """Вставляет начальные данные в базу данных, если их нет."""
    conn = connect_db()
    cursor = conn.cursor()
    
    users_to_insert = [
        ("admin", hash_password("12345"), "Администратор системы", "administrator", None),
        ("lab", hash_password('12345'), "Иванов Иван Иванович", "lab_technician", None),
        ("res", hash_password('12345'), "Петров Петр Петрович", "research_lab_technician", None),
        ("acc", hash_password('12345'), "Сидорова Анна Сергеевна", "accountant", None),
        ("patient1", hash_password('12345'), "Смирнов Дмитрий Сергеевич", "patient", {
            'date_of_birth': '1990-01-15', 'passport_series': '1234', 'passport_number': '567890',
            'phone': '89123456789', 'email': 'patient@example.com', 'insurance_policy_number': 'ABC123456',


            'insurance_policy_type': 'ОМС', 'insurance_company': 'Nomad Insurance'

        }),
        ("patient2", hash_password('12345'), "Кузнецов Олег Игоревич", "patient", {
            'date_of_birth': '1985-05-20', 'passport_series': '5678', 'passport_number': '123456',
            'phone': '89001112233', 'email': 'oleg@example.com', 'insurance_policy_number': 'XYZ987654',

            'insurance_policy_type': 'ДМС', 'insurance_company': 'Eurasia'
        })
    ]
    
    for login, plain_password, full_name, role, extra_data in users_to_insert: # Изменяем pwd_hash на plain_password
        cursor.execute("SELECT COUNT(*) FROM users WHERE login = ?", (login,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (login, password, full_name, role) VALUES (?, ?, ?, ?)",
                        (login, plain_password, full_name, role)) # Используем plain_password
            user_id = cursor.lastrowid
            if role == "patient" and extra_data:
                cursor.execute("""
                    INSERT INTO patients_details (user_id, date_of_birth, passport_series, passport_number, phone, email, insurance_policy_number, insurance_policy_type, insurance_company)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, extra_data['date_of_birth'], extra_data['passport_series'], extra_data['passport_number'],
                    extra_data['phone'], extra_data['email'], extra_data['insurance_policy_number'],
                    extra_data['insurance_policy_type'], extra_data['insurance_company']))
    
    # Услуги
    services_to_insert = [
        ('Общий анализ крови', 500.00, 'S001', 1, 0.5),
        ('Анализ мочи', 350.00, 'S002', 1, 0.3),
        ('Биохимический анализ крови', 1200.00, 'S003', 2, 0.8),
        ('Глюкоза в крови', 250.00, 'S004', 1, 0.2)
    ]

    for name, cost, code, days, deviation in services_to_insert:
        cursor.execute("SELECT COUNT(*) FROM services WHERE code = ?", (code,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO services (name, cost, code, completion_time_days, avg_deviation) VALUES (?, ?, ?, ?, ?)",
                           (name, cost, code, days, deviation))

    # Тестовые заказы
    cursor.execute("SELECT id FROM users WHERE login = 'patient1'")
    patient_id_1 = cursor.fetchone()
    if patient_id_1:
        patient_id_1 = patient_id_1[0]
        cursor.execute("SELECT COUNT(*) FROM orders WHERE patient_id = ? AND order_status = 'Ожидает оплаты'", (patient_id_1,))
        if cursor.fetchone()[0] == 0:
            order_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO orders (patient_id, creation_date, order_status) VALUES (?, ?, ?)",
                           (patient_id_1, order_date, 'Ожидает оплаты'))
            order_id = cursor.lastrowid
            
            cursor.execute("SELECT id FROM services WHERE code = 'S001'")
            service1_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM services WHERE code = 'S003'")
            service2_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO order_services (order_id, service_id, service_status) VALUES (?, ?, ?)",
                           (order_id, service1_id, 'Ожидает оплаты'))
            cursor.execute("INSERT INTO order_services (order_id, service_id, service_status) VALUES (?, ?, ?)",
                           (order_id, service2_id, 'Ожидает оплаты'))

    cursor.execute("SELECT id FROM users WHERE login = 'patient2'")
    patient_id_2 = cursor.fetchone()
    if patient_id_2:
        patient_id_2 = patient_id_2[0]
        cursor.execute("SELECT COUNT(*) FROM orders WHERE patient_id = ? AND order_status = 'Выполнен'", (patient_id_2,))
        if cursor.fetchone()[0] == 0:
            order_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO orders (patient_id, creation_date, order_status, completion_time_days) VALUES (?, ?, ?, ?)",
                           (patient_id_2, order_date, 'Выполнен', 2))
            order_id_completed = cursor.lastrowid
            
            cursor.execute("SELECT id FROM services WHERE code = 'S002'")
            service_s002_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM services WHERE code = 'S004'")
            service_s004_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO order_services (order_id, service_id, service_status, result) VALUES (?, ?, ?, ?)",
                           (order_id_completed, service_s002_id, 'Выполнена', 'Норма (pH 6.0)'))
            cursor.execute("INSERT INTO order_services (order_id, service_id, service_status, result) VALUES (?, ?, ?, ?)",
                           (order_id_completed, service_s004_id, 'Выполнена', '5.5 ммоль/л'))

    conn.commit()
    conn.close()

# --- 2. Utility Functions ---
def hash_password(password):
    """Хеширует пароль с использованием SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Проверяет соответствие введенного пароля хешированному."""
    return hashed_password == hash_password(user_password)

def generate_captcha(length=4):
    """Генерирует CAPTCHA изображение и текст."""
    width, height = 150, 60
    image = Image.new('RGB', (width, height), color = (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 40) 
    except IOError:
        font = ImageFont.load_default()

    characters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choice(characters) for _ in range(length))

    for i, char in enumerate(captcha_text):
        char_x = random.randint(i * (width // length) + 5, (i + 1) * (width // length) - 25)
        char_y = random.randint(5, height - 45) 
        
        angle = random.randint(-25, 25)
        
        char_img = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((0, 0), char, font=font, fill=(0, 0, 0))
        
        char_img = char_img.rotate(angle, expand=1)
        
        image.paste(char_img, (char_x, char_y), char_img)

        if random.random() > 0.5:
            draw.line((char_x, char_y + random.randint(0, height // 2),
                       char_x + random.randint(20, 40), char_y + random.randint(0, height // 2)),
                      fill=(0, 0, 0), width=2)

    for _ in range(random.randint(50, 100)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    image = image.filter(ImageFilter.SMOOTH)

    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    return captcha_text, byte_arr.getvalue()

def log_login_attempt(user_login, role, status):
    """Записывает попытку входа в систему."""
    conn = connect_db()
    cursor = conn.cursor()
    login_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO login_logs (user_login, role, login_datetime, status) VALUES (?, ?, ?, ?)",
        (user_login, role, login_datetime, status)
    )
    conn.commit()
    conn.close()

def get_login_logs():
    """Извлекает все логи входа."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM login_logs ORDER BY login_datetime DESC")
    logs = cursor.fetchall()
    conn.close()
    return [dict(log) for log in logs]

class SessionTimer:
    """Класс для управления таймером сессии пользователя с использованием Tkinter.after()."""
    def __init__(self, session_duration_minutes, warning_time_minutes, callback_warning, callback_end, master_window):
        self.session_duration_minutes = session_duration_minutes
        self.warning_time_minutes = warning_time_minutes
        self.callback_warning = callback_warning
        self.callback_end = callback_end
        self.master_window = master_window 
        self.start_time = None
        self.after_id = None # Для хранения ID вызова after()
        self.running = False

    def start(self):
        """Запускает таймер сессии."""
        self.start_time = time.time()
        self.running = True
        self._run_timer() # Начинаем рекурсивный вызов

    def _run_timer(self):
        """Основная логика работы таймера, вызываемая через after()."""
        if not self.running: # Проверяем, был ли таймер остановлен извне
            return

        # Проверяем, существует ли главное окно, прежде чем пытаться взаимодействовать с ним.
        if not self.master_window.winfo_exists():
            self.stop() # Останавливаем таймер, если окно исчезло
            return

        elapsed_time = time.time() - self.start_time
        remaining_time = (self.session_duration_minutes * 60) - elapsed_time

        if remaining_time <= self.warning_time_minutes * 60 and remaining_time > 0:
            if self.callback_warning:
                self.callback_warning(remaining_time)
        
        if remaining_time <= 0:
            self.stop()
            if self.callback_end:
                self.callback_end()
            return # Выходим, так как сессия завершена
        
        # Планируем следующий вызов через 1 секунду
        self.after_id = self.master_window.after(1000, self._run_timer)

    def stop(self):
        """Останавливает таймер."""
        self.running = False
        if self.after_id:
            self.master_window.after_cancel(self.after_id)
            self.after_id = None
        self.start_time = None

    def get_remaining_time(self):
        """Возвращает оставшееся время сессии в секундах."""
        if self.running and self.start_time:
            elapsed_time = time.time() - self.start_time
            return max(0, (self.session_duration_minutes * 60) - elapsed_time)
        return 0

# --- 3. Models (Data Access Layer) ---
class User:
    """Статические методы для аутентификации и получения данных пользователя."""
    @staticmethod
    def authenticate(login, password):
        """
        Пытается аутентифицировать пользователя.
        Обновляет last_login_datetime для бухгалтера при успешном входе.
        """
        conn = connect_db()
        cursor = conn.cursor()
        hashed_password = hash_password(password)

        roles_mapping = {
            "patient": "patient",
            "lab_technician": "lab_technician",
            "research_lab_technician": "research_lab_technician",
            "accountant": "accountant",
            "administrator": "administrator"
        }

        cursor.execute("SELECT * FROM users WHERE login = ? AND password = ? AND is_archived = 0", (login, hashed_password))
        user_data = cursor.fetchone()

        if user_data:
            role_name = user_data['role']
            
            # Обновление last_login_datetime для бухгалтера
            if role_name == "accountant":
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute("UPDATE users SET last_login_datetime = ? WHERE id = ?",
                                   (current_datetime, user_data['id']))
                    conn.commit()
                except Exception as e:
                    print(f"Ошибка при обновлении last_login_datetime для бухгалтера: {e}")

            # Если это пациент, подгружаем дополнительные данные
            if role_name == "patient":
                cursor.execute("SELECT * FROM patients_details WHERE user_id = ?", (user_data['id'],))
                patient_details = cursor.fetchone()
                if patient_details:
                    user_dict = dict(user_data)
                    user_dict.update(dict(patient_details)) # Объединяем данные
                    conn.close()
                    return {"role": role_name, "data": user_dict}

            conn.close()
            return {"role": role_name, "data": dict(user_data)}
        
        conn.close()
        return None

class Order:
    """Класс для работы с заказами."""
    def __init__(self, patient_id, creation_date, order_status, completion_time_days=None, id=None, is_archived=0):
        self.id = id
        self.patient_id = patient_id
        self.creation_date = creation_date
        self.order_status = order_status
        self.completion_time_days = completion_time_days
        self.is_archived = is_archived

    def get_services(self):
        """Возвращает список услуг, входящих в данный заказ."""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, os.service_status, os.id AS order_service_id, os.result
            FROM order_services os
            JOIN services s ON os.service_id = s.id
            WHERE os.order_id = ?
        """, (self.id,))
        services_data = cursor.fetchall()
        conn.close()
        return [dict(s) for s in services_data]

    def can_archive(self):
        """Проверяет, может ли заказ быть архивирован (все услуги должны быть выполнены)."""
        services = self.get_services()
        for service in services:
            if service['service_status'] != "Выполнена":
                return False
        return True

# --- 4. GUI Components (refactored) ---

class UserInfoFrame(tk.Frame):
    """Виджет для отображения информации о текущем пользователе."""
    def __init__(self, parent, user_data, role, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.user_data = user_data
        self.role = role
        self.configure(borderwidth=2, relief="groove")

        # Соответствие ролей и файлов изображений
        role_images = {
            "Пациент": "pac.png",
            "Лаборант": "lab.png",
            "Лаборант-исследователь": "lab_res.png",
            "Бухгалтер": "acc.png",
            "Администратор": "admin.png"
        }

        # Получаем путь к изображению для текущей роли
        image_file = role_images.get(self.role)
        
        if not image_file:
            raise ValueError(f"Нет изображения для роли: {self.role}")
        
        # Полный путь к файлу изображения
        image_path = os.path.join(os.path.dirname(__file__), image_file)
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл изображения не найден: {image_path}")

        # Загружаем и отображаем изображение
        try:
            img = Image.open(image_path)
            img = img.resize((50, 50), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            
            tk.Label(self, image=self.photo).pack(side="left", padx=5, pady=5)
            
            info_frame = tk.Frame(self)
            info_frame.pack(side="left", padx=5, pady=5)
            
            full_name = self.user_data.get('full_name', self.user_data.get('login', 'Неизвестно'))
            tk.Label(info_frame, text=f"ФИО: {full_name}").pack(anchor="w")
            tk.Label(info_frame, text=f"Роль: {self.role}").pack(anchor="w")
            
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки изображения: {e}") from e

        info_frame = tk.Frame(self)
        info_frame.pack(side="left", padx=5, pady=5)

 
class BaseRoleWindow(tk.Toplevel):
    """Базовый класс для окон ролей (Лаборант, Бухгалтер, Администратор и т.д.)."""
    def __init__(self, master, user_data, role_name, on_logout_callback, session_timed=False):
        super().__init__(master)
        self.master = master
        self.user_data = user_data
        self.role_name = role_name
        self.on_logout_callback = on_logout_callback
        self.session_timed = session_timed
        self.timer = None
        self.session_blocked = False
        self.warning_shown = False

        self.title(f"Рабочее место {self.role_name}")
        self.geometry("1000x700") # Увеличен размер окна по умолчанию
        self.protocol("WM_DELETE_WINDOW", self.confirm_logout)

        self._create_base_widgets()
        if self.session_timed:
            self.start_session_timer()

    def _create_base_widgets(self):
        """Создает общие виджеты для всех окон ролей."""
        user_info_frame = UserInfoFrame(self, self.user_data, self.role_name)
        user_info_frame.pack(side="top", fill="x", padx=10, pady=10)

        if self.session_timed:
            self.timer_label = tk.Label(self, text="Время сеанса: 00:00", font=("Arial", 14))
            self.timer_label.pack(side="top", anchor="e", padx=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.add_role_specific_tabs()

        tk.Button(self, text="Выход", command=self.confirm_logout).pack(pady=20)

    def add_role_specific_tabs(self):
        """
        Метод для добавления вкладок, специфичных для каждой роли.
        Должен быть переопределен в дочерних классах.
        """
        pass

    def start_session_timer(self):
        """Запускает таймер сессии."""
        self.timer = SessionTimer(
            session_duration_minutes=10, 
            warning_time_minutes=5,
            callback_warning=self._show_timer_warning,
            callback_end=self._end_session,
            master_window=self
        )
        self.timer.start()
        self._update_timer_display()

    def _update_timer_display(self):
        """Обновляет отображение оставшегося времени таймера."""
        if self.timer and self.timer.running:
            remaining_seconds = self.timer.get_remaining_time()
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            self.timer_label.config(text=f"Время сеанса: {minutes:02d}:{seconds:02d}")
            # The SessionTimer class now handles scheduling its own updates via after()
            # so we don't need `self.after(1000, self._update_timer_display)` here
            # Instead, the SessionTimer's _run_timer will call a method that updates this label
            # Let's adjust SessionTimer to update a display label directly or pass back time.
            # For simplicity and to avoid circular dependencies, the current setup of calling _update_timer_display
            # from the BaseRoleWindow is fine, it just needs to be scheduled carefully.
            self.after(1000, self._update_timer_display) # Keep this if SessionTimer doesn't update it.

    def _show_timer_warning(self, remaining_seconds):
        """Показывает предупреждение об окончании сеанса."""
        if not self.session_blocked and not self.warning_shown:
            self.warning_shown = True  # Больше не показывать
            messagebox.showwarning(
                "Предупреждение",
                f"Внимание! До окончания сеанса осталось {int(remaining_seconds / 60)} минут {int(remaining_seconds % 60)} секунд!"
            )


    def _end_session(self):
        """Завершает сессию пользователя и блокирует вход на 1 минуту."""
        if not self.session_blocked: # Предотвращаем повторное завершение
            messagebox.showinfo("Сеанс завершен", "Время сеанса истекло. Вы будете отключены. Вход заблокирован на 1 минуту.")
            self.session_blocked = True
            if self.timer: # Останавливаем таймер явно
                self.timer.stop()
            self.destroy()
            self.on_logout_callback() # Возвращаемся к окну входа
            # Устанавливаем время, до которого вход заблокирован
            self.master.login_block_until = time.time() + 60

    def confirm_logout(self):
        """Подтверждает выход из учетной записи."""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти из учетной записи?"):
            if self.timer: # Останавливаем таймер перед выходом
                self.timer.stop()
            self.destroy()
            self.on_logout_callback()

class LabTechWindow(BaseRoleWindow):
    """Окно рабочего места лаборанта."""
    def __init__(self, master, user_data, on_logout_callback):
        super().__init__(master, user_data, "Лаборант", on_logout_callback, session_timed=True)

    def add_role_specific_tabs(self):
        """Добавляет вкладки для лаборанта."""
        # Для простоты пока используем кнопки на главной вкладке
        tk.Button(self, text="Принять биоматериал", command=self.accept_biomaterial).pack(pady=10)
        tk.Button(self, text="Сформировать отчеты", command=self.generate_reports).pack(pady=10)

    def accept_biomaterial(self):
        """Открывает окно принятия биоматериала."""
        AcceptBiomaterialWindow(self, self.user_data)

    def generate_reports(self):
        """Открывает окно формирования отчетов лаборанта."""
        GenerateLabTechReportsWindow(self, self.user_data)

class ResearchLabTechWindow(BaseRoleWindow):
    """Окно рабочего места лаборанта-исследователя."""
    def __init__(self, master, user_data, on_logout_callback):
        super().__init__(master, user_data, "Лаборант-исследователь", on_logout_callback, session_timed=True)

    def add_role_specific_tabs(self):
        """Добавляет вкладки для лаборанта-исследователя."""
        # Для простоты пока используем кнопки на главной вкладке
        tk.Button(self, text="Работать с анализатором", command=self.work_with_analyzer).pack(pady=10)
        tk.Button(self, text="Просмотр и изменение результатов", command=self.view_edit_results).pack(pady=10)

    def work_with_analyzer(self):
        """Открывает окно симуляции анализатора."""
        AnalyzerSimulationWindow(self)

    def view_edit_results(self):
        """Открывает окно просмотра и редактирования результатов анализов."""
        ViewEditLabResultsWindow(self)

class AccountantWindow(BaseRoleWindow):
    """Окно рабочего места бухгалтера."""
    def __init__(self, master, user_data, on_logout_callback):
        super().__init__(master, user_data, "Бухгалтер", on_logout_callback, session_timed=False) # Бухгалтеры обычно без таймера сессии

    def add_role_specific_tabs(self):
        """Добавляет вкладки для бухгалтера."""
        self.last_login_label = tk.Label(self, text="Последний вход: Неизвестно", font=("Arial", 10))
        self.last_login_label.pack(side="top", anchor="w", padx=10)
        self.update_last_login_time_display()

        # Для простоты пока используем кнопки на главной вкладке
        tk.Button(self, text="Посмотреть отчеты", command=self.view_reports).pack(pady=10)
        tk.Button(self, text="Сформировать счет страховой", command=self.generate_invoice).pack(pady=10)
        tk.Button(self, text="Просмотреть выставленные счета", command=self.view_invoices).pack(pady=10)

    def update_last_login_time_display(self):
        """Обновляет отображение последнего времени входа бухгалтера."""
        conn = connect_db()
        cursor = conn.cursor()
        # Извлекаем last_login_datetime из user_data, которое было обновлено при логине.
        # Это более эффективно, чем снова лезть в БД, если user_data уже актуальны.
        # Однако, если accountant_id не в user_data, или требуется самое последнее значение,
        # то запрос к БД нужен. Предполагаем, что user_data['last_login_datetime'] обновляется.
        # Если нет, то нужно запросить из БД:
        cursor.execute("SELECT last_login_datetime FROM users WHERE id = ?", (self.user_data['id'],))
        last_login = cursor.fetchone()[0]
        self.last_login_label.config(text=f"Последний вход: {last_login if last_login else 'Неизвестно'}")
        conn.close()

    def view_reports(self):
        """Открывает окно отчетов для бухгалтера."""
        ReportsAccountantWindow(self)

    def generate_invoice(self):
        """Открывает окно формирования счета страховой."""
        GenerateInvoiceWindow(self, self.user_data['id'])

    def view_invoices(self):
        """Открывает окно для просмотра выставленных счетов."""
        invoice_viewer_window = tk.Toplevel(self)
        invoice_viewer_window.title("Выставленные счета")
        invoice_viewer_window.geometry("800x600") # Увеличен размер

        tree = ttk.Treeview(invoice_viewer_window, columns=("ID", "Компания", "Дата", "Сумма", "Заказ ID"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Компания", text="Страховая компания")
        tree.heading("Дата", text="Дата")
        tree.heading("Сумма", text="Сумма")
        tree.heading("Заказ ID", text="Заказ ID")

        # Настройка ширины столбцов
        tree.column("ID", width=50, stretch=tk.NO)
        tree.column("Компания", width=200, stretch=tk.YES)
        tree.column("Дата", width=150, stretch=tk.NO)
        tree.column("Сумма", width=100, stretch=tk.NO)
        tree.column("Заказ ID", width=80, stretch=tk.NO)
        
        tree.pack(expand=True, fill="both")

        conn = connect_db()
        cursor = conn.cursor()
        # Получаем accountant_id из user_data
        accountant_id = self.user_data['id'] 
        cursor.execute("SELECT id, insurance_company, invoice_date, amount, order_id FROM invoices WHERE accountant_id = ? ORDER BY invoice_date DESC", (accountant_id,))
        invoices = cursor.fetchall()
        conn.close()

        if not invoices:
            tk.Label(invoice_viewer_window, text="Выставленных счетов пока нет.").pack(pady=20)
        else:
            for invoice in invoices:
                # ВОТ ЗДЕСЬ МОГЛА БЫТЬ ПРОБЛЕМА:
                # Если `invoice` - это sqlite3.Row, то при прямом `values=invoice` 
                # он мог не конвертироваться правильно, или порядок не соответствовать.
                # Явно извлекаем значения по имени:
                tree.insert("", "end", values=(
                    invoice['id'],
                    invoice['insurance_company'],
                    invoice['invoice_date'],
                    f"{invoice['amount']:.2f}", # Форматируем сумму, если это float
                    invoice['order_id']
                ))

class AdminWindow(BaseRoleWindow):
    """Окно рабочего места администратора."""
    def __init__(self, master, user_data, on_logout_callback):
        super().__init__(master, user_data, "Администратор", on_logout_callback, session_timed=False)

    def add_role_specific_tabs(self):
        """Добавляет вкладки для администратора."""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Логи входа")
        self.create_login_logs_tab(logs_frame)

        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="Управление пользователями")
        self.create_user_management_tab(users_frame)

        services_frame = ttk.Frame(self.notebook)
        self.notebook.add(services_frame, text="Управление услугами")
        self.create_services_management_tab(services_frame)

    def create_login_logs_tab(self, parent_frame):
        """Создает вкладку для просмотра логов входа."""
        tree = ttk.Treeview(parent_frame, columns=("Логин", "Роль", "Дата/Время", "Статус"), show="headings")
        tree.heading("Логин", text="Логин")
        tree.heading("Роль", text="Роль")
        tree.heading("Дата/Время", text="Дата и время")
        tree.heading("Статус", text="Статус")

        # Настройка ширины столбцов
        tree.column("Логин", width=150, stretch=tk.YES)
        tree.column("Роль", width=150, stretch=tk.YES)
        tree.column("Дата/Время", width=200, stretch=tk.YES)
        tree.column("Статус", width=100, stretch=tk.YES)

        tree.pack(expand=True, fill="both")
        for log in get_login_logs():
            tree.insert("", "end", values=(log['user_login'], log['role'], log['login_datetime'], log['status']))

    def create_user_management_tab(self, parent_frame):
        """Создает вкладку для управления пользователями."""
        self.user_tree = ttk.Treeview(parent_frame, columns=("ID", "Логин", "ФИО", "Роль", "Архивирован"), show="headings")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Логин", text="Логин")
        self.user_tree.heading("ФИО", text="ФИО")
        self.user_tree.heading("Роль", text="Роль")
        self.user_tree.heading("Архивирован", text="Архивирован")

        # Настройка ширины столбцов
        self.user_tree.column("ID", width=50, stretch=tk.NO)
        self.user_tree.column("Логин", width=120, stretch=tk.YES)
        self.user_tree.column("ФИО", width=250, stretch=tk.YES) # Увеличенная ширина
        self.user_tree.column("Роль", width=150, stretch=tk.YES)
        self.user_tree.column("Архивирован", width=100, stretch=tk.NO)

        self.user_tree.pack(expand=True, fill="both")
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)

        control_frame = tk.Frame(parent_frame)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Заблокировать/Разблокировать", command=self.toggle_user_block).pack(side="left", padx=5)
        tk.Button(control_frame, text="Сбросить пароль", command=self.reset_password).pack(side="left", padx=5)
        tk.Button(control_frame, text="Обновить список", command=self.load_users).pack(side="left", padx=5)
        self.load_users()

    def load_users(self):
        """Загружает список пользователей в Treeview."""
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        conn = connect_db()
        cursor = conn.cursor()
        
        # Получаем всех пользователей из общей таблицы
        cursor.execute("SELECT id, login, full_name, role, is_archived FROM users")
        for user in cursor.fetchall():
            # Если full_name пустое (например, для admin, если не заполнено), используем логин
            display_name = user['full_name'] if user['full_name'] else user['login'] 
            self.user_tree.insert("", "end", values=(user['id'], user['login'], display_name, user['role'], "Да" if user['is_archived'] else "Нет"), iid=f"{user['role']}_{user['id']}")
        conn.close()

    def on_user_select(self, event):
        """Обработчик выбора пользователя в Treeview."""
        selected_item = self.user_tree.focus()
        if selected_item:
            values = self.user_tree.item(selected_item, "values")
            self.selected_user_id, self.selected_user_role = values[0], values[3]
        else: 
            self.selected_user_id, self.selected_user_role = None, None

    def _execute_user_action(self, action_type, success_msg, error_msg, value=None):
        """Вспомогательная функция для выполнения действий над пользователями."""
        if not self.selected_user_id:
            messagebox.showwarning("Ошибка", "Выберите пользователя.")
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        try:
            if action_type == "toggle_archive":
                cursor.execute(f"SELECT is_archived FROM users WHERE id = ?", (self.selected_user_id,))
                current_status = cursor.fetchone()[0]
                new_status = 1 if current_status == 0 else 0
                cursor.execute(f"UPDATE users SET is_archived = ? WHERE id = ?", (new_status, self.selected_user_id))
            elif action_type == "reset_password":
                cursor.execute(f"UPDATE users SET password = ? WHERE id = ?", (value, self.selected_user_id))
            conn.commit()
            messagebox.showinfo("Успех", success_msg)
            self.load_users() # Обновляем список пользователей
        except Exception as e:
            messagebox.showerror("Ошибка", f"{error_msg}: {e}")
            conn.rollback()
        finally:
            conn.close()

    def toggle_user_block(self):
        """Блокирует/разблокирует выбранного пользователя."""
        self._execute_user_action("toggle_archive", "Пользователь заблокирован/разблокирован.", "Не удалось изменить статус пользователя")

    def reset_password(self):
        """Сбрасывает пароль выбранного пользователя на '123'."""
        self._execute_user_action("reset_password", "Пароль пользователя сброшен на '123'.", "Не удалось сбросить пароль", hash_password("123"))

    def create_services_management_tab(self, parent_frame):
        """Создает вкладку для управления услугами."""
        self.service_tree = ttk.Treeview(parent_frame, columns=("ID", "Название", "Стоимость", "Код", "Срок (дни)", "Отклонение", "Архивирован"), show="headings")
        self.service_tree.pack(expand=True, fill="both")
        
        # Настройка ширины столбцов
        self.service_tree.column("ID", width=50, stretch=tk.NO)
        self.service_tree.column("Название", width=200, stretch=tk.YES)
        self.service_tree.column("Стоимость", width=100, stretch=tk.NO)
        self.service_tree.column("Код", width=80, stretch=tk.NO)
        self.service_tree.column("Срок (дни)", width=100, stretch=tk.NO)
        self.service_tree.column("Отклонение", width=120, stretch=tk.NO)
        self.service_tree.column("Архивирован", width=100, stretch=tk.NO)

        for col in self.service_tree["columns"]: self.service_tree.heading(col, text=col) # Устанавливаем заголовки
        self.service_tree.bind("<<TreeviewSelect>>", self.on_service_select)
        
        control_frame = tk.Frame(parent_frame)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Добавить услугу", command=self.add_service).pack(side="left", padx=5)
        tk.Button(control_frame, text="Редактировать услугу", command=self.edit_service).pack(side="left", padx=5)
        tk.Button(control_frame, text="Архивировать/Разархивировать услугу", command=self.toggle_service_archive).pack(side="left", padx=5)
        tk.Button(control_frame, text="Обновить список услуг", command=self.load_services).pack(side="left", padx=5)
        
        self.load_services()

    def load_services(self):
        """Загружает список услуг в Treeview."""
        for item in self.service_tree.get_children(): self.service_tree.delete(item)
        conn = connect_db()
        cursor = conn.cursor()
        for service in cursor.execute("SELECT id, name, cost, code, completion_time_days, avg_deviation, is_archived FROM services").fetchall():
            self.service_tree.insert("", "end", values=(service['id'], service['name'], service['cost'], service['code'], service['completion_time_days'], service['avg_deviation'], "Да" if service['is_archived'] else "Нет"), iid=f"service_{service['id']}")
        conn.close()

    def on_service_select(self, event):
        """Обработчик выбора услуги в Treeview."""
        selected_item = self.service_tree.focus()
        self.selected_service_id = self.service_tree.item(selected_item, "values")[0] if selected_item else None

    def add_service(self):
        """Открывает окно для добавления новой услуги."""
        AddEditServiceWindow(self, self.load_services)

    def edit_service(self):
        """Открывает окно для редактирования выбранной услуги."""
        if not self.selected_service_id:
            messagebox.showwarning("Ошибка", "Выберите услугу для редактирования.")
            return
        AddEditServiceWindow(self, self.load_services, self.selected_service_id)

    def toggle_service_archive(self):
        """Архивирует/разархивирует выбранную услугу."""
        if not self.selected_service_id:
            messagebox.showwarning("Ошибка", "Выберите услугу.")
            return
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT is_archived FROM services WHERE id = ?", (self.selected_service_id,))
            current_status = cursor.fetchone()[0]
            new_status = 1 if current_status == 0 else 0
            cursor.execute("UPDATE services SET is_archived = ? WHERE id = ?", (new_status, self.selected_service_id))
            conn.commit()
            messagebox.showinfo("Успех", f"Услуга {'архивирована' if new_status else 'разархивирована'}.")
            self.load_services()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            conn.rollback()
        finally:
            conn.close()

class PatientWindow(BaseRoleWindow):
    """Окно рабочего места пациента."""
    def __init__(self, master, user_data, on_logout_callback):
        super().__init__(master, user_data, "Пациент", on_logout_callback, session_timed=False)

    def add_role_specific_tabs(self):
        """Добавляет вкладки для пациента."""
        my_orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(my_orders_frame, text="Мои заказы")
        self.create_my_orders_tab(my_orders_frame)

        book_service_frame = ttk.Frame(self.notebook)
        self.notebook.add(book_service_frame, text="Запись на услугу")
        self.create_book_service_tab(book_service_frame)

    def create_my_orders_tab(self, parent_frame):
        """Создает вкладку для просмотра заказов пациента."""
        tk.Label(parent_frame, text="Здесь вы можете просмотреть историю ваших заказов.").pack(pady=10)
        
        tree = ttk.Treeview(parent_frame, columns=("ID Заказа", "Дата создания", "Статус Заказа", "Услуга", "Статус Услуги", "Результат"), show="headings")
        tree.heading("ID Заказа", text="ID Заказа")
        tree.heading("Дата создания", text="Дата создания")
        tree.heading("Статус Заказа", text="Статус Заказа")
        tree.heading("Услуга", text="Услуга")
        tree.heading("Статус Услуги", text="Статус Услуги")
        tree.heading("Результат", text="Результат")

        # Настройка ширины столбцов
        tree.column("ID Заказа", width=80, stretch=tk.NO)
        tree.column("Дата создания", width=150, stretch=tk.NO) # Corrected to tk.NO
        tree.column("Статус Заказа", width=120, stretch=tk.NO)
        tree.column("Услуга", width=200, stretch=tk.YES)
        tree.column("Статус Услуги", width=120, stretch=tk.NO)
        tree.column("Результат", width=250, stretch=tk.YES) # Увеличенная ширина

        tree.pack(expand=True, fill="both")

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id AS order_id, o.creation_date, o.order_status, s.name AS service_name, os.service_status, os.result
            FROM orders o 
            JOIN order_services os ON o.id = os.order_id 
            JOIN services s ON os.service_id = s.id
            WHERE o.patient_id = ? 
            ORDER BY o.creation_date DESC, o.id
        """, (self.user_data['id'],))
        orders_data = cursor.fetchall()
        conn.close()

        if not orders_data: 
            tk.Label(parent_frame, text="У вас пока нет заказов.", font=("Arial", 12)).pack(pady=20)
        else:
            for row in orders_data:
                tree.insert("", "end", values=(row['order_id'], row['creation_date'], row['order_status'], row['service_name'], row['service_status'], row['result'] or "Нет данных"))

    def create_book_service_tab(self, parent_frame):
        """Создает вкладку для записи на услуги с прокруткой."""
        tk.Label(parent_frame, text="Выберите услуги для записи:").pack(pady=10)
        conn = connect_db()
        available_services = conn.execute("SELECT id, name, cost FROM services WHERE is_archived = 0").fetchall()
        conn.close()
        self.selected_services = {} 
        
        # Контейнер для прокрутки услуг
        services_canvas = tk.Canvas(parent_frame, borderwidth=0)
        services_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        services_scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=services_canvas.yview)
        services_scrollbar.pack(side="right", fill="y")

        services_canvas.configure(yscrollcommand=services_scrollbar.set)
        # При изменении размера канваса, обновляем область прокрутки
        services_canvas.bind('<Configure>', lambda e: services_canvas.configure(scrollregion = services_canvas.bbox("all")))

        self.scrollable_services_frame = tk.Frame(services_canvas)
        services_canvas.create_window((0, 0), window=self.scrollable_services_frame, anchor="nw")
        
        if not available_services:
            tk.Label(self.scrollable_services_frame, text="Нет доступных услуг для записи.").pack(pady=10)
        else:
            for service in available_services:
                var = tk.BooleanVar()
                self.selected_services[service['id']] = var
                tk.Checkbutton(self.scrollable_services_frame, text=f"{service['name']} ({service['cost']:.2f} тг.)", variable=var).pack(anchor="w", padx=5, pady=2)
        
        tk.Button(parent_frame, text="Записаться на выбранные услуги", command=self.submit_booking).pack(pady=20)

    def submit_booking(self):
        """Обрабатывает запись пациента на выбранные услуги."""
        selected_ids = [s_id for s_id, var in self.selected_services.items() if var.get()]
        if not selected_ids:
            messagebox.showwarning("Запись на услугу", "Пожалуйста, выберите хотя бы одну услугу.")
            return
        conn = connect_db()
        cursor = conn.cursor()
        try:
            creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO orders (patient_id, creation_date, order_status) VALUES (?, ?, ?)",
                           (self.user_data['id'], creation_date, 'Ожидает оплаты'))
            order_id = cursor.lastrowid
            for service_id in selected_ids:
                cursor.execute("INSERT INTO order_services (order_id, service_id, service_status) VALUES (?, ?, ?)",
                               (order_id, service_id, 'Ожидает оплаты'))
            conn.commit()
            messagebox.showinfo("Запись успешна", f"Ваш заказ №{order_id} успешно создан. Ожидайте дальнейших инструкций по оплате.")
            
            # Обновляем вкладку "Мои заказы" после создания нового заказа
            # Находим вкладку "Мои заказы" по имени
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == "Мои заказы":
                    # Удаляем старую вкладку
                    self.notebook.forget(tab_id)
                    # Создаем новую вкладку и добавляем её
                    new_my_orders_frame = ttk.Frame(self.notebook)
                    self.notebook.add(new_my_orders_frame, text="Мои заказы")
                    self.create_my_orders_tab(new_my_orders_frame)
                    # Переключаемся на новую вкладку
                    self.notebook.select(new_my_orders_frame)
                    break

        except Exception as e:
            messagebox.showerror("Ошибка при записи", f"Произошла ошибка при создании заказа: {e}")
            conn.rollback()
        finally:
            conn.close()

class RegistrationWindow(tk.Toplevel):
    """Окно для регистрации нового пациента."""
    def __init__(self, master):
        super().__init__(master)
        self.title("Регистрация пациента")
        self.geometry("600x750") # Увеличен размер окна
        self.resizable(False, False)
        self.grab_set() # Делает окно модальным
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты формы регистрации."""
        form_frame = tk.Frame(self, padx=20, pady=20)
        form_frame.pack(expand=True, fill="both")

        # Список полей для регистрации пациента
        labels_and_keys = [
            ("Логин:", "login"), ("Пароль:", "password"), ("ФИО:", "full_name"), 
            ("Дата рождения (ГГГГ-ММ-ДД):", "date_of_birth"), ("Серия паспорта:", "passport_series"), 
            ("Номер паспорта:", "passport_number"), ("Телефон:", "phone"), ("Email:", "email"), 
            ("Номер страхового полиса:", "insurance_policy_number"), 
            ("Тип страхового полиса:", "insurance_policy_type"), ("Страховая компания:", "insurance_company")
        ]
        self.entries = {}
        for i, (label_text, key) in enumerate(labels_and_keys):
            tk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            entry = tk.Entry(form_frame, show="*" if key == "password" else None)
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            self.entries[key] = entry
        
        # Кнопки
        tk.Button(form_frame, text="Зарегистрироваться", command=self.register_patient).grid(row=len(labels_and_keys), columnspan=2, pady=10)
        tk.Button(form_frame, text="Отмена", command=self.destroy).grid(row=len(labels_and_keys)+1, columnspan=2, pady=5)

    def register_patient(self):
        """Обрабатывает регистрацию нового пациента."""
        data = {key: entry.get() for key, entry in self.entries.items()}
        
        # Проверка заполнения всех полей
        if not all(data.values()):
            messagebox.showwarning("Ошибка регистрации", "Все поля должны быть заполнены.")
            return

        conn = connect_db()
        cursor = conn.cursor()
        try:
            hashed_password = hash_password(data['password'])
            
            # Вставляем пользователя в общую таблицу users
            cursor.execute("INSERT INTO users (login, password, full_name, role) VALUES (?, ?, ?, ?)",
                           (data['login'], hashed_password, data['full_name'], 'patient'))
            user_id = cursor.lastrowid # Получаем ID только что вставленного пользователя

            # Вставляем дополнительные детали пациента в patients_details
            cursor.execute("""
                INSERT INTO patients_details (user_id, date_of_birth, passport_series, passport_number, phone, email, insurance_policy_number, insurance_policy_type, insurance_company)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, data['date_of_birth'], data['passport_series'], data['passport_number'], 
                  data['phone'], data['email'], data['insurance_policy_number'], 
                  data['insurance_policy_type'], data['insurance_company']))

            conn.commit()
            messagebox.showinfo("Регистрация успешна", "Аккаунт пациента успешно создан. Теперь вы можете войти.")
            self.destroy()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.login" in str(e):
                messagebox.showerror("Ошибка регистрации", "Логин уже существует. Выберите другой логин.")
            else:
                messagebox.showerror("Ошибка регистрации", f"Произошла ошибка базы данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка регистрации", f"Произошла непредвиденная ошибка: {e}")
        finally:
            conn.close()

class LoginWindow(tk.Toplevel):
    """Окно входа в систему."""
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success
        self.title("Вход в систему")
        self.geometry("450x450") # Увеличен размер окна
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.master.on_closing)
        self.login_attempts = 0
        self.captcha_text = ""
        self.captcha_image_tk = None
        # self.block_until инициализируется в App классе, но мы можем использовать self.master.login_block_until
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты окна входа."""
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="Логин:").pack(pady=5)
        self.login_entry = tk.Entry(main_frame); self.login_entry.pack(pady=5)
        
        tk.Label(main_frame, text="Пароль:").pack(pady=5)
        self.password_entry = tk.Entry(main_frame, show="*"); self.password_entry.pack(pady=5)
        
        self.show_password_var = tk.BooleanVar()
        tk.Checkbutton(main_frame, text="Показать пароль", variable=self.show_password_var, command=self.toggle_password_visibility).pack(pady=2)
        
        self.captcha_frame = tk.Frame(main_frame)
        self.captcha_image_label = tk.Label(self.captcha_frame)
        self.captcha_image_label.pack(pady=5)
        self.captcha_entry = tk.Entry(self.captcha_frame); self.captcha_entry.pack(pady=5)
        tk.Button(self.captcha_frame, text="Обновить CAPTCHA", command=self.show_captcha).pack(pady=2)
        self.captcha_frame.pack_forget() # Изначально скрываем CAPTCHA
        
        self.login_button = tk.Button(main_frame, text="Войти", command=self.authenticate_user); self.login_button.pack(pady=10)
        
        self.retry_password_button = tk.Button(main_frame, text="Повторить ввод пароля", command=self.clear_password_entry); self.retry_password_button.pack_forget()
        
        tk.Button(main_frame, text="Регистрация пациента", command=self.open_registration_window).pack(pady=10)

    def toggle_password_visibility(self):
        """Переключает видимость пароля."""
        self.password_entry.config(show="" if self.show_password_var.get() else "*")

    def show_captcha(self):
        """Отображает CAPTCHA."""
        self.captcha_text, img_bytes = generate_captcha()
        image = Image.open(io.BytesIO(img_bytes))
        self.captcha_image_tk = ImageTk.PhotoImage(image)
        self.captcha_image_label.config(image=self.captcha_image_tk)
        self.captcha_image_label.image = self.captcha_image_tk # Сохраняем ссылку на изображение
        self.captcha_frame.pack(pady=5)
        self.captcha_entry.delete(0, tk.END) # Очищаем поле ввода CAPTCHA

    def clear_password_entry(self):
        """Очищает поле пароля."""
        self.password_entry.delete(0, tk.END)
        self.retry_password_button.pack_forget()

    def authenticate_user(self):
        """Проверяет учетные данные пользователя."""
        current_time = time.time()
        # Проверяем, не заблокирован ли вход на системном уровне
        if current_time < self.master.login_block_until:
            remaining_block_time = int(self.master.login_block_until - current_time)
            messagebox.showwarning("Блокировка", f"Вход заблокирован на {remaining_block_time} секунд.")
            return

        login, password = self.login_entry.get(), self.password_entry.get()

        # Проверка CAPTCHA, если она отображается
        if self.login_attempts >= 1 and self.captcha_frame.winfo_ismapped(): # Проверяем, отображается ли виджет
            if self.captcha_entry.get().upper() != self.captcha_text.upper():
                log_login_attempt(login, "Неизвестно", "Неуспешная (CAPTCHA)")
                messagebox.showerror("Ошибка входа", "Неверная CAPTCHA. Вход заблокирован на 10 секунд.")
                self.master.login_block_until = time.time() + 10 # Блокируем вход на 10 секунд
                self.login_attempts += 1 
                self.captcha_entry.delete(0, tk.END)
                self.show_captcha() # Показываем новую CAPTCHA
                return

        auth_result = User.authenticate(login, password)

        if auth_result:
            log_login_attempt(login, auth_result["role"], "Успешно")
            self.login_attempts = 0 # Сбрасываем попытки при успешном входе
            self.master.login_block_until = 0 # Снимаем системную блокировку при успешном входе
            self.destroy()
            self.on_login_success(auth_result["role"], auth_result["data"])
        else:
            self.login_attempts += 1
            log_login_attempt(login, "Неизвестно", "Неуспешная")
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
            self.retry_password_button.pack(pady=5)
            if self.login_attempts >= 1: # Показываем CAPTCHA после первой неудачной попытки
                self.show_captcha()
    
    def open_registration_window(self):
        """Открывает окно регистрации пациента."""
        RegistrationWindow(self)

class AcceptBiomaterialWindow(tk.Toplevel):
    """Окно для принятия биоматериала от пациента."""
    def __init__(self, master, lab_tech_data):
        super().__init__(master)
        self.title("Принять биоматериал")
        self.geometry("700x600") # Увеличен размер окна
        self.grab_set()
        self.lab_tech_data = lab_tech_data
        self.selected_patient_id = None
        self.selected_services = {} # Словарь для хранения состояний Checkbutton
        self.create_widgets()
        self.load_patients()
        self.load_services()

    def create_widgets(self):
        """Создает виджеты для формы принятия биоматериала."""
        tk.Label(self, text="Выберите пациента:").pack(pady=5)
        self.patient_combobox = ttk.Combobox(self, state="readonly"); 
        self.patient_combobox.pack(pady=5, fill="x", padx=10)
        self.patient_combobox.bind("<<ComboboxSelected>>", self.on_patient_selected)
        
        tk.Label(self, text="Выберите услуги:").pack(pady=5)
        
        # Фрейм с прокруткой для списка услуг
        self.services_frame = tk.Frame(self, borderwidth=1, relief="sunken")
        self.services_frame.pack(pady=5, fill="both", expand=True, padx=10)
        
        self.canvas = tk.Canvas(self.services_frame)
        self.scrollbar = ttk.Scrollbar(self.services_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # Привязка для обновления scrollregion при изменении размера содержимого
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        tk.Button(self, text="Принять биоматериал и создать/обновить заказ", command=self.submit_biomaterial_acceptance).pack(pady=10)

    def load_patients(self):
        """Загружает список пациентов в ComboBox."""
        conn = connect_db()
        # Для отображения ФИО пациента, если есть, иначе логин.
        patients = conn.execute("SELECT u.id, u.full_name, u.login FROM users u WHERE u.role = 'patient' AND u.is_archived = 0").fetchall()
        conn.close()
        self.patient_data = {}
        for p in patients:
            display_name = p['full_name'] if p['full_name'] else p['login']
            self.patient_data[f"{display_name} (ID: {p['id']})"] = p['id']
        self.patient_combobox['values'] = list(self.patient_data.keys())

    def load_services(self):
        """Загружает список доступных услуг в прокручиваемый фрейм."""
        for widget in self.scrollable_frame.winfo_children(): 
            widget.destroy() # Очищаем предыдущие виджеты
        self.selected_services = {}
        conn = connect_db()
        services = conn.execute("SELECT id, name, cost FROM services WHERE is_archived = 0").fetchall()
        conn.close()
        
        if not services:
            tk.Label(self.scrollable_frame, text="Нет доступных услуг для выбора.").pack(pady=10)
        else:
            for service in services:
                var = tk.BooleanVar()
                self.selected_services[service['id']] = var

                tk.Checkbutton(self.scrollable_frame, text=f"{service['name']} ({service['cost']:.2f} тг.)", variable=var).pack(anchor="w", padx=5, pady=2)
    
    def on_patient_selected(self, event):
        """Обработчик выбора пациента из ComboBox."""
        self.selected_patient_id = self.patient_data.get(self.patient_combobox.get())
        if self.selected_patient_id:
            messagebox.showinfo("Пациент выбран", f"Выбран пациент: {self.patient_combobox.get()}")
        else:
            self.selected_patient_id = None

    def submit_biomaterial_acceptance(self):
        """Обрабатывает принятие биоматериала и создание/обновление заказа."""
        if not self.selected_patient_id: 
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите пациента."); return
        
        selected_service_ids = [s_id for s_id, var in self.selected_services.items() if var.get()]
        if not selected_service_ids: 
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите хотя бы одну услугу."); return
        
        conn = connect_db()
        cursor = conn.cursor()
        try:
            # Ищем существующие незавершенные заказы для этого пациента
            cursor.execute("SELECT id FROM orders WHERE patient_id = ? AND order_status IN ('Ожидает оплаты', 'В процессе', 'Принят')", (self.selected_patient_id,))
            existing_order = cursor.fetchone()

            if existing_order:
                order_id = existing_order['id']
                messagebox.showinfo("Заказ найден", f"Найден существующий заказ №{order_id}. Услуги будут добавлены к нему.")
            else:
                # Если заказа нет, создаем новый
                cursor.execute("INSERT INTO orders (patient_id, creation_date, order_status) VALUES (?, ?, ?)", 
                               (self.selected_patient_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Принят'))
                order_id = cursor.lastrowid
                messagebox.showinfo("Новый заказ", f"Создан новый заказ №{order_id}.")
            
            added_count = 0
            for service_id in selected_service_ids:
                # Проверяем, нет ли уже этой услуги в заказе
                if conn.execute("SELECT COUNT(*) FROM order_services WHERE order_id = ? AND service_id = ?", (order_id, service_id)).fetchone()[0] == 0:
                    cursor.execute("INSERT INTO order_services (order_id, service_id, service_status) VALUES (?, ?, ?)", 
                                   (order_id, service_id, 'В процессе')) # Ставим статус "В процессе" для новых услуг
                    added_count += 1
                else: 
                    messagebox.showinfo("Предупреждение", f"Услуга ID {service_id} уже добавлена к заказу №{order_id}.")
            
            if added_count > 0:
                # Обновляем статус основного заказа на "Принят", если он еще не такой
                cursor.execute("UPDATE orders SET order_status = 'Принят' WHERE id = ?", (order_id,))
                conn.commit()
                messagebox.showinfo("Успех", f"Биоматериал принят. Заказ №{order_id} обновлен/создан с {added_count} новыми услугами. Статус: 'Принят'.")
                self.destroy()
            else: 
                messagebox.showinfo("Информация", "Все выбранные услуги уже присутствуют в заказе."); 
                conn.rollback() # Откатываем, если ничего не добавлено, чтобы не фиксировать пустые транзакции
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при принятии биоматериала: {e}"); 
            conn.rollback()
        finally: 
            conn.close()

class GenerateLabTechReportsWindow(tk.Toplevel):
    """Окно для формирования отчетов лаборанта."""
    def __init__(self, master, lab_tech_data):
        super().__init__(master); self.title("Отчеты лаборанта"); self.geometry("700x500"); self.grab_set(); self.lab_tech_data = lab_tech_data
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты для формы отчетов."""
        tk.Label(self, text="Сформировать отчет о принятых биоматериалах", font=("Arial", 12, "bold")).pack(pady=10)
        
        date_frame = tk.Frame(self)
        date_frame.pack(pady=10)

        tk.Label(date_frame, text="Дата начала (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.start_date_entry = tk.Entry(date_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.start_date_entry.insert(0, (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="Дата окончания (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.end_date_entry = tk.Entry(date_frame)
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.end_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(self, text="Сформировать отчет", command=self.generate_acceptance_report).pack(pady=10)
        
        self.report_text = tk.Text(self, height=15, width=80, font=("Consolas", 10)); 
        self.report_text.pack(pady=10, fill="both", expand=True, padx=10)

    def generate_acceptance_report(self):
        """Генерирует отчет о принятых биоматериалах за выбранный период."""
        start_date_str, end_date_str = self.start_date_entry.get(), self.end_date_entry.get()
        try: 
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            if start_date > end_date:
                messagebox.showerror("Ошибка ввода даты", "Дата начала не может быть позже даты окончания."); return

        except ValueError: messagebox.showerror("Ошибка ввода даты", "Введите даты в формате ГГГГ-ММ-ДД."); return
        
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT o.id) AS total_orders_accepted, COUNT(os.id) AS total_services_accepted
            FROM orders o JOIN order_services os ON o.id = os.order_id
            WHERE o.creation_date BETWEEN ? AND ? AND o.order_status = 'Принят'
        """, (start_date_str + " 00:00:00", end_date_str + " 23:59:59"))
        report_data = cursor.fetchone(); conn.close()
        
        self.report_text.delete(1.0, tk.END)
        if report_data and (report_data['total_orders_accepted'] > 0 or report_data['total_services_accepted'] > 0):
            self.report_text.insert(tk.END, f"Отчет о принятых биоматериалах за период с {start_date_str} по {end_date_str}:\n\n")
            self.report_text.insert(tk.END, f"Всего принятых заказов: {report_data['total_orders_accepted']}\n")
            self.report_text.insert(tk.END, f"Всего принятых услуг: {report_data['total_services_accepted']}\n")
        else: self.report_text.insert(tk.END, "За указанный период нет данных о принятых биоматериалах.")

class AnalyzerSimulationWindow(tk.Toplevel):
    """Окно для симуляции работы анализатора."""
    def __init__(self, master):
        super().__init__(master); self.title("Имитация работы анализатора"); self.geometry("550x350"); self.grab_set() # Немного увеличен
        
        tk.Label(self, text="Введите ID услуги в заказе для симуляции анализа:", font=("Arial", 11)).pack(pady=10)
        self.order_service_id_entry = tk.Entry(self); self.order_service_id_entry.pack(pady=5)
        
        tk.Button(self, text="Запустить анализ (симуляция)", command=self.simulate_analysis).pack(pady=10)
        
        self.result_label = tk.Label(self, text="", wraplength=500, justify="left"); # Добавлен wraplength
        self.result_label.pack(pady=10, fill="x", padx=10)

    def simulate_analysis(self):
        """Симулирует анализ и обновляет статус услуги."""
        order_service_id_str = self.order_service_id_entry.get()
        if not order_service_id_str.isdigit(): 
            messagebox.showerror("Ошибка", "Введите корректный ID услуги в заказе (число)."); return
        
        order_service_id = int(order_service_id_str)
        conn = connect_db(); cursor = conn.cursor()
        try:
            service_info = conn.execute("""
                SELECT os.service_status, s.name, os.order_id FROM order_services os JOIN services s ON os.service_id = s.id WHERE os.id = ?
            """, (order_service_id,)).fetchone()
            
            if not service_info: 
                messagebox.showerror("Ошибка", "Услуга с таким ID в заказе не найдена."); return
            
            if service_info['service_status'] == 'Выполнена': 
                messagebox.showwarning("Информация", "Эта услуга уже выполнена."); return
            
            simulated_result = f"Результат для '{service_info['name']}': Нормальные показатели ({random.randint(5, 15)} ед.). Дополнительные сведения: Без патологий."
            
            cursor.execute("UPDATE order_services SET service_status = ?, result = ? WHERE id = ?", ('Выполнена', simulated_result, order_service_id))
            conn.commit()
            
            self.result_label.config(text=f"Анализ завершен! Результат для услуги ID {order_service_id}: {simulated_result}\nСтатус обновлен на 'Выполнена'.")
            messagebox.showinfo("Успех", "Анализ успешно симулирован и результаты записаны.")
            
            order_id = service_info['order_id']
            # Проверяем, все ли услуги в заказе выполнены
            if conn.execute("SELECT COUNT(*) FROM order_services WHERE order_id = ? AND service_status != 'Выполнена'", (order_id,)).fetchone()[0] == 0:
                cursor.execute("UPDATE orders SET order_status = 'Выполнен' WHERE id = ?", (order_id,)); conn.commit()
                messagebox.showinfo("Заказ завершен", f"Все услуги в заказе №{order_id} выполнены. Статус заказа изменен на 'Выполнен'.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при симуляции анализа: {e}"); 
            conn.rollback()
        finally: 
            conn.close()

class ViewEditLabResultsWindow(tk.Toplevel):
    """Окно для просмотра и изменения результатов анализов лаборантом-исследователем."""
    def __init__(self, master):
        super().__init__(master); self.title("Просмотр и изменение результатов"); self.geometry("900x700"); self.grab_set() # Увеличен размер окна
        self.create_widgets(); self.load_uncompleted_services()

    def create_widgets(self):
        """Создает виджеты для просмотра и редактирования результатов."""
        tk.Label(self, text="Услуги, ожидающие выполнения или с результатами:", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.tree = ttk.Treeview(self, columns=("ID Услуги в заказе", "ID Заказа", "Пациент", "Услуга", "Статус", "Результат"), show="headings")
        self.tree.heading("ID Услуги в заказе", text="ID Услуги в заказе")
        self.tree.heading("ID Заказа", text="ID Заказа")
        self.tree.heading("Пациент", text="Пациент")
        self.tree.heading("Услуга", text="Услуга")
        self.tree.heading("Статус", text="Статус")
        self.tree.heading("Результат", text="Результат")

        # Настройка ширины столбцов
        self.tree.column("ID Услуги в заказе", width=120, stretch=tk.NO)
        self.tree.column("ID Заказа", width=80, stretch=tk.NO)
        self.tree.column("Пациент", width=150, stretch=tk.YES)
        self.tree.column("Услуга", width=150, stretch=tk.YES)
        self.tree.column("Статус", width=100, stretch=tk.NO)
        self.tree.column("Результат", width=250, stretch=tk.YES) # Увеличенная ширина

        self.tree.pack(expand=True, fill="both"); 
        self.tree.bind("<<TreeviewSelect>>", self.on_service_select)
        
        control_frame = tk.Frame(self); control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Результат:").pack(side="left", padx=5)
        self.result_entry = tk.Entry(control_frame, width=60); # Увеличенная ширина поля ввода
        self.result_entry.pack(side="left", padx=5)
        
        tk.Button(control_frame, text="Изменить статус на 'Выполнена' и сохранить результат", command=self.update_service_status).pack(side="left", padx=5)
        
        tk.Button(self, text="Обновить список", command=self.load_uncompleted_services).pack(pady=10)
        
        self.selected_order_service_id, self.selected_order_id = None, None

    def load_uncompleted_services(self):
        """Загружает список услуг, ожидающих выполнения, или с уже введенными результатами."""
        for item in self.tree.get_children(): self.tree.delete(item)
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("""
            SELECT os.id AS order_service_id, o.id AS order_id, u.full_name AS patient_name, s.name AS service_name, os.service_status, os.result
            FROM order_services os 
            JOIN orders o ON os.order_id = o.id 
            JOIN services s ON os.service_id = s.id 
            JOIN users u ON o.patient_id = u.id
            WHERE os.service_status != 'Выполнена' OR os.result IS NOT NULL 
            ORDER BY o.id, os.id
        """)
        for service in cursor.fetchall():
            self.tree.insert("", "end", values=(service['order_service_id'], service['order_id'], service['patient_name'], service['service_name'], service['service_status'], service['result'] or ""))
        conn.close()

    def on_service_select(self, event):
        """Обработчик выбора услуги в Treeview."""
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, "values")
            self.selected_order_service_id, self.selected_order_id = values[0], values[1]
            self.result_entry.delete(0, tk.END); self.result_entry.insert(0, values[5])
        else: 
            self.selected_order_service_id, self.selected_order_id = None, None
            self.result_entry.delete(0, tk.END)

    def update_service_status(self):
        """Обновляет статус услуги на 'Выполнена' и сохраняет результат."""
        if not self.selected_order_service_id: 
            messagebox.showwarning("Ошибка", "Выберите услугу для обновления."); return
          
        new_result = self.result_entry.get()
        if not new_result: 
            messagebox.showwarning("Ошибка", "Введите результат исследования."); return
        
        conn = connect_db(); cursor = conn.cursor()
        try:
            cursor.execute("UPDATE order_services SET service_status = 'Выполнена', result = ? WHERE id = ?", (new_result, self.selected_order_service_id))
            conn.commit()
            messagebox.showinfo("Успех", f"Статус услуги ID {self.selected_order_service_id} обновлен на 'Выполнена', результат сохранен.")
            
            # Проверяем, все ли услуги в заказе выполнены
            if conn.execute("SELECT COUNT(*) FROM order_services WHERE order_id = ? AND service_status != 'Выполнена'", (self.selected_order_id,)).fetchone()[0] == 0:
                cursor.execute("UPDATE orders SET order_status = 'Выполнен' WHERE id = ?", (self.selected_order_id,)); conn.commit()
                messagebox.showinfo("Заказ завершен", f"Все услуги в заказе №{self.selected_order_id} выполнены. Статус заказа изменен на 'Выполнен'.")
            
            self.load_uncompleted_services(); 
            self.result_entry.delete(0, tk.END); 
            self.selected_order_service_id, self.selected_order_id = None, None
        except Exception as e: 
            messagebox.showerror("Ошибка", f"Произошла ошибка при обновлении статуса: {e}"); 
            conn.rollback()
        finally: 
            conn.close()

class ReportsAccountantWindow(tk.Toplevel):
    """Окно для формирования отчетов бухгалтера."""
    def __init__(self, master):
        super().__init__(master); self.title("Отчеты бухгалтера"); self.geometry("750x550"); self.grab_set() # Немного увеличен
        notebook = ttk.Notebook(self); notebook.pack(expand=True, fill="both", padx=10, pady=10)
        income_report_frame = ttk.Frame(notebook); notebook.add(income_report_frame, text="Отчет по доходам")
        self.create_income_report_tab(income_report_frame)

    def create_income_report_tab(self, parent_frame):
        """Создает вкладку для отчета по доходам."""
        tk.Label(parent_frame, text="Отчет о доходах по завершенным заказам", font=("Arial", 12, "bold")).pack(pady=10)
        
        date_frame = tk.Frame(parent_frame)
        date_frame.pack(pady=10)

        tk.Label(date_frame, text="Дата начала (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.income_start_date_entry = tk.Entry(date_frame)
        self.income_start_date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.income_start_date_entry.insert(0, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="Дата окончания (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.income_end_date_entry = tk.Entry(date_frame)
        self.income_end_date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.income_end_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(parent_frame, text="Сформировать отчет", command=self.generate_income_report).pack(pady=10)
        
        self.income_report_text = tk.Text(parent_frame, height=15, width=80, font=("Consolas", 10)); 
        self.income_report_text.pack(pady=10, fill="both", expand=True, padx=10)

    def generate_income_report(self):
        """Генерирует отчет о доходах за выбранный период."""
        start_date_str, end_date_str = self.income_start_date_entry.get(), self.income_end_date_entry.get()
        try: 
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            if start_date > end_date:
                messagebox.showerror("Ошибка ввода даты", "Дата начала не может быть позже даты окончания."); return
        except ValueError: messagebox.showerror("Ошибка ввода даты", "Введите даты в формате ГГГГ-ММ-ДД."); return
        
        conn = connect_db(); cursor = conn.cursor()
        total_income = conn.execute("""
            SELECT SUM(s.cost) FROM orders o 
            JOIN order_services os ON o.id = os.order_id 
            JOIN services s ON os.service_id = s.id
            WHERE o.order_status = 'Выполнен' 
            AND os.service_status = 'Выполнена' 
            AND o.creation_date BETWEEN ? AND ?
        """, (start_date_str + " 00:00:00", end_date_str + " 23:59:59")).fetchone()['SUM(s.cost)']
        conn.close()
        
        self.income_report_text.delete(1.0, tk.END)
        if total_income is not None:
            self.income_report_text.insert(tk.END, f"Отчет о доходах за период с {start_date_str} по {end_date_str}:\n\n")

            self.income_report_text.insert(tk.END, f"Общий доход по завершенным заказам: {total_income:.2f} тг.\n")
        else: self.income_report_text.insert(tk.END, "За указанный период нет данных о доходах по завершенным заказам.")

class GenerateInvoiceWindow(tk.Toplevel):
    """Окно для формирования счета страховой компании."""
    def __init__(self, master, accountant_id):
        super().__init__(master); self.title("Сформировать счет страховой"); self.geometry("750x650"); self.grab_set() # Увеличен размер
        self.accountant_id = accountant_id; self.selected_patient_id = None; self.selected_order_id = None; self.order_services = []
        self.create_widgets(); self.load_patients()

    def create_widgets(self):
        """Создает виджеты для формы формирования счета."""
        tk.Label(self, text="Выберите пациента:").pack(pady=5)
        self.patient_combobox = ttk.Combobox(self, state="readonly"); 
        self.patient_combobox.pack(pady=5, fill="x", padx=10)
        self.patient_combobox.bind("<<ComboboxSelected>>", self.on_patient_selected)
        
        tk.Label(self, text="Выберите заказ:").pack(pady=5)
        self.order_combobox = ttk.Combobox(self, state="readonly"); 
        self.order_combobox.pack(pady=5, fill="x", padx=10)
        self.order_combobox.bind("<<ComboboxSelected>>", self.on_order_selected)
        
        tk.Label(self, text="Страховая компания:").pack(pady=5); 
        self.insurance_company_label = tk.Label(self, text="Не выбрано", font=("Arial", 11, "bold"))
        self.insurance_company_label.pack(pady=5); 
        
        tk.Label(self, text="Сумма к оплате:").pack(pady=5)

        self.amount_label = tk.Label(self, text="0.00 тг.", font=("Arial", 14, "bold")); 

        self.amount_label.pack(pady=5)
        
        tk.Label(self, text="Услуги в заказе:").pack(pady=5)
        self.services_tree = ttk.Treeview(self, columns=("Название", "Стоимость", "Статус"), show="headings")
        self.services_tree.heading("Название", text="Название услуги")
        self.services_tree.heading("Стоимость", text="Стоимость")
        self.services_tree.heading("Статус", text="Статус услуги")

        # Настройка ширины столбцов
        self.services_tree.column("Название", width=250, stretch=tk.YES)
        self.services_tree.column("Стоимость", width=100, stretch=tk.NO)
        self.services_tree.column("Статус", width=150, stretch=tk.NO)

        self.services_tree.pack(expand=True, fill="both", padx=10, pady=5)
        
        tk.Button(self, text="Сформировать счет", command=self.submit_invoice).pack(pady=20)

    def load_patients(self):
        """Загружает список пациентов для выбора."""
        conn = connect_db()
        # Извлекаем данные пациента, включая страховую компанию из patients_details
        patients = conn.execute("""
            SELECT u.id, u.full_name, u.login, pd.insurance_company 
            FROM users u 
            JOIN patients_details pd ON u.id = pd.user_id
            WHERE u.role = 'patient' AND u.is_archived = 0
        """).fetchall()
        conn.close()
        
        self.patient_data = {}
        for p in patients:
            display_name = p['full_name'] if p['full_name'] else p['login']
            self.patient_data[f"{display_name} (ID: {p['id']})"] = dict(p) # Сохраняем все данные пациента
        self.patient_combobox['values'] = list(self.patient_data.keys()); self.patient_combobox.set("")

    def on_patient_selected(self, event):
        """Обработчик выбора пациента."""
        patient_info_key = self.patient_combobox.get()
        patient_info = self.patient_data.get(patient_info_key)
        if patient_info:
            self.selected_patient_id = patient_info['id']
            self.insurance_company_label.config(text=patient_info['insurance_company'])
            self.load_orders_for_patient(self.selected_patient_id)
        else:
            self.selected_patient_id = None
            self.order_combobox['values'] = []; self.order_combobox.set("")
            self.insurance_company_label.config(text="Не выбрано")

            self.amount_label.config(text="0.00 тг.")

            self.clear_services_tree()

    def load_orders_for_patient(self, patient_id):
        """Загружает выполненные заказы для выбранного пациента."""
        conn = connect_db()
        orders = conn.execute("SELECT id, creation_date, order_status FROM orders WHERE patient_id = ? AND order_status = 'Выполнен' AND is_archived = 0 ORDER BY creation_date DESC", (patient_id,)).fetchall()
        conn.close()
        
        self.order_data = {f"Заказ ID: {o['id']} (Дата: {o['creation_date'].split(' ')[0]})": o['id'] for o in orders}
        self.order_combobox['values'] = list(self.order_data.keys()); 
        self.order_combobox.set("")
        self.clear_services_tree(); 

        self.amount_label.config(text="0.00 тг.")


    def on_order_selected(self, event):
        """Обработчик выбора заказа."""
        self.selected_order_id = self.order_data.get(self.order_combobox.get())
        self.clear_services_tree()
        if self.selected_order_id: 
            self.load_order_services(self.selected_order_id)
        else: 

            self.amount_label.config(text="0.00 тг.")


    def load_order_services(self, order_id):
        """Загружает услуги для выбранного заказа."""
        conn = connect_db(); 
        self.order_services = conn.execute("""
            SELECT s.name, s.cost, os.service_status FROM order_services os 
            JOIN services s ON os.service_id = s.id 
            WHERE os.order_id = ?
        """, (order_id,)).fetchall(); conn.close()
        
        total_amount = 0
        for item in self.order_services:
            self.services_tree.insert("", "end", values=(item['name'], item['cost'], item['service_status']))
            if item['service_status'] == 'Выполнена': # Считаем только выполненные услуги
                total_amount += item['cost']

        self.amount_label.config(text=f"{total_amount:.2f} тг.")


    def clear_services_tree(self):
        """Очищает Treeview услуг."""
        for item in self.services_tree.get_children(): self.services_tree.delete(item)
        self.order_services = []

    def submit_invoice(self):
        """Формирует и сохраняет счет страховой компании."""
        if not self.selected_patient_id or not self.selected_order_id: 
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите пациента и заказ."); return
        
        insurance_company = self.patient_data[self.patient_combobox.get()]['insurance_company']

        amount = float(self.amount_label.cget("text").replace(" тг.", ""))

        
        if amount == 0: 
            messagebox.showwarning("Ошибка", "Сумма счета не может быть нулевой. Убедитесь, что в заказе есть выполненные услуги."); return
        
        conn = connect_db(); cursor = conn.cursor()
        try:
            # Проверяем, не был ли счет для этого заказа уже сформирован
            if conn.execute("SELECT COUNT(*) FROM invoices WHERE order_id = ?", (self.selected_order_id,)).fetchone()[0] > 0:
                messagebox.showwarning("Предупреждение", "Счет для этого заказа уже сформирован."); return
            
            cursor.execute("""
                INSERT INTO invoices (accountant_id, insurance_company, invoice_date, amount, order_id)
                VALUES (?, ?, ?, ?, ?)
            """, (self.accountant_id, insurance_company, datetime.datetime.now().strftime("%Y-%m-%d"), amount, self.selected_order_id))
            conn.commit()

            messagebox.showinfo("Успех", f"Счет на {amount:.2f} тг. для {insurance_company} (Заказ ID: {self.selected_order_id}) успешно создан.")

            self.destroy() # Закрываем окно после создания счета
        except Exception as e: 
            messagebox.showerror("Ошибка", f"Не удалось создать счет: {e}"); 
            conn.rollback()
        finally: 
            conn.close()

class AddEditServiceWindow(tk.Toplevel):
    """Окно для добавления или редактирования услуги."""
    def __init__(self, master, refresh_callback, service_id=None):
        super().__init__(master); self.master = master; self.refresh_callback = refresh_callback
        self.service_id = service_id; 
        self.title("Редактировать услугу" if service_id else "Добавить услугу"); 
        self.geometry("450x350"); # Немного увеличен
        self.grab_set()
        self.create_widgets()
        if self.service_id: self.load_service_data()

    def create_widgets(self):
        """Создает виджеты формы услуги."""
        labels = ["Название:", "Стоимость:", "Код услуги:", "Срок выполнения (дни):", "Среднее отклонение:"]
        self.entries = {}
        for i, text in enumerate(labels):
            tk.Label(self, text=text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = tk.Entry(self); 
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entries[text] = entry
        
        tk.Button(self, text="Сохранить", command=self.save_service).grid(row=len(labels), columnspan=2, pady=10)

    def load_service_data(self):
        """Загружает данные услуги для редактирования."""
        conn = connect_db(); 
        service_data = conn.execute("SELECT name, cost, code, completion_time_days, avg_deviation FROM services WHERE id = ?", (self.service_id,)).fetchone(); 
        conn.close()
        if service_data:
            self.entries["Название:"].insert(0, service_data['name'])
            self.entries["Стоимость:"].insert(0, service_data['cost'])
            self.entries["Код услуги:"].insert(0, service_data['code'])
            self.entries["Срок выполнения (дни):"].insert(0, service_data['completion_time_days'])
            self.entries["Среднее отклонение:"].insert(0, service_data['avg_deviation'])

    def save_service(self):
        """Сохраняет (добавляет или обновляет) данные услуги."""
        name, cost_str, code, completion_time_days_str, avg_deviation_str = [self.entries[l].get() for l in ["Название:", "Стоимость:", "Код услуги:", "Срок выполнения (дни):", "Среднее отклонение:"]]
        
        if not all([name, cost_str, code, completion_time_days_str, avg_deviation_str]): 
            messagebox.showwarning("Ошибка", "Все поля должны быть заполнены."); return
        
        try: 
            cost = float(cost_str)
            completion_time_days = int(completion_time_days_str)
            avg_deviation = float(avg_deviation_str)
        except ValueError: 
            messagebox.showerror("Ошибка ввода", "Стоимость, срок и отклонение должны быть числами."); return
        
        conn = connect_db(); cursor = conn.cursor()
        try:
            if self.service_id:
                cursor.execute("UPDATE services SET name=?, cost=?, code=?, completion_time_days=?, avg_deviation=? WHERE id=?", (name, cost, code, completion_time_days, avg_deviation, self.service_id))
                messagebox.showinfo("Успех", "Услуга успешно обновлена.")
            else:
                cursor.execute("INSERT INTO services (name, cost, code, completion_time_days, avg_deviation) VALUES (?, ?, ?, ?, ?)", (name, cost, code, completion_time_days, avg_deviation))
                messagebox.showinfo("Успех", "Услуга успешно добавлена.")
            conn.commit(); 
            self.refresh_callback(); # Обновляем список услуг в родительском окне
            self.destroy()
        except sqlite3.IntegrityError: 
            messagebox.showerror("Ошибка", "Код услуги должен быть уникальным.")
        except Exception as e: 
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
        finally: 
            conn.close()

# --- 5. Main Application Class ---
class App(tk.Tk):
    """Главный класс приложения."""
    def __init__(self):
        super().__init__()
        self.title("Лабораторная информационная система")
        self.geometry("1x1"); self.withdraw() # Скрываем основное окно Tkinter сразу
        
        create_tables()
        insert_initial_data()
        
        self.current_user_role, self.current_user_data, self.active_window = None, None, None
        self.login_block_until = 0 # Время, до которого вход заблокирован (для таймера сессии лаборанта)
        
        self.show_login_window()

    def show_login_window(self):
        """Показывает окно входа."""
        if self.active_window: 
            self.active_window.destroy(); self.active_window = None
        
        current_time = time.time()
        if current_time < self.login_block_until:
            remaining_block_time = int(self.login_block_until - current_time)
            messagebox.showwarning("Блокировка входа", f"Вход заблокирован на {remaining_block_time} секунд.")
            # Планируем повторный вызов show_login_window после окончания блокировки
            self.after(remaining_block_time * 1000, self.show_login_window); return
        
        self.login_window = LoginWindow(self, self.on_login_success); 
        self.login_window.grab_set(); # Делает окно входа модальным
        self.login_window.wait_window() # Ждем, пока окно входа закроется

    def on_login_success(self, role, user_data):
        """Обработчик успешного входа."""
        self.current_user_role, self.current_user_data = role, user_data
        
        role_window_map = {
            "lab_technician": LabTechWindow, 
            "research_lab_technician": ResearchLabTechWindow,
            "accountant": AccountantWindow, 
            "administrator": AdminWindow, 
            "patient": PatientWindow
        }
        window_class = role_window_map.get(role)
        
        if window_class:
            self.active_window = window_class(self, user_data, self.on_logout)
        else:
            messagebox.showinfo("Информация", f"Успешный вход как {role}. Интерфейс для этой роли пока не реализован.")
            self.active_window = tk.Toplevel(self)
            self.active_window.title("Добро пожаловать!")
            tk.Label(self.active_window, text=f"Добро пожаловать, {user_data.get('full_name', user_data['login'])}!").pack(pady=20)
            tk.Button(self.active_window, text="Выйти", command=self.on_logout).pack(pady=10)
        
        if self.active_window:
            self.active_window.grab_set(); # Делает окно роли модальным
            self.active_window.protocol("WM_DELETE_WINDOW", self.on_logout); 
            self.active_window.wait_window() # Ждем, пока окно роли закроется

    def on_logout(self):
        """Обработчик выхода из системы."""
        if self.active_window:
            try:
                # Пытаемся остановить таймер, если он есть у текущего окна
                if self.active_window.timer: self.active_window.timer.stop()
            except AttributeError: 
                pass # Если у окна нет таймера, игнорируем
            self.active_window.destroy(); self.active_window = None
        self.current_user_role, self.current_user_data = None, None
        self.show_login_window() # Возвращаемся к окну входа

    def on_closing(self):
        """Обработчик закрытия главного окна приложения."""
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти из приложения?"): 
            self.destroy() # Закрываем приложение

if __name__ == "__main__":
    app = App()
    app.mainloop() # Запускаем главный цикл обработки событий Tkinter
