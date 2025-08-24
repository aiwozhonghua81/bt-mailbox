#!/bin/bash
# 企业级邮箱系统完整部署脚本
# 适用于Ubuntu + 宝塔面板环境
# 支持一键部署所有组件和服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 配置变量
PROJECT_ROOT="/opt/bt-mailbox"
DOMAIN=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
MYSQL_ROOT_PASSWORD=""
MYSQL_DB_PASSWORD=""
REDIS_PASSWORD=""
JWT_SECRET=""

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查宝塔面板
check_baota() {
    log_step "检查宝塔面板环境..."
    
    if ! command -v bt &> /dev/null; then
        log_error "未检测到宝塔面板，请先安装宝塔面板"
        exit 1
    fi
    
    # 检查宝塔面板服务状态
    if ! systemctl is-active --quiet bt; then
        log_error "宝塔面板服务未运行"
        exit 1
    fi
    
    log_info "宝塔面板环境检查通过"
}

# 获取用户输入
get_user_input() {
    log_step "配置系统参数..."
    
    # 域名配置
    while [[ -z "$DOMAIN" ]]; do
        read -p "请输入邮箱系统域名 (例: mail.example.com): " DOMAIN
        if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            log_warn "域名格式不正确，请重新输入"
            DOMAIN=""
        fi
    done
    
    # 管理员邮箱
    while [[ -z "$ADMIN_EMAIL" ]]; do
        read -p "请输入管理员邮箱 (例: admin@${DOMAIN}): " ADMIN_EMAIL
        if [[ ! "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            log_warn "邮箱格式不正确，请重新输入"
            ADMIN_EMAIL=""
        fi
    done
    
    # 管理员密码
    while [[ -z "$ADMIN_PASSWORD" ]]; do
        read -s -p "请输入管理员密码 (至少8位): " ADMIN_PASSWORD
        echo
        if [[ ${#ADMIN_PASSWORD} -lt 8 ]]; then
            log_warn "密码长度至少8位，请重新输入"
            ADMIN_PASSWORD=""
        fi
    done
    
    # 生成随机密码
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
    MYSQL_DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -base64 64)
    
    log_info "配置参数设置完成"
}

# 安装系统依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    # 更新包列表
    apt update
    
    # 安装基础依赖
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm
    
    # 安装邮件服务器组件
    apt install -y \
        postfix \
        postfix-mysql \
        dovecot-core \
        dovecot-imapd \
        dovecot-pop3d \
        dovecot-lmtpd \
        dovecot-mysql \
        spamassassin \
        clamav \
        clamav-daemon \
        amavisd-new
    
    log_info "系统依赖安装完成"
}

# 创建项目目录结构
create_directories() {
    log_step "创建项目目录结构..."
    
    mkdir -p ${PROJECT_ROOT}/{backend,frontend,ai-services,mail-server,monitoring,scripts,logs,config,ssl,backup}
    mkdir -p ${PROJECT_ROOT}/mail-server/{postfix,dovecot}
    mkdir -p ${PROJECT_ROOT}/monitoring/{prometheus,grafana}
    mkdir -p /var/mail/vhosts
    mkdir -p /var/log/mailbox
    
    # 创建邮件用户
    groupadd -g 5000 vmail || true
    useradd -g vmail -u 5000 vmail -d /var/mail || true
    chown -R vmail:vmail /var/mail/vhosts
    
    log_info "目录结构创建完成"
}

# 配置MySQL数据库
setup_mysql() {
    log_step "配置MySQL数据库..."
    
    # 通过宝塔面板API创建数据库
    bt_mysql_root_password=$(bt default | grep "MySQL root" | awk '{print $4}')
    
    # 创建邮箱数据库
    mysql -uroot -p${bt_mysql_root_password} <<EOF
CREATE DATABASE IF NOT EXISTS mailbox_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'mailbox_user'@'localhost' IDENTIFIED BY '${MYSQL_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON mailbox_db.* TO 'mailbox_user'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # 创建数据库表
    mysql -umailbox_user -p${MYSQL_DB_PASSWORD} mailbox_db <<EOF
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    quota INT DEFAULT 1024,
    enabled BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_enabled (enabled)
);

-- 域名表
CREATE TABLE IF NOT EXISTS domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_domain (domain),
    INDEX idx_enabled (enabled)
);

-- 邮件日志表
CREATE TABLE IF NOT EXISTS mail_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject TEXT,
    size INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'received',
    spam_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入默认数据
INSERT IGNORE INTO domains (domain) VALUES ('${DOMAIN}');
INSERT IGNORE INTO users (email, password_hash, name, is_admin) 
VALUES ('${ADMIN_EMAIL}', '\$2b\$12\$dummy_hash_will_be_updated', '系统管理员', TRUE);
EOF
    
    log_info "MySQL数据库配置完成"
}

# 配置Redis
setup_redis() {
    log_step "配置Redis..."
    
    # 安装Redis
    apt install -y redis-server
    
    # 配置Redis
    cat > /etc/redis/redis.conf <<EOF
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
requirepass ${REDIS_PASSWORD}
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF
    
    systemctl enable redis-server
    systemctl restart redis-server
    
    log_info "Redis配置完成"
}

# 配置Postfix
setup_postfix() {
    log_step "配置Postfix邮件服务器..."
    
    # 复制配置文件
    cp ${PROJECT_ROOT}/mail-server/postfix/main.cf /etc/postfix/main.cf
    
    # 替换配置中的变量
    sed -i "s/example.com/${DOMAIN}/g" /etc/postfix/main.cf
    sed -i "s/mail.example.com/mail.${DOMAIN}/g" /etc/postfix/main.cf
    
    # 创建MySQL配置文件
    cat > /etc/postfix/mysql-virtual-domains.cf <<EOF
user = mailbox_user
password = ${MYSQL_DB_PASSWORD}
hosts = localhost
dbname = mailbox_db
query = SELECT 1 FROM domains WHERE domain='%s' AND enabled=1
EOF
    
    cat > /etc/postfix/mysql-virtual-users.cf <<EOF
user = mailbox_user
password = ${MYSQL_DB_PASSWORD}
hosts = localhost
dbname = mailbox_db
query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') FROM users WHERE email='%s' AND enabled=1
EOF
    
    cat > /etc/postfix/mysql-virtual-aliases.cf <<EOF
user = mailbox_user
password = ${MYSQL_DB_PASSWORD}
hosts = localhost
dbname = mailbox_db
query = SELECT email FROM users WHERE email='%s' AND enabled=1
EOF
    
    # 设置权限
    chmod 640 /etc/postfix/mysql-*.cf
    chown root:postfix /etc/postfix/mysql-*.cf
    
    # 启动服务
    systemctl enable postfix
    systemctl restart postfix
    
    log_info "Postfix配置完成"
}

# 配置Dovecot
setup_dovecot() {
    log_step "配置Dovecot IMAP/POP3服务器..."
    
    # 复制配置文件
    cp ${PROJECT_ROOT}/mail-server/dovecot/dovecot.conf /etc/dovecot/dovecot.conf
    
    # 创建SQL配置文件
    cat > /etc/dovecot/dovecot-sql.conf.ext <<EOF
driver = mysql
connect = host=localhost dbname=mailbox_db user=mailbox_user password=${MYSQL_DB_PASSWORD}
default_pass_scheme = PBKDF2
password_query = SELECT email as user, password_hash as password FROM users WHERE email='%u' AND enabled=1
user_query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') as home, 5000 as uid, 5000 as gid FROM users WHERE email='%u' AND enabled=1
EOF
    
    # 设置权限
    chmod 600 /etc/dovecot/dovecot-sql.conf.ext
    chown vmail:dovecot /etc/dovecot/dovecot-sql.conf.ext
    
    # 生成DH参数
    openssl dhparam -out /etc/dovecot/dh.pem 2048
    
    # 启动服务
    systemctl enable dovecot
    systemctl restart dovecot
    
    log_info "Dovecot配置完成"
}

# 部署后端API服务
deploy_backend() {
    log_step "部署后端API服务..."
    
    # 创建Python虚拟环境
    cd ${PROJECT_ROOT}/backend
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装Python依赖
    pip install --upgrade pip
    pip install \
        flask \
        flask-sqlalchemy \
        flask-jwt-extended \
        flask-cors \
        flask-limiter \
        pymysql \
        redis \
        psutil \
        scikit-learn \
        pandas \
        numpy \
        nltk \
        jieba \
        werkzeug \
        gunicorn
    
    # 创建环境变量文件
    cat > ${PROJECT_ROOT}/backend/.env <<EOF
SECRET_KEY=${JWT_SECRET}
DATABASE_URL=mysql+pymysql://mailbox_user:${MYSQL_DB_PASSWORD}@localhost/mailbox_db
JWT_SECRET_KEY=${JWT_SECRET}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0
DOMAIN=${DOMAIN}
EOF
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/mailbox-backend.service <<EOF
[Unit]
Description=Mailbox Backend API Service
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=${PROJECT_ROOT}/backend
Environment=PATH=${PROJECT_ROOT}/backend/venv/bin
ExecStart=${PROJECT_ROOT}/backend/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # 启动服务
    systemctl daemon-reload
    systemctl enable mailbox-backend
    systemctl start mailbox-backend
    
    log_info "后端API服务部署完成"
}

# 部署前端界面
deploy_frontend() {
    log_step "部署前端管理界面..."
    
    cd ${PROJECT_ROOT}/frontend
    
    # 安装Node.js依赖
    npm install
    
    # 构建生产版本
    npm run build
    
    # 复制到Nginx目录
    rm -rf /www/wwwroot/${DOMAIN}/admin
    mkdir -p /www/wwwroot/${DOMAIN}/admin
    cp -r dist/* /www/wwwroot/${DOMAIN}/admin/
    
    log_info "前端界面部署完成"
}

# 配置SSL证书
setup_ssl() {
    log_step "配置SSL证书..."
    
    # 通过宝塔面板API申请SSL证书
    bt ssl -d ${DOMAIN} -auto
    
    # 如果自动申请失败，创建自签名证书
    if [[ ! -f /www/server/panel/vhost/cert/${DOMAIN}/fullchain.pem ]]; then
        log_warn "自动申请SSL证书失败，创建自签名证书"
        
        mkdir -p /etc/ssl/certs /etc/ssl/private
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/ssl/private/mailserver.key \
            -out /etc/ssl/certs/mailserver.crt \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=${DOMAIN}"
        
        chmod 600 /etc/ssl/private/mailserver.key
        chmod 644 /etc/ssl/certs/mailserver.crt
    else
        # 复制宝塔证书到邮件服务器
        cp /www/server/panel/vhost/cert/${DOMAIN}/fullchain.pem /etc/ssl/certs/mailserver.crt
        cp /www/server/panel/vhost/cert/${DOMAIN}/privkey.pem /etc/ssl/private/mailserver.key
    fi
    
    log_info "SSL证书配置完成"
}

# 配置Nginx
setup_nginx() {
    log_step "配置Nginx..."
    
    # 创建网站配置
    cat > /www/server/panel/vhost/nginx/${DOMAIN}.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    
    ssl_certificate /etc/ssl/certs/mailserver.crt;
    ssl_certificate_key /etc/ssl/private/mailserver.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    root /www/wwwroot/${DOMAIN};
    index index.html;
    
    # 管理后台
    location /admin {
        try_files \$uri \$uri/ /admin/index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Webmail (RoundCube)
    location /webmail {
        alias /www/wwwroot/${DOMAIN}/webmail;
        index index.php;
        
        location ~ \.php\$ {
            fastcgi_pass unix:/tmp/php-cgi-74.sock;
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME \$request_filename;
            include fastcgi_params;
        }
    }
    
    # 静态文件
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # 重启Nginx
    nginx -t && systemctl reload nginx
    
    log_info "Nginx配置完成"
}

# 部署AI服务
deploy_ai_services() {
    log_step "部署AI智能服务..."
    
    cd ${PROJECT_ROOT}/ai-services
    
    # 创建Python虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip
    pip install \
        scikit-learn \
        pandas \
        numpy \
        nltk \
        jieba \
        redis \
        tensorflow
    
    # 下载NLTK数据
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
    
    # 创建模型目录
    mkdir -p ${PROJECT_ROOT}/models
    
    log_info "AI服务部署完成"
}

# 创建维护脚本
create_maintenance_scripts() {
    log_step "创建维护脚本..."
    
    # 备份脚本
    cat > ${PROJECT_ROOT}/scripts/backup.sh <<'EOF'
#!/bin/bash
# 邮箱系统备份脚本

BACKUP_DIR="/opt/bt-mailbox/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p ${BACKUP_DIR}/${DATE}

# 备份数据库
mysqldump -umailbox_user -p${MYSQL_DB_PASSWORD} mailbox_db > ${BACKUP_DIR}/${DATE}/database.sql

# 备份邮件数据
tar -czf ${BACKUP_DIR}/${DATE}/mail_data.tar.gz /var/mail/vhosts

# 备份配置文件
tar -czf ${BACKUP_DIR}/${DATE}/config.tar.gz /etc/postfix /etc/dovecot /opt/bt-mailbox/config

# 清理旧备份（保留7天）
find ${BACKUP_DIR} -type d -mtime +7 -exec rm -rf {} \;

echo "备份完成: ${BACKUP_DIR}/${DATE}"
EOF
    
    # 日志轮转脚本
    cat > ${PROJECT_ROOT}/scripts/logrotate.sh <<'EOF'
#!/bin/bash
# 日志轮转脚本

LOG_DIR="/var/log/mailbox"
MAX_SIZE="100M"
MAX_AGE=30

# 轮转应用日志
for log_file in ${LOG_DIR}/*.log; do
    if [[ -f "$log_file" ]] && [[ $(stat -c%s "$log_file") -gt $(numfmt --from=iec ${MAX_SIZE}) ]]; then
        mv "$log_file" "${log_file}.$(date +%Y%m%d_%H%M%S)"
        touch "$log_file"
        chmod 644 "$log_file"
    fi
done

# 清理旧日志
find ${LOG_DIR} -name "*.log.*" -mtime +${MAX_AGE} -delete

echo "日志轮转完成"
EOF
    
    # 健康检查脚本
    cat > ${PROJECT_ROOT}/scripts/health_check.sh <<'EOF'
#!/bin/bash
# 系统健康检查脚本

check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✓ $service 运行正常"
        return 0
    else
        echo "✗ $service 服务异常"
        return 1
    fi
}

echo "=== 邮箱系统健康检查 ==="
echo "检查时间: $(date)"
echo

# 检查核心服务
check_service postfix
check_service dovecot
check_service mysql
check_service redis-server
check_service nginx
check_service mailbox-backend

# 检查端口
echo
echo "=== 端口检查 ==="
netstat -tlnp | grep -E ':(25|143|993|110|995|80|443|5000) '

# 检查磁盘空间
echo
echo "=== 磁盘空间 ==="
df -h /var/mail /opt/bt-mailbox

# 检查内存使用
echo
echo "=== 内存使用 ==="
free -h

echo
echo "健康检查完成"
EOF
    
    # 设置执行权限
    chmod +x ${PROJECT_ROOT}/scripts/*.sh
    
    # 添加定时任务
    cat > /tmp/mailbox_crontab <<EOF
# 邮箱系统定时任务
0 2 * * * ${PROJECT_ROOT}/scripts/backup.sh >> /var/log/mailbox/backup.log 2>&1
0 3 * * * ${PROJECT_ROOT}/scripts/logrotate.sh >> /var/log/mailbox/logrotate.log 2>&1
*/10 * * * * ${PROJECT_ROOT}/scripts/health_check.sh >> /var/log/mailbox/health.log 2>&1
EOF
    
    crontab /tmp/mailbox_crontab
    rm /tmp/mailbox_crontab
    
    log_info "维护脚本创建完成"
}

# 保存部署信息
save_deployment_info() {
    log_step "保存部署信息..."
    
    cat > ${PROJECT_ROOT}/deployment_info.txt <<EOF
企业级邮箱系统部署信息
========================

部署时间: $(date)
域名: ${DOMAIN}
管理员邮箱: ${ADMIN_EMAIL}

服务地址:
- 管理后台: https://${DOMAIN}/admin
- Webmail: https://${DOMAIN}/webmail
- API接口: https://${DOMAIN}/api

数据库信息:
- 数据库名: mailbox_db
- 用户名: mailbox_user
- 密码: ${MYSQL_DB_PASSWORD}

Redis信息:
- 端口: 6379
- 密码: ${REDIS_PASSWORD}

重要文件位置:
- 项目根目录: ${PROJECT_ROOT}
- 邮件存储: /var/mail/vhosts
- 日志目录: /var/log/mailbox
- 配置文件: ${PROJECT_ROOT}/config

维护命令:
- 备份: ${PROJECT_ROOT}/scripts/backup.sh
- 健康检查: ${PROJECT_ROOT}/scripts/health_check.sh
- 查看日志: tail -f /var/log/mailbox/*.log

注意事项:
1. 请及时配置DNS记录 (MX, A, TXT)
2. 建议定期备份数据
3. 监控系统资源使用情况
4. 定期更新SSL证书

EOF
    
    # 设置权限
    chmod 600 ${PROJECT_ROOT}/deployment_info.txt
    
    log_info "部署信息已保存到 ${PROJECT_ROOT}/deployment_info.txt"
}

# 主函数
main() {
    echo "========================================"
    echo "    企业级邮箱系统自动部署脚本"
    echo "========================================"
    echo
    
    check_root
    check_baota
    get_user_input
    
    log_info "开始部署邮箱系统..."
    
    install_dependencies
    create_directories
    setup_mysql
    setup_redis
    setup_postfix
    setup_dovecot
    deploy_backend
    deploy_frontend
    deploy_ai_services
    setup_ssl
    setup_nginx
    create_maintenance_scripts
    save_deployment_info
    
    echo
    log_info "========================================"
    log_info "邮箱系统部署完成！"
    log_info "========================================"
    echo
    log_info "管理后台: https://${DOMAIN}/admin"
    log_info "管理员邮箱: ${ADMIN_EMAIL}"
    log_info "管理员密码: ${ADMIN_PASSWORD}"
    echo
    log_info "详细信息请查看: ${PROJECT_ROOT}/deployment_info.txt"
    echo
    log_warn "请记得配置DNS记录以确保邮件服务正常工作！"
    echo
}

# 执行主函数
main "$@"
