import sys, os, random, string
from io import BytesIO
from datetime import datetime
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QAbstractItemView, QInputDialog
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from captcha.image import ImageCaptcha
from models import Session, User, Patient, Invoice, Log, Service, Order, order_service_association


class Login(QDialog):
    def __init__(self, delayed_block=0):
        super(Login, self).__init__()
        uic.loadUi("login.ui", self)

        self.delayed_block = delayed_block

        self.updatecaptcha.hide()
        self.captcha.hide()
        self.captcha_label.hide()

        self.join.clicked.connect(self.login)
        self.updatecaptcha.clicked.connect(self.generate_captcha)
        self.generate_captcha()

        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.showpassword.clicked.connect(self.show_password)
        self.updatepassword.clicked.connect(self.update_password)
        self.register_button.clicked.connect(self.open_registration)

        self.block_timer = QTimer(self)
        self.block_timer.timeout.connect(self.update_timer)
        self.remaining_time = 0

        if self.delayed_block > 0:
            self.start_block_timer(self.delayed_block)

    def show_password(self):
        if self.password.echoMode() == QtWidgets.QLineEdit.Password:
            self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.password.setEchoMode(QtWidgets.QLineEdit.Password)

    def update_password(self):
        self.password.setText("")

    def login(self):
        username = self.loginbox.text()
        user_password = self.password.text()
        captcha_input = self.captcha.text().strip().upper()

        if not self.captcha.isHidden() and captcha_input != self.captcha_text:
            self.generate_captcha()
            self.start_block_timer(10)
            QMessageBox.warning(self, "Ошибка", "Неверная капча!")
            return

        session = Session()
        user = session.query(User).filter_by(username=username, password=user_password).first()

        if user:
            if getattr(user, 'is_blocked', False):
                QMessageBox.critical(self, "Заблокирован", "Этот пользователь заблокирован администратором.")
                return
            user.last_login = datetime.now()
            session.add(Log(user_id=user.id, action="Вход в систему", timestamp=datetime.now()))
            session.commit()

            self.mainwindow = MainApp(user)
            self.mainwindow.show()
            self.close()
        else:
            self.updatecaptcha.show()
            self.captcha.show()
            self.captcha_label.show()
            self.generate_captcha()
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")

    def generate_captcha(self):
        self.captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        image = ImageCaptcha(width=280, height=90)
        img = image.generate_image(self.captcha_text)

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read(), "PNG")
        self.captcha_label.setPixmap(pixmap)

    def start_block_timer(self, duration):
        self.remaining_time = duration
        self.join.setEnabled(False)
        self.block_timer.start(1000)

    def update_timer(self):
        self.remaining_time -= 1
        if self.remaining_time > 0:
            self.time.setText(f"Блокировка {self.remaining_time} сек.")
        else:
            self.time.setText("")
            self.join.setEnabled(True)
            self.block_timer.stop()

    def open_registration(self):
        self.registration_window = Registration()
        self.registration_window.show()

class Registration(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("registration.ui", self)
        self.register_submit.clicked.connect(self.register_user)
        self.choose_photo_button.clicked.connect(self.select_photo_file)

    def register_user(self):
        session = Session()

        username = self.reg_username.text()
        password = self.reg_password.text()
        full_name = self.reg_fullname.text()
        photo = self.reg_photo.text()
        passport = self.reg_passport.text()
        date_of_birth = self.reg_birthdate.date().toPyDate()
        phone = self.reg_phone.text()
        email = self.reg_email.text()
        insurance_number = self.reg_insurance_number.text()
        insurance_type = self.reg_insurance_type.text()
        insurance_company = self.reg_insurance_company.text()

        if session.query(User).filter_by(username=username).first():
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует.")
            return

        new_user = Patient(
            username=username,
            password=password,
            full_name=full_name,
            role='пациент',
            photo=photo,
            date_of_birth=date_of_birth,
            passport=passport,
            phone=phone,
            email=email,
            insurance_number=insurance_number,
            insurance_type=insurance_type,
            insurance_company=insurance_company,
            is_blocked=False
        )

        session.add(new_user)
        session.commit()

        QMessageBox.information(self, "Успех", "Пациент зарегистрирован.")
        self.close()

    def select_photo_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите фото", "",
                                                             "Изображения (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.reg_photo.setText(file_path)

class MainApp(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.user = user
        self.setWindowTitle("Главная страница")

        self.label_name.setText(user.full_name)
        self.label_role.setText(user.role)
        if user.photo and os.path.exists(user.photo):
            self.label_photo.setPixmap(QPixmap(user.photo))

        self.role_pages = {
            'пациент': 'patient',
            'администратор': 'admin',
            'бухгалтер': 'accountant',
            'лаборант': 'laborant',
            'лаборант-исследователь': 'laborant_researcher'
        }

        self.switch_role_page()
        self.setup_role_features()

        if hasattr(self, 'exitbutton'):
            self.exitbutton.clicked.connect(self.logout)

    def switch_role_page(self):
        role_page = self.role_pages.get(self.user.role.lower())
        if hasattr(self, role_page):
            index = self.mainwidget.indexOf(getattr(self, role_page))
            if index != -1:
                self.mainwidget.setCurrentIndex(index)

    def setup_role_features(self):
        if self.user.role.lower() == 'администратор':
            self.userstable.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.userstable.setSelectionMode(QAbstractItemView.SingleSelection)
            self.resetbutton.clicked.connect(self.reset_password)
            self.blockbutton.clicked.connect(self.toggle_block_status)
            self.load_users_table()
            self.load_logs_table()

        if self.user.role.lower() == 'бухгалтер':
            self.addservice.clicked.connect(self.add_service)
            self.changeservice.clicked.connect(self.change_service)
            self.archiveservice.clicked.connect(self.archive_service)
            self.invoicebutton.clicked.connect(self.issue_invoice)
            self.reportbutton.clicked.connect(self.generate_report)
            self.load_services_table()
            self.load_invoices_table()
            self.load_last_login_table()

        if self.user.role.lower() == 'пациент':
            self.load_services_table()
            self.createorderbutton.clicked.connect(self.open_order_dialog)
            self.reportbutton.clicked.connect(self.generate_report)
            self.load_patient_orders()

        if self.user.role.lower() == 'лаборант':
            self.resetbutton_4.clicked.connect(self.accept_biomaterial)
            self.load_services_for_acceptance()
            self.resetbutton_5.clicked.connect(self.generate_lab_report)
            self.load_accepted_services()

        if self.user.role.lower() == 'лаборант-исследователь':
            self.load_services_for_analysis()
            self.analizatorbutton.clicked.connect(self.analyze_service)


        if self.user.role.lower() in ['лаборант', 'лаборант-исследователь']:
            self.start_work_timer()

    def load_accepted_services(self):
        session = Session()
        results = session.execute(
            order_service_association.select()
            .where(order_service_association.c.service_status == 'Ожидает анализирования')
            .where(order_service_association.c.accepted_by_id == self.user.id)
        ).fetchall()

        model = QStandardItemModel(len(results), 4)
        model.setHorizontalHeaderLabels(['Order ID', 'Услуга', 'Принят', 'Дата приёма'])

        for row, r in enumerate(results):
            service = session.query(Service).get(r.service_id)
            model.setItem(row, 0, QStandardItem(str(r.order_id)))
            model.setItem(row, 1, QStandardItem(service.name if service else ''))
            model.setItem(row, 2, QStandardItem("Да"))
            model.setItem(row, 3, QStandardItem(r.accepted_at.strftime('%Y-%m-%d %H:%M') if r.accepted_at else ''))

        self.logtable_4.setModel(model)
        self.logtable_4.resizeColumnsToContents()

    def generate_lab_report(self):
        from datetime import datetime

        session = Session()
        today = datetime.utcnow().date()

        results = session.execute(
            order_service_association.select()
            .where(order_service_association.c.accepted_by_id == self.user.id)
        ).fetchall()

        lines = []
        today_count = 0

        for r in results:
            order = session.query(Order).get(r.order_id)
            patient = session.query(User).get(order.patient_id) if order else None
            service = session.query(Service).get(r.service_id)
            accepted_at = r.accepted_at.strftime('%Y-%m-%d %H:%M') if r.accepted_at else '—'
            created_at = order.created_at.strftime('%Y-%m-%d %H:%M') if order else '—'

            if r.accepted_at and r.accepted_at.date() == today:
                today_count += 1

            lines.append(
                f"Заказ #{r.order_id}\n"
                f"  Пациент: {patient.full_name if patient else '—'}\n"
                f"  Услуга: {service.name if service else '—'}\n"
                f"  Статус: {r.service_status}\n"
                f"  Результат: {r.result or '—'}\n"
                f"  Дата создания заказа: {created_at}\n"
                f"  Дата приёма: {accepted_at}\n"
                "----------------------------------------\n"
            )

        summary = f"Итого: принято сегодня ({today.strftime('%Y-%m-%d')}): {today_count} образцов\n"
        lines.insert(0, summary)

        # Сохраняем в TXT
        path = f"lab_report_{self.user.username}_{today.strftime('%Y%m%d')}.txt"
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        QMessageBox.information(self, "Отчёт", f"Отчёт сохранён в файл:\n{path}")

    def start_work_timer(self):
        self.work_duration = 240
        self.remaining_time = self.work_duration
        self.warning_shown = False

        self.label_timer.setText(self.format_time_label(self.remaining_time))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_work_timer)
        self.timer.start(1000)

    def update_work_timer(self):
        self.remaining_time -= 1
        self.label_timer.setText(self.format_time_label(self.remaining_time))

        if self.remaining_time <= 5 * 60 and not self.warning_shown:
            QMessageBox.warning(self, "Предупреждение", "Осталось 5 минут до завершения сессии.")
            self.warning_shown = True

        if self.remaining_time <= 0:
            self.timer.stop()
            self.label_timer.setText("Сессия завершена.")
            self.block_user_for_time(60)

    def format_time_label(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"Осталось времени: {mins:02}:{secs:02}"

    def block_user_for_time(self, seconds):
        QMessageBox.information(self, "Время истекло",
                                f"Ваша сессия завершена. Повторный вход будет доступен через {seconds} секунд.")
        self.logout(block_seconds=seconds)

    def load_patient_orders(self):
        session = Session()
        orders = session.query(Order).filter_by(patient_id=self.user.id).all()
        model = QStandardItemModel(len(orders), 4)
        model.setHorizontalHeaderLabels(['ID', 'Дата создания', 'Статус', 'Архив'])
        for row, order in enumerate(orders):
            model.setItem(row, 0, QStandardItem(str(order.id)))
            model.setItem(row, 1, QStandardItem(order.created_at.strftime('%Y-%m-%d %H:%M')))
            model.setItem(row, 2, QStandardItem(order.status))
            model.setItem(row, 3, QStandardItem("Да" if order.is_archived else "Нет"))
        self.myorders.setModel(model)
        self.myorders.resizeColumnsToContents()

    def logout(self, block_seconds=0):
        from main import Login
        self.login_window = Login(delayed_block=block_seconds)
        self.login_window.show()
        self.close()

    def load_users_table(self):
        session = Session()
        users = session.query(User).all()
        model = QStandardItemModel(len(users), 5)
        model.setHorizontalHeaderLabels(['ID', 'Логин', 'ФИО', 'Роль', 'Заблокирован'])
        for row, user in enumerate(users):
            model.setItem(row, 0, QStandardItem(str(user.id)))
            model.setItem(row, 1, QStandardItem(user.username))
            model.setItem(row, 2, QStandardItem(user.full_name))
            model.setItem(row, 3, QStandardItem(user.role))
            model.setItem(row, 4, QStandardItem("Да" if user.is_blocked else "Нет"))
        self.userstable.setModel(model)
        self.userstable.resizeColumnsToContents()

    def reset_password(self):
        selected = self.userstable.selectionModel().selectedRows()
        if not selected: return
        user_id = int(self.userstable.model().item(selected[0].row(), 0).text())
        session = Session()
        user = session.query(User).get(user_id)
        new_password, ok = QInputDialog.getText(self, "Новый пароль", f"Введите новый пароль для {user.username}:")
        if ok and new_password.strip():
            user.password = new_password
            session.add(Log(user_id=user.id, action="Сброс пароля"))
            session.commit()
            QMessageBox.information(self, "Готово", "Пароль успешно изменён.")

    def toggle_block_status(self):
        selected = self.userstable.selectionModel().selectedRows()
        if not selected: return
        user_id = int(self.userstable.model().item(selected[0].row(), 0).text())
        session = Session()
        user = session.query(User).get(user_id)
        user.is_blocked = not user.is_blocked
        session.add(Log(user_id=user.id, action="Блокировка" if user.is_blocked else "Разблокировка"))
        session.commit()
        self.load_users_table()
        QMessageBox.information(self, "Готово", f"Пользователь {'заблокирован' if user.is_blocked else 'разблокирован'}.")

    def load_logs_table(self):
        session = Session()
        logs = session.query(Log).all()
        model = QStandardItemModel(len(logs), 3)
        model.setHorizontalHeaderLabels(['ID', 'Пользователь', 'Действие'])
        for row, log in enumerate(logs):
            model.setItem(row, 0, QStandardItem(str(log.id)))
            model.setItem(row, 1, QStandardItem(str(log.user_id)))
            model.setItem(row, 2, QStandardItem(log.action))
        self.logtable.setModel(model)
        self.logtable.resizeColumnsToContents()

    def load_invoices_table(self):
        session = Session()
        invoices = session.query(Invoice).all()
        model = QStandardItemModel(len(invoices), 4)
        model.setHorizontalHeaderLabels(['ID', 'Сумма', 'Компания', 'Статус'])
        for row, inv in enumerate(invoices):
            model.setItem(row, 0, QStandardItem(str(inv.id)))
            model.setItem(row, 1, QStandardItem(f"{inv.amount:.2f}"))
            model.setItem(row, 2, QStandardItem(inv.company))
            model.setItem(row, 3, QStandardItem(inv.status))
        self.logtable_2.setModel(model)
        self.logtable_2.resizeColumnsToContents()

    def load_last_login_table(self):
        session = Session()
        users = session.query(User).all()
        model = QStandardItemModel(len(users), 3)
        model.setHorizontalHeaderLabels(['ФИО', 'Роль', 'Последний вход'])
        for row, u in enumerate(users):
            last_login = 'Никогда'
            try:
                if u.last_login:
                    last_login = u.last_login.strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass
            model.setItem(row, 0, QStandardItem(u.full_name))
            model.setItem(row, 1, QStandardItem(u.role))
            model.setItem(row, 2, QStandardItem(last_login))
        self.userslastlogin.setModel(model)
        self.userslastlogin.resizeColumnsToContents()

    def load_services_table(self):
        session = Session()
        services = session.query(Service).filter_by(is_archived=False).all()
        model = QStandardItemModel(len(services), 4)
        model.setHorizontalHeaderLabels(['ID', 'Название', 'Цена', 'Среднее отклонение', 'Код'])
        for row, s in enumerate(services):
            model.setItem(row, 0, QStandardItem(str(s.id)))
            model.setItem(row, 1, QStandardItem(s.name))
            model.setItem(row, 2, QStandardItem(str(s.price)))
            model.setItem(row, 3, QStandardItem(str(s.average_deviation)))
            model.setItem(row, 4, QStandardItem(s.code))
        self.services.setModel(model)
        self.services.resizeColumnsToContents()

        self.serviceavailabletable.setModel(model)
        self.serviceavailabletable.resizeColumnsToContents()

    def add_service(self):
        name, ok = QInputDialog.getText(self, "Название услуги", "Введите название:")
        if not ok or not name.strip(): return
        code, ok = QInputDialog.getText(self, "Код услуги", "Введите код:")
        if not ok or not code.strip(): return
        price, ok = QInputDialog.getDouble(self, "Цена", "Введите цену:")
        if not ok: return
        days = [str(i) for i in range(1, 5)]
        duration_str, ok = QInputDialog.getItem(self, "Время выполнения", "Количество дней:", days, 0, False)
        if not ok:
            return

        duration_days = int(duration_str)
        average_deviation, ok = QInputDialog.getDouble(self, "Отклонение", "Введите отклонение:")
        if not ok: return

        session = Session()
        service = Service(name=name, code=code, price=price, duration_days=duration_days,average_deviation=average_deviation)
        session.add(service)
        session.commit()
        self.load_services_table()

    def change_service(self):
        selected = self.services.selectionModel().selectedRows()
        if not selected: return
        service_id = int(self.services.model().item(selected[0].row(), 0).text())
        session = Session()
        service = session.query(Service).get(service_id)

        name, ok = QInputDialog.getText(self, "Новое название", "Введите новое название:", text=service.name)
        if ok: service.name = name
        price, ok = QInputDialog.getDouble(self, "Новая цена", "Введите новую цену:", value=service.price)
        if ok: service.price = price
        session.commit()
        self.load_services_table()

    def archive_service(self):
        selected = self.services.selectionModel().selectedRows()
        if not selected: return
        service_id = int(self.services.model().item(selected[0].row(), 0).text())
        session = Session()
        service = session.query(Service).get(service_id)
        service.is_archived = True
        session.commit()
        self.load_services_table()

    def issue_invoice(self):
        session = Session()
        completed_orders = session.query(Order).filter(Order.status == 'Выполнен', Order.is_archived == False).all()
        if not completed_orders:
            QMessageBox.information(self, "Информация", "Нет выполненных заказов для выставления счетов.")
            return

        for order in completed_orders:
            patient = session.query(Patient).get(order.patient_id)
            total_amount = sum(service.price for service in order.services)
            invoice = Invoice(amount=total_amount, company=patient.insurance_company, status='Выставлен', accountant_id=self.user.id)
            session.add(invoice)
            order.is_archived = True
        session.commit()
        self.load_invoices_table()
        QMessageBox.information(self, "Успех", "Счета успешно выставлены.")

    def generate_report(self):
        from sqlalchemy.orm import joinedload

        session = Session()
        invoices = session.query(Invoice).options(joinedload(Invoice.accountant)).all()

        total_sum = 0
        report_lines = ["Счета и застрахованные лица:\n"]

        for invoice in invoices:
            order = session.query(Order).filter_by(is_archived=True).join(Order.services).first()
            if not order or not order.patient:
                continue

            patient = order.patient
            total_sum += invoice.amount

            report_lines.append(
                f"ФИО: {patient.full_name}\n"
                f"Телефон: {patient.phone or '-'}\n"
                f"Email: {patient.email or '-'}\n"
                f"Компания страховки: {patient.insurance_company or '-'}\n"
                f"Тип страховки: {patient.insurance_type or '-'}\n"
                f"Номер полиса: {patient.insurance_number or '-'}\n"
                f"Сумма: {invoice.amount:.2f}₸ | Статус: {invoice.status}\n"
                f"{'-' * 40}"
            )

        report_lines.insert(1, f"Общая сумма: {total_sum:.2f}₸")
        report_text = "\n".join(report_lines)

        with open("invoices_report.txt", "w", encoding="utf-8") as f:
            f.write(report_text)

        QMessageBox.information(self, "Отчёт", f"Отчёт сохранён в invoices_report.txt\nОбщая сумма: {total_sum:.2f}₸")

    def create_order(self):
        selected = self.serviceavailabletable.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну услугу для заказа.")
            return

        session = Session()
        service_ids = [int(self.serviceavailabletable.model().item(row.row(), 0).text()) for row in selected]
        services = session.query(Service).filter(Service.id.in_(service_ids)).all()

        new_order = Order(
            patient_id=self.user.id,
            services=services,
            status="Новый",
            created_at=datetime.utcnow()
        )
        session.add(new_order)
        session.commit()

        QMessageBox.information(self, "Успех", "Заказ успешно создан.")
        self.load_patient_orders()

    def load_available_services(self):
        session = Session()
        services = session.query(Service).filter_by(is_archived=False).all()
        model = QStandardItemModel(len(services), 4)
        model.setHorizontalHeaderLabels(['ID', 'Название', 'Цена', 'Код'])
        for row, s in enumerate(services):
            model.setItem(row, 0, QStandardItem(str(s.id)))
            model.setItem(row, 1, QStandardItem(s.name))
            model.setItem(row, 2, QStandardItem(str(s.price)))
            model.setItem(row, 3, QStandardItem(s.code))
        self.serviceavailabletable.setModel(model)
        self.serviceavailabletable.resizeColumnsToContents()

    def open_order_dialog(self):
        dialog = OrderDialog(self.user.id)
        if dialog.exec_():
            self.load_patient_orders()

    def load_services_for_acceptance(self):
        session = Session()
        results = session.execute(
            order_service_association.select().where(order_service_association.c.service_status == 'Ожидает')
        ).fetchall()

        model = QStandardItemModel(len(results), 3)
        model.setHorizontalHeaderLabels(['Order ID', 'Услуга', 'Статус'])
        for row, record in enumerate(results):
            service = session.query(Service).get(record.service_id)
            model.setItem(row, 0, QStandardItem(str(record.order_id)))
            model.setItem(row, 1, QStandardItem(service.name if service else ''))
            model.setItem(row, 2, QStandardItem(record.service_status))
        self.order_servicestable.setModel(model)
        self.order_servicestable.resizeColumnsToContents()

    def accept_biomaterial(self):
        selected = self.order_servicestable.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите услугу для приёма.")
            return

        session = Session()
        for index in selected:
            order_id = int(self.order_servicestable.model().item(index.row(), 0).text())
            service_name = self.order_servicestable.model().item(index.row(), 1).text()
            service = session.query(Service).filter_by(name=service_name).first()

            session.execute(
                order_service_association.update()
                .where(order_service_association.c.order_id == order_id)
                .where(order_service_association.c.service_id == service.id)
                .values(service_status='Ожидает анализирования', accepted_by_id=self.user.id)
            )

        session.commit()
        self.load_services_for_acceptance()
        self.load_accepted_services()
        QMessageBox.information(self, "Готово", "Биоматериал принят.")

    def load_services_for_analysis(self):
        session = Session()
        results = session.execute(
            order_service_association.select().where(order_service_association.c.service_status == 'Ожидает анализирования')
        ).fetchall()

        model = QStandardItemModel(len(results), 3)
        model.setHorizontalHeaderLabels(['Order ID', 'Услуга', 'Статус'])
        for row, record in enumerate(results):
            service = session.query(Service).get(record.service_id)
            model.setItem(row, 0, QStandardItem(str(record.order_id)))
            model.setItem(row, 1, QStandardItem(service.name if service else ''))
            model.setItem(row, 2, QStandardItem(record.service_status))
        self.order_servicestable_2.setModel(model)
        self.order_servicestable_2.resizeColumnsToContents()

    def analyze_service(self):
        selected = self.order_servicestable_2.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите услугу для анализа.")
            return

        session = Session()
        for index in selected:
            order_id = int(self.order_servicestable_2.model().item(index.row(), 0).text())
            service_name = self.order_servicestable_2.model().item(index.row(), 1).text()
            service = session.query(Service).filter_by(name=service_name).first()

            result_text, ok = QInputDialog.getText(self, "Результат анализа", f"Введите результат для {service.name}:")
            if ok and result_text:
                session.execute(
                    order_service_association.update()
                    .where(order_service_association.c.order_id == order_id)
                    .where(order_service_association.c.service_id == service.id)
                    .values(service_status='Выполнен', result=result_text)
                )

                statuses = session.execute(
                    order_service_association.select()
                    .where(order_service_association.c.order_id == order_id)
                ).fetchall()
                if all(s.service_status == 'Выполнен' for s in statuses):
                    order = session.query(Order).get(order_id)
                    order.status = 'Выполнен'
                    order.completed_at = datetime.utcnow()
                    QMessageBox.information(self, "Готово", f"Заказ №{order_id} полностью выполнен.")

        session.commit()
        self.load_services_for_analysis()
        QMessageBox.information(self, "Готово", "Анализ завершён.")

class OrderDialog(QDialog):
    def __init__(self, patient_id):
        super().__init__()
        uic.loadUi("create_order.ui", self)
        self.patient_id = patient_id

        self.pushButton.clicked.connect(self.create_order)
        self.load_services()

    def load_services(self):
        session = Session()
        services = session.query(Service).filter_by(is_archived=False).all()
        self.listWidget.clear()
        for service in services:
            item = QtWidgets.QListWidgetItem(f"{service.name} — {service.price:.2f}₸")
            item.setData(QtCore.Qt.UserRole, service.id)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.listWidget.addItem(item)

    def create_order(self):
        session = Session()
        service_ids = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                service_ids.append(item.data(QtCore.Qt.UserRole))

        if not service_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну услугу.")
            return

        services = session.query(Service).filter(Service.id.in_(service_ids)).all()
        new_order = Order(
            patient_id=self.patient_id,
            services=services,
            status="В работе",
            created_at=datetime.utcnow()
        )
        session.add(new_order)
        session.commit()

        QMessageBox.information(self, "Успех", "Заказ успешно создан.")
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Login()
    window.show()
    sys.exit(app.exec_())
