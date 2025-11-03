# 日历整合和共享系统

一个强大的多日历源整合工具，能够从多个 CalDAV 日历源同步事件，合并成一个统一的日历，并通过 Web 服务提供订阅。

## 功能特性

- 🔄 **多源同步** - 支持从多个 CalDAV 服务器同步日历事件
- 🎯 **智能去重** - 基于时间、标题和位置自动去重事件
- 🌐 **Web 服务** - 提供 iCalendar 文件下载和 RESTful API
- 📋 **一键订阅** - Web 界面提供"订阅日历"按钮，点击自动复制订阅地址并弹窗提醒
- 💾 **数据持久化** - 支持 SQLite 和 JSON 两种存储方式
- ⏰ **自动同步** - 可配置的定时自动同步机制
- 📊 **监控统计** - 提供详细的同步统计和事件分析
- 🔒 **错误恢复** - 完善的错误处理和数据备份机制

## 快速开始

### 环境要求

- Python 3.8+
- 支持的 CalDAV 服务器（如 iCloud、Google Calendar、企业邮箱等）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置日历源

1. **创建配置文件**：复制 `cal_setting.json.example` 并重命名为 `cal_setting.json`
2. **编辑配置文件**，配置你的 CalDAV 服务器：

```json
[
  {
    "name": "公司邮箱",
    "url": "https://caldav.company.com/username",
    "username": "your_email@company.com",
    "password": "your_password"
  },
  {
    "name": "个人日历", 
    "url": "https://caldav.icloud.com/username",
    "username": "your_icloud_email",
    "password": "app_specific_password"
  }
]
```

**注意**：`cal_setting.json` 文件包含敏感信息，已被 `.gitignore` 忽略，不会被提交到代码仓库。请参考 `cal_setting.json.example` 文件创建你的配置。

### 启动服务

```bash
python main.py
```

服务启动后，访问 http://localhost:8056 查看管理界面。

## API 文档

### 获取整合日历文件

```
GET /calendar.ics
```

返回 iCalendar 格式的整合日历文件，可直接被日历应用订阅。

**响应**: `text/calendar` 文件

### 获取事件列表

```
GET /api/events?start_date=2024-01-01&end_date=2024-01-31&source=日历源名称
```

**查询参数**:
- `start_date` (可选): 开始日期过滤
- `end_date` (可选): 结束日期过滤  
- `source` (可选): 按日历源过滤

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "uid": "event-123456",
      "title": "团队会议",
      "start_time": "2024-01-15T10:00:00+08:00",
      "end_time": "2024-01-15T11:00:00+08:00",
      "location": "会议室A",
      "description": "每周团队例会",
      "source_calendar": "公司邮箱",
      "categories": ["会议", "团队"]
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### 手动触发同步

```
POST /api/sync
```

立即执行日历同步操作。

**响应**:
```json
{
  "success": true,
  "message": "同步完成",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### 获取统计信息

```
GET /api/stats
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_events": 150,
    "events_by_source": {
      "公司邮箱": 100,
      "个人日历": 50
    },
    "last_updated": "2024-01-15T10:00:00Z"
  }
}
```

## 客户端订阅

### 在日历应用中订阅

#### 一键复制订阅地址 (推荐)

1. 访问 Web 界面: `http://your-server:8056`
2. 点击"订阅日历"按钮
3. 订阅地址会自动复制到剪贴板，并显示提醒弹窗
4. 在您的日历应用中直接粘贴地址进行订阅

#### 手动输入订阅地址

1. **macOS 日历**:
   - 打开"日历"应用
   - 文件 → 新建日历订阅
   - 输入URL: `http://your-server:8056/calendar.ics`

2. **iOS 日历**:
   - 设置 → 日历 → 账户 → 添加账户
   - 选择"其他" → 添加CalDAV账户
   - 服务器: `your-server.com`
   - 端口: `8056`
   - 路径: `/calendar.ics`

3. **Google Calendar**:
   - 设置 → 添加日历 → 从URL导入
   - 输入: `http://your-server:8056/calendar.ics`

4. **Outlook**:
   - 日历视图 → 添加日历 → 从互联网订阅
   - 输入日历URL

### 支持的客户端

- ✅ Apple Calendar (macOS/iOS)
- ✅ Google Calendar
- ✅ Microsoft Outlook
- ✅ Thunderbird (Lightning)
- ✅ 任何支持 iCalendar 订阅的客户端

## 配置说明

### 主要配置项

在 `config.py` 中修改：

```python
# 服务器配置
HOST = '0.0.0.0'  # 监听地址
PORT = 8056        # 监听端口
DEBUG = True       # 调试模式

# 同步配置
SYNC_INTERVAL = 300      # 同步间隔（秒）
SYNC_RETRY_COUNT = 3     # 重试次数
SYNC_TIMEOUT = 30        # 请求超时（秒）

# 数据存储
DATA_DIR = './data'      # 数据目录
DATABASE_PATH = './data/calendars.db'  # 数据库路径
```

### 支持的 CalDAV 服务器

- **iCloud**: `https://caldav.icloud.com`
- **Google Calendar**: `https://apidata.googleusercontent.com/caldav/v2`
- **腾讯企业邮箱**: `https://exmail.qq.com/cgi-bin/caldav`
- **微软 Exchange**: 根据服务器配置
- **Zimbra**: `https://your-zimbra-server/home/username/Calendar`
- **Nextcloud**: `https://nextcloud-server/remote.php/dav`

## 部署指南

### 开发环境

```bash
# 克隆项目
git clone <repository-url>
cd calendar_merger

# 安装依赖
pip install -r requirements.txt

# 配置日历源
vim config.py

# 启动服务
python main.py
```

### 生产环境部署

#### 使用 systemd (Linux)

创建服务文件 `/etc/systemd/system/calendar-merger.service`:

```ini
[Unit]
Description=Calendar Merger Service
After=network.target

[Service]
Type=simple
User=calendar
WorkingDirectory=/opt/calendar-merger
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable calendar-merger
sudo systemctl start calendar-merger
```

#### 使用 Docker

创建 `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8056
CMD ["python", "main.py"]
```

构建和运行:
```bash
docker build -t calendar-merger .
docker run -d -p 8056:8056 --name calendar-merger calendar-merger
```

#### 使用 Docker Compose

在 docker 子目录运行 Docker Compose 部署：

```bash
cd docker
docker-compose up -d
```

该配置支持完整的数据卷映射：

```yaml
version: '3.8'

services:
  caldav-merger:
    build:
      context: ..  # 项目根目录作为构建上下文
      dockerfile: ./docker/Dockerfile
    container_name: caldav-merger
    ports:
      - "8056:8056"
    volumes:
      # 将配置文件映射到宿主机，便于修改
      - ../cal_setting.json:/app/cal_setting.json:ro
      # 将日志目录映射到宿主机
      - ../calendar_data:/app/calendar_data
      # 将数据库和备份目录映射到宿主机
      - ../data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    command: python main.py
```

## 故障排除

### 常见问题

1. **同步失败 404 错误**
   - 检查 CalDAV URL 是否正确
   - 验证用户名和密码
   - 确认服务器支持 CalDAV 协议

2. **事件重复**
   - 系统会自动去重，检查去重逻辑
   - 查看日志了解具体原因

3. **订阅不更新**
   - 客户端缓存问题，尝试手动刷新
   - 检查服务端同步状态

4. **性能问题**
   - 调整同步间隔
   - 检查网络连接
   - 查看数据库性能

### 日志查看

日志文件位于 `./calendar_data/application.log`，包含详细的操作记录和错误信息。

```bash
# 查看实时日志
tail -f ./calendar_data/application.log

# 搜索错误信息
grep "ERROR" ./calendar_data/application.log
```

### 数据备份

系统会自动创建数据备份，位于 `./data/backups/` 目录。

手动备份:
```bash
# 备份数据库
cp ./data/calendars.db ./backups/calendars.db.backup

# 导出事件为JSON
curl http://localhost:8000/api/events > events_backup.json
```

## 项目结构

```
caldav/
├── main.py                    # 主程序入口
├── config.py                  # 项目配置文件
├── cal_setting.json           # CalDAV服务器配置文件（已忽略）
├── cal_setting.json.example   # CalDAV配置文件示例
├── requirements.txt           # 依赖列表
├── .gitignore                 # Git忽略配置
├── docker/                    # Docker部署相关文件
│   ├── Dockerfile             # Docker镜像构建文件
│   ├── docker-compose.yml     # Docker Compose配置文件
│   ├── DOCKER-DEPLOYMENT.md   # Docker部署详细指南
│   └── docker-readme.md       # Docker简明使用说明
├── storage/                   # 数据存储模块
│   ├── base.py                # 存储基类
│   ├── sqlite_storage.py      # SQLite 实现
│   └── json_storage.py        # JSON 实现
├── merger/                    # 日历合并模块
│   └── calendar_merger.py     # 日历合并器核心逻辑
├── server/                    # Web 服务器模块
│   └── web_server.py          # Flask Web服务器实现
└── data/                      # 数据目录（自动创建）
    ├── calendars.db           # SQLite数据库文件
    └── backups/               # 备份文件目录
```

## 开发指南

### 添加新的存储后端

继承 `BaseCalendarStorage` 类并实现所有抽象方法：

```python
from storage.base import BaseCalendarStorage

class MySQLCalendarStorage(BaseCalendarStorage):
    def __init__(self, connection_string):
        # 初始化连接
        pass
    
    def save_events(self, events):
        # 实现保存逻辑
        pass
    
    # 实现其他方法...
```

### 扩展日历源支持

在 `CalendarMerger` 类中添加新的日历源类型支持：

```python
def fetch_custom_calendar(self, custom_config):
    # 实现自定义日历源的获取逻辑
    pass
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请：
1. 查看本文档的故障排除部分
2. 检查日志文件中的错误信息
3. 提交 GitHub Issue
4. 联系开发团队

## 版本历史

- v1.0.0 (2025-11-2)
  - 初始版本发布
  - 支持多 CalDAV 源同步
  - 提供 Web 订阅服务
  - SQLite 数据存储