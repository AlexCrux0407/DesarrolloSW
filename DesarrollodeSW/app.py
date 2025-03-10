from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from datetime import date
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Restaurante API",
    description="API para administrar sucursales de restaurante",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database connection
def get_connection():
    try:
        # First connect without specifying a database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Change to your MySQL username
            password='1917248zzz'   # Change to your MySQL password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check if database exists first
            cursor.execute("SHOW DATABASES LIKE 'restaurante_db'")
            result = cursor.fetchone()
            
            # Create the database only if it doesn't exist
            if not result:
                cursor.execute("CREATE DATABASE restaurante_db")
                print("Database created successfully")
            
            # Use the database
            cursor.execute("USE restaurante_db")
            
            print("Database connected successfully")
            cursor.close()
            return connection
    except Exception as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()

# Create tables on startup
@app.on_event("startup")
def startup_db_client():
    connection = get_connection()
    if connection:
        create_tables(connection)
        close_connection(connection)

def create_tables(connection):
    try:
        cursor = connection.cursor()
        
        # Create sucursales table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sucursales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            num_empleados INT NOT NULL,
            num_proveedores INT DEFAULT 0,
            num_pedidos INT DEFAULT 0
        )
        """)
        
        # Create empleados table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            puesto VARCHAR(50) NOT NULL,
            fecha_contratacion DATE NOT NULL,
            sucursal_id INT NOT NULL,
            FOREIGN KEY (sucursal_id) REFERENCES sucursales(id)
        )
        """)
        
        # Create proveedores table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            producto VARCHAR(100) NOT NULL,
            inicio_contrato DATE NOT NULL,
            sucursal_id INT NOT NULL,
            FOREIGN KEY (sucursal_id) REFERENCES sucursales(id)
        )
        """)
        
        connection.commit()
        print("Tables verified successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

# Pydantic models for request/response
class SucursalBase(BaseModel):
    nombre: str
    num_empleados: int
    num_proveedores: Optional[int] = 0
    num_pedidos: Optional[int] = 0

class SucursalCreate(SucursalBase):
    pass

class Sucursal(SucursalBase):
    id: int

    class Config:
        orm_mode = True

class EmpleadoBase(BaseModel):
    nombre: str
    puesto: str
    fecha_contratacion: date
    sucursal_id: int

class EmpleadoCreate(EmpleadoBase):
    pass

class Empleado(EmpleadoBase):
    id: int

    class Config:
        orm_mode = True

class ProveedorBase(BaseModel):
    nombre: str
    producto: str
    inicio_contrato: date
    sucursal_id: int

class ProveedorCreate(ProveedorBase):
    pass

class Proveedor(ProveedorBase):
    id: int

    class Config:
        orm_mode = True

# Root endpoint
@app.get("/", tags=["web"])
async def web_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Sucursales API routes
@app.get("/sucursales", response_model=List[Sucursal], tags=["sucursales"])
def get_all_sucursales():
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sucursales")
        sucursales = cursor.fetchall()
        return sucursales
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.get("/sucursales/{sucursal_id}", response_model=Sucursal, tags=["sucursales"])
def get_sucursal(sucursal_id: int):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sucursales WHERE id = %s", (sucursal_id,))
        sucursal = cursor.fetchone()
        
        if not sucursal:
            raise HTTPException(status_code=404, detail="Sucursal not found")
        
        return sucursal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.post("/sucursales", response_model=Sucursal, tags=["sucursales"])
def create_sucursal(sucursal: SucursalCreate):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        INSERT INTO sucursales (nombre, num_empleados, num_proveedores, num_pedidos)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            sucursal.nombre,
            sucursal.num_empleados,
            sucursal.num_proveedores,
            sucursal.num_pedidos
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        last_id = cursor.lastrowid
        cursor.execute("SELECT * FROM sucursales WHERE id = %s", (last_id,))
        new_sucursal = cursor.fetchone()
        
        return new_sucursal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.put("/sucursales/{sucursal_id}", response_model=Sucursal, tags=["sucursales"])
def update_sucursal(sucursal_id: int, sucursal: SucursalCreate):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        UPDATE sucursales 
        SET nombre = %s, num_empleados = %s, num_proveedores = %s, num_pedidos = %s
        WHERE id = %s
        """
        values = (
            sucursal.nombre,
            sucursal.num_empleados,
            sucursal.num_proveedores,
            sucursal.num_pedidos,
            sucursal_id
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sucursal not found")
        
        cursor.execute("SELECT * FROM sucursales WHERE id = %s", (sucursal_id,))
        updated_sucursal = cursor.fetchone()
        
        return updated_sucursal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.delete("/sucursales/{sucursal_id}", tags=["sucursales"])
def delete_sucursal(sucursal_id: int):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sucursales WHERE id = %s", (sucursal_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sucursal not found")
        
        return {"message": "Sucursal deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

# Empleados API routes
@app.get("/empleados", response_model=List[Empleado], tags=["empleados"])
def get_all_empleados():
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM empleados")
        empleados = cursor.fetchall()
        return empleados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.get("/empleados/sucursal/{sucursal_id}", response_model=List[Empleado], tags=["empleados"])
def get_empleados_by_sucursal(sucursal_id: int):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM empleados WHERE sucursal_id = %s", (sucursal_id,))
        empleados = cursor.fetchall()
        return empleados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.post("/empleados", response_model=Empleado, tags=["empleados"])
def create_empleado(empleado: EmpleadoCreate):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        # First check if the sucursal exists
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM sucursales WHERE id = %s", (empleado.sucursal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Sucursal not found")
        
        cursor = connection.cursor(dictionary=True)
        query = """
        INSERT INTO empleados (nombre, puesto, fecha_contratacion, sucursal_id)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            empleado.nombre,
            empleado.puesto,
            empleado.fecha_contratacion,
            empleado.sucursal_id
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        # Update the number of employees in the sucursal
        cursor.execute("UPDATE sucursales SET num_empleados = num_empleados + 1 WHERE id = %s", 
                      (empleado.sucursal_id,))
        connection.commit()
        
        last_id = cursor.lastrowid
        cursor.execute("SELECT * FROM empleados WHERE id = %s", (last_id,))
        new_empleado = cursor.fetchone()
        
        return new_empleado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

@app.delete("/empleados/{empleado_id}", tags=["empleados"])
def delete_empleado(empleado_id: int):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        cursor = connection.cursor()
        
        # Get the sucursal_id before deleting
        cursor.execute("SELECT sucursal_id FROM empleados WHERE id = %s", (empleado_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Empleado not found")
        
        sucursal_id = result[0]
        
        # Delete the empleado
        cursor.execute("DELETE FROM empleados WHERE id = %s", (empleado_id,))
        connection.commit()
        
        # Update the employee count in the sucursal
        cursor.execute("UPDATE sucursales SET num_empleados = num_empleados - 1 WHERE id = %s", 
                      (sucursal_id,))
        connection.commit()
        
        return {"message": "Empleado deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        close_connection(connection)

# Web interface routes
@app.get("/web/sucursales", tags=["web"])
async def web_sucursales(request: Request):
    connection = get_connection()
    if not connection:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Database connection error"})
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sucursales")
        sucursales = cursor.fetchall()
        return templates.TemplateResponse("sucursales.html", {"request": request, "sucursales": sucursales})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(e)})
    finally:
        cursor.close()
        close_connection(connection)



# New routes for creating sucursales
@app.get("/web/sucursales/nueva", tags=["web"])
async def web_nueva_sucursal(request: Request):
    return templates.TemplateResponse("sucursal_form.html", {"request": request})

@app.post("/web/sucursales/nueva", tags=["web"])
async def web_crear_sucursal(request: Request, nombre: str = Form(...), num_empleados: int = Form(0)):
    connection = get_connection()
    if not connection:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Database connection error"})
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        INSERT INTO sucursales (nombre, num_empleados, num_proveedores, num_pedidos)
        VALUES (%s, %s, %s, %s)
        """
        values = (nombre, num_empleados, 0, 0)
        
        cursor.execute(query, values)
        connection.commit()
        
        return RedirectResponse(url="/web/sucursales", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(e)})
    finally:
        cursor.close()
        close_connection(connection)
        
        
        
@app.get("/web/sucursales/{sucursal_id}", tags=["web"])
async def web_sucursal_detail(request: Request, sucursal_id: int):
    connection = get_connection()
    if not connection:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Database connection error"})
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sucursales WHERE id = %s", (sucursal_id,))
        sucursal = cursor.fetchone()
        
        if not sucursal:
            return templates.TemplateResponse("error.html", {"request": request, "message": "Sucursal not found"})
        
        # Get employees for this branch
        cursor.execute("SELECT * FROM empleados WHERE sucursal_id = %s", (sucursal_id,))
        empleados = cursor.fetchall()
        
        return templates.TemplateResponse("sucursal_detalle.html", {
            "request": request, 
            "sucursal": sucursal,
            "empleados": empleados
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(e)})
    finally:
        cursor.close()
        close_connection(connection)