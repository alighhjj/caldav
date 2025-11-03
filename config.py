import os
import json
from datetime import timedelta

class Config:
    # 基础配置
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8056
    
    # 数据存储配置
    DATA_DIR = './data'
    DATABASE_PATH = os.path.join(DATA_DIR, 'calendars.db')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # 日历同步配置
    SYNC_INTERVAL = 300  # 5分钟
    SYNC_RETRY_COUNT = 3
    SYNC_TIMEOUT = 30
    
    # 从配置文件中读取 CalDAV 服务器配置
    @staticmethod
    def _load_caldav_servers():
        setting_file = 'cal_setting.json'
        if os.path.exists(setting_file):
            with open(setting_file, 'r', encoding='utf-8') as f:
                servers = json.load(f)
                # 验证配置项并保持与原格式一致
                validated_servers = []
                for server in servers:
                    if 'url' in server and 'username' in server and 'password' in server:
                        validated_server = {
                            'name': server.get('name', server['username']),
                            'url': server['url'],
                            'username': server['username'],
                            'password': server['password']
                        }
                        validated_servers.append(validated_server)
                return validated_servers
        # 如果配置文件不存在，返回空列表
        return []
    
    CALDAV_SERVERS = _load_caldav_servers()
    
    # Web 服务配置
    WEB_TITLE = "整合日历服务"
    WEB_DESCRIPTION = "多个日历源整合服务"
    
    # 安全配置
    ALLOWED_HOSTS = ['*']
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 创建必要的目录
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.BACKUP_DIR, exist_ok=True)