from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


order_service_association = Table(
    'order_services', Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('service_id', Integer, ForeignKey('services.id')),
    Column('service_status', String, default='Ожидает'),
    Column('result', String),
    Column('accepted_by_id', Integer, ForeignKey('users.id')),
    Column('accepted_at', DateTime, default=datetime.utcnow),
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    photo = Column(String, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)

    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'user'
    }


class Patient(User):
    __tablename__ = 'patients'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    date_of_birth = Column(DateTime, nullable=False)
    passport = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    insurance_number = Column(String)
    insurance_type = Column(String)
    insurance_company = Column(String)

    orders = relationship('Order', back_populates='patient')

    __mapper_args__ = {
        'polymorphic_identity': 'пациент'
    }



class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    code = Column(String, unique=True, nullable=False)
    duration_days = Column(Integer, nullable=False)
    average_deviation = Column(Float)
    is_archived = Column(Boolean, default=False)



class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='Новый')  # Статус заказа: Новый, В процессе, Выполнен, Архив и т.д.
    completed_at = Column(DateTime)  # когда заказ завершён
    is_archived = Column(Boolean, default=False)

    patient_id = Column(Integer, ForeignKey('patients.id'))
    patient = relationship('Patient', back_populates='orders')

    services = relationship('Service', secondary=order_service_association, backref='orders')


class Accountant(User):
    __tablename__ = 'accountants'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    services_set = Column(String)
    invoices = relationship('Invoice', back_populates='accountant')

    __mapper_args__ = {
        'polymorphic_identity': 'бухгалтер'
    }


class Admin(User):
    __tablename__ = 'admins'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'администратор'
    }


class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float, nullable=False)
    company = Column(String, nullable=False)
    status = Column(String, default='Выставлен')  # Статус счета: Выставлен, Оплачен, Отклонен

    accountant_id = Column(Integer, ForeignKey('accountants.id'))
    accountant = relationship('Accountant', back_populates='invoices')

class Laboratorian(User):
    __tablename__ = 'laboratorians'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'лаборант'
    }


class Researcher(User):
    __tablename__ = 'researcher_labs'
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'лаборант-исследователь'
    }

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')

engine = create_engine('sqlite:///database.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)