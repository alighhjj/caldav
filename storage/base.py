from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class BaseCalendarStorage(ABC):
    """日历存储基础接口"""
    
    @abstractmethod
    def save_events(self, events: List[Dict]) -> bool:
        """保存事件列表"""
        pass
    
    @abstractmethod
    def load_events(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None,
                   source_calendar: Optional[str] = None) -> List[Dict]:
        """加载事件列表"""
        pass
    
    @abstractmethod
    def delete_event(self, event_uid: str) -> bool:
        """删除事件"""
        pass
    
    @abstractmethod
    def get_event(self, event_uid: str) -> Optional[Dict]:
        """获取单个事件"""
        pass
    
    @abstractmethod
    def backup(self) -> str:
        """创建备份"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass