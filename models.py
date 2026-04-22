from app import db
from datetime import datetime
from cryptography.fernet import Fernet
import os

# Encryption key for sensitive data
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-key-change-in-production').encode()
cipher = Fernet(ENCRYPTION_KEY)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    credentials = db.relationship('Credentials', backref='user', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='user', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Credentials(db.Model):
    __tablename__ = 'credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    wix_api_key = db.Column(db.Text, nullable=False)  # Encrypted
    wix_account_id = db.Column(db.String(255), nullable=False)
    cloudflare_proxy_url = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def encrypt_api_key(self, api_key):
        self.wix_api_key = cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self):
        return cipher.decrypt(self.wix_api_key.encode()).decode()
    
    def __repr__(self):
        return f'<Credentials user_id={self.user_id}>'

class Site(db.Model):
    __tablename__ = 'sites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    site_name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    wix_site_id = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    blog_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='site', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='site', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Site {self.site_name}>'

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    meta_description = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default='draft')  # draft, published, failed
    wix_post_id = db.Column(db.String(255), nullable=True)
    wix_post_url = db.Column(db.String(500), nullable=True)
    
    topic = db.Column(db.String(100), nullable=True)
    tone = db.Column(db.String(50), nullable=True)
    length = db.Column(db.String(20), nullable=True)
    
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    
    frequency = db.Column(db.String(20), default='weekly')  # weekly, bi-weekly, monthly
    day_of_week = db.Column(db.Integer, default=0)  # 0=Monday, 6=Sunday
    hour_of_day = db.Column(db.Integer, default=9)  # 9am
    
    enabled = db.Column(db.Boolean, default=False)
    next_run = db.Column(db.DateTime, nullable=True)
    last_run = db.Column(db.DateTime, nullable=True)
    
    topic = db.Column(db.String(100), default='disassembly')
    tone = db.Column(db.String(50), default='helpful')
    length = db.Column(db.String(20), default='medium')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Schedule site_id={self.site_id}>'

class ApiLog(db.Model):
    __tablename__ = 'api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiLog {self.endpoint} {self.status_code}>'
