from fastapi import FastAPI, HTTPException , status, Request, Form
from app.dbservice import *
from app.schemas import *
from fastapi.middleware.cors import CORSMiddleware 
from app.security import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


app = FastAPI()
db = SessionLocal()
templates = Jinja2Templates(directory="templates")


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
                branch_location = branch.branch_location,
                status_id=branch.status_id
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

# status create
@app.post('/add-status')
def add_status(status:StatusRequest):
    try:
        existing_status=db.query(Status).filter(Status.name==status.name).first()
        
        if existing_status:
            raise HTTPException(status_code=409, detail="status already exists")
        
        register_status=Status(
            name=status.name
        )
        db.add(register_status)
        db.commit()
        db.refresh(register_status)
        return {"message":"status registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error adding status: {str(e)}")
    
@app.get('/status', response_model=list[StatusResponse])
def get_status():
    try:
        status=db.query(Status).all()

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to fetch resources: {str(e)}")
    
@app.delete('/del-status/{status_id}')
def del_status(status_id:int):
    try:
        status=db.query(Status).filter(Status.id==status_id).first()

        db.delete(status)
        db.commit()
        return {'message':'status deleted successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed !: {str(e)}")

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

# register employee details
@app.post('/employee')
def add_employee(employee: EmployeeCreate):
    password = pwd_context.hash(employee.password)
    existing_employee = db.query(Employee).filter(Employee.national_id_number==employee.national_id_number).first()

    if not existing_employee:
        try:

            new_employee = Employee(
                employee_name=employee.employee_name,
                employee_email = employee.employee_email,
                national_id_number = employee.national_id_number,
                branch_id = employee.branch_id,
                password = password,
                role_id = employee.role_id,
                status_id=employee.status_id
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
    
# get all registered employee
@app.get('/employees', response_model=list[EmployeeResponse])
def get_employees():
    existing_employees = db.query(Employee).all()
     
    return existing_employees

# get employee details
@app.get('/employees/{employee_id}', response_model=list[EmployeeResponse])
def get_employee_details(employee_id:int):

    existing_employees = db.query(Employee).filter(Employee.id==employee_id).all()
    
    return existing_employees

# update employee details
@app.put('/employee/{employee_id}')
def update_employee_details(employee_id:int, request:EmployeeUpdate):
    try:
        employee=db.query(Employee).filter(Employee.id==employee_id).first()

        if not employee:
            raise HTTPException(status_code=409, detail="Employee does not exist")
       
        if request.employee_name:
            employee.employee_name=request.employee_name

        if request.employee_email:
            employee.employee_email==request.employee_email

        if request.status_id:
            employee.status_id=request.status_id

        if request.role_id:
            employee.role_id==request.role_id

        db.commit()

        return {'message':'details updated successfully!'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error updating details:{str(e)}")
    
# @app.delete('/delete_emloyee/{employee_id}')
# def delete_employee(employee_id:int):
#     try:
#         employee=db.query(Employee).filter(Employee.id==employee_id).first()

#         db.delete(employee)
#         db.commit()
#         return {'message':'employee details deleted successfully'}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"failed !: {str(e)}")


# reset password

@app.post("/password-reset-request/")
async def password_reset_request(request: PasswordResetRequest):
    
    user = db.query(Employee).filter(Employee.employee_email == request.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    token = create_reset_token(user.employee_email)

    send_reset_email(user.employee_email, token)
    return {"msg": "Password reset email has been sent. Link will expire in 15 minutes!"}

@app.get("/reset_password/{token}", response_class=HTMLResponse)
async def get_reset_password_form(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/reset-password/")
async def reset_password( 
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...) 
    
    ):

    # Verify the token and get the email
    email = verify_reset_token(token)
    
    # confirm password match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    # Query the Employee table
    user = db.query(Employee).filter(Employee.employee_email == email).first()
    
    # If the user is not found in either table, raise a 404 error
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Hash the new password
    hashed_password = get_password_hash(new_password)

    # Update the password based on user type
    user.password = hashed_password

    db.commit()

    # Commit the changes to the database
    db.commit()
    
    return {"msg": "Password reset successful."}

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


    
