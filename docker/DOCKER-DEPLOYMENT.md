# CalDAV 日历合并服务 Docker 部署指南

## 项目结构

```
caldav/
├── Dockerfile                 # Docker 构建文件
├── docker-compose.yml         # Docker Compose 配置
├── cal_setting.json          # CalDAV 服务器配置文件（需手动创建）
├── main.py                   # 主程序
├── config.py                 # 配置文件
├── merger/                   # 日历合并模块
├── server/                   # Web 服务器模块
├── storage/                  # 数据存储模块
├── calendar_data/            # 日志目录 (容器映射)
├── data/                     # 数据目录 (容器映射)
└── requirements.txt          # Python 依赖
```

## Dockerfile 说明

使用 Python 3.12-slim 作为基础镜像，安装依赖并设置工作目录：

```dockerfile
# 使用官方 Python 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据和日志目录
RUN mkdir -p /app/data /app/calendar_data

# 暴露端口
EXPOSE 8056

# 设置启动命令
CMD ["python", "main.py"]
```

## Docker Compose 配置

docker-compose.yml 提供了卷映射和端口映射：

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

## 部署步骤

### 1. 准备环境

确保您的系统已安装 Docker 和 Docker Compose。

### 2. 配置 CalDAV 服务器

创建 `cal_setting.json` 文件，配置您的 CalDAV 服务器信息：

```json
[
  {
    "name": "个人日历",
    "url": "https://caldav.example.com",
    "username": "your-username",
    "password": "your-password"
  }
]
```

### 3. 启动服务

```bash
# 构建并启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 数据持久化

容器的以下目录已映射到宿主机：

- **配置文件**: `./cal_setting.json` → Container: `/app/cal_setting.json` (只读)
- **日志目录**: `./calendar_data/` → Container: `/app/calendar_data/`
- **数据目录**: `./data/` → Container: `/app/data/`

这些映射确保了：

1. 配置文件可以直接在宿主机上修改，便于调整 CalDAV 服务器设置
2. 日志文件可以持久保存在宿主机上，便于问题排查
3. 数据库文件和备份文件持久保存在宿主机上，防止数据丢失

## 常用管理命令

```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看服务日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 重启服务
docker-compose restart

# 查看容器资源使用情况
docker stats caldav-merger
```

## 故障排除

### 服务启动失败

检查日志：
```bash
docker-compose logs
```

### 配置文件修改后不生效

配置文件是只读映射的，修改后需要重启容器：
```bash
docker-compose restart
```

### 端口冲突

如果端口 8056 已被占用，在 docker-compose.yml 中修改端口映射：
```yaml
ports:
  - "8080:8056"  # 将宿主机端口改为 8080
```

## 访问服务

服务启动后，可以通过以下地址访问：

- **Web 界面**: http://localhost:8056
- **日历订阅**: http://localhost:8056/calendar.ics
- **API 接口**: http://localhost:8056/api/events

## 安全建议

1. 将 `cal_setting.json` 中的敏感信息保护好
2. 考虑使用环境变量替代硬编码的密码
3. 在生产环境中配置 HTTPS 反向代理
4. 定期备份 `/data` 目录中的数据库文件

## 更新服务

当需要更新应用代码时：

```bash
# 1. 停止当前服务
docker-compose down

# 2. 更新代码
git pull  # 或复制新的代码文件

# 3. 重新构建并启动
docker-compose up -d --build
```