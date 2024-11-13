import imp
from flask import render_template, Blueprint, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import *

# api 所對應到的 html templates 資料夾
api = Blueprint('api', __name__, template_folder='./templates')

login_manager = LoginManager(api)
login_manager.login_view = 'api.login'
login_manager.login_message = "請先登入"

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(userid):  
    user = User()
    user.id = userid
    data = Member.get_role(userid)
    try:
        user.role = data[0]
        user.name = data[1]
    except:
        pass
    return user

@api.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        user_id = request.form['user_id']
        password = request.form['password']
        identity = request.form['identity']
        data = Member.get_member(user_id) 

        try:
            user_id = data[0][0]
            name = data[0][1]
            DB_password = data[0][2]
            DB_identity = data[0][3]

        except:
            flash('*沒有此帳號')
            return redirect(url_for('api.login'))

        if(DB_password == password):
            user = User()
            user.id = user_id
            login_user(user)

            if(DB_identity == identity):
                if(identity == 'user'):
                    return redirect(url_for('carstore.carstore'))
                else:
                    return redirect(url_for('manager.productManager'))
            else:
                flash('登入身分錯誤')

        else:
            flash('*密碼錯誤，請再試一次')
            return redirect(url_for('api.login'))

    
    return render_template('login.html')

@api.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        u_id = request.form['user_id']
        u_name = request.form['name']
        passwd = request.form['password']
        identity = request.form['identity']

        exist_uid = Member.get_all_uid()
        
        uid_list = []

        for i in exist_uid: # exist_uid 型態為tuple -> ((uid, ), ....)
            uid_list.append(i[0])

        # 檢查 uid 是否已經存在
        if(u_id in uid_list):
            flash('新增失敗，身份證字號已存在!')
            return redirect(url_for('api.register'))
        else:
            input = { 
                'user_id': u_id,
                'name': u_name, 
                'password': passwd,
                'identity': identity
            }
            Member.create_member(input)
            return redirect(url_for('api.login'))

    return render_template('register.html')

@api.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))