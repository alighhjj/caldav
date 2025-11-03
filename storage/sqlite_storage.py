import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import BaseCalendarStorage
import logging

logger = logging.getLogger(__name__)

class SQLiteCalendarStorage(BaseCalendarStorage):
    """SQLite 日历存储实现"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 事件主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT,
                description TEXT,
                source_calendar TEXT NOT NULL,
                source_event_id TEXT,
                created_time TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                recurrence_rule TEXT,
                organizer TEXT,
                status TEXT DEFAULT 'confirmed',
                categories TEXT,
                priority INTEGER DEFAULT 0,
                metadata TEXT,
                is_deleted INTEGER DEFAULT 0,
                UNIQUE(uid)
            )
        ''')
        
        # 参与者表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_uid TEXT NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                role TEXT DEFAULT 'REQ-PARTICIPANT',
                status TEXT DEFAULT 'NEEDS-ACTION',
                FOREIGN KEY (event_uid) REFERENCES events (uid) ON DELETE CASCADE
            )
        ''')
        
        # 同步日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_time TEXT NOT NULL,
                source_calendar TEXT NOT NULL,
                events_fetched INTEGER DEFAULT 0,
                events_processed INTEGER DEFAULT 0,
                errors TEXT,
                duration_seconds REAL
            )
        ''')
        
        # 错误日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                module TEXT,
                message TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_uid ON events(uid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON events(start_time, end_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_calendar)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_deleted ON events(is_deleted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendees_event ON attendees(event_uid)')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def save_events(self, events: List[Dict]) -> bool:
        """保存事件列表到数据库"""
        if not events:
            return True
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        success_count = 0
        
        for event in events:
            try:
                # 插入或更新事件
                cursor.execute('''
                    INSERT OR REPLACE INTO events (
                        uid, title, start_time, end_time, location, description,
                        source_calendar, source_event_id, created_time, last_updated,
                        recurrence_rule, organizer, status, categories, priority, metadata, is_deleted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, ?), ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.get('uid'),
                    event.get('title', ''),
                    event.get('start_time'),
                    event.get('end_time'),
                    event.get('location', ''),
                    event.get('description', ''),
                    event.get('source_calendar', 'unknown'),
                    event.get('source_event_id'),
                    event.get('created_time'),
                    current_time,
                    current_time,
                    event.get('recurrence_rule'),
                    event.get('organizer'),
                    event.get('status', 'confirmed'),
                    json.dumps(event.get('categories', []), ensure_ascii=False),
                    event.get('priority', 0),
                    json.dumps(event.get('metadata', {}), ensure_ascii=False),
                    0  # is_deleted
                ))
                
                # 处理参与者
                attendees = event.get('attendees', [])
                cursor.execute('DELETE FROM attendees WHERE event_uid = ?', (event.get('uid'),))
                
                for attendee in attendees:
                    if isinstance(attendee, str):
                        cursor.execute('''
                            INSERT INTO attendees (event_uid, email) VALUES (?, ?)
                        ''', (event.get('uid'), attendee))
                    else:
                        cursor.execute('''
                            INSERT INTO attendees (event_uid, email, name, role, status)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            event.get('uid'),
                            attendee.get('email', ''),
                            attendee.get('name', ''),
                            attendee.get('role', 'REQ-PARTICIPANT'),
                            attendee.get('status', 'NEEDS-ACTION')
                        ))
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"保存事件失败 {event.get('uid')}: {e}")
                self._log_error('save_events', f"保存事件失败 {event.get('uid')}", str(e))
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"成功保存 {success_count}/{len(events)} 个事件")
        return success_count > 0
    
    def load_events(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None,
                   source_calendar: Optional[str] = None) -> List[Dict]:
        """从数据库加载事件"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM events WHERE is_deleted = 0"
        params = []
        
        if start_date:
            query += " AND end_time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date)
        
        if source_calendar:
            query += " AND source_calendar = ?"
            params.append(source_calendar)
        
        query += " ORDER BY start_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            try:
                event = dict(row)
                
                # 解析JSON字段
                if event['categories']:
                    event['categories'] = json.loads(event['categories'])
                else:
                    event['categories'] = []
                    
                if event['metadata']:
                    event['metadata'] = json.loads(event['metadata'])
                else:
                    event['metadata'] = {}
                
                # 加载参与者
                cursor.execute('SELECT * FROM attendees WHERE event_uid = ?', (event['uid'],))
                attendees = [dict(attendee) for attendee in cursor.fetchall()]
                event['attendees'] = attendees
                
                events.append(event)
            except Exception as e:
                logger.error(f"解析事件失败 {row['uid']}: {e}")
                continue
        
        conn.close()
        return events
    
    def delete_event(self, event_uid: str) -> bool:
        """软删除事件"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE events SET is_deleted = 1, last_updated = ? WHERE uid = ?',
                (datetime.now().isoformat(), event_uid)
            )
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除事件失败 {event_uid}: {e}")
            return False
    
    def get_event(self, event_uid: str) -> Optional[Dict]:
        """获取单个事件"""
        events = self.load_events()
        for event in events:
            if event['uid'] == event_uid:
                return event
        return None
    
    def backup(self) -> str:
        """创建数据库备份"""
        try:
            backup_path = f"{self.db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conn = self._get_connection()
            backup_conn = sqlite3.connect(backup_path)
            
            conn.backup(backup_conn)
            
            conn.close()
            backup_conn.close()
            
            logger.info(f"数据库备份已创建: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总事件数
        cursor.execute('SELECT COUNT(*) FROM events WHERE is_deleted = 0')
        stats['total_events'] = cursor.fetchone()[0]
        
        # 按来源统计
        cursor.execute('''
            SELECT source_calendar, COUNT(*) 
            FROM events WHERE is_deleted = 0 
            GROUP BY source_calendar
        ''')
        stats['events_by_source'] = dict(cursor.fetchall())
        
        # 最近同步时间
        cursor.execute('''
            SELECT MAX(sync_time) FROM sync_logs 
            WHERE errors IS NULL OR errors = ''
        ''')
        stats['last_sync'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def _log_error(self, module: str, message: str, details: str = ""):
        """记录错误日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs (timestamp, module, message, details)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), module, message, details))
        
        conn.commit()
        conn.close()