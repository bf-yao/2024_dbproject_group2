import re
from typing_extensions import Self
from flask import Flask, request, template_rendered, Blueprint
from flask import url_for, redirect, flash
from flask import render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, product
import random, string
from sqlalchemy import null
from link import *
import math
from base64 import b64encode
from api.sql import Member, Order_List, Product, Record, Cart
from datetime import datetime

store = Blueprint('carstore', __name__, template_folder='../templates')

@store.route('/', methods=['GET', 'POST'])
@login_required
def carstore():
    result = Product.count()
    count = math.ceil(result[0]/9)
    flag = 0
    
    if request.method == 'GET':
        if(current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager.home'))

    if 'keyword' in request.args and 'page' in request.args:
        total = 0
        single = 1
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        search = request.values.get('keyword')
        keyword = search
        
        cursor.execute('SELECT * FROM PRODUCT WHERE model LIKE %s', ('%' + search + '%',))
        car_row = cursor.fetchall()
        car_data = []
        final_data = []
        
        for i in car_row:
            car = {
                '車輛編號': i[0],
                '車輛品牌': i[1],
                '車輛型號': i[2]
            }
            car_data.append(car)
            total = total + 1
        
        if(len(car_data) < end):
            end = len(car_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(car_data[j])
            
        count = math.ceil(total/9)
        
        return render_template('carstore.html', single=single, keyword=search, car_data=car_data, user=current_user.name, page=1, flag=flag, count=count)    

    #這裡是送進product.html
    elif 'pid' in request.args:
        pid = request.args['pid']
        data = Product.get_product(pid)
        
        brand = data[1]
        model = data[2]
        year = data[3]
        mileage = data[4]
        color = data[5]
        price = data[6]
        status = data[7]
        image = data[8]+'.png' if data[8] else 'sdg.jpg'
        
        product = {
            '車輛編號': pid,
            '車輛品牌': brand,
            '車輛型號': model,
            '年分': year,
            '里程': mileage,
            '顏色': color,
            '租金': price,
            '車輛狀態': status,
            '商品圖片': image
        }

        return render_template('product.html', data = product, user=current_user.name)
    
    elif 'page' in request.args:
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        
        car_row = Product.get_all_product()
        car_data = []
        final_data = []
        
        for i in car_row:
            car = {
                '車輛編號': i[0],
                '車輛品牌': i[1],
                '車輛型號': i[2]
            }
            car_data.append(car)
            
        if(len(car_data) < end):
            end = len(car_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(car_data[j])
        
        return render_template('carstore.html', car_data=final_data, user=current_user.name, page=page, flag=flag, count=count)    
    
    elif 'keyword' in request.args:
        single = 1
        search = request.values.get('keyword')
        keyword = search
        cursor.execute('SELECT * FROM PRODUCT WHERE model LIKE %s', ('%' + search + '%',))
        car_row = cursor.fetchall()
        car_data = []
        total = 0
        
        for i in car_row:
            car = {
                '車輛編號': i[0],
                '車輛品牌': i[1],
                '車輛型號': i[2]
            }

            car_data.append(car)
            total = total + 1
            
        if(len(car_data) < 9):
            flag = 1
        
        count = math.ceil(total/9)    
        
        return render_template('carstore.html', keyword=search, single=single, car_data=car_data, user=current_user.name, page=1, flag=flag, count=count)    
    
    else:
        car_row = Product.get_all_product()
        car_data = []
        temp = 0
        for i in car_row:
            car = {
                '車輛編號': i[0],
                '車輛品牌': i[1],
                '車輛型號': i[2],
            }
            if len(car_data) < 9:
                car_data.append(car)
        
        return render_template('carstore.html', car_data=car_data, user=current_user.name, page=1, flag=flag, count=count)

# 會員購物車
@store.route('/cart', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def cart():
    # 以防管理者誤闖
    if request.method == 'GET':
        if (current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager.home'))

    # 回傳有 pid 代表要加商品
    if request.method == 'POST':
        if "pid" in request.form:
            data = Cart.get_cart(current_user.id)

            if data is None:  # 假如購物車裡面沒有他的資料
                time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                Cart.add_cart(current_user.id, time)  # 幫他加一台購物車
                data = Cart.get_cart(current_user.id)

            tno = data[1]  # 取得交易編號
            pid = request.form.get('pid')  # 使用者想要購買的東西，使用 `request.form.get()` 來避免 KeyError
            if not pid:
                flash('Product ID is missing.')
                return redirect(url_for('carstore.cart'))  # 返回購物車頁面並顯示錯誤信息

            # 檢查購物車裡面有沒有商品
            product = Record.check_product(tno)
            # 取得商品價錢
            price = Product.get_product(pid)[6]

            # 如果購物車裡面沒有的話，把它加一個進去
            if product is None:
                start_date = request.form.get(f"{pid}_start") # 從form裡面拿取車時間
                end_date = request.form.get(f"{pid}_end") # 從form裡面拿還車時間
                Record.add_product({'pid': pid, 'tno': tno, 'saleprice': price, 'total': price, 'startdate':start_date, 'enddate':end_date})
            else:
                # 若購物車內已經有商品
                # existing_order = Record.get_record(tno)  
                # existing_pid = existing_order[0][1] # pid(已存在車輛編號)
                start_date = request.form.get(f"{pid}_start")
                end_date = request.form.get(f"{pid}_end")
                Record.delete_product(tno)
                Record.add_product({'pid': pid, 'tno': tno, 'saleprice': price, 'total': price, 'startdate':start_date, 'enddate':end_date})
                # Record.update_product({'pid': pid, 'tno': tno, 'amount': 0, 'total': price, 'startdate': start_date, 'enddate': end_date})
                print("已覆蓋原有訂單。")

        elif "delete" in request.form:
            pid = request.form.get('delete')
            tno = Cart.get_cart(current_user.id)[1]
            Member.delete_product(tno, pid)
            product_data = only_cart()
        #點擊繼續選車
        elif "user_edit" in request.form:
            tno = Cart.get_cart(current_user.id)[1]
            pid = Cart.get_pid(str(tno))
            start_date = request.form.get(f"{pid}_start") # 從form裡面拿取車時間
            end_date = request.form.get(f"{pid}_end") # 從form裡面拿還車時間
            if start_date and end_date: 
                change_order()
            else:
                pass
            return redirect(url_for('carstore.carstore'))
        #點擊下一步(到確認駕駛資訊)
        elif "buy" in request.form:
            tno = Cart.get_cart(current_user.id)[1]
            pid = Cart.get_pid(str(tno))
            start_date = request.form.get(f"{pid[0]}_start") # 從form裡面拿取車時間
            end_date = request.form.get(f"{pid[0]}_end") # 從form裡面拿還車時間

            if start_date and end_date: 
                change_order()
            else:
                flash("請選擇時間")
                return redirect(url_for('carstore.cart'))   
            return redirect(url_for('carstore.license'))    
        
        elif "undo" in request.form:
            return redirect(url_for('carstore.license'))  

        elif "order" in request.form:
            tno = Cart.get_cart(current_user.id)[1]
            total = Record.get_total_money(tno)
            Cart.clear_cart(current_user.id)

            time = str(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
            format = 'yyyy/mm/dd hh24:mi:ss'
            Order_List.add_order({'mid': current_user.id, 'ordertime': time, 'total': total, 'format': format, 'tno': tno})

            return render_template('complete.html', user=current_user.name)

    product_data = only_cart()
    if product_data == 0:
        return render_template('empty.html', user=current_user.name)
    else:
        return render_template('cart.html', data=product_data, user=current_user.name)

#點擊直接結帳後將購物車內商品送入order頁面
@store.route('/order')
def order():    
    data = Cart.get_cart(current_user.id)
    tno = data[1]

    product_row = Record.get_record(tno)
    product_data = []

    for i in product_row:
        model = Product.get_name(i[1])
        product = {
            '車輛編號': i[1],
            '車輛型號': model,
            '租金': i[3],
            '時數': i[6]
        }
        product_data.append(product)
    
    total = float(Record.get_total(tno))  # 將 Decimal 轉換為 float


    return render_template('order.html', data=product_data, total=total, user=current_user.name)

@store.route('/orderlist')
def orderlist():
    if "oid" in request.args :
        pass
    
    user_id = current_user.id

    data = Member.get_order(user_id)
    orderlist = []

    for i in data:
        temp = {
            '訂單編號': i[0],
            '訂單總價': i[3],
            '訂單時間': i[2]
        }
        orderlist.append(temp)
    
    orderdetail_row = Order_List.get_orderdetail()
    orderdetail = []

    for j in orderdetail_row:
        temp = {
            '訂單編號': j[0],
            '車輛型態': j[1],
            '租金': j[2],
            '天數': j[3]
        }
        orderdetail.append(temp)


    return render_template('orderlist.html', data=orderlist, detail=orderdetail, user=current_user.name)

def change_order():
    data = Cart.get_cart(current_user.id)
    tno = data[1] # 使用者有購物車了，購物車的交易編號是什麼
    product_row = Record.get_record(data[1])


    for i in product_row:
        # i[0]：交易編號 / i[1]：商品編號 / i[2]：每日租金 / i[3]：總價 / i[4]/i[5]:取車/還車時間 / i[6]:天數 
        # if int(request.form[i[1]]) != i[2]:

        # 將字符串轉換為 datetime 對象
        startdate = datetime.fromisoformat(request.form.get(f"{i[1]}_start")).strftime('%Y-%m-%dT%H:%M')
        enddate = datetime.fromisoformat(request.form.get(f"{i[1]}_end")).strftime('%Y-%m-%dT%H:%M')
        time_difference = datetime.strptime(enddate, '%Y-%m-%dT%H:%M')-datetime.strptime(startdate, '%Y-%m-%dT%H:%M') # 計算時間差異
        
        # 總小時數
        hours = time_difference.days*24 + time_difference.seconds // 3600
      
        Record.update_product({
            'startdate':startdate,
            'enddate':enddate,
            'amount':hours,
            'pid':i[1],
            'tno':tno,
            'total':hours*int(i[2]) # 租的時數*每小時租金
        })
        print('change')

    return 0

#用來將該會員購物車內的商品(record)送入購物車頁面
def only_cart():
    count = Cart.check(current_user.id)

    if count is None:
        return 0

    data = Cart.get_cart(current_user.id)
    tno = data[1]
    product_row = Record.get_record(tno)
    product_data = []

    for i in product_row:
        pid = i[1]
        model = Product.get_name(i[1])
        price = i[2]
        amount = i[6]
        startdate = i[4]
        enddate = i[5]

        product = {
            '車輛編號': pid,
            '車輛型號': model,
            '租金': price,
            '天數': amount,
            '取車時間':startdate,
            '還車時間':enddate
        }
        product_data.append(product)

    return product_data

# 確認駕駛資訊
@store.route('/license', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def license():
    data = Member.get_member(current_user.id)

    # 檢查資料是否存在並取出欄位，沒有資料則設為空字串
    user_data = {
        'user_id': data[0][0] if data[0][0] else '',
        'user_name': data[0][1] if data[0][1] else '',
        'password': data[0][2] if data[0][2] else '',
        'identity': data[0][3] if data[0][3] else '',
        'license_number': data[0][4] if data[0][4] else '',
        'phone_number': data[0][5] if data[0][5] else '',
        'address': data[0][6] if data[0][6] else ''
    }
    # 點擊去付款
    if "pay" in request.form:
        if request.method == 'POST':  # 如果是 POST 請求
            input_data = {
                'user_id' : data[0][0],
                'user_name' : data[0][1],
                'license_number' : request.values.get('license_number'),
                'phone_number' : request.values.get('phone_number'),
                'address' : request.values.get('address')
            }

            # 檢查 "駕照號碼" 是否已經存在
            exist_lid = Member.get_all_lid()
            find_lid = Member.find_lid(current_user.id) # 找到自己的lid

            lid_list = []
            for i in exist_lid: 
                if i[0] != find_lid[0]: 
                    lid_list.append(i[0])

            if (input_data['license_number'] in lid_list): 
                flash("輸入駕照號碼有重複")
                return redirect(url_for('carstore.license')) 

            else:
                # 判斷字典中的每個值是否都不為空
                if all(value for value in input_data.values()):
                    # 如果所有值都不為空，將會員駕照資料存入資料庫
                    try: 
                        Member.update_member(input_data)
                    except Exception as e:
                        print(e)
                else:
                    # 如果有任何值為空，執行錯誤處理或顯示提示
                    flash("資料有缺失，請補充所有欄位。")
                    return redirect(url_for('carstore.license'))

        return redirect(url_for('carstore.order'))
    
    elif "undo" in request.form:
        return redirect(url_for('carstore.cart'))

    return render_template('license.html', user=current_user.name, **user_data)

# 修改會員資訊
@store.route('/userinfo', methods=['GET', 'POST'])
def userinfo():
    data = Member.get_member(current_user.id)
    
    # 檢查資料是否存在並取出欄位，沒有資料則設為空字串
    user_data = {
        'user_id': data[0][0] if data[0][0] else '',
        'user_name': data[0][1] if data[0][1] else '',
        'password': data[0][2] if data[0][2] else '',
        'identity': data[0][3] if data[0][3] else '',
        'license_number': data[0][4] if data[0][4] else '',
        'phone_number': data[0][5] if data[0][5] else '',
        'address': data[0][6] if data[0][6] else ''
    }

    if request.method == 'POST':  # 如果是 POST 請求
        input_data = {
            'user_id' : request.values.get('user_id'),
            'user_name' : request.values.get('user_name'),
            'license_number' : request.values.get('license_number'),
            'phone_number' : request.values.get('phone_number'),
            'address' : request.values.get('address')
        }

        # 檢查 uid 是否已經存在
        exist_uid = Member.get_all_uid()
        uid_list = []
        for i in exist_uid: 
            if i[0] != current_user.id: # 找到自己以外的uid
                uid_list.append(i[0])

        if (input_data['user_id'] in uid_list): 
            flash("輸入身分證字號有重複")
            return redirect(url_for('carstore.userinfo')) 
        
        # uid 不存在目前資料庫則可修改 uid
        else: 
            try: # 將新的資料存入資料庫
                Member.update_member(input_data)
                flash("會員資料修改成功")
            except Exception as e:
                print(e)
                flash("修改失敗，請重試")
            return redirect(url_for('carstore.userinfo')) 

    return render_template('userinfo.html', **user_data, user=current_user.name )