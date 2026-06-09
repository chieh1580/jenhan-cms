import os
import io
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, abort
)
from PIL import Image as PILImage
from models import db, Image, Project, Work, News

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jenhan-dev-key-change-me')

# Database
database_url = os.environ.get('DATABASE_URL', 'sqlite:///jenhan.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

db.init_app(app)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'jenhan2026')


# ─── Auth ───
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Image helper ───
def save_uploaded_image(file):
    """壓縮並存入資料庫，回傳 Image 物件"""
    if not file or file.filename == '':
        return None
    img = PILImage.open(file.stream)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    # 限制最大寬度 1600px
    max_w = 1600
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85, optimize=True)
    buf.seek(0)
    image = Image(
        filename=file.filename,
        data=buf.read(),
        mimetype='image/jpeg'
    )
    db.session.add(image)
    db.session.flush()
    return image


# ─── Serve uploaded images ───
@app.route('/uploads/<int:image_id>')
def serve_image(image_id):
    img = db.session.get(Image, image_id)
    if not img:
        abort(404)
    return send_file(io.BytesIO(img.data), mimetype=img.mimetype)


# ─── Public Routes ───
@app.route('/')
def index():
    projects = Project.query.filter_by(visible=True).order_by(Project.sort_order).all()
    works = Work.query.filter_by(visible=True).order_by(Work.sort_order).all()
    news_list = News.query.filter_by(published=True).order_by(News.sort_order).limit(3).all()
    return render_template('public/index.html',
                           projects=projects, works=works, news_list=news_list)


# ─── Admin: Login ───
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('密碼錯誤', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ─── Admin: Dashboard ───
@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html',
                           project_count=Project.query.count(),
                           work_count=Work.query.count(),
                           news_count=News.query.count())


# ─── Admin: 在售建案 CRUD ───
@app.route('/admin/projects')
@login_required
def admin_projects():
    items = Project.query.order_by(Project.sort_order).all()
    return render_template('admin/projects.html', items=items)


@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        image = save_uploaded_image(request.files.get('image'))
        item = Project(
            name=request.form['name'],
            location=request.form.get('location', ''),
            product_type=request.form.get('product_type', '住宅建案'),
            status=request.form.get('status', '銷售中'),
            description=request.form.get('description', ''),
            link=request.form.get('link', ''),
            image_id=image.id if image else None,
            sort_order=int(request.form.get('sort_order', 0)),
            visible='visible' in request.form,
        )
        db.session.add(item)
        db.session.commit()
        flash('在售建案已新增', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/item_form.html',
                           title='新增在售建案', item=None, item_type='project')


@app.route('/admin/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(id):
    item = db.session.get(Project, id) or abort(404)
    if request.method == 'POST':
        item.name = request.form['name']
        item.location = request.form.get('location', '')
        item.product_type = request.form.get('product_type', '住宅建案')
        item.status = request.form.get('status', '銷售中')
        item.description = request.form.get('description', '')
        item.link = request.form.get('link', '')
        item.sort_order = int(request.form.get('sort_order', 0))
        item.visible = 'visible' in request.form
        new_image = save_uploaded_image(request.files.get('image'))
        if new_image:
            item.image_id = new_image.id
        db.session.commit()
        flash('在售建案已更新', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/item_form.html',
                           title='編輯在售建案', item=item, item_type='project')


@app.route('/admin/projects/<int:id>/delete', methods=['POST'])
@login_required
def admin_project_delete(id):
    item = db.session.get(Project, id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('admin_projects'))


# ─── Admin: 歷屆建案 CRUD ───
@app.route('/admin/works')
@login_required
def admin_works():
    items = Work.query.order_by(Work.sort_order).all()
    return render_template('admin/works.html', items=items)


@app.route('/admin/works/new', methods=['GET', 'POST'])
@login_required
def admin_work_new():
    if request.method == 'POST':
        image = save_uploaded_image(request.files.get('image'))
        item = Work(
            name=request.form['name'],
            location=request.form.get('location', ''),
            product_type=request.form.get('product_type', '住宅建案'),
            status=request.form.get('status', '完銷'),
            service_content=request.form.get('service_content', '建案企劃｜銷售整合｜案場銷售'),
            description=request.form.get('description', ''),
            link=request.form.get('link', ''),
            image_id=image.id if image else None,
            sort_order=int(request.form.get('sort_order', 0)),
            visible='visible' in request.form,
        )
        db.session.add(item)
        db.session.commit()
        flash('歷屆建案已新增', 'success')
        return redirect(url_for('admin_works'))
    return render_template('admin/item_form.html',
                           title='新增歷屆建案', item=None, item_type='work')


@app.route('/admin/works/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_work_edit(id):
    item = db.session.get(Work, id) or abort(404)
    if request.method == 'POST':
        item.name = request.form['name']
        item.location = request.form.get('location', '')
        item.product_type = request.form.get('product_type', '住宅建案')
        item.status = request.form.get('status', '完銷')
        item.service_content = request.form.get('service_content', '建案企劃｜銷售整合｜案場銷售')
        item.description = request.form.get('description', '')
        item.link = request.form.get('link', '')
        item.sort_order = int(request.form.get('sort_order', 0))
        item.visible = 'visible' in request.form
        new_image = save_uploaded_image(request.files.get('image'))
        if new_image:
            item.image_id = new_image.id
        db.session.commit()
        flash('歷屆建案已更新', 'success')
        return redirect(url_for('admin_works'))
    return render_template('admin/item_form.html',
                           title='編輯歷屆建案', item=item, item_type='work')


@app.route('/admin/works/<int:id>/delete', methods=['POST'])
@login_required
def admin_work_delete(id):
    item = db.session.get(Work, id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('admin_works'))


# ─── Admin: 最新消息 CRUD ───
@app.route('/admin/news')
@login_required
def admin_news():
    items = News.query.order_by(News.sort_order).all()
    return render_template('admin/news.html', items=items)


@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
def admin_news_new():
    if request.method == 'POST':
        image = save_uploaded_image(request.files.get('image'))
        item = News(
            category=request.form.get('category', ''),
            title=request.form['title'],
            summary=request.form.get('summary', ''),
            content=request.form.get('content', ''),
            link=request.form.get('link', ''),
            image_id=image.id if image else None,
            published='published' in request.form,
            sort_order=int(request.form.get('sort_order', 0)),
        )
        db.session.add(item)
        db.session.commit()
        flash('最新消息已新增', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/news_form.html',
                           title='新增最新消息', item=None)


@app.route('/admin/news/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_news_edit(id):
    item = db.session.get(News, id) or abort(404)
    if request.method == 'POST':
        item.category = request.form.get('category', '')
        item.title = request.form['title']
        item.summary = request.form.get('summary', '')
        item.content = request.form.get('content', '')
        item.link = request.form.get('link', '')
        item.published = 'published' in request.form
        item.sort_order = int(request.form.get('sort_order', 0))
        new_image = save_uploaded_image(request.files.get('image'))
        if new_image:
            item.image_id = new_image.id
        db.session.commit()
        flash('最新消息已更新', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/news_form.html',
                           title='編輯最新消息', item=item)


@app.route('/admin/news/<int:id>/delete', methods=['POST'])
@login_required
def admin_news_delete(id):
    item = db.session.get(News, id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('admin_news'))


# ─── Init DB & Seed ───
def seed_data():
    """首次啟動時匯入現有建案資料"""
    if Project.query.first():
        return  # 已有資料，跳過

    # 在售建案
    projects = [
        Project(name='勤源青崧居', location='龍潭區', product_type='住宅建案',
                status='銷售中', sort_order=1, visible=True),
        Project(name='富鏵巨蛋捷境', location='中壢區', product_type='住宅建案',
                status='銷售中', sort_order=2, visible=True),
    ]
    for p in projects:
        db.session.add(p)

    # 歷屆建案
    works_data = [
        ('我居9', '八德區・龍岡重劃區', '住宅建案', '完銷', 1),
        ('我居8', '大溪區・埔頂重劃區', '住宅建案', '完銷', 2),
        ('我居5', '大溪區・埔頂重劃區', '5戶住宅', '完銷', 3),
        ('涵露6', '楊梅區・富岡重劃區', '9戶住宅', '完銷', 4),
        ('涵露5', '楊梅區・楊梅重劃區', '23戶住宅', '完銷', 5),
        ('我居2', '大溪區・埔頂重劃區', '6戶住宅', '完銷', 6),
    ]
    for name, loc, ptype, status, order in works_data:
        db.session.add(Work(
            name=name, location=loc, product_type=ptype,
            status=status, service_content='建案企劃｜銷售整合｜案場銷售',
            sort_order=order, visible=True
        ))

    # 最新消息
    news_data = [
        ('合建知識', '地主第一次了解合建，應該先準備哪些資料？',
         '整理土地位置、地號、現況照片與基本需求，有助於初步判斷土地條件與合建方向。', 1),
        ('建案銷售', '建案代銷不只是銷售，更是產品價值的整理與溝通',
         '從產品定位、銷售說法到案場接待，讓建案特色更容易被購屋者理解。', 2),
        ('桃園房市觀察', '桃園重劃區、實價登錄與推案資訊該如何一起看？',
         '透過重劃區發展、成交資料與推案資訊，整理房地產決策可參考的觀察方向。', 3),
    ]
    for cat, title, summary, order in news_data:
        db.session.add(News(
            category=cat, title=title, summary=summary,
            published=True, sort_order=order
        ))

    db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
