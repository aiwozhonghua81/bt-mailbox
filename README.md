# 企业级宝塔邮箱系统（bt-mailbox）

> 一句话说清楚：**这是一个装在 Ubuntu + 宝塔面板上的自建邮箱服务器**。
> 装好以后，你就有了自己的域名邮箱（比如 `zhangsan@yourdomain.com`），
> 可以收验证码邮件、发邮件、批量管理邮箱账号，还带一个 AI 垃圾邮件过滤器和一个网页管理后台。
>
> 仓库地址：<https://github.com/aiwozhonghua81/bt-mailbox>
> 许可证：MIT（可以随便改、随便用、随便商用）

---

## 📖 目录

- [一、这个项目到底是干啥的](#一这个项目到底是干啥的)
- [二、它长什么样，能干哪些事](#二它长什么样能干哪些事)
- [三、跑起来需要什么](#三跑起来需要什么)
- [四、最快的装法（一键脚本）](#四最快的装法一键脚本)
- [五、装的时候它会问你什么](#五装的时候它会问你什么)
- [六、装完之后的 15 个步骤到底干了啥](#六装完之后的-15-个步骤到底干了啥)
- [七、装完之后你必须去做的四件事](#七装完之后你必须去做的四件事)
- [八、目录结构说明](#八目录结构说明)
- [九、后台 API 接口一览](#九后台-api-接口一览)
- [十、宝塔面板插件](#十宝塔面板插件)
- [十一、AI 垃圾邮件过滤是怎么工作的](#十一ai-垃圾邮件过滤是怎么工作的)
- [十二、邮件服务器配置要点（Postfix / Dovecot）](#十二邮件服务器配置要点postfix--dovecot)
- [十三、日常运维命令速查](#十三日常运维命令速查)
- [十四、常见问题排查](#十四常见问题排查)
- [十五、安全提醒（重要）](#十五安全提醒重要)
- [十六、这个项目的现状说明（请先读）](#十六这个项目的现状说明请先读)
- [十七、致谢](#十七致谢)

---

## 一、这个项目到底是干啥的

先说人话。

你有没有过这种经历：

- 想注册一个国外网站，结果它要收邮箱验证码，但你的常用邮箱已经注册过了；
- 想用某个服务专门收广告邮件，不想污染主邮箱；
- 公司要一个「看起来很正规」的企业邮箱域名，但不想按月给服务商交钱；
- 看到别人做的 Webmail 界面很好看，想自己也搞一个。

这个项目就是干这些事的：**在你的服务器上，用 Postfix + Dovecot 搭一个真正的邮件服务器**，收信发信都走标准 SMTP / IMAP 协议，所以 Outlook、Apple 邮件、Thunderbird、手机自带邮件 App 全都能用；再配一个 Flask 后端和一个网页后台，用来批量管理邮箱账号、看统计数据、开垃圾邮件过滤。

### 它不是什么

先把话说清楚，免得你期望错位：

| 它**是** | 它**不是** |
| --- | --- |
| 自建邮件服务器（你自己控制数据） | 公共云邮箱服务（不是 Gmail 那种） |
| 收验证码邮件的"专用号"机器 | 群发广告邮件的工具 |
| 单域名、多账号的邮箱系统 | 微软 Exchange / Google Workspace 那种企业级全家桶 |
| 一个**能跑起来的脚手架** | 一个开箱即用、零调整的产品 |

---

## 二、它长什么样，能干哪些事

### 2.1 邮件收发能力

- **无限注册邮箱账号** —— 后台点几下就多一个 `xxx@yourdomain.com`，专门的验证码邮箱可以批量搞。
- **标准协议** —— SMTP 发信（25 / 587 端口）、IMAP 收信（143 / 993 端口）、POP3（110 / 995 端口）。用啥客户端都行。
- **多域名支持** —— 数据库里有 `domains` 表，你可以同时挂多个域名，每个域名单独开关。
- **TLS 加密** —— Postfix 和 Dovecot 都配了证书路径，发信收信全程加密。
- **Sieve 邮件过滤规则** —— Dovecot 配了 sieve 插件，能写规则自动归档、删除、转发。

### 2.2 AI 垃圾邮件过滤

`ai-services/spam_detector.py` 是一个**独立的垃圾邮件识别器**，用机器学习的方式判断一封邮件是不是广告 / 诈骗。

它长这样：

```
输入：一封邮件（发件人、主题、正文、附件数……）
   ↓
① 文本预处理：去 HTML 标签、去停用词、英文词干还原、中文 jieba 分词
   ↓
② 语言识别：自动判断这封邮件是中文还是英文
   ↓
③ 三路模型同时打分：
   · 朴素贝叶斯 (MultinomialNB)
   · 随机森林 (RandomForest)
   · 逻辑回归 (LogisticRegression)
   ↓
④ 关键词兜底：中英文各一份垃圾词库
   ↓
⑤ 加权投票 → 输出 0~1 的垃圾概率 + 判定结果
   ↓
⑥ Redis 缓存：以邮件哈希为 key，重复邮件直接读缓存，不重复算
```

### 2.3 后台管理

- **Web 管理后台** —— `admin/index.html`，一个单文件页面，不用编译就能用。
- **Vue 3 前端工程** —— `frontend/`，用 Vue 3 + Element Plus + ECharts 写的完整后台工程，开发用 `npm run serve`，打包用 `npm run build`。
- **用户管理** —— 增删改查、启用/禁用、改配额。
- **实时统计** —— CPU / 内存 / 磁盘占用、用户数、邮件处理量、垃圾邮件命中率。
- **邮件日志** —— 在后台直接看收发的日志，不用 SSH 上服务器翻文件。

### 2.4 宝塔面板集成

`baota-plugin/mailbox_system/` 是按宝塔插件规范写的，可以在宝塔面板里直接装成一个「应用商店」条目，里面有 8 个菜单：系统概览、用户管理、域名管理、邮件管理、系统监控、AI 设置、备份管理、系统设置。

---

## 三、跑起来需要什么

### 3.1 服务器

| 项目 | 最低 | 推荐 |
| --- | --- | --- |
| 操作系统 | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| CPU | 1 核 | 2 核以上 |
| 内存 | 2 GB | 4 GB 以上 |
| 硬盘 | 20 GB | 50 GB 以上（邮件很占地方） |
| 必须是公网 IP | ✅ | ✅ |

### 3.2 软件

| 软件 | 版本要求 | 干什么用 |
| --- | --- | --- |
| 宝塔面板 | 7.0 以上 | 脚本会检测 `/www/server/panel/BT-Panel`，没有就直接退出 |
| MySQL | 5.7 以上 | 存用户、域名、配置 |
| Redis | 5.0 以上 | 缓存 + 做限流计数 |
| Python | 3.8 以上 | 跑 Flask 后端和 AI 服务 |
| Node.js | 16 以上 | 只在你要构建 Vue 前端时用得到 |
| Postfix | apt 装的就行 | 发信 |
| Dovecot | apt 装的就行 | 收信 |

### 3.3 需要开的端口

| 端口 | 用途 | 谁连 |
| --- | --- | --- |
| 25 | SMTP 发信 | 全球邮件服务器 |
| 587 | SMTP 提交（带认证） | 你的客户端 |
| 110 / 995 | POP3 / POP3S | 你的客户端 |
| 143 / 993 | IMAP / IMAPS | 你的客户端 |
| 80 / 443 | 网站 + 管理后台 | 你的浏览器 |
| 5000 | 后端 API | Nginx 反代（外部不直接开） |
| 3306 | MySQL | 只允许本机 |
| 6379 | Redis | 只允许本机 |

**端口 25 是自建邮件服务器的生死线。** 国内很多云厂商（阿里云、腾讯云轻量、华为云等）默认封 25 端口，有的要提工单才解封。国外 VPS（DigitalOcean、Vultr、Linode、Hetzner）一般直接可用。所以：**买服务器时优先看「25 端口是否解封」，这比配置重要得多。**

---

## 四、最快的装法（一键脚本）

### 4.1 第一步：克隆代码

```bash
git clone https://github.com/aiwozhonghua81/bt-mailbox.git
cd bt-mailbox
```

### 4.2 第二步：跑完整部署脚本

```bash
sudo bash scripts/complete_deploy.sh
```

或者从 raw 直接拉（不想 clone 就用这个）：

```bash
wget https://raw.githubusercontent.com/aiwozhonghua81/bt-mailbox/main/scripts/complete_deploy.sh
chmod +x complete_deploy.sh
sudo ./complete_deploy.sh
```

> ⚠️ 这脚本**很重**：会 `apt install` 一堆东西、改 `/etc/postfix/` 和 `/etc/dovecot/`、建 MySQL 库、写 systemd 服务、动 Nginx 配置、建 crontab。
> **建议先在测试机上跑一遍**，别一上来就往生产服务器上砸。

### 4.3 另一个脚本：deploy.sh

`deploy.sh` 是**轻量版**，它不装 Postfix/Dovecot，只做：建目录 → 建库 → 部署一个 Flask 后端 → 部署一个静态首页 → 配 Nginx → 存一份账号信息到 `/opt/bt-mailbox/credentials.txt`。

适合这种场景：你想先看看界面长什么样，或者你已经有自己的邮件服务器了，只想要后台和统计面板。

```bash
sudo bash deploy.sh
```

> ⚠️ **注意一件容易搞混的事**：`deploy.sh` **不用仓库里的 `backend/app.py`**。它在 `deploy_backend()` 里用 heredoc **现场生成**一个全新的 `app.py`（约 90 行，MD5 存密码、无 JWT、无 AI、无邮件日志表），配套建的是 `bt_mailbox` 库 + `users` 表（密码字段叫 `password`）。
>
> 所以 `deploy.sh` 部署出来的是**另一个简化版系统**，功能只有：登录、用户增删查、一个统计接口。它跟你读 `backend/app.py` 看到的代码**不是一回事**。想用完整的 AI 过滤 + JWT + 邮件日志，**必须用 `scripts/complete_deploy.sh`**。

**两者的区别（很重要）：**

| | `scripts/complete_deploy.sh` | `deploy.sh` |
| --- | --- | --- |
| 用哪套后端代码 | 仓库里的 `backend/app.py` | **现场另生成一个**（约 90 行简化版） |
| 装 Postfix + Dovecot | ✅ | ❌ |
| 部署 AI 垃圾邮件服务 | ✅ | ❌ |
| JWT 登录 | ✅ | ❌（只有简单 MD5 密码比对） |
| 邮件日志表 | ✅ | ❌ |
| 配 SSL | ✅ | ❌（留给你在宝塔里点） |
| 建维护脚本 + 定时任务 | ✅ | ❌ |
| 数据库名 | `mailbox_db` | `bt_mailbox` |
| 管理员密码怎么来 | **你自己输入**（≥8 位） | **脚本随机生成** |
| 产物 | `/opt/bt-mailbox/deployment_info.txt` | `/opt/bt-mailbox/credentials.txt` |

---

## 五、装的时候它会问你什么

跑 `scripts/complete_deploy.sh` 的时候，它会**交互式**问你几个问题（`get_user_input()`，脚本第 69 行起）。第一次跑之前先看一眼要准备什么：

### 5.1 问题 1：邮箱域名

```
请输入邮箱系统域名 (如: mail.example.com):
```

- **格式要求**：必须像域名，比如 `mail.example.com`、`mycompany.com`
- **正则校验**：`^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$`
- 格式不对会一直循环让你重输
- ❗ **这个域名必须是你自己的，而且你得能在 DNS 服务商那边改解析**

### 5.2 问题 2：管理员邮箱

```
请输入管理员邮箱:
```

- 就是你登录后台用的账号，比如 `admin@yourdomain.com`
- ❗ **必须是你域名下的地址**，因为注册接口会检查「这个域名在 `domains` 表里而且是 enabled 状态」

### 5.3 问题 3：管理员密码

```
请输入管理员密码 (至少8位):
```

- 输入时**不回显**（脚本用的是 `read -s`），屏幕上只看不到字符，正常打字就行
- **至少 8 位**，不够会警告并让你重输
- 这一个是你自己定的密码（`deploy.sh` 才是随机生成）

### 5.4 它还会自己生成四组密码

| 密码 | 生成方式 | 用途 |
| --- | --- | --- |
| `MYSQL_ROOT_PASSWORD` | `openssl rand -base64 32` | MySQL root 密码 |
| `MYSQL_DB_PASSWORD` | `openssl rand -base64 32` | 数据库用户 `mailbox_user` 的密码 |
| `REDIS_PASSWORD` | `openssl rand -base64 32` | Redis 密码 |
| `JWT_SECRET` | `openssl rand -base64 64` | JWT 签名密钥 |

> 🔐 **这些随机密码只打印一次**（管理员密码是你自己定的），之后只能在 `/opt/bt-mailbox/deployment_info.txt` 里看（文件权限 `600`）。部署完立刻把这个文件存到你的密码管理器里。
>
> ⚠️ `openssl rand -base64` 生成的密码里可能有 `/`、`+`、`=` 这类字符，写进某些配置文件或 URL 的时候需要转义。如果碰到莫名其妙的连接错误，**先怀疑是密码里的特殊字符**。

---

## 六、装完之后的 15 个步骤到底干了啥

`main()` 函数（脚本第 740 行）按顺序跑了 15 步。知道每步干了啥，出了问题才知道去哪儿翻。

| # | 函数 | 干了啥 |
| --- | --- | --- |
| 1 | `check_root` | 检查是不是 root，不是就直接退出 |
| 2 | `check_baota` | 检查 `/www/server/panel/BT-Panel` 在不在，不在就退出并提示宝塔安装命令 |
| 3 | `get_user_input` | 交互式收集域名、管理员邮箱、管理员密码；生成 4 组随机密码 |
| 4 | `install_dependencies` | `apt install` postfix / dovecot / postfix-mysql / dovecot-mysql / spamassassin / clamav / amavisd-new 等 |
| 5 | `create_directories` | 建 `/opt/bt-mailbox/{backend,frontend,ai-services,mail-server,monitoring,scripts,logs,config,ssl,backup}`，建 `vmail` 用户（UID 5000） |
| 6 | `setup_mysql` | 建 `mailbox_db` 库 + `mailbox_user` 用户，建 4 张表，插入管理员和域名 |
| 7 | `setup_redis` | **整体重写** `/etc/redis/redis.conf`，设密码 + 256MB 上限 + LRU 淘汰，重启 |
| 8 | `setup_postfix` | 复制 `main.cf` 到 `/etc/postfix/`，`sed` 替换域名，建 MySQL 虚拟用户映射表 |
| 9 | `setup_dovecot` | 复制 `dovecot.conf`，建 `dovecot-sql.conf.ext`，生成 2048 位 DH 参数 |
| 10 | `deploy_backend` | 建 venv、pip 装 18 个包、写 `.env`、建 systemd 服务 `mailbox-backend`、启动 |
| 11 | `deploy_frontend` | `npm install` + `npm run build`，产物拷到 `/www/wwwroot/${DOMAIN}/admin/` |
| 12 | `deploy_ai_services` | 给 AI 服务建独立 venv，装 tensorflow 等，下载 NLTK 数据，建 `models/` 目录 |
| 13 | `setup_ssl` | 调宝塔 `bt ssl -d 域名 -auto` 申请证书；失败则生成 365 天自签名证书 |
| 14 | `setup_nginx` | 写 `/www/server/panel/vhost/nginx/${DOMAIN}.conf`，反代 `/api`，配置 `/admin` 和 `/webmail` |
| 15 | `create_maintenance_scripts` + `save_deployment_info` | 生成备份/日志轮转/健康检查脚本，写 crontab，保存部署信息 |

### 6.1 第 15 步生成的三个脚本

⚠️ **注意：这三个脚本不在仓库里！** 它们是部署的时候才被脚本生成到 `/opt/bt-mailbox/scripts/` 目录下的。

| 脚本 | 干什么 | crontab 计划 |
| --- | --- | --- |
| `backup.sh` | 备份数据库（`mysqldump`）+ 邮件数据（`tar`）+ 配置文件，保留 7 天 | 每天 02:00 |
| `logrotate.sh` | 日志超过 100MB 就切一份，30 天前的删掉 | 每天 03:00 |
| `health_check.sh` | 检查 6 个服务状态 + 9 个端口 + 磁盘 + 内存 | 每 10 分钟 |

所以部署完之后你跑 `ls /opt/bt-mailbox/scripts/` 就能看到它们了。

### 6.2 部署产物清单

```
/opt/bt-mailbox/
├── deployment_info.txt      # 所有密码和路径（权限 600）
├── config/                  # 配置文件
├── logs/                    # 日志
├── storage/                 # 存储
├── scripts/                 # ← 上面那三个脚本是部署时生成的
└── backend/ frontend/ mail-server/ monitoring/

/var/mail/vhosts/            # 邮件正文实际存放地
/var/log/mailbox/            # 应用日志
/var/log/postfix.log         # Postfix 日志
/var/log/dovecot.log         # Dovecot 日志
```

---

## 七、装完之后你必须去做的四件事

部署脚本跑完，**邮件大概率还发不出去**，因为下面这四件事脚本做不了。

### 7.1 改 DNS 解析（最关键）

去你的域名服务商（阿里云 / 腾讯云 / Cloudflare / Namecheap…）加这几条记录：

| 类型 | 主机记录 | 指向 | 用途 |
| --- | --- | --- | --- |
| **A** | `mail`（或你填的域名） | 你的服务器 IP | 邮件服务器本体 |
| **MX** | `@`（根域） | `mail.你的域名` 优先级 10 | 告诉全世界「发到这个域名的信该送到我这」 |
| **TXT (SPF)** | `@` | `v=spf1 mx ~all` | 声明只有我的服务器能代表这个域名发信，防伪造 |
| **TXT (DKIM)** | `default._domainkey` | 部署脚本生成的公钥 | 邮件签名，防伪造（强烈建议） |
| **TXT (DMARC)** | `_dmarc` | `v=DMARC1; p=none; rua=mailto:admin@你的域名` | 告诉收件方遇到可疑邮件怎么办 |

> **⚠️ MX 记录是最容易搞错的。** MX 记录的「值」必须写主机名（`mail.yourdomain.com`），不能写 IP（IP 写在对应的 A 记录里）。写错了邮件直接进垃圾箱或者被退回。
>
> **Cloudflare 用户注意**：Cloudflare 代理（橙色小云）**只对 HTTP/HTTPS 有用，SMTP 根本不经过它**，所以邮件记录要设成「仅 DNS」（灰色小云）。

### 7.2 申请 SSL 证书

在宝塔面板 → 网站 → 你的域名 → SSL → Let's Encrypt → 申请，然后开启「强制 HTTPS」。

脚本的 `setup_ssl` 步骤只准备了配置位置，证书得你自己申请（宝塔一键最省事）。

### 7.3 开防火墙

```bash
# ufw 放行
ufw allow 22/tcp
ufw allow 25/tcp      # 发信，最重要
ufw allow 587/tcp     # 客户端提交
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 110/tcp
ufw allow 143/tcp
ufw allow 993/tcp
ufw allow 995/tcp
ufw enable
```

另外**云厂商的安全组也要放行同样的端口**——很多人在云控制台那层卡住，只改了服务器内的 ufw 没用。

### 7.4 验证一下装好没有

```bash
# 1. 服务是不是都在跑
systemctl status postfix dovecot redis-server nginx mailbox-backend

# 2. 端口有没有起来
netstat -tlnp | grep -E ':(25|587|143|993|6379|5000) '

# 3. 后端 API 活着没
curl http://127.0.0.1:5000/api/health

# 4. 发一封测试信到自己邮箱
echo "测试邮件" | mail -s "bt-mailbox 测试" your@qq.com

# 5. 看发信日志
tail -f /var/log/postfix.log
```

---

## 八、目录结构说明

```
bt-mailbox/
├── backend/
│   ├── app.py                 # Flask 主应用（669 行），所有 API 都在这
│   └── requirements.txt       # Python 依赖清单
│
├── frontend/
│   ├── package.json           # Vue 3 + Element Plus + ECharts + axios
│   └── src/
│       ├── App.vue            # 后台主组件
│       └── main.js            # 入口
│
├── ai-services/
│   └── spam_detector.py       # AI 垃圾邮件检测器（626 行）
│
├── mail-server/
│   ├── postfix/main.cf        # Postfix 主配置（虚拟用户、MySQL、SASL、TLS、限速）
│   └── dovecot/dovecot.conf   # Dovecot 配置（IMAP/POP3/LMTP、配额、Sieve、LUCENE 全文搜索）
│
├── baota-plugin/
│   └── mailbox_system/
│       ├── mailbox_system_main.py   # 宝塔插件主程序
│       ├── config.json             # 插件配置（8 个菜单、9 个 API、权限列表）
│       └── templates/index.html     # 插件页面模板
│
├── scripts/
│   └── complete_deploy.sh     # 完整一键部署脚本（782 行，15 步）
│
├── admin/
│   └── index.html             # 独立管理后台（单文件，免构建）
│
├── deploy.sh                  # 轻量部署脚本（只做后台 + 页面 + Nginx）
└── README.md
```

**根目录没有 `docs/` 目录**，也**没有** `scripts/backup.sh`、`scripts/health_check.sh`（后两个是部署时生成的）。README 里如果提到它们，都是指装完之后服务器上的文件。

---

## 九、后台 API 接口一览

所有接口都以 `/api/` 开头，前缀由 Nginx 反代到 `127.0.0.1:5000`。

### 9.1 免登录的接口

| 方法 | 路径 | 作用 | 限流 |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | 管理员登录，返回 JWT | **10 次/分钟** |
| POST | `/api/auth/register` | 用户自助注册 | **5 次/分钟** |
| GET | `/api/health` | 健康检查（给监控用） | 无 |

**注册接口有个前置条件**：你填的邮箱域名必须已经在 `domains` 表里，而且 `enabled = true`，否则直接拒绝。想让某个域名开放自助注册，先去后台「域名管理」把它加进来并启用。

### 9.2 需要 JWT 令牌的接口

登录成功拿到的 JWT **有效期 24 小时**。之后每个请求带上：

```
Authorization: Bearer <你的token>
```

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/users` | 用户列表 |
| POST | `/api/users` | 新建用户 |
| PUT | `/api/users/<id>` | 改用户（资料、配额、启停） |
| DELETE | `/api/users/<id>` | 删用户 |
| GET | `/api/stats` | 系统统计（用户数、CPU、内存、磁盘、服务状态） |
| POST | `/api/ai/spam-check` | 让 AI 判一封邮件是不是垃圾邮件 |
| GET | `/api/ai/stats` | AI 检测的统计（检出率、样本数等） |
| GET | `/api/mail-logs` | 翻邮件日志 |

### 9.3 JWT 密钥的事

代码里 `SECRET_KEY` / `JWT_SECRET_KEY` 的默认值是 `secrets.token_hex(32)`——**每次重启都不一样**。这意味着：

- 重启后端 → 所有人手里的 token 全部失效 → 得重新登录
- 多进程部署（比如 gunicorn 起 4 个 worker）→ 不同 worker 密钥不同 → 登录时拿到 A worker 的 token，发请求打到 B worker 就 401

**生产环境必须在 `.env` 里显式指定固定的 `JWT_SECRET`**，别用默认值。

---

## 十、宝塔面板插件

`baota-plugin/mailbox_system/config.json` 里定义了插件的全部元信息：

### 10.1 8 个菜单

| id | 标题 | 模板 |
| --- | --- | --- |
| `dashboard` | 系统概览 | `dashboard.html` |
| `users` | 用户管理 | `users.html` |
| `domains` | 域名管理 | `domains.html` |
| `mail` | 邮件管理 | `mail.html` |
| `monitoring` | 系统监控 | `monitoring.html` |
| `ai` | AI 设置 | `ai.html` |
| `backup` | 备份管理 | `backup.html` |
| `settings` | 系统设置 | `settings.html` |

> ⚠️ `config.json` 里只带了 `templates/index.html` 一个模板文件。上表里其他 7 个模板需要你自己按 `index.html` 的风格补，或者改成跳转主控台。

### 10.2 插件调用的 9 个后端接口

| 路径 | 方法 | 说明 |
| --- | --- | --- |
| `/get_stats` | GET | 系统统计 |
| `/get_users` | GET | 用户列表 |
| `/add_user` | POST | 加用户 |
| `/delete_user` | POST | 删用户 |
| `/toggle_user_status` | POST | 切换启用状态 |
| `/restart_service` | POST | 重启服务 |
| `/get_logs` | GET | 拿日志 |
| `/backup_system` | POST | 触发备份 |

> ⚠️ 这 9 个接口是**插件内部调用**的路径约定，需要由 `mailbox_system_main.py` 转发到后端的 `/api/*`。注意它们和第九节列的 `/api/*` 不是同一套路由，改造时要自己对齐。

### 10.3 插件声明的权限

```
read_users         看用户
write_users        改用户
manage_services    管服务
view_logs          看日志
system_backup      备份
system_config      改配置
```

---

## 十一、AI 垃圾邮件过滤是怎么工作的

`ai-services/spam_detector.py` 里的 `SpamDetector` 类是这个项目的技术亮点，值得单独讲。

### 11.1 三个模型一起投票

| 模型 | 文件名 | 特点 |
| --- | --- | --- |
| 多项式朴素贝叶斯 | `naive_bayes.pkl` | 快，适合文本这种高维稀疏特征 |
| 随机森林 | `random_forest.pkl` | 抗过拟合，能抓非线性规则 |
| 逻辑回归 | `logistic_regression.pkl` | 输出概率平滑，阈值好调 |

`predict_spam()` 会调三个模型，各自出分，然后按权重合成最终概率。**单模型容易偏，多模型互相纠正更稳。**

### 11.2 中英文分开处理

- **英文**：NLTK 停用词表 + Porter 词干还原（`running` / `runs` / `ran` 归一）
- **中文**：jieba 分词（`垃圾邮件` → `垃圾` + `邮件`）

`_detect_language()` 会自动判断，不用手动指定。

### 11.3 关键词兜底

万一模型还没训练好或者遇到模型没见过的新型诈骗，关键词库能兜住：

```python
'zh': ['中奖', '恭喜', '免费', '赚钱', '贷款', '信用卡',
       '点击', '立即', '限时', '保证', '无风险', '优惠',
       '特价', '促销', '折扣', '返利', '投资', '理财']
'en': ['viagra', 'cialis', 'lottery', 'winner', 'congratulations',
       'free money', 'click here', 'urgent', 'limited time',
       'act now', 'guaranteed', 'risk free', 'no obligation',
       'credit card', 'loan', 'debt', 'refinance', 'mortgage']
```

### 11.4 没有训练数据怎么办

`_generate_training_data()` 会**自动生成**一套带噪声的训练样本，然后 `_train_models()` 现场训练。所以你**不需要**自己去下载垃圾邮件语料库，第一次跑起来它就能工作（当然，准确率不如真实语料，需要你用 `update_model()` 喂真实反馈慢慢调准）。

模型文件存在 `/opt/bt-mailbox/models/`，Redis 缓存默认在 `127.0.0.1:6379`。

### 11.5 手动调一次

```bash
cd /opt/bt-mailbox/ai-services
python3 spam_detector.py
```

或者调后端接口：

```bash
curl -X POST http://127.0.0.1:5000/api/ai/spam-check \
  -H "Authorization: Bearer <你的token>" \
  -H "Content-Type: application/json" \
  -d '{"sender":"unknown@spam.xyz","subject":"恭喜中奖","body":"点击链接立即领取"}'
```

---

## 十二、邮件服务器配置要点（Postfix / Dovecot）

### 12.1 Postfix 关键项（`mail-server/postfix/main.cf`）

| 配置 | 值 | 说明 |
| --- | --- | --- |
| `message_size_limit` | 52428800（50MB） | 单封邮件最大 50MB |
| `smtpd_use_tls` | yes | 开启 TLS |
| `smtpd_tls_security_level` | may | 有证书就连，不强求（**上线后建议改 `encrypt` 去掉明文**） |
| `smtpd_tls_protocols` | 排除 SSLv2/v3、TLSv1/1.1 | 只留 TLS 1.2+ |
| `virtual_mailbox_domains` | MySQL 查表 | 虚拟域名从数据库读 |
| `virtual_mailbox_base` | `/var/mail/vhosts` | 邮件存储路径 |
| `smtpd_sasl_type` | dovecot | 用 Dovecot 做 SMTP 认证（单一密码源） |
| `smtpd_sender_restrictions` | 含 `reject_unknown_sender_domain` | 防伪造发件人 |
| `smtpd_recipient_restrictions` | 含 `reject_unknown_recipient_domain` | 防邮件炸弹 |
| `smtpd_client_connection_count_limit` | 50 | 单 IP 最多 50 个并发连接 |
| `smtpd_client_connection_rate_limit` | 30 / 60s | 单 IP 每分钟最多 30 次连接 |
| `smtpd_client_message_rate_limit` | 100 | 单客户端发信速率上限 |
| `default_process_limit` | 100 | Postfix 进程数上限 |
| `milter_default_action` | accept | ⚠️ milter 挂了不拦邮件（保可用性，但要注意） |

### 12.2 Dovecot 关键项（`mail-server/dovecot/dovecot.conf`）

| 配置 | 值 | 说明 |
| --- | --- | --- |
| `protocols` | imap pop3 lmtp | 三种协议都开 |
| `ssl` | required | 强制加密 |
| `mail_location` | `maildir:/var/mail/vhosts/%d/%n` | 按域名和用户名分目录存信 |
| `first_valid_uid` / `last_valid_uid` | 5000 | 虚拟用户统一用 UID 5000 |
| `quota_rule` | `*:storage=1G` | 每个邮箱默认 1G 配额 |
| `quota_rule2` | `Trash:storage=+100M` | 回收站额外给 100M |
| `quota_warning` | 80% / 95% | 到 80%、95% 发提醒 |
| `fts` | lucene | 全文搜索引擎（Lucene） |
| `expire` | Trash / Spam | 回收站、垃圾箱自动过期清理 |
| `mail_plugins` | quota / sieve / imap_quota | 配额 + Sieve 规则 + IMAP 配额 |
| `mail_max_userip_connections` | 20（IMAP） | 防单 IP 疯狂连接 |
| `service doveadm` | 端口 12345 | 运维命令通道 |

### 12.3 ⚠️ 上线前必须改的几处

| 位置 | 现在是 | 应该改成 | 为什么 |
| --- | --- | --- | --- |
| `dovecot.conf` | `doveadm_password = {PLAIN}admin_password_here` | 换成你自己的强密码 | 这是个占位符！不改等于留了个空门 |
| `dovecot.conf` | `mail_replica = tcp:backup.example.com:12345` | 注释掉或换成真实备份机 | 备份功能默认是假的，指向一个不存在的地址 |
| `dovecot.conf` | `postmaster_address = postmaster@example.com` | 换成你自己的 | 只是回信地址 |
| `main.cf` | `debug_peer_level = 2` | 生产改 `0` | 调试日志会量大且慢 |
| `main.cf` | `smtpd_tls_security_level = may` | `encrypt` | 强制加密 |
| `.env` | 随机生成的 `JWT_SECRET` | 固定下来 | 多 worker 会 401 |

### 12.4 ⚠️ 部署脚本里已知的几个坑（实测读代码确认）

下面这些不是猜测，是把 `scripts/complete_deploy.sh` 和 `backend/app.py` 对着看之后发现的。**部署完请逐条检查**。

| # | 现象 | 原因 | 怎么修 |
| --- | --- | --- | --- |
| 1 | **管理员账号密码存的是假值** | `setup_mysql` 插入管理员时写的是 `'$2b$12$dummy_hash_will_be_updated'`（一个 bcrypt 占位串），**你在部署时输入的管理员密码根本没进数据库** | 见下面的「修复管理员密码」命令 |
| 2 | **`.env` 里没有 `EnvironmentFile`，后端读不到配置** | `deploy_backend` 生成的 systemd 单元**没有 `EnvironmentFile=` 这一行**，而 `backend/app.py` 也没有 `load_dotenv()`。所以 `SECRET_KEY` / `DATABASE_URL` / `JWT_SECRET_KEY` / `REDIS_URL` 全都读不到 | 在 `/etc/systemd/system/mailbox-backend.service` 的 `[Service]` 段加一行 `EnvironmentFile=/opt/bt-mailbox/backend/.env`，然后 `systemctl daemon-reload && systemctl restart mailbox-backend` |
| 3 | **Redis 连不上** | `setup_redis` 给 Redis 设了 `requirepass`，但 `backend/app.py:70` 和 `spam_detector.py:89` 都是 `redis.Redis(host='127.0.0.1', port=6379, db=0/2)`，**没带密码** | 在这两处加上 `password=os.getenv('REDIS_PASSWORD')`（AI 服务用 `db=2`，后端用 `db=0`，别搞混） |
| 4 | **Dovecot 登录校验对不上** | `dovecot-sql.conf.ext` 里 `default_pass_scheme = PBKDF2`，但后端 `set_password()` 用的是 Werkzeug 默认的 `scrypt` 哈希 | 把 `default_pass_scheme` 改成 `SCRYPT`（Werkzeug 2.3+ 默认就是 scrypt），或者在后端改用 `generate_password_hash(password, method='pbkdf2:sha256')` |
| 5 | **`/webmail` 打不开** | Nginx 配置里有 `location /webmail` 指向 `/www/wwwroot/${DOMAIN}/webmail` 和 PHP socket `php-cgi-74.sock`，但**脚本从来没装 RoundCube，也没建这个目录** | 自己装 RoundCube，或者把这段配置删掉 |
| 6 | **前端 `npm run build` 可能失败** | `package.json` 里 `vue-template-compiler` 是 `^2.7`（Vue 2 的编译器），但 `vue` 是 `^3.3`——**版本对不上** | 删掉 `vue-template-compiler` 这个依赖，Vue 3 用 `@vue/compiler-sfc` |
| 7 | **AI 服务缺依赖** | `deploy_ai_services` 装了 `tensorflow`（几个 GB），但 `spam_detector.py` 里**没有任何 tensorflow 的 import**，纯属浪费磁盘和时间 | 可以从部署步骤里去掉 tensorflow |
| 8 | **`mail_logs` 表要靠脚本建** | 后端有 `MailLog` 模型（`backend/app.py:137`），但表结构是 `setup_mysql` 用裸 SQL 建的，不是 ORM 建的 | 正常走脚本就没问题；若手工建库，记得照 `setup_mysql` 里的 SQL 补上 `mail_logs` |

**修复管理员密码（第 1 条）**：

```bash
cd /opt/bt-mailbox/backend
source venv/bin/activate
python3 -c "
from app import app, db, User
with app.app_context():
    u = User.query.filter_by(email='你的管理员邮箱').first()
    u.set_password('你想要的密码')
    db.session.commit()
    print('密码已更新')
"
```

**注意**：后端用 `backend/app.py` 里的 `init_db()` 还会自动建一个 `admin@example.com` / `admin123` 的账号（`backend/app.py:639`）。这个是**后端兜底逻辑**，只在 `__main__` 直接运行时触发。**部署完第一件事就是把这个默认账号删掉或者改掉密码。**

```sql
DELETE FROM users WHERE email = 'admin@example.com';
```

---

## 十三、日常运维命令速查

### 13.1 服务管理

```bash
systemctl status postfix dovecot redis-server nginx mailbox-backend
systemctl restart postfix
systemctl restart dovecot
systemctl restart mailbox-backend
systemctl restart nginx
```

### 13.2 看日志

```bash
# Postfix（发信）
tail -f /var/log/postfix.log

# Dovecot（收信）
tail -f /var/log/dovecot.log

# 应用日志
tail -f /var/log/mailbox/*.log

# 宝塔面板自己的错误日志
tail -f /www/server/panel/logs/error.log
```

### 13.3 备份与恢复

```bash
# 手动跑备份（部署时生成的脚本）
/opt/bt-mailbox/scripts/backup.sh

# 备份产物长这样
ls -la /opt/bt-mailbox/backup/20261111_020000/
# database.sql      ← 数据库
# mail_data.tar.gz  ← 所有邮件正文
# config.tar.gz     ← postfix / dovecot / 项目配置

# 恢复数据库
mysql -u mailbox_user -p mailbox_db < /opt/bt-mailbox/backup/20261111_020000/database.sql

# 恢复邮件数据
tar -xzf /opt/bt-mailbox/backup/20261111_020000/mail_data.tar.gz -C /
```

备份计划已经写进 crontab：每天 02:00 备份、03:00 轮转日志、每 10 分钟健康检查。

### 13.4 查用户

```bash
mysql -u mailbox_user -p mailbox_db -e "SELECT id,email,name,enabled,is_admin FROM users;"
mysql -u mailbox_user -p mailbox_db -e "SELECT id,domain,enabled FROM domains;"
```

### 13.5 清理队列（邮件发不出去时）

```bash
postqueue -p          # 看队列里有多少封
postqueue -f          # 强制立刻重试
postsuper -d ALL      # 删掉所有排队邮件
```

---

## 十四、常见问题排查

### 14.1 邮件发不出去

按这个顺序查：

1. **DNS 对不对** —— `dig MX 你的域名`，应该返回你的 `mail.xxx`；`dig A mail.xxx` 应该返回服务器 IP
2. **25 端口通不通** —— 在另一台机器上 `telnet 你的IP 25`，连不上就是云厂商封了
3. **SPF 有没有配** —— `dig TXT 你的域名`，缺 SPF 很容易被判垃圾
4. **看 Postfix 日志** —— `tail -f /var/log/postfix.log`，里面会明确写拒收原因
5. **队列堆积** —— `postqueue -p`

### 14.2 邮件收不到

1. **MX 记录** —— 跟上面一样，先 `dig MX`
2. **Dovecot 在跑吗** —— `systemctl status dovecot`
3. **防火墙** —— `ufw status` + 云安全组
4. **配额满了** —— 1G 配额用完信就进不来，`quota_rule = *:storage=1G`
5. **反垃圾规则误杀** —— 看 `/var/log/mail.log` 里有没有被 spamassassin 拦的记录

### 14.3 后台打不开

1. `curl http://127.0.0.1:5000/api/health` —— 后端活着没
2. `systemctl status nginx` —— Nginx 活着没
3. Nginx 的 `/api/` 反代配对没 —— `proxy_pass http://127.0.0.1:5000/api/;`
4. SSL 证书过期没 —— 宝塔里续签

### 14.4 登录报 401 / token 一直失效

**大概率是 JWT 密钥没被加载。** 后端读的是环境变量 `SECRET_KEY` / `JWT_SECRET_KEY`，但 `complete_deploy.sh` 生成的 systemd 单元**漏了 `EnvironmentFile=` 那一行**（见 12.4 第 2 条）。读不到就用默认值 `secrets.token_hex(32)`——**每次重启都变，而且 gunicorn 起的 4 个 worker 各有各的密钥**，所以登录时拿到的 token 发到别的 worker 就 401。

```bash
# 1. 检查 systemd 有没有加载 .env
grep EnvironmentFile /etc/systemd/system/mailbox-backend.service

# 2. 没有就加上
# 在 [Service] 段加：EnvironmentFile=/opt/bt-mailbox/backend/.env

# 3. 重新加载并重启
systemctl daemon-reload
systemctl restart mailbox-backend

# 4. 确认 .env 里有固定的值
grep -E 'SECRET_KEY|JWT_SECRET_KEY|DATABASE_URL' /opt/bt-mailbox/backend/.env
```

### 14.5 后端起不来 / 报数据库连接错误

大概率也是 `EnvironmentFile` 没加上，导致 `DATABASE_URL` 用了代码里的默认值 `mysql+pymysql://mailbox_user:mailbox_pass@localhost/mailbox_db`（注意密码是 `mailbox_pass`，**这是个假密码**）。

```bash
systemctl status mailbox-backend
journalctl -u mailbox-backend -n 50 --no-pager
```

### 14.6 AI 功能报错

1. **模型文件** —— `ls /opt/bt-mailbox/models/`，没有的话会现场训练，第一次启动慢是正常的
2. **NLTK 数据** —— `_download_nltk_data()` 需要联网下载；服务器没外网就手动下 `stopwords`、`punkt`、`punkt_tab`
3. **Redis 连不上** —— `redis-cli -a $REDIS_PASSWORD ping`，返回 `PONG` 才正常。注意后端代码里没带密码（见 12.4 第 3 条），后端日志会打 `Redis连接失败` 警告
4. **日志** —— `tail -f /var/log/mailbox/spam_detector.log`

### 14.7 注册接口返回「域名未启用」

`register()` 会检查域名在 `domains` 表里且 `enabled = true`。解决：

```bash
mysql -u mailbox_user -p mailbox_db -e \
  "INSERT INTO domains (domain, enabled) VALUES ('yourdomain.com', 1) ON DUPLICATE KEY UPDATE enabled=1;"
```

### 14.8 数据库连接错误（库名对不上）

`deploy.sh` 建的是 `bt_mailbox` 库，`complete_deploy.sh` 建的是 `mailbox_db`。用错库名会连不上。对照 `/opt/bt-mailbox/deployment_info.txt` 里的实际值。

```bash
mysql -u mailbox_user -p -e "SHOW DATABASES;"
```

---

## 十五、安全提醒（重要）

这一节请认真读，自建邮箱是**邮件服务里被攻击最频繁的类型**。

### 15.1 部署前

- [ ] **换一个强密码**。别用脚本默认生成的那一串（base64 可能有 `/`、`+`、`=` 之类的字符，某些配置文件里需要转义）。
- [ ] **改掉 `doveadm_password`**（第 12.3 节），这个占位符是绝对不能留的。
- [ ] **固定 `JWT_SECRET`**，别用随机默认值。
- [ ] **确认 25 端口没被云厂商封**，不然装完也白搭。

### 15.2 部署后

- [ ] **把 `/opt/bt-mailbox/deployment_info.txt` 存到密码管理器**，然后考虑删掉服务器上的副本（或改成 `chmod 600` 且确保只有你能 SSH）。
- [ ] **3306 和 6379 不要暴露到公网**。MySQL 和 Redis 只监听 `127.0.0.1`。
- [ ] **改 SSH 端口 + 禁用密码登录 + 用密钥**。
- [ ] **装 fail2ban** 挡暴力破解。
- [ ] **定期更新**：`apt update && apt upgrade -y`，Postfix/Dovecot 的安全更新很关键。
- [ ] **DNS 加 SPF + DKIM + DMARC**，这是防伪造和防进垃圾箱的关键三件套。
- [ ] **定期验证备份能恢复**。备份文件不等于能用的备份——定期演练恢复流程。

### 15.3 ⚠️ 关于「无限注册」

`/api/auth/register` 对外开放（5 次/分钟限流），意味着**任何人都能用你的域名注册邮箱账号**。这在某些场景是优点（专门收验证码），在某些场景是灾难（被拿去发垃圾邮件，你域名信誉直接报废）。

建议：

- 只开你自己要用的域名
- 配合 DKIM/SPF 严格配置
- 定期看 `mail-logs` 里有没有可疑的注册行为
- 域名信誉一旦坏了，修复要好几天，所以**别开放给不信任的人**

### 15.4 关于 SPF 的一票否决

**只发信不收信的域名** 可以用 `v=spf1 -all`（明确禁止任何服务器代表它发信）。

**又发又收信的域名** 用 `v=spf1 mx ~all`。别用 `+all`、`~all` 以外宽松的 `?all`，也别超过 10 次 DNS 查询（会触发 SPF permerror）。

### 15.5 版权与合规

- 自建邮箱本身合法。
- 但**给别人大量发信要谨慎**——《反垃圾邮件法》《CAN-SPAM Act》都有约束。
- 别用这个系统群发广告，你的域名 IP 会被拉黑，连收信都受影响。

---

## 十六、这个项目的现状说明（请先读）

这项目是**一个能跑起来的脚手架**，不是成熟商业产品。上手前心里有数：

| 部分 | 现状 |
| --- | --- |
| `backend/app.py` | ✅ 完整可用，JWT + 限流 + CRUD 都有 |
| `ai-services/spam_detector.py` | ✅ 完整可用，自带训练数据生成 |
| `scripts/complete_deploy.sh` | ✅ 流程完整可用，但**有 8 个已知坑**（见 12.4），部署后要逐条检查 |
| `deploy.sh` | ⚠️ **建议别用**：它部署的是**另一个简化版系统**（现场生成自己的 `app.py`、MD5 密码、无 JWT、无 AI），不是仓库里的 `backend/app.py` |
| `mail-server/*.cf` | ⚠️ 配置模板可用，**占位符必须替换**（见 12.3） |
| `frontend/` | ⚠️ Vue 工程骨架，`package.json` 里 `vue-template-compiler@^2.7` 和 Vue 3 混用，**构建会报错**，需要自己调 |
| `admin/index.html` | ✅ 单文件后台，能直接用 |
| `baota-plugin/` | ⚠️ 只带了 1 个模板，其他 7 个菜单的模板要自己补 |
| `docs/` 目录 | ❌ **不存在**，本 README 就是文档 |

**欢迎提 Issue 和 PR。** 特别是：真实环境下的部署踩坑记录、Postfix/Dovecot 的调优、AI 模型的调参经验、前端构建问题的修复 —— 这些都很有价值。

---

## 十七、致谢

- [Postfix](http://www.postfix.org/) —— 世界上最主流的邮件传输代理
- [Dovecot](https://www.dovecot.org/) —— IMAP / POP3 服务器
- [Flask](https://flask.palletsprojects.com/) —— Python Web 框架
- [Vue.js](https://vuejs.org/) —— 渐进式前端框架
- [Element Plus](https://element-plus.org/) —— Vue 3 组件库
- [ECharts](https://echarts.apache.org/) —— 图表可视化
- [scikit-learn](https://scikit-learn.org/) —— 机器学习
- [NLTK](https://www.nltk.org/) —— 自然语言工具包
- [jieba](https://github.com/fxsjy/jieba) —— 中文分词
- [宝塔面板](https://www.bt.cn/) —— 服务器管理面板

---

## 📄 许可证

MIT License，详见 [LICENSE](LICENSE) 文件。

**用之前请自己过一遍，也请遵守你所在地区的邮件服务相关法规。**
