from ast import For
from datetime import datetime
import re
from turtle import st
from fastapi import FastAPI, Request, Cookie
from fastapi.params import Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import starlette.status as status
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# creating a FastAPI object
app = FastAPI()
security = HTTPBasic()

# configuring the static, which serve static
app.mount("/static", StaticFiles(directory="static"), name="static")


# adding the Session Middleware
app.add_middleware(SessionMiddleware, secret_key='MyApp')

# configuring the HTML pages
templates = Jinja2Templates(directory="templates")

#constant name for DATABASE_NAME
DATABASE_NAME = "app.db"


# declaring urls
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/dev", response_class=HTMLResponse)
def dev(request: Request):
    return templates.TemplateResponse("dev.html", {"request": request})

@app.post("/dev", response_class=HTMLResponse)
def dev(request: Request):
          return RedirectResponse("/.html", status_code=status.HTTP_302_FOUND)

@app.get("/appointment", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("/appointment.html", {"request": request})

@app.post("/appointment", response_class=HTMLResponse)
def index(request: Request, pname:str = Form(...), date_request:str = Form(...)):

     with sqlite3.connect("app.db") as con:
        cur = con.cursor()
        cur.execute ("INSERT into appointment(name, date_request) values(?,?)",
                  (pname, date_request))
        con.commit()
        return RedirectResponse("/appointment", status_code=status.HTTP_302_FOUND)

@app.get("/flash", response_class=HTMLResponse)
def flash(request: Request):
    return templates.TemplateResponse("flash.html", {"request": request})

@app.post("/flash", response_class=HTMLResponse)
def flash(request: Request):
          return RedirectResponse("/.html", status_code=status.HTTP_302_FOUND)        

@app.get("/review", response_class=HTMLResponse)
def review_page(request: Request):
    return templates.TemplateResponse("review.html", {"request": request})

@app.post("/review", response_class=HTMLResponse)
def review_page(request: Request, mreviews:str = Form(...)):
    with sqlite3.connect("app.db") as con:
        cur = con.cursor()
        review_query = "INSERT into reviews(review) values('{}')".format(mreviews)
        cur.execute (review_query)
        con.commit()
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.get("/prescription", response_class=HTMLResponse)
def prescription(request: Request):
    return templates.TemplateResponse("prescription.html", {"request": request})

@app.post("/prescription", response_class=HTMLResponse)
def prescription(request: Request):
          return RedirectResponse("/prescription", status_code=status.HTTP_302_FOUND) 


@app.get("/shop", response_class=HTMLResponse)
def shop(request: Request):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products")
    plants = cur.fetchall()
    con.close
    return templates.TemplateResponse("shop.html", {"request": request, "plants": plants})


@app.get("/details/{pid}", response_class=HTMLResponse)
def detail(request: Request, pid: int):
    if not request.session.get('isLogin'):
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products where id =?", [pid])
    description = cur.fetchall()
    con.close

    return templates.TemplateResponse("details.html", {"request": request, "pid": pid, "description": description[0]})


@app.get("/register",response_class=HTMLResponse)
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
def do_register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...),
                address: str = Form(...), phone: str = Form(...)):
    with sqlite3.connect(DATABASE_NAME) as con:
        cur = con.cursor()
        cur.execute("INSERT into users(username, password, email, address, phone) values(?,?,?,?,?)",
                    (username, password, email, address, phone))
        con.commit()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@app.get("/login",response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
def do_login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from users where username =? and password=?", [username, password])
    user = cur.fetchone()
    if not user:
        return templates.TemplateResponse("/login.html", {"request": request, "msg": "Invalid Username or Password"})
    else:
        request.session.setdefault("isLogin", True)
        request.session.setdefault('username', user['username'])
        request.session.setdefault('uid', user['id'])
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@app.get("/addtocart", response_class=HTMLResponse)
async def addtocart(request: Request, pid:int = 1, qty:int = 1):
    uid = request.session.get('uid')
    with sqlite3.connect(DATABASE_NAME, check_same_thread=False) as con:
        cur = con.cursor()
        cur.execute("INSERT into carts(pid, qty, uid) values(?,?,?)",
                    (pid, qty, uid))
        con.commit()
    return RedirectResponse("/cart", status_code=status.HTTP_302_FOUND)


@app.get("/cart", response_class=HTMLResponse)
def cart(request: Request):
    if not request.session.get('isLogin'):
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

    uid = request.session.get('uid')

    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT *,c.id as cid from USERS u,carts c, products p where u.id=c.uid and c.pid=p.id and c.uid =?", [uid])
    items = cur.fetchall()
    total = sum(map(lambda item: int(item['qty']) * int(item['price']), items))
    con.close
    return templates.TemplateResponse("/cart.html", {"request": request, "items": items, "total" :total})


@app.get("/deletecart/{cid}", response_class=HTMLResponse)
def delete_cart_item(request: Request, cid: int):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("Delete from carts where id =?", [cid])
    con.commit()
    con.close
    return RedirectResponse("/cart", status_code=status.HTTP_302_FOUND)


@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@app.get("/confrim", response_class=HTMLResponse)
def confrim(request: Request,payment_id:str=""):    
    uid = request.session.get('uid')
    with sqlite3.connect(DATABASE_NAME, check_same_thread=False) as con:
        cur = con.cursor()
        print(payment_id)
        cur.execute("SELECT * from carts where uid = ? ",[uid])
        carts = cur.fetchall()
        for cart in carts:
            cur.execute("select * from products where id=?", [cart[1]])
            products = cur.fetchall()
            actual_value = int(products[0][7])
            update_stock_value = actual_value - int(cart[2])
            cur.execute("UPDATE products set stocks = ? where id=?",[update_stock_value, cart[1]])
            now = datetime.now()
            order_time = now.strftime("%d/%m/%Y %H:%M:%S")
            cur.execute("INSERT into orders(pid, qty, uid,status,date) values(?,?,?,?,?)",
                        [cart[1], cart[2], cart[3], "ORDERED", order_time])
        cur.execute("Delete from carts where uid = ? ", [uid])
        con.commit()

    return RedirectResponse("/orders", status_code=status.HTTP_302_FOUND)


@app.get("/orders",response_class=HTMLResponse)
def orders(request : Request):
    if not request.session.get('isLogin'):
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

    uid = request.session.get('uid')

    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT *,o.id as oid from USERS u,orders o, products p where u.id=o.uid and o.pid=p.id and o.uid =?",
                [uid])
    orders = cur.fetchall()
    con.close
    return templates.TemplateResponse("/orders.html", {"request": request, "orders": orders})


@app.get("/admin/", response_class=HTMLResponse)
def admin_index(request: Request):
    return templates.TemplateResponse("/admin/index.html", {"request": request})


@app.post("/admin/", response_class=HTMLResponse)
def admin_index(request: Request, username: str = Form(...), password: str = Form(...)):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from admin where username =? and password=?", [username, password])
    admin = cur.fetchone()
    if not admin:
        return templates.TemplateResponse("/admin/index.html", {"request": request, "msg": "Invalid Username or Password"})
    else:
        request.session.setdefault("isLogin", True)
        request.session.setdefault('username', admin['username'])
        request.session.setdefault('uid', admin['id'])
        request.session.setdefault('role', admin['role'])
        return RedirectResponse("/admin/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products")
    products = cur.fetchall()
    cur.execute("select * from appointment")
    appointments = cur.fetchall()
    con.close
    return templates.TemplateResponse("/admin/dashboard.html", {"request": request, "items": products, "requests": appointments})

@app.get("/promo", response_class=HTMLResponse)
def promo(request: Request):
    return templates.TemplateResponse("/admin/promo.html", {"request": request})



@app.get("/admin/products", response_class=HTMLResponse)
def admin_products(request: Request):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products")
    products = cur.fetchall()
    con.close
    return templates.TemplateResponse("/admin/products.html", {"request": request, "products": products})


@app.get("/admin/products/create", response_class=HTMLResponse)
def admin_products_create(request: Request):
    return templates.TemplateResponse("/admin/products_create.html", {"request": request})


@app.post("/admin/products/create", response_class=HTMLResponse)
def admin_products_create(request: Request, pname:str = Form(...), price: str = Form(...), image: str = Form(...), details: str = Form(...), tags: str = Form(...), category:str = Form(...)):
    with sqlite3.connect(DATABASE_NAME) as con:
        cur = con.cursor()
        cur.execute("INSERT into products(name, price, details, image, tags, category) values(?, ?, ?, ?, ?, ?)",
                    (pname, price, details, image, tags, category))
        con.commit()
    return RedirectResponse("/admin/products",status_code=status.HTTP_302_FOUND)


@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders(request: Request):
    con = sqlite3.connect(DATABASE_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT *, o.id as oid from users u, products p, orders o where o.uid = u.id and o.pid = p.id")
    orders = cur.fetchall()
    con.close
    return templates.TemplateResponse("/admin/orders.html", {"request": request, "orders": orders})


@app.get("/admin/logout", response_class=HTMLResponse)
def admin_logout(request: Request):
    return templates.TemplateResponse("/admin/logout", {"request": request})


@app.get("/admin/products_edit/{pid}", response_class=HTMLResponse)
def admin_product_edit(request: Request, pid: int = 0):
    return templates.TemplateResponse("/admin/products_edit.html", {"request": request})


@app.get("/admin/products_delete/{pid}", response_class=HTMLResponse)
def admin_product_delete(request: Request, pid: int = 0):
    return RedirectResponse("/admin/products", status_code=status.HTTP_302_FOUND)


@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders(request: Request):
    return templates.TemplateResponse("/admin/orders.html", {"request": request})


@app.get("/admin/orders_view/{oid}", response_class=HTMLResponse)
def admin_order_view(request: Request, oid: int = 0):
    return templates.TemplateResponse("/admin/orders_view.html", {"request": request})


@app.get("/products", response_class=HTMLResponse)
def products(request: Request):
    con = sqlite3.connect("app.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products")
    products = cur.fetchall()
    con.close
    return templates.TemplateResponse("/products.html", {"request" : request, "products": products })  

@app.get("/view/{pid}", response_class=HTMLResponse)
def view(request: Request, pid: int = 0): 
    con = sqlite3.connect("app.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from products where id =?", [pid])
    product = cur.fetchall()
    con.close
    return templates.TemplateResponse("/view.html", {"request": request, "product": product[0]}) 
