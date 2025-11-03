# CalDAV 日历合并服务 Docker 版

## 项目简介

这是一个 CalDAV 日历合并服务，可以从多个 CalDAV 服务器获取事件并合并到一个统一的日历中，通过 Web 接口提供订阅功能。

## 快速开始

### 1. 准备配置文件

在项目根目录下创建 `cal_setting.json` 文件，配置您的 CalDAV 服务器信息：

```json
[
  {
    "name": "日历1",
    "url": "https://your-caldav-server.com",
    "username": "your-username",
    "password": "your-password"
  },
  {
    "name": "日历2", 
    "url": "https://another-caldav-server.com",
    "username": "another-username",
    "password": "another-password"
  }
]
```

### 2. 启动服务

使用 Docker Compose 启动服务：

```bash
docker-compose up -d
```

### 3. 访问服务

服务启动后，可以通过以下地址访问：

- Web 界面: `http://localhost:8056`
- 日历订阅: `http://localhost:8056/calendar.ics`
- API 接口: `http://localhost:8056/api/events`

## 数据卷说明

容器中的以下目录已映射到宿主机：

- `/app/cal_setting.json` → `./cal_setting.json` (只读，便于修改配置)
- `/app/calendar_data` → `./calendar_data` (日志文件)
- `/app/data` → `./data` (数据库和备份文件)

## 手动构建和运行

如果不使用 docker-compose，也可以手动构建和运行：

```bash
# 构建镜像
docker build -t caldav-merger .

# 运行容器
docker run -d \
  --name caldav-merger \
  -p 8056:8056 \
  -v $(pwd)/cal_setting.json:/app/cal_setting.json:ro \
  -v $(pwd)/calendar_data:/app/calendar_data \
  -v $(pwd)/data:/app/data \
  caldav-merger
```

## 管理命令

```bash
# 查看日志
docker logs caldav-merger

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 进入容器
docker exec -it caldav-merger bash
```

## 注意事项

1. 确保 `cal_setting.json` 文件存在且格式正确
2. 容器启动后会自动开始同步日历事件
3. 同步间隔可在 `config.py` 中调整（默认为 300 秒）
4. 修改配置文件后需要重启容器才能生效