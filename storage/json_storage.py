import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import BaseCalendarStorage
import logging

logger = logging.getLogger(__name__)

class JSONCalendarStorage(BaseCalendarStorage):
    """JSON 文件存储实现（用于备份和简单场景）"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.latest_file = os.path.join(storage_dir, 'calendar_events_latest.json')
    
    def save_events(self, events: List[Dict]) -> bool:
        """保存事件到JSON文件"""
        try:
            data = {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "total_events": len(events),
                    "source_calendars": list(set(
                        event.get('source_calendar', 'unknown') for event in events
                    ))
                },
                "events": events
            }
            
            # 保存最新版本
            with open(self.latest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 创建时间戳备份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.storage_dir, f'backup_{timestamp}.json')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(events)} 个事件到 JSON")
            return True
            
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            return False
    
    def load_events(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None,
                   source_calendar: Optional[str] = None) -> List[Dict]:
        """从JSON文件加载事件"""
        if not os.path.exists(self.latest_file):
            return []
        
        try:
            with open(self.latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            events = data.get("events", [])
            
            # 过滤事件
            filtered_events = []
            for event in events:
                # 时间过滤
                if start_date and event.get('end_time', '') < start_date:
                    continue
                if end_date and event.get('start_time', '') > end_date:
                    continue
                # 来源过滤
                if source_calendar and event.get('source_calendar') != source_calendar:
                    continue
                
                filtered_events.append(event)
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            return []
    
    def delete_event(self, event_uid: str) -> bool:
        """从JSON中删除事件"""
        events = self.load_events()
        original_count = len(events)
        
        events = [event for event in events if event.get('uid') != event_uid]
        
        if len(events) < original_count:
            return self.save_events(events)
        return False
    
    def get_event(self, event_uid: str) -> Optional[Dict]:
        """获取单个事件"""
        events = self.load_events()
        for event in events:
            if event.get('uid') == event_uid:
                return event
        return None
    
    def backup(self) -> str:
        """创建备份（JSON存储本身就是备份）"""
        return self.latest_file
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        events = self.load_events()
        
        stats = {
            'total_events': len(events),
            'events_by_source': {},
            'last_updated': None
        }
        
        # 按来源统计
        for event in events:
            source = event.get('source_calendar', 'unknown')
            stats['events_by_source'][source] = stats['events_by_source'].get(source, 0) + 1
        
        # 获取最新更新时间
        if os.path.exists(self.latest_file):
            stats['last_updated'] = datetime.fromtimestamp(
                os.path.getmtime(self.latest_file)
            ).isoformat()
        
        return stats