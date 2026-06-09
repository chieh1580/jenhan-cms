from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Image(db.Model):
    """上傳圖片，以 binary 存在資料庫（Railway 檔案系統不持久）"""
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    """在售建案"""
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), default='')
    product_type = db.Column(db.String(50), default='住宅建案')
    status = db.Column(db.String(20), default='銷售中')
    description = db.Column(db.Text, default='')
    link = db.Column(db.String(500), default='')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    image = db.relationship('Image', foreign_keys=[image_id])
    sort_order = db.Column(db.Integer, default=0)
    visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Work(db.Model):
    """歷屆建案"""
    __tablename__ = 'works'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), default='')
    product_type = db.Column(db.String(50), default='住宅建案')
    status = db.Column(db.String(20), default='完銷')
    service_content = db.Column(db.String(200), default='建案企劃｜銷售整合｜案場銷售')
    description = db.Column(db.Text, default='')
    link = db.Column(db.String(500), default='')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    image = db.relationship('Image', foreign_keys=[image_id])
    sort_order = db.Column(db.Integer, default=0)
    visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class News(db.Model):
    """最新消息"""
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), default='')
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, default='')
    content = db.Column(db.Text, default='')
    link = db.Column(db.String(500), default='')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    image = db.relationship('Image', foreign_keys=[image_id])
    published = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
