#!/usr/bin/python
# coding: utf-8

import os
import sys
import json
import time
import subprocess
import mysql.connector
import redis
from datetime import datetime

# 添加宝塔面板路径
sys.path.append('/www/server/panel/class')
import public

class mailbox_system_main:
    """
    企业级邮箱系统宝塔插件主程序
    """
    
    def __init__(self):
        self.plugin_path = '/www/server/panel/plugin/mailbox_system'
        self.project_path = '/opt/bt-mailbox'
        self.site_path = '/www/wwwroot'
        self.config_file = os.path.join(self.plugin_path, 'config.json')
        self.load_config()
    
    def load_config(self):
        """加载插件配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except:
            self.config = {
                'domain': '',
                'admin_email': '',
                'db_password': '',
                'redis_password': '',
                'installed': False
            }
    
    def save_config(self):
        """保存插件配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def get_index(self, args):
        """获取插件主页面"""
        try:
            # 检查是否已安装
            if not self.config.get('installed', False):
                return self.get_install_page()
            
            # 获取系统统计信息
            stats = self.get_system_stats()
            
            # 渲染主页面
            template_file = os.path.join(self.plugin_path, 'templates', 'index.html')
            with open(template_file, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 替换模板变量
            template = template.replace('{{DOMAIN}}', self.config.get('domain', ''))
            template = template.replace('{{STATS}}', json.dumps(stats))
            
            return template
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def get_install_page(self):
        """获取安装页面"""
        template_file = os.path.join(self.plugin_path, 'templates', 'install.html')
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def install_system(self, args):
        """安装邮箱系统"""
        try:
            domain = args.get('domain', '').strip()
            admin_email = args.get('admin_email', '').strip()
            
            if not domain or not admin_email:
                return public.returnMsg(False, '请填写完整信息')
            
            # 检查域名格式
            import re
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$', domain):
                return public.returnMsg(False, '域名格式不正确')
            
            # 执行安装脚本
            install_script = os.path.join(self.plugin_path, 'scripts', 'install.sh')
            cmd = f'bash {install_script} {domain} {admin_email}'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 更新配置
                self.config['domain'] = domain
                self.config['admin_email'] = admin_email
                self.config['installed'] = True
                self.config['install_time'] = datetime.now().isoformat()
                self.save_config()
                
                return public.returnMsg(True, '邮箱系统安装成功')
            else:
                return public.returnMsg(False, f'安装失败: {result.stderr}')
                
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def get_system_stats(self):
        """获取系统统计信息"""
        try:
            stats = {
                'users_count': 0,
                'active_users': 0,
                'mail_count': 0,
                'storage_used': 0,
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'services': []
            }
            
            # 获取数据库统计
            if self.config.get('db_password'):
                try:
                    conn = mysql.connector.connect(
                        host='localhost',
                        user='bt_mailbox_user',
                        password=self.config['db_password'],
                        database='bt_mailbox'
                    )
                    cursor = conn.cursor()
                    
                    # 用户统计
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats['users_count'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users WHERE enabled = 1")
                    stats['active_users'] = cursor.fetchone()[0]
                    
                    conn.close()
                except:
                    pass
            
            # 获取系统资源使用情况
            try:
                import psutil
                stats['cpu_percent'] = psutil.cpu_percent()
                stats['memory_percent'] = psutil.virtual_memory().percent
                stats['disk_percent'] = psutil.disk_usage('/').percent
            except:
                pass
            
            # 获取服务状态
            services = ['postfix', 'dovecot', 'redis-server', 'mysql', 'bt-mailbox-api']
            for service in services:
                try:
                    result = subprocess.run(f'systemctl is-active {service}', 
                                          shell=True, capture_output=True, text=True)
                    status = 'running' if result.stdout.strip() == 'active' else 'stopped'
                    stats['services'].append({
                        'name': service,
                        'status': status,
                        'display_name': self.get_service_display_name(service)
                    })
                except:
                    stats['services'].append({
                        'name': service,
                        'status': 'unknown',
                        'display_name': self.get_service_display_name(service)
                    })
            
            return stats
            
        except Exception as e:
            return {
                'error': str(e),
                'users_count': 0,
                'active_users': 0,
                'services': []
            }
    
    def get_service_display_name(self, service):
        """获取服务显示名称"""
        service_names = {
            'postfix': 'SMTP服务',
            'dovecot': 'IMAP服务',
            'redis-server': 'Redis缓存',
            'mysql': 'MySQL数据库',
            'bt-mailbox-api': 'API服务'
        }
        return service_names.get(service, service)
    
    def get_users(self, args):
        """获取用户列表"""
        try:
            if not self.config.get('db_password'):
                return public.returnMsg(False, '数据库未配置')
            
            conn = mysql.connector.connect(
                host='localhost',
                user='bt_mailbox_user',
                password=self.config['db_password'],
                database='bt_mailbox'
            )
            cursor = conn.cursor(dictionary=True)
            
            # 分页参数
            page = int(args.get('page', 1))
            limit = int(args.get('limit', 20))
            offset = (page - 1) * limit
            
            # 搜索参数
            search = args.get('search', '').strip()
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE email LIKE %s OR name LIKE %s"
                params = [f'%{search}%', f'%{search}%']
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取用户列表
            sql = f"""
                SELECT id, email, name, quota, enabled, is_admin, created_at 
                FROM users {where_clause} 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [limit, offset])
            users = cursor.fetchall()
            
            # 格式化日期
            for user in users:
                if user['created_at']:
                    user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            conn.close()
            
            return public.returnMsg(True, '获取成功', {
                'users': users,
                'total': total,
                'page': page,
                'limit': limit
            })
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def add_user(self, args):
        """添加用户"""
        try:
            email = args.get('email', '').strip()
            password = args.get('password', '').strip()
            name = args.get('name', '').strip()
            quota = int(args.get('quota', 1073741824))  # 默认1GB
            enabled = args.get('enabled', True)
            
            if not email or not password:
                return public.returnMsg(False, '邮箱和密码不能为空')
            
            # 验证邮箱格式
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return public.returnMsg(False, '邮箱格式不正确')
            
            conn = mysql.connector.connect(
                host='localhost',
                user='bt_mailbox_user',
                password=self.config['db_password'],
                database='bt_mailbox'
            )
            cursor = conn.cursor()
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                conn.close()
                return public.returnMsg(False, '邮箱已存在')
            
            # 密码加密
            import hashlib
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            # 插入用户
            sql = """
                INSERT INTO users (email, password, name, quota, enabled, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (email, password_hash, name, quota, enabled, datetime.now()))
            conn.commit()
            
            user_id = cursor.lastrowid
            conn.close()
            
            # 创建邮箱目录
            self.create_mailbox(email)
            
            return public.returnMsg(True, '用户创建成功', {'user_id': user_id})
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def create_mailbox(self, email):
        """创建邮箱目录"""
        try:
            domain = email.split('@')[1]
            username = email.split('@')[0]
            
            mailbox_path = f'/var/mail/vhosts/{domain}/{username}'
            os.makedirs(f'{mailbox_path}/Maildir/cur', exist_ok=True)
            os.makedirs(f'{mailbox_path}/Maildir/new', exist_ok=True)
            os.makedirs(f'{mailbox_path}/Maildir/tmp', exist_ok=True)
            
            # 设置权限
            subprocess.run(f'chown -R vmail:vmail {mailbox_path}', shell=True)
            subprocess.run(f'chmod -R 755 {mailbox_path}', shell=True)
            
            return True
        except:
            return False
    
    def delete_user(self, args):
        """删除用户"""
        try:
            user_id = int(args.get('user_id', 0))
            if not user_id:
                return public.returnMsg(False, '用户ID不能为空')
            
            conn = mysql.connector.connect(
                host='localhost',
                user='bt_mailbox_user',
                password=self.config['db_password'],
                database='bt_mailbox'
            )
            cursor = conn.cursor()
            
            # 获取用户邮箱
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return public.returnMsg(False, '用户不存在')
            
            email = result[0]
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            conn.close()
            
            # 删除邮箱目录
            domain = email.split('@')[1]
            username = email.split('@')[0]
            mailbox_path = f'/var/mail/vhosts/{domain}/{username}'
            subprocess.run(f'rm -rf {mailbox_path}', shell=True)
            
            return public.returnMsg(True, '用户删除成功')
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def toggle_user_status(self, args):
        """切换用户状态"""
        try:
            user_id = int(args.get('user_id', 0))
            if not user_id:
                return public.returnMsg(False, '用户ID不能为空')
            
            conn = mysql.connector.connect(
                host='localhost',
                user='bt_mailbox_user',
                password=self.config['db_password'],
                database='bt_mailbox'
            )
            cursor = conn.cursor()
            
            # 获取当前状态
            cursor.execute("SELECT enabled FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return public.returnMsg(False, '用户不存在')
            
            new_status = not result[0]
            
            # 更新状态
            cursor.execute("UPDATE users SET enabled = %s WHERE id = %s", (new_status, user_id))
            conn.commit()
            conn.close()
            
            status_text = '启用' if new_status else '禁用'
            return public.returnMsg(True, f'用户已{status_text}')
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def restart_service(self, args):
        """重启服务"""
        try:
            service_name = args.get('service_name', '').strip()
            if not service_name:
                return public.returnMsg(False, '服务名称不能为空')
            
            # 安全检查
            allowed_services = ['postfix', 'dovecot', 'redis-server', 'mysql', 'bt-mailbox-api']
            if service_name not in allowed_services:
                return public.returnMsg(False, '不允许操作此服务')
            
            result = subprocess.run(f'systemctl restart {service_name}', 
                                  shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return public.returnMsg(True, f'{service_name} 服务重启成功')
            else:
                return public.returnMsg(False, f'服务重启失败: {result.stderr}')
                
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def get_logs(self, args):
        """获取系统日志"""
        try:
            log_type = args.get('log_type', 'system')
            lines = int(args.get('lines', 100))
            
            log_files = {
                'system': '/var/log/syslog',
                'mail': '/var/log/mail.log',
                'api': '/opt/bt-mailbox/logs/api.log'
            }
            
            log_file = log_files.get(log_type, log_files['system'])
            
            if not os.path.exists(log_file):
                return public.returnMsg(True, '日志文件不存在', {'logs': []})
            
            result = subprocess.run(f'tail -n {lines} {log_file}', 
                                  shell=True, capture_output=True, text=True)
            
            logs = result.stdout.split('\n') if result.stdout else []
            
            return public.returnMsg(True, '获取成功', {'logs': logs})
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def backup_system(self, args):
        """备份系统"""
        try:
            backup_type = args.get('backup_type', 'full')  # full, database, config
            
            backup_dir = f'/opt/bt-mailbox/backups/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(backup_dir, exist_ok=True)
            
            if backup_type in ['full', 'database']:
                # 备份数据库
                db_backup_file = os.path.join(backup_dir, 'database.sql')
                cmd = f'mysqldump -u bt_mailbox_user -p{self.config["db_password"]} bt_mailbox > {db_backup_file}'
                subprocess.run(cmd, shell=True)
            
            if backup_type in ['full', 'config']:
                # 备份配置文件
                config_backup_dir = os.path.join(backup_dir, 'config')
                os.makedirs(config_backup_dir, exist_ok=True)
                subprocess.run(f'cp -r /opt/bt-mailbox/config/* {config_backup_dir}/', shell=True)
                subprocess.run(f'cp -r /etc/postfix {config_backup_dir}/', shell=True)
                subprocess.run(f'cp -r /etc/dovecot {config_backup_dir}/', shell=True)
            
            # 创建备份信息文件
            backup_info = {
                'type': backup_type,
                'created_at': datetime.now().isoformat(),
                'size': self.get_directory_size(backup_dir)
            }
            
            with open(os.path.join(backup_dir, 'backup_info.json'), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return public.returnMsg(True, '备份创建成功', {'backup_path': backup_dir})
            
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def get_directory_size(self, path):
        """获取目录大小"""
        try:
            result = subprocess.run(f'du -sh {path}', shell=True, capture_output=True, text=True)
            return result.stdout.split()[0] if result.stdout else '0'
        except:
            return '0'
    
    def uninstall_plugin(self, args):
        """卸载插件"""
        try:
            # 停止相关服务
            services = ['bt-mailbox-api', 'postfix', 'dovecot']
            for service in services:
                subprocess.run(f'systemctl stop {service}', shell=True)
                subprocess.run(f'systemctl disable {service}', shell=True)
            
            # 删除数据库
            if self.config.get('db_password'):
                try:
                    conn = mysql.connector.connect(
                        host='localhost',
                        user='root',
                        password=public.M('mysql').get_root()
                    )
                    cursor = conn.cursor()
                    cursor.execute("DROP DATABASE IF EXISTS bt_mailbox")
                    cursor.execute("DROP USER IF EXISTS 'bt_mailbox_user'@'localhost'")
                    conn.commit()
                    conn.close()
                except:
                    pass
            
            # 删除项目文件
            subprocess.run(f'rm -rf {self.project_path}', shell=True)
            
            # 删除网站文件
            if self.config.get('domain'):
                site_path = os.path.join(self.site_path, self.config['domain'])
                subprocess.run(f'rm -rf {site_path}', shell=True)
            
            # 重置配置
            self.config = {'installed': False}
            self.save_config()
            
            return public.returnMsg(True, '插件卸载成功')
            
        except Exception as e:
            return public.returnMsg(False, str(e))

# 插件入口函数
def main():
    plugin = mailbox_system_main()
    return plugin
