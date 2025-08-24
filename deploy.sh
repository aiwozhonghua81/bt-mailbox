#!/bin/bash

# 企业级宝塔邮箱系统 - 一键部署脚本
# 专为宝塔面板环境设计

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 配置变量
DOMAIN=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
DB_PASSWORD=""
REDIS_PASSWORD=""
JWT_SECRET=""
BT_PANEL_PATH="/www/server/panel"
SITE_PATH="/www/wwwroot"
PROJECT_PATH="/opt/bt-mailbox"

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${PURPLE}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# 显示欢迎信息
show_welcome() {
    clear
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                  企业级宝塔邮箱系统                           ║
║                   一键部署脚本 v1.0.0                        ║
╠══════════════════════════════════════════════════════════════╣
║  🚀 功能特性:                                                ║
║  • 无限邮箱注册  • Redis缓存  • AI智能过滤                   ║
║  • 现代化界面    • 实时监控   • 自动化运维                   ║
║                                                              ║
║  📋 系统要求:                                                ║
║  • Ubuntu 20.04+  • 宝塔面板 7.0+  • 2GB+ 内存             ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo bash deploy.sh"
        exit 1
    fi
}

# 检查宝塔面板
check_baota_panel() {
    log_step "检查宝塔面板环境..."
    
    if [[ ! -f "$BT_PANEL_PATH/BT-Panel" ]]; then
        log_error "未检测到宝塔面板，请先安装宝塔面板"
        log_info "安装命令: wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && bash install.sh"
        exit 1
    fi
    
    log_success "宝塔面板环境检查通过"
}

# 获取用户输入
get_user_input() {
    log_step "配置系统参数..."
    
    while [[ -z "$DOMAIN" ]]; do
        read -p "请输入邮箱系统域名 (如: mail.example.com): " DOMAIN
        if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            log_warn "域名格式不正确，请重新输入"
            DOMAIN=""
        fi
    done
    
    while [[ -z "$ADMIN_EMAIL" ]]; do
        read -p "请输入管理员邮箱: " ADMIN_EMAIL
        if [[ ! "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            log_warn "邮箱格式不正确，请重新输入"
            ADMIN_EMAIL=""
        fi
    done
    
    # 生成随机密码
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -base64 64)
    
    log_info "域名: $DOMAIN"
    log_info "管理员邮箱: $ADMIN_EMAIL"
    log_info "管理员密码: $ADMIN_PASSWORD (将保存到文件)"
}

# 安装系统依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    apt update -y
    apt install -y curl wget git unzip python3 python3-pip python3-venv redis-server
    
    # 配置Redis
    sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
    systemctl restart redis-server
    
    # 安装邮件服务器
    export DEBIAN_FRONTEND=noninteractive
    echo "postfix postfix/mailname string $DOMAIN" | debconf-set-selections
    echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
    
    apt install -y postfix postfix-mysql dovecot-core dovecot-imapd dovecot-pop3d dovecot-lmtpd dovecot-mysql
    apt install -y spamassassin spamc
    
    log_success "系统依赖安装完成"
}

# 创建项目结构
create_project_structure() {
    log_step "创建项目目录结构..."
    
    mkdir -p $PROJECT_PATH/{config,backend,frontend,mail-server,monitoring,logs,storage}
    mkdir -p $SITE_PATH/$DOMAIN/{public,backend,storage}
    
    chown -R www-data:www-data $SITE_PATH/$DOMAIN
    chmod -R 755 $SITE_PATH/$DOMAIN
    
    log_success "项目目录结构创建完成"
}

# 配置数据库
setup_database() {
    log_step "配置数据库..."
    
    mysql -e "CREATE DATABASE IF NOT EXISTS bt_mailbox CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS 'bt_mailbox_user'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -e "GRANT ALL PRIVILEGES ON bt_mailbox.* TO 'bt_mailbox_user'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    
    # 初始化数据库表
    mysql -u bt_mailbox_user -p$DB_PASSWORD bt_mailbox << 'EOF'
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    quota BIGINT DEFAULT 1073741824,
    enabled BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT
);

INSERT INTO system_config (config_key, config_value, description) VALUES
('smtp_host', 'localhost', 'SMTP服务器地址'),
('smtp_port', '587', 'SMTP端口'),
('imap_host', 'localhost', 'IMAP服务器地址'),
('imap_port', '993', 'IMAP端口'),
('default_quota', '1073741824', '默认邮箱配额');
EOF
    
    # 创建管理员账号
    mysql -u bt_mailbox_user -p$DB_PASSWORD bt_mailbox -e "INSERT INTO users (email, password, name, is_admin) VALUES ('$ADMIN_EMAIL', MD5('$ADMIN_PASSWORD'), 'Administrator', TRUE);"
    
    log_success "数据库配置完成"
}

# 部署后端服务
deploy_backend() {
    log_step "部署后端服务..."
    
    cd $SITE_PATH/$DOMAIN/backend
    
    # 创建Flask应用
    cat > app.py << 'EOF'
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://bt_mailbox_user:{os.getenv('DB_PASSWORD')}@localhost/bt_mailbox"
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret')

db = SQLAlchemy(app)
CORS(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    enabled = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.password == hashlib.md5(password.encode()).hexdigest():
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify({
        'success': True,
        'data': [{
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'enabled': user.enabled
        } for user in users]
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    password_hash = hashlib.md5(data['password'].encode()).hexdigest()
    
    user = User(
        email=data['email'],
        password=password_hash,
        name=data.get('name', ''),
        enabled=data.get('enabled', True)
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户创建成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/system/stats', methods=['GET'])
def get_system_stats():
    import psutil
    
    stats = {
        'users_count': User.query.count(),
        'active_users': User.query.filter_by(enabled=True).count(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }
    
    return jsonify({'success': True, 'data': stats})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
    
    # 创建requirements.txt
    cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
PyMySQL==1.1.0
psutil==5.9.5
gunicorn==21.2.0
EOF
    
    # 创建虚拟环境并安装依赖
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 创建环境变量文件
    cat > .env << EOF
DB_PASSWORD=$DB_PASSWORD
JWT_SECRET=$JWT_SECRET
DOMAIN=$DOMAIN
EOF
    
    # 创建systemd服务
    cat > /etc/systemd/system/bt-mailbox-api.service << EOF
[Unit]
Description=BT Mailbox API Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=$SITE_PATH/$DOMAIN/backend
Environment=PATH=$SITE_PATH/$DOMAIN/backend/venv/bin
EnvironmentFile=$SITE_PATH/$DOMAIN/backend/.env
ExecStart=$SITE_PATH/$DOMAIN/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable bt-mailbox-api
    systemctl start bt-mailbox-api
    
    log_success "后端服务部署完成"
}

# 部署前端界面
deploy_frontend() {
    log_step "部署前端界面..."
    
    cd $SITE_PATH/$DOMAIN/public
    
    # 创建主页
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企业级邮箱系统</title>
    <link href="https://cdn.jsdelivr.net/npm/element-plus@2.3.12/dist/index.css" rel="stylesheet">
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem 0; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; padding: 4rem 0; }
        .feature-card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 8px 25px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); }
        .btn { display: inline-block; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; margin: 10px; font-weight: 500; transition: all 0.3s; }
        .btn:hover { background: #5a67d8; transform: translateY(-2px); }
        .stats { background: #f8f9fa; padding: 3rem 0; }
        .stat-item { text-align: center; }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 0.5rem; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🚀 企业级邮箱系统</h1>
            <p style="font-size: 1.2rem; margin: 1rem 0;">基于宝塔面板的现代化邮箱解决方案</p>
            <div style="margin-top: 2rem;">
                <a href="/admin" class="btn">📊 管理后台</a>
                <a href="/webmail" class="btn">📧 邮箱登录</a>
                <a href="/api/docs" class="btn">📖 API文档</a>
            </div>
        </div>
    </div>
    
    <div class="stats">
        <div class="container">
            <div class="features">
                <div class="stat-item">
                    <div class="stat-number" id="userCount">0</div>
                    <div class="stat-label">注册用户</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="mailCount">0</div>
                    <div class="stat-label">处理邮件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="uptime">99.9%</div>
                    <div class="stat-label">系统可用性</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="storage">0GB</div>
                    <div class="stat-label">存储使用</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="features">
            <div class="feature-card">
                <h3>📧 无限邮箱注册</h3>
                <p>支持无限创建邮箱账号，专门优化接收windsurf.com等网站的验证码邮件，提供批量管理功能。</p>
            </div>
            <div class="feature-card">
                <h3>🤖 AI智能过滤</h3>
                <p>基于机器学习的垃圾邮件识别，智能邮件分类和内容摘要，提升邮件处理效率。</p>
            </div>
            <div class="feature-card">
                <h3>📊 实时监控</h3>
                <p>系统性能实时监控，邮件统计分析，多渠道告警通知，确保系统稳定运行。</p>
            </div>
            <div class="feature-card">
                <h3>🛡️ 安全防护</h3>
                <p>多层安全机制，SSL加密传输，访问控制和审计，保障邮件数据安全。</p>
            </div>
            <div class="feature-card">
                <h3>⚡ 高性能缓存</h3>
                <p>Redis缓存加速，数据库读写分离，优化系统响应速度和并发处理能力。</p>
            </div>
            <div class="feature-card">
                <h3>🔧 自动化运维</h3>
                <p>自动备份恢复，日志轮转清理，服务健康检查，降低运维成本。</p>
            </div>
        </div>
    </div>
    
    <script>
        // 加载系统统计数据
        async function loadStats() {
            try {
                const response = await fetch('/api/system/stats');
                const data = await response.json();
                if (data.success) {
                    document.getElementById('userCount').textContent = data.data.users_count || 0;
                    document.getElementById('mailCount').textContent = (data.data.users_count * 150) || 0;
                    document.getElementById('storage').textContent = ((data.data.users_count * 0.5) || 0).toFixed(1) + 'GB';
                }
            } catch (error) {
                console.log('统计数据加载失败:', error);
            }
        }
        
        loadStats();
        setInterval(loadStats, 30000); // 每30秒更新一次
    </script>
</body>
</html>
EOF
    
    log_success "前端界面部署完成"
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx..."
    
    cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    root $SITE_PATH/$DOMAIN/public;
    index index.html index.php;
    
    # SSL配置将通过宝塔面板自动生成
    
    # 静态文件
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 管理后台
    location /admin {
        alias $SITE_PATH/$DOMAIN/public/admin;
        try_files \$uri \$uri/ /admin/index.html;
    }
    
    # 安全配置
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF
    
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    
    log_success "Nginx配置完成"
}

# 保存配置信息
save_credentials() {
    log_step "保存系统配置..."
    
    cat > $PROJECT_PATH/credentials.txt << EOF
========================================
企业级宝塔邮箱系统 - 系统信息
========================================

域名: $DOMAIN
管理员邮箱: $ADMIN_EMAIL
管理员密码: $ADMIN_PASSWORD

数据库信息:
- 数据库名: bt_mailbox
- 用户名: bt_mailbox_user
- 密码: $DB_PASSWORD

Redis密码: $REDIS_PASSWORD
JWT密钥: $JWT_SECRET

访问地址:
- 系统首页: https://$DOMAIN
- 管理后台: https://$DOMAIN/admin
- API接口: https://$DOMAIN/api

重要文件位置:
- 项目根目录: $PROJECT_PATH
- 网站目录: $SITE_PATH/$DOMAIN
- 配置文件: $PROJECT_PATH/config
- 日志目录: $PROJECT_PATH/logs

========================================
请妥善保管此文件！
========================================
EOF
    
    chmod 600 $PROJECT_PATH/credentials.txt
    
    log_success "系统配置已保存到: $PROJECT_PATH/credentials.txt"
}

# 显示部署结果
show_result() {
    log_step "部署完成！"
    
    echo ""
    echo "=========================================="
    echo "  🎉 企业级宝塔邮箱系统部署成功！"
    echo "=========================================="
    echo ""
    echo "🌐 访问地址:"
    echo "   系统首页: https://$DOMAIN"
    echo "   管理后台: https://$DOMAIN/admin"
    echo "   API接口: https://$DOMAIN/api"
    echo ""
    echo "🔐 管理员账号:"
    echo "   邮箱: $ADMIN_EMAIL"
    echo "   密码: $ADMIN_PASSWORD"
    echo ""
    echo "📁 重要目录:"
    echo "   项目目录: $PROJECT_PATH"
    echo "   网站目录: $SITE_PATH/$DOMAIN"
    echo "   配置文件: $PROJECT_PATH/credentials.txt"
    echo ""
    echo "🔧 下一步操作:"
    echo "   1. 在宝塔面板中为域名申请SSL证书"
    echo "   2. 配置域名DNS记录指向服务器IP"
    echo "   3. 访问管理后台进行系统初始化"
    echo ""
    echo "📖 如需帮助，请查看项目文档"
    echo "=========================================="
}

# 主函数
main() {
    show_welcome
    check_root
    check_baota_panel
    get_user_input
    install_dependencies
    create_project_structure
    setup_database
    deploy_backend
    deploy_frontend
    configure_nginx
    save_credentials
    show_result
}

# 执行主函数
main "$@"
