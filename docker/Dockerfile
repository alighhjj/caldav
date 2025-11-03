# 使用官方 Python 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 配置 pip 使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（从项目根目录）
COPY . .

# 创建数据和日志目录
RUN mkdir -p /app/data /app/calendar_data

# 暴露端口
EXPOSE 8056

# 设置启动命令
CMD ["python", "main.py"]