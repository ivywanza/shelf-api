from fastapi import FastAPI, HTTPException , status
from dbservice import *
from schemas import *
from fastapi.middleware.cors import CORSMiddleware 
from security import *


app = FastAPI()
db = SessionLocal()

origins = [
    "http://localhost",
    "http://localhost:5173"
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.post('/branch')
def create_branch(branch: BranchRequest):
    existing_branch = db.query(Branch).filter(Branch.branch_name == branch.branch_name).first()

    if not existing_branch:
        try:
            new_branch=Branch(
                branch_name = branch.branch_name,
                branch_location = branch.branch_location
            )
            db.add(new_branch)
            db.commit()
            db.refresh(new_branch)
            db.close()

            return {'detail': ' branch added succesfully'}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    else:
        return {'detail' : 'branch is already registered'}
        
@app.get('/branches' , response_model = list[BranchResponse])
def get_branches():

    branches = db.query(Branch).all()
    if branches is None:
        raise HTTPException(status_code=404, detail="There are no registered branches")

    return branches

@app.post('/user_login')
def login_user(login_details: LoginRequest):

    user = authenticate_user(login_details.email, login_details.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.employee_email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/employee')
def add_employee(employee: EmployeeCreate):
    password = pwd_context.hash(employee.password)
    existing_employee = db.query(Employee).filter(Employee.national_id_number==employee.national_id).first()

    if not existing_employee:
        try:

            new_employee = Employee(
                employee_name=employee.employee_name,
                employee_email = employee.employee_email,
                national_id_number = employee.national_id,
                branch_id = employee.branch_id,
                password = password,
                role = employee.role
            )
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)

            return {'detail': ' employee added succesfully'}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    else:
        return {'detail' : 'employee is already registered'}
    
@app.get('/employees', response_model=list[EmployeeResponse])
def get_employees():
    existing_employees = db.query(Employee).all()
     
    return existing_employees

@app.get('/employees/{employee_id}', response_model=list[EmployeeResponse])
def get_employee_details(employee_id:int):

    existing_employees = db.query(Employee).filter(Employee.id==employee_id).first()
    
    return existing_employees

@app.post('/shelf')
def add_shelf(shelf: ShelfRequest):
    shelves= db.query(Shelf).filter(Shelf.account_number == shelf.account_number).first()

    if not shelves:
        try:
            new_shelf=Shelf(
                account_number= shelf.account_number,
                shelf_type_id=shelf.shelf_type_id,
                status = shelf.status
            )
            db.add(new_shelf)
            db.commit()
            db.refresh(new_shelf)

            return {'detail' : 'shelf added succesfully!'}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    else:
        return {'detail' : 'shelf already exist'}
    
@app.get('/shelves', response_model=list[ShelfResponse])
def get_shelves():
    shelves=db.query(Shelf).all()

    if shelves is None:
        raise HTTPException(status_code=404, detail="no shelf registered")
    return shelves

@app.post('/shelf_type')
def add_shelf_type(shelf_type :ShelfTypeRequest):
    existing_shelf_type = db.query(ShelfType).filter(ShelfType.description==shelf_type.description and ShelfType.size == shelf_type.description).first()

    if not existing_shelf_type:
        try:
            new_shelf_type = ShelfType(
                size = shelf_type.size,
                description = shelf_type.description,
                price = shelf_type.price
            )
            
            db.add(new_shelf_type)
            db.commit()
            db.refresh(new_shelf_type)

            return {'detail' : 'shelf_type added succesfully'}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    else:
        return {'detail' : 'shelf_type already exists'}
        
@app.get('/shelf_type' ,response_model=list[ShelfTypeResponse])
def get_existing_shelfTypes():
    
    existing_shelf_types = db.query(ShelfType).all()

    if existing_shelf_types is None:
        raise HTTPException(status_code=404, detail="null")
    
    return existing_shelf_types

@app.post('/client')
def add_client(client: ClientCreate):
    existing_client= db.query(Client).filter(Client.client_email==client.client_email).first()

    if not existing_client :
        try:
            new_client = Client(
                client_name = client.client_name,
                client_email = client.client_email,
                phone_number = client.phone_number,
                start_date = client.start_date,
                shelf_id = client.shelf_id
            )
            db.add(new_client)
            db.commit()
            db.refresh(new_client)

            return {'detail'  : 'client added succesfully'}
        
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    return {'detail' : 'client with that email already exists'}

@app.get('/clients', response_model=list[ClientResponse])
def get_clients():

    clients = db.query(Client).all()

    if clients is None:
        raise HTTPException(status_code=404, detail="null")
    
    return clients

@app.post('/payment_method')
def add_payment_method(payment_methods : PaymentMethodRequest):
    existing_payment_methods = db.query(PaymentMethod).filter(PaymentMethod.payment_method == payment_methods.payment_method).first()

    if not existing_payment_methods :
        try:
            new_payment_method = PaymentMethod(
                payment_method= payment_methods.payment_method
            ) 
            db.add(new_payment_method)
            db.commit()
            db.refresh(new_payment_method)

            return {'detail' : 'payment method added succesfully !'}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    else :
        return {'detail' : 'payment method already exists'}
    

@app.post('/payment')
def make_payment(payment: PaymentRequest):

    payment_made = db.query(Payment).filter(Payment.shelf_id==payment.shelf_id and Payment.amount == payment.amount and Payment.payment_date == payment.payment_date).first()

    if not payment_made:
        try:
            new_payment = Payment(
                payment_method_id = payment.payment_method_id,
                shelf_id = payment.shelf_id,
                amount = payment.amount,
                payment_date = payment.payment_date,
                status= payment.status
            )
            db.add(new_payment)
            db.commit()
            db.refresh(new_payment)

            return {'detail': 'payment recorded succesfully!'}
        
        
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    return {'detail' : 'Ensure you input correct details!'}
    

@app.get('/payments', response_model=list[PaymentResponse])
def get_payments():
    existing_payment_records = db.query(Payment).all()

    if existing_payment_records is None:
        raise HTTPException(status_code=404, detail="null")
    
    return existing_payment_records


    
