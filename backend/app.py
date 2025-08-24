#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级邮箱系统后端API服务
基于Flask的RESTful API，支持用户管理、邮件处理、AI功能等
"""

import os
import sys
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import redis
import psutil
import subprocess

# 添加AI服务路径
sys.path.append('/opt/bt-mailbox/ai-services')
from spam_detector import SpamDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mailbox/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'mysql+pymysql://mailbox_user:mailbox_pass@localhost/mailbox_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# 限流器
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Redis连接
try:
    redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis连接失败: {e}")
    redis_client = None

# 初始化AI服务
spam_detector = None
try:
    spam_detector = SpamDetector()
    logger.info("AI垃圾邮件检测服务初始化成功")
except Exception as e:
    logger.warning(f"AI服务初始化失败: {e}")

# 数据库模型
class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    quota = db.Column(db.Integer, default=1024)  # MB
    enabled = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'quota': self.quota,
            'enabled': self.enabled,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Domain(db.Model):
    """域名模型"""
    __tablename__ = 'domains'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MailLog(db.Model):
    """邮件日志模型"""
    __tablename__ = 'mail_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text)
    size = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='received')  # received, spam, blocked
    spam_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'size': self.size,
            'status': self.status,
            'spam_score': self.spam_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# API路由
@app.before_request
def before_request():
    """请求前处理"""
    g.start_time = datetime.now()

@app.after_request
def after_request(response):
    """请求后处理"""
    if hasattr(g, 'start_time'):
        duration = (datetime.now() - g.start_time).total_seconds()
        logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# 认证相关API
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': '邮箱或密码错误'}), 401
        
        if not user.enabled:
            return jsonify({'error': '账户已被禁用'}), 403
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 生成访问令牌
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({'error': '登录失败'}), 500

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """用户注册"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 验证域名
        domain = email.split('@')[-1]
        if not Domain.query.filter_by(domain=domain, enabled=True).first():
            return jsonify({'error': '不支持的邮箱域名'}), 400
        
        # 创建用户
        user = User(email=email, name=name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"新用户注册: {email}")
        
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500

# 用户管理API
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        if search:
            query = query.filter(
                db.or_(
                    User.email.contains(search),
                    User.name.contains(search)
                )
            )
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return jsonify({'error': '获取用户列表失败'}), 500

@app.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        quota = data.get('quota', 1024)
        enabled = data.get('enabled', True)
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建用户
        user = User(
            email=email,
            name=name,
            quota=quota,
            enabled=enabled
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"管理员创建用户: {email}")
        
        return jsonify({
            'message': '用户创建成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        db.session.rollback()
        return jsonify({'error': '创建用户失败'}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            user.name = data['name']
        if 'quota' in data:
            user.quota = data['quota']
        if 'enabled' in data:
            user.enabled = data['enabled']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': '用户更新成功',
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新用户失败: {e}")
        db.session.rollback()
        return jsonify({'error': '更新用户失败'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.id == current_user.id:
            return jsonify({'error': '不能删除自己'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"管理员删除用户: {user.email}")
        
        return jsonify({'message': '用户删除成功'})
        
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        db.session.rollback()
        return jsonify({'error': '删除用户失败'}), 500

# 系统统计API
@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """获取系统统计信息"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        # 基础统计
        total_users = User.query.count()
        active_users = User.query.filter_by(enabled=True).count()
        total_domains = Domain.query.count()
        
        # 今日邮件统计
        today = datetime.utcnow().date()
        today_mails = MailLog.query.filter(
            db.func.date(MailLog.created_at) == today
        ).count()
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 服务状态
        services = get_service_status()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'domains': {
                'total': total_domains
            },
            'mails': {
                'today': today_mails
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_total': memory.total,
                'disk_percent': (disk.used / disk.total) * 100,
                'disk_used': disk.used,
                'disk_total': disk.total
            },
            'services': services,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'error': '获取统计信息失败'}), 500

def get_service_status():
    """获取服务状态"""
    services = [
        {'name': 'postfix', 'display_name': 'Postfix (SMTP)'},
        {'name': 'dovecot', 'display_name': 'Dovecot (IMAP/POP3)'},
        {'name': 'redis-server', 'display_name': 'Redis'},
        {'name': 'mysql', 'display_name': 'MySQL'},
        {'name': 'nginx', 'display_name': 'Nginx'}
    ]
    
    for service in services:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service['name']],
                capture_output=True, text=True, timeout=5
            )
            service['status'] = 'running' if result.returncode == 0 else 'stopped'
        except Exception:
            service['status'] = 'unknown'
    
    return services

# AI功能API
@app.route('/api/ai/spam-check', methods=['POST'])
@jwt_required()
def check_spam():
    """检查垃圾邮件"""
    try:
        if not spam_detector:
            return jsonify({'error': 'AI服务不可用'}), 503
        
        data = request.get_json()
        email_data = {
            'subject': data.get('subject', ''),
            'body': data.get('body', ''),
            'from': data.get('from', '')
        }
        
        result = spam_detector.predict_spam(email_data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"垃圾邮件检测失败: {e}")
        return jsonify({'error': '检测失败'}), 500

@app.route('/api/ai/stats', methods=['GET'])
@jwt_required()
def get_ai_stats():
    """获取AI统计信息"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        if not spam_detector:
            return jsonify({'error': 'AI服务不可用'}), 503
        
        stats = spam_detector.get_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取AI统计失败: {e}")
        return jsonify({'error': '获取统计失败'}), 500

# 邮件日志API
@app.route('/api/mail-logs', methods=['GET'])
@jwt_required()
def get_mail_logs():
    """获取邮件日志"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        
        query = MailLog.query
        
        # 非管理员只能查看自己的邮件日志
        if not current_user.is_admin:
            query = query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(MailLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"获取邮件日志失败: {e}")
        return jsonify({'error': '获取邮件日志失败'}), 500

# 健康检查API
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db.session.execute('SELECT 1')
        
        # 检查Redis连接
        redis_status = 'ok'
        if redis_client:
            try:
                redis_client.ping()
            except:
                redis_status = 'error'
        else:
            redis_status = 'not_configured'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'ok',
            'redis': redis_status,
            'ai_service': 'ok' if spam_detector else 'not_available'
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# 初始化数据库
def init_db():
    """初始化数据库"""
    try:
        db.create_all()
        
        # 创建默认管理员
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='系统管理员',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # 创建默认域名
        domain = Domain.query.filter_by(domain='example.com').first()
        if not domain:
            domain = Domain(domain='example.com')
            db.session.add(domain)
        
        db.session.commit()
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        db.session.rollback()

if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        init_db()
    
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
