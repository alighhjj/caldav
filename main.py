#!/usr/bin/env python3
"""
日历整合和共享系统主程序
"""

import logging
import threading
import time
import signal
import sys
import os
from datetime import datetime

from config import Config
from storage.sqlite_storage import SQLiteCalendarStorage
from storage.json_storage import JSONCalendarStorage
from merger.calendar_merger import CalendarMerger
from server.web_server import CalendarWebServer

# 确保日志目录存在
log_dir = './calendar_data'
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./calendar_data/application.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CalendarService:
    """日历服务主类"""
    
    def __init__(self):
        self.running = False
        self.storage = None
        self.merger = None
        self.server = None
        self.sync_thread = None
        
    def initialize(self):
        """初始化服务"""
        logger.info("正在初始化日历服务...")
        
        try:
            # 初始化存储
            self.storage = SQLiteCalendarStorage(Config.DATABASE_PATH)
            logger.info("存储系统初始化完成")
            
            # 初始化日历合并器
            self.merger = CalendarMerger(self.storage)
            logger.info("日历合并器初始化完成")
            
            # 初始化 Web 服务器
            self.server = CalendarWebServer(self.storage, self.merger)
            logger.info("Web 服务器初始化完成")
            
            # 执行初始同步
            logger.info("执行初始日历同步...")
            self.merger.merge_all_events()
            
            return True
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            return False
    
    def start_sync_scheduler(self):
        """启动定时同步"""
        def sync_worker():
            while self.running:
                try:
                    logger.info("开始定时同步...")
                    self.merger.merge_all_events()
                    logger.info(f"定时同步完成，等待 {Config.SYNC_INTERVAL} 秒")
                except Exception as e:
                    logger.error(f"定时同步失败: {e}")
                
                # 等待下次同步
                for _ in range(Config.SYNC_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.sync_thread = threading.Thread(target=sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        logger.info(f"定时同步已启动，间隔: {Config.SYNC_INTERVAL} 秒")
    
    def start(self):
        """启动服务"""
        if not self.initialize():
            logger.error("初始化失败，服务无法启动")
            return False
        
        self.running = True
        
        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info("收到停止信号，正在关闭服务...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动定时同步
        self.start_sync_scheduler()
        
        # 启动 Web 服务器
        logger.info(f"启动 Web 服务器: http://{Config.HOST}:{Config.PORT}")
        try:
            self.server.run(debug=Config.DEBUG, use_reloader=False)
        except Exception as e:
            logger.error(f"Web 服务器启动失败: {e}")
            self.stop()
        
        return True
    
    def stop(self):
        """停止服务"""
        logger.info("正在停止日历服务...")
        self.running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        
        logger.info("日历服务已停止")

def main():
    """主函数"""
    service = CalendarService()
    
    try:
        if service.start():
            logger.info("日历服务启动成功")
        else:
            logger.error("日历服务启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断服务")
        service.stop()
    except Exception as e:
        logger.error(f"服务运行异常: {e}")
        service.stop()
        sys.exit(1)

if __name__ == '__main__':
    main()