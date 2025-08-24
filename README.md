# 企业级邮箱系统 - Ubuntu宝塔面板版

一个基于Ubuntu和宝塔面板的现代化企业级邮箱解决方案，支持无限用户注册、AI智能垃圾邮件过滤、实时监控和现代化Web管理界面。

## 🚀 核心特性

### 📧 邮件服务
- **无限用户注册** - 支持无限制创建邮箱账户
- **完整邮件收发** - 基于Postfix(SMTP) + Dovecot(IMAP/POP3)
- **多域名支持** - 支持管理多个邮件域名
- **SSL/TLS加密** - 全程加密传输保障安全

### 🤖 AI智能功能
- **垃圾邮件检测** - 基于机器学习的智能识别
- **邮件分类** - 自动分类和标签管理
- **内容摘要** - AI生成邮件内容摘要
- **中英文支持** - 完美支持中英文邮件处理

### 🛡️ 安全防护
- **IP访问控制** - 白名单/黑名单管理
- **JWT认证** - 安全的API访问控制
- **SSL证书** - 自动申请和续期
- **审计日志** - 完整的操作记录

### 📊 监控管理
- **实时监控** - 系统资源和服务状态监控
- **性能图表** - 直观的数据可视化
- **日志管理** - 集中化日志查看和分析
- **自动备份** - 定时数据备份和恢复

### 💻 现代化界面
- **Vue 3前端** - 响应式现代化管理界面
- **宝塔插件** - 完美集成宝塔面板
- **移动端适配** - 支持手机和平板访问
- **多语言支持** - 中英文界面切换

## 📁 项目结构

```
bt-mailbox/
├── backend/                    # 后端API服务
│   ├── app.py                 # Flask主应用
│   ├── requirements.txt       # Python依赖
│   └── .env                   # 环境变量配置
├── frontend/                   # 前端管理界面
│   ├── src/
│   │   ├── App.vue           # Vue主组件
│   │   └── main.js           # 入口文件
│   └── package.json          # Node.js依赖
├── ai-services/               # AI智能服务
│   └── spam_detector.py      # 垃圾邮件检测
├── mail-server/               # 邮件服务器配置
│   ├── postfix/
│   │   └── main.cf           # Postfix主配置
│   └── dovecot/
│       └── dovecot.conf      # Dovecot配置
├── baota-plugin/              # 宝塔面板插件
│   └── mailbox_system/
│       ├── mailbox_system_main.py  # 插件主程序
│       ├── config.json       # 插件配置
│       └── templates/        # 插件模板
├── scripts/                   # 部署和维护脚本
│   ├── complete_deploy.sh    # 完整部署脚本
│   ├── backup.sh            # 备份脚本
│   └── health_check.sh      # 健康检查脚本
├── admin/                     # 独立管理后台
│   └── index.html           # 管理界面
├── deploy.sh                  # 快速部署脚本
└── README.md                 # 项目说明
```

## 🔧 系统要求

### 服务器环境
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **内存**: 最低 2GB，推荐 4GB 或更高
- **存储**: 最低 20GB，推荐 50GB 或更高
- **网络**: 公网IP，开放端口 25, 143, 993, 110, 995, 80, 443

### 软件依赖
- **宝塔面板**: 7.0 或更高版本
- **MySQL**: 5.7 或更高版本
- **Redis**: 5.0 或更高版本
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本

## 🚀 快速部署

### 方法一：一键自动部署（推荐）

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/bt-mailbox/main/scripts/complete_deploy.sh

# 给予执行权限
chmod +x complete_deploy.sh

# 运行部署脚本
sudo ./complete_deploy.sh
```

### 方法二：手动部署

1. **下载项目代码**
```bash
git clone https://github.com/your-repo/bt-mailbox.git
cd bt-mailbox
```

2. **运行部署脚本**
```bash
sudo bash deploy.sh
```

3. **配置DNS记录**
```
MX记录: mail.yourdomain.com (优先级10)
A记录: mail.yourdomain.com -> 服务器IP
TXT记录: SPF和DKIM配置
```

## 📋 部署后配置

### 1. 访问管理后台
- 地址: `https://yourdomain.com/admin`
- 默认账户: `admin@yourdomain.com`
- 默认密码: 部署时设置的密码

### 2. 配置域名DNS
```bash
# MX记录
yourdomain.com.    IN    MX    10    mail.yourdomain.com.

# A记录
mail.yourdomain.com.    IN    A    YOUR_SERVER_IP

# SPF记录
yourdomain.com.    IN    TXT    "v=spf1 mx ~all"

# DKIM记录（可选）
default._domainkey.yourdomain.com.    IN    TXT    "v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY"
```

### 3. 测试邮件收发
```bash
# 发送测试邮件
echo "测试邮件内容" | mail -s "测试主题" test@yourdomain.com

# 检查邮件日志
tail -f /var/log/mail.log
```

## 🔧 系统管理

### 服务管理
```bash
# 查看服务状态
systemctl status postfix dovecot mysql redis nginx mailbox-backend

# 重启邮件服务
systemctl restart postfix dovecot

# 重启后端API
systemctl restart mailbox-backend
```

### 日志查看
```bash
# 邮件服务日志
tail -f /var/log/mail.log

# 系统日志
tail -f /var/log/mailbox/*.log

# 宝塔面板日志
tail -f /www/server/panel/logs/error.log
```

### 备份恢复
```bash
# 手动备份
/opt/bt-mailbox/scripts/backup.sh

# 恢复数据库
mysql -u mailbox_user -p mailbox_db < backup/database.sql

# 恢复邮件数据
tar -xzf backup/mail_data.tar.gz -C /
```

## 🔍 故障排除

### 常见问题

1. **邮件无法发送**
   - 检查DNS MX记录配置
   - 确认端口25未被运营商封禁
   - 查看Postfix日志: `tail -f /var/log/mail.log`

2. **无法接收邮件**
   - 检查Dovecot服务状态
   - 确认用户配额未满
   - 检查防火墙端口开放

3. **管理后台无法访问**
   - 检查Nginx配置
   - 确认SSL证书有效
   - 查看后端API服务状态

4. **AI功能不工作**
   - 检查Python环境和依赖
   - 确认Redis连接正常
   - 查看AI服务日志

### 性能优化

1. **数据库优化**
```sql
-- 优化MySQL配置
SET GLOBAL innodb_buffer_pool_size = 1073741824;  -- 1GB
SET GLOBAL query_cache_size = 268435456;          -- 256MB
```

2. **Redis优化**
```bash
# 编辑Redis配置
vim /etc/redis/redis.conf

# 设置最大内存
maxmemory 512mb
maxmemory-policy allkeys-lru
```

3. **系统优化**
```bash
# 增加文件描述符限制
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf
```

## 📊 监控指标

### 系统监控
- CPU使用率
- 内存使用率
- 磁盘空间
- 网络流量

### 邮件监控
- 每日邮件量
- 垃圾邮件检出率
- 用户活跃度
- 存储使用情况

### 服务监控
- Postfix队列状态
- Dovecot连接数
- MySQL查询性能
- Redis命中率

## 🔐 安全建议

1. **定期更新系统**
```bash
apt update && apt upgrade -y
```

2. **配置防火墙**
```bash
ufw allow 22,25,80,143,443,993,995/tcp
ufw enable
```

3. **启用fail2ban**
```bash
apt install fail2ban
systemctl enable fail2ban
```

4. **定期备份**
- 设置自动备份计划
- 异地备份重要数据
- 定期测试恢复流程

## 🤝 技术支持

### 文档资源
- [安装指南](docs/installation.md)
- [配置说明](docs/configuration.md)
- [API文档](docs/api.md)
- [故障排除](docs/troubleshooting.md)

### 社区支持
- GitHub Issues: 报告问题和建议
- 技术交流群: 加入用户交流群
- 邮件支持: support@example.com

## 📄 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢以下开源项目的贡献：
- [Postfix](http://www.postfix.org/) - 邮件传输代理
- [Dovecot](https://www.dovecot.org/) - IMAP/POP3服务器
- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI组件库
- [宝塔面板](https://www.bt.cn/) - 服务器管理面板

---

**企业级邮箱系统** - 为现代企业提供安全、可靠、智能的邮件解决方案
