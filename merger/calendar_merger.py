import caldav
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time
from config import Config

logger = logging.getLogger(__name__)

class CalendarMerger:
    """日历合并器"""
    
    def __init__(self, storage):
        self.storage = storage
        self.source_calendars = []
        self.setup_calendar_sources()
    
    def setup_calendar_sources(self):
        """设置日历源"""
        for server_config in Config.CALDAV_SERVERS:
            try:
                client = caldav.DAVClient(
                    url=server_config['url'],
                    username=server_config['username'],
                    password=server_config['password'],
                    timeout=Config.SYNC_TIMEOUT
                )
                
                # 测试连接
                principal = client.principal()
                calendars = principal.calendars()
                
                if calendars:
                    self.source_calendars.append({
                        'name': server_config['name'],
                        'client': client,
                        'calendar': calendars[0],
                        'config': server_config
                    })
                    logger.info(f"成功连接日历源: {server_config['name']}")
                else:
                    logger.warning(f"日历源 {server_config['name']} 没有找到日历")
                    
            except Exception as e:
                logger.error(f"连接日历源失败 {server_config['name']}: {e}")
    
    def fetch_events_from_source(self, source: Dict, days: int = 30) -> List[Dict]:
        """从单个日历源获取事件"""
        events = []
        try:
            calendar = source['calendar']
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            # 搜索事件
            caldav_events = calendar.search(
                start=start_date,
                end=end_date,
                event=True
            )
            
            for caldav_event in caldav_events:
                try:
                    ical_component = caldav_event.icalendar_component
                    if not ical_component:
                        continue
                    
                    # 转换为统一格式
                    event_data = self._parse_ical_event(ical_component, source['name'])
                    if event_data:
                        events.append(event_data)
                        
                except Exception as e:
                    logger.error(f"解析事件失败: {e}")
                    continue
            
            logger.info(f"从 {source['name']} 获取到 {len(events)} 个事件")
            
        except Exception as e:
            logger.error(f"从 {source['name']} 获取事件失败: {e}")
        
        return events
    
    def _parse_ical_event(self, ical_event, source_name: str) -> Optional[Dict]:
        """解析 iCalendar 事件为统一格式"""
        try:
            # 基础信息
            uid = str(ical_event.get('uid', ''))
            if not uid:
                uid = f"generated-{int(time.time())}-{hash(str(ical_event))}"
            
            title = str(ical_event.get('summary', '未命名事件'))
            
            # 时间处理
            start_time = ical_event.get('dtstart')
            end_time = ical_event.get('dtend')
            
            if not start_time:
                return None
                
            start_time_str = start_time.dt.isoformat()
            end_time_str = end_time.dt.isoformat() if end_time else start_time_str
            
            # 其他信息
            location = str(ical_event.get('location', '未指定'))
            description = str(ical_event.get('description', ''))
            organizer = str(ical_event.get('organizer', ''))
            status = str(ical_event.get('status', 'confirmed'))
            
            # 参与者
            attendees = []
            for attendee in ical_event.get('attendee', []):
                if hasattr(attendee, 'params') and 'CN' in attendee.params:
                    attendees.append({
                        'email': str(attendee),
                        'name': attendee.params['CN']
                    })
                else:
                    attendees.append(str(attendee))
            
            # 分类
            categories = []
            for category in ical_event.get('categories', []):
                if hasattr(category, 'cats'):
                    categories.extend(category.cats)
                else:
                    categories.append(str(category))
            
            return {
                'uid': uid,
                'title': title,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'location': location,
                'description': description,
                'source_calendar': source_name,
                'source_event_id': uid,
                'created_time': datetime.now().isoformat(),
                'organizer': organizer,
                'status': status,
                'categories': categories,
                'attendees': attendees,
                'metadata': {
                    'original_calendar': source_name,
                    'parsed_time': datetime.now().isoformat(),
                    'recurrence': bool(ical_event.get('rrule'))
                }
            }
            
        except Exception as e:
            logger.error(f"解析 iCal 事件失败: {e}")
            return None
    
    def merge_all_events(self) -> bool:
        """合并所有日历源的事件"""
        all_events = []
        sync_start = datetime.now()
        
        for source in self.source_calendars:
            try:
                events = self.fetch_events_from_source(source)
                all_events.extend(events)
                logger.info(f"从 {source['name']} 合并了 {len(events)} 个事件")
            except Exception as e:
                logger.error(f"合并 {source['name']} 事件失败: {e}")
                continue
        
        # 去重处理
        unique_events = self._remove_duplicates(all_events)
        
        # 保存到存储
        if self.storage.save_events(unique_events):
            sync_duration = (datetime.now() - sync_start).total_seconds()
            logger.info(f"同步完成: 共 {len(unique_events)} 个事件, 耗时 {sync_duration:.2f}秒")
            return True
        else:
            logger.error("保存合并后的事件失败")
            return False
    
    def _remove_duplicates(self, events: List[Dict]) -> List[Dict]:
        """基于关键信息去重"""
        seen = set()
        unique_events = []
        
        for event in events:
            # 创建唯一标识键
            key = (
                event.get('title', ''),
                event.get('start_time', ''),
                event.get('location', ''),
                event.get('source_calendar', '')
            )
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        logger.info(f"去重后剩余 {len(unique_events)} 个事件 (原 {len(events)} 个)")
        return unique_events
    
    def generate_icalendar(self) -> str:
        """生成 iCalendar 格式数据"""
        events = self.storage.load_events()
        
        # 创建日历
        calendar = Calendar()
        calendar.add('prodid', '-//Calendar Merger//example.com//')
        calendar.add('version', '2.0')
        calendar.add('x-wr-calname', '整合日历')
        calendar.add('x-wr-caldesc', '多个日历源整合')
        calendar.add('x-wr-timezone', 'Asia/Shanghai')
        
        # 添加事件
        for event_data in events:
            event = Event()
            event.add('uid', event_data['uid'])
            event.add('summary', event_data['title'])
            event.add('dtstart', datetime.fromisoformat(event_data['start_time']))
            event.add('dtend', datetime.fromisoformat(event_data['end_time']))
            
            if event_data['location'] and event_data['location'] != '未指定':
                event.add('location', event_data['location'])
            
            if event_data['description']:
                event.add('description', event_data['description'])
            
            event.add('status', event_data.get('status', 'CONFIRMED'))
            
            # 添加分类
            if event_data['categories']:
                event.add('categories', event_data['categories'])
            
            # 添加来源信息
            event.add('x-source-calendar', event_data['source_calendar'])
            
            calendar.add_component(event)
        
        return calendar.to_ical().decode('utf-8')