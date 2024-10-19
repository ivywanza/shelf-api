from sqlalchemy import Enum, create_engine, Column,Integer,String,ForeignKey,Float,DateTime,MetaData,Boolean
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum


SQLALCHEMY_DATABASE_URL = "sqlite:///.rent_a_shelf.db"
engine= create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Company(Base):
    __tablename__="companies"

    id=Column(Integer,primary_key=True,autoincrement=True)
    company_name=Column(String, nullable=False)
    company_email=Column(String(80), nullable=False, unique=True)
    phone_number=Column(String(20),nullable=False, unique=True)
    company_password=Column(String, nullable=False)
    company_location=Column(String, nullable=True)
    registration_date=Column(DateTime, default=datetime.utcnow)
    role_id =  Column(Integer, ForeignKey('companies.id'))


    # role=Column(Enum(UserRole),default=UserRole.SUPERIORADMIN)
    is_active=Column(Boolean, default=True)

    # relationships
    employee = relationship('Employee', backref="company_employees")
    customer = relationship('Customer', backref='company_customers')
    role = relationship("Role", backref='companies')
    branch = relationship('Branch', backref='company_branches')
    product = relationship('Product', backref='company_products')
    payment_method = relationship('CustomerToCompanyPaymentMethod', backref='company_customer_payment')
    sales = relationship('Sale', backref='company_sale')
    payments = relationship('Payment', backref='company_payments')


class Status(Base):
    __tablename__="status"

    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String,nullable=False)

    # relationship
    branch=relationship('Branch', backref='branch_status')
    employee=relationship('Employee', backref='employee_status')


class Branch(Base):
    __tablename__='branches'

    id=Column(Integer,primary_key=True,autoincrement=True)
    branch_location=Column(String(100), nullable=False)
    branch_name = Column(String(80), nullable=False)
    status_id=Column(Integer,ForeignKey('status.id'), nullable=False)

    #relationships
    employee=relationship('Employee', backref='branches_employees')

class Role(Base):
    __tablename__="roles"

    id=Column(Integer,primary_key=True,autoincrement=True)
    roleName=Column(String, nullable=False)

    #relationships
    employees=relationship('Employee',backref='employee_roles') 

class Employee(Base):
    __tablename__= 'employees'

    id=Column(Integer,primary_key=True,autoincrement=True)
    employee_name=Column(String(50) ,nullable=False)
    employee_email=Column(String(100) ,nullable=False , unique=True)
    national_id_number = Column(String(80), nullable=False, unique=True)
    password=Column(String(255), nullable=False, unique=True)
    branch_id=Column(Integer, ForeignKey('branches.id'))
    role_id=Column(Integer, ForeignKey('roles.id'),nullable=False)
    status_id=Column(Integer, ForeignKey('status.id'), nullable=False)

    #Relationship
    # branch=relationship('Branch',backref='employees')

class ShelfType(Base):
    __tablename__= 'shelf_types'

    id=Column(Integer,primary_key=True,autoincrement=True)
    size=Column(String(80),nullable=False)
    description=Column(String(255))
    price=Column(Float(2),nullable=False)

    #relationship
    shelf = relationship('Shelf', backref='shelf_types')

class Shelf(Base):
    __tablename__ = 'shelves'

    id=Column(Integer,primary_key=True,autoincrement=True)
    account_number = Column(String(70), nullable=False, unique=True)
    status = Column(String(30) , nullable=False)
    shelf_type_id = Column(Integer, ForeignKey("shelf_types.id"))
    #relationship
    
    Payment=relationship('Payment' ,backref='shelves')
    client=relationship('Client', backref='shelves') 

class PaymentMethod(Base):
    __tablename__= 'payment_methods'

    id=Column(Integer,primary_key=True,autoincrement=True)
    payment_method=Column(String(150), nullable=False)

    #relationships
    payment=relationship('Payment',backref='payment_methods')
    

class Payment(Base):
    __tablename__='payments'

    id=Column(Integer,primary_key=True,autoincrement=True)
    payment_method_id=Column(Integer, ForeignKey("payment_methods.id"),nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    shelf_id = Column(Integer, ForeignKey("shelves.id"))
    amount = Column(Float(2),nullable=False)
    status= Column(String, nullable=False)

class Client(Base):
    __tablename__ = 'clients'

    id=Column(Integer,primary_key=True,autoincrement=True)
    client_name = Column(String(100), nullable=False)
    client_email= Column(String(100), nullable=False, unique=True)
    phone_number=Column(String(20),unique=True)
    start_date= Column(DateTime, default=datetime.utcnow, nullable=False)
    shelf_id= Column(Integer, ForeignKey('shelves.id'))

Base.metadata.create_all(bind=engine)