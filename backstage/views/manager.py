from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import *
import imp, random, os, string
import psycopg2
from werkzeug.utils import secure_filename
from flask import current_app
from io import BytesIO

UPLOAD_FOLDER = 'static/product'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'pjp', 'pjpeg', 'jfif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

manager = Blueprint('manager', __name__, template_folder='../templates')

def config():
    current_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    config = current_app.config['UPLOAD_FOLDER'] 
    return config

@manager.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return redirect(url_for('manager.productManager'))

@manager.route('/productManager', methods=['GET', 'POST'])
@login_required
def productManager():
    if request.method == 'GET':
        if(current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('index'))
        
    if 'delete' in request.values:
        pid = request.values.get('delete')
        data = Record.delete_check(pid)
        
        if(data != None):
            flash('failed')
        else:
            #data = Product.get_product(pid)
            Product.delete_product(pid)
    
    elif 'edit' in request.values:
        pid = request.values.get('edit')
        return redirect(url_for('manager.edit', pid=pid))
    
    car_data = car()
    return render_template('productManager.html', car_data = car_data, user=current_user.name)

def car():
    car_row = Product.get_all_product()
    car_data = []
    for i in car_row:
        car = {
            '車輛編號': i[0],
            '車輛品牌': i[1],
            '車輛型號': i[2],
            '出廠年份': i[3],
            '總里程': i[4],
            '車輛顏色': i[5],
            '價格': i[6],
        }
        car_data.append(car)
    return car_data

@manager.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        if (request.values.get('submit')=='true'):
            data = ""
            #pid = "0"
            while(data != None):
                number = str(random.randrange( 1000, 10000))
                en = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
                pid = en.upper() + '-' + number
                data = Product.get_product(pid)
            
            brand = request.values.get('brand')
            model = request.values.get('model')
            year = request.values.get('year')
            mileage = request.values.get('mileage')
            color = request.values.get('color')
            price = request.values.get('price')
            status = request.values.get('status')
            file = request.files.get('file')
            image_data = None

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_data = file.read()

            # 檢查是否正確獲取到所有欄位的數據
            if brand is None or price is None or model is None or year is None or mileage is None or color is None or status is None:
                flash('所有欄位都是必填的，請確認輸入內容。')
                return redirect(url_for('manager.productManager'))

            # 檢查欄位的長度
            if len(brand) < 1 or len(price) < 1:
                flash('商品名稱或價格不可為空。')
                return redirect(url_for('manager.productManager'))

            # if (len(pname) < 1 or len(price) < 1):
            #     return redirect(url_for('manager.productManager'))
            
            Product.add_product(
                {
                'pid' : pid,
                'brand' : brand,
                'model' : model,
                'year' : year,
                'mileage' : mileage,
                'color' : color,
                'price' : price,
                'status': status,
                'image': image_data
                }
            )
            return redirect(url_for('manager.productManager'))

    return render_template('productManager.html')

@manager.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'GET':
        if(current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('bookstore'))

    if request.method == 'POST':
        if(request.values.get('submit')=='true'):
            file = request.files.get('file')
            pid = request.values.get('pid')
            image_data = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 如果有上傳圖片，將其保存並轉換為二進制數據
                image_data = file.read()
            else:
                image_data = Product.get_image(pid)
            
            Product.update_product(
                {
                'brand' : request.values.get('brand'),
                'model' : request.values.get('model'),
                'year' : request.values.get('year'), 
                'mileage' : request.values.get('mileage'),
                'color' : request.values.get('color'),
                'price' : request.values.get('price'),
                'status' : request.values.get('status'),
                'pid' : pid,
                'image': image_data
                }
            )       
        
        return redirect(url_for('manager.productManager'))

    else:
        product = show_info()
        return render_template('edit.html', data=product)


def show_info():
    pid = request.args['pid']
    data = Product.get_product(pid)
    brand = data[1]
    model = data[2]
    year = data[3]
    mileage = data[4]
    color = data[5]
    price = data[6]
    status = data[7]
    image = data[8]

    product = {
        '車輛編號': pid,
        '車輛品牌': brand,
        '車輛型號': model,
        '出廠年份': year,
        '總里程': mileage,
        '車輛顏色': color,
        '價格': price,
        '車輛敘述': status
    }
    return product


@manager.route('/orderManager', methods=['GET', 'POST'])
@login_required
def orderManager():
    if request.method == 'POST':
        pass
    else:
        order_row = Order_List.get_order()
        order_data = []
        for i in order_row:
            order = {
                '訂單編號': i[0],
                '訂購人': i[1],
                '訂單總價': i[2],
                '訂單時間': i[3]
            }
            order_data.append(order)
            
        orderdetail_row = Order_List.get_orderdetail()
        order_detail = []

        for j in orderdetail_row:
            orderdetail = {
                '訂單編號': j[0],
                '車輛型號': j[1],
                '車輛價格': j[2],
                '租用時數': j[3],
                '租車時間': j[4],
                '還車時間': j[5]
            }
            order_detail.append(orderdetail)

    return render_template('orderManager.html', orderData = order_data, orderDetail = order_detail, user=current_user.name)