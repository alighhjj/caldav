import json
import caldav
from datetime import datetime
import os

def load_settings():
    """从 cal_setting.json 文件加载 CalDAV 设置"""
    with open('cal_setting.json', 'r', encoding='utf-8') as f:
        settings_data = json.load(f)
    
    # 如果配置是单个对象，转换为列表
    if isinstance(settings_data, dict):
        return [settings_data]
    # 如果配置是列表，直接返回
    elif isinstance(settings_data, list):
        return settings_data
    else:
        raise ValueError("配置文件格式错误，应为对象或对象数组")

def connect_to_caldav(settings):
    """建立与 CalDAV 服务器的连接"""
    client = caldav.DAVClient(
        url=settings.get('caldav_url') or settings.get('url'),
        username=settings.get('username'),
        password=settings.get('password')
    )
    return client

def get_calendar(client, calendar_name):
    """根据名称获取指定日历"""
    principal = client.principal()
    calendars = principal.calendars()
    
    for calendar in calendars:
        if calendar.name == calendar_name:
            return calendar
    
    # 如果未找到特定日历，则返回第一个日历
    if calendars:
        print(f"未找到日历 '{calendar_name}'。使用第一个可用日历: {calendars[0].name}")
        return calendars[0]
    
    return None

def fetch_events(calendar, start_date=None, end_date=None):
    """从日历中获取事件"""
    if start_date is None:
        # 默认从今天开始获取事件
        start_date = datetime.now()
    if end_date is None:
        # 默认获取未来30天的事件
        from datetime import timedelta
        end_date = start_date + timedelta(days=30)
    
    # 使用推荐的搜索方法并设置正确参数
    events = calendar.search(start=start_date, end=end_date, event=True)
    return events

def parse_event(event):
    """解析单个日历事件并提取相关信息"""
    try:
        # 获取事件的原始数据（根据caldav库的API）
        event_data = event.data if hasattr(event, 'data') else event._data
        
        # 使用icalendar库解析数据
        from icalendar import Calendar
        ical = Calendar.from_ical(event_data)
        
        # 获取第一个组件（通常是VEVENT）
        component = None
        for comp in ical.walk():
            if comp.name == "VEVENT":
                component = comp
                break
                
        if component is None:
            print(f"事件 {event.id} 中没有找到 VEVENT 组件")
            return None
        
        event_info = {
            'id': event.id,
            'name': str(component.get('summary', '无标题')),
            'start': component.get('dtstart').dt if component.get('dtstart') else None,
            'end': component.get('dtend').dt if component.get('dtend') else None,
            'location': str(component.get('location', '')),
            'description': str(component.get('description', '')),
            'created': component.get('created').dt if component.get('created') else None,
            'last_modified': component.get('last-modified').dt if component.get('last-modified') else None
        }
        
        return event_info
    except Exception as e:
        print(f"解析事件 {event.id} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数，运行 CalDAV 客户端"""
    try:
        print("正在加载 CalDAV 设置...")
        config_list = load_settings()
        print(f"找到 {len(config_list)} 个配置")
        
        for i, settings in enumerate(config_list):
            url = settings.get('caldav_url') or settings.get('url') or 'Unknown URL'
            username = settings.get('username') or 'Unknown User'
            print(f"\n正在处理第 {i+1} 个配置: {url}, {username}")
            
            try:
                print("正在连接到 CalDAV 服务器...")
                client = connect_to_caldav(settings)
                print("成功连接到 CalDAV 服务器")
                
                # 生成基于配置信息的唯一时间戳
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                username = settings.get('username') or 'unknown'
                config_id = f"{username.replace('@', '_').replace('.', '_')}_{i+1}"
                
                # 保存客户端对象信息
                client_info = {
                    "server_url": str(client.url),
                    "server_info": str(client.server_info) if hasattr(client, 'server_info') else "Not available",
                    "data": client,
                    "principal": client.principal(),
                    "calendars": [cal.name for cal in client.principal().calendars()],
                    "config_index": i+1,
                    "username": settings.get('username') or 'unknown'
                }
                
                with open(f"client_info_{config_id}_{timestamp}.json", 'w', encoding='utf-8') as f:
                    import json
                    json.dump(client_info, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"客户端信息已保存到: client_info_{config_id}_{timestamp}.json")
                
                print("正在获取日历...")
                # 兼容 calendar_name 或 name 字段，或默认为空字符串
                calendar_name = settings.get('calendar_name') or settings.get('name', '')
                calendar = get_calendar(client, calendar_name)
                
                if calendar is None:
                    print("未找到日历!")
                    continue  # 继续处理下一个配置
                
                print(f"已连接到日历: {calendar.name}")
                
                # 保存日历的详细信息
                calendar_info = {
                    "name": calendar.name,
                    "url": str(calendar.url),
                    "id": calendar.id if hasattr(calendar, 'id') else "Not available",
                }
                
                # 获取所有日历对象的详细信息
                all_calendars = client.principal().calendars()
                all_calendars_info = []
                for cal in all_calendars:
                    cal_info = {
                        "name": cal.name,
                        "url": str(cal.url),
                        "id": cal.id if hasattr(cal, 'id') else "Not available"
                    }
                    all_calendars_info.append(cal_info)
                
                calendar_details = {
                    "selected_calendar": calendar_info,
                    "all_calendars": all_calendars_info,
                    "config_index": i+1,
                    "username": settings.get('username') or 'unknown'
                }
                
                with open(f"calendar_details_{config_id}_{timestamp}.json", 'w', encoding='utf-8') as f:
                    json.dump(calendar_details, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"日历详细信息已保存到: calendar_details_{config_id}_{timestamp}.json")
                
                print("正在获取日历事件...")
                events = fetch_events(calendar)
                
                print(f"找到 {len(events)} 个事件:")
                print("-" * 50)
                
                # 存储所有事件数据
                all_events_data = []
                raw_events_data = []  # 存储原始事件数据
                
                for event in events:
                    # 保存原始事件数据
                    raw_event_data = {
                        "id": event.id,
                        "url": str(event.url) if hasattr(event, 'url') else "Not available",
                        "data": event.data if hasattr(event, 'data') else str(event)
                    }
                    raw_events_data.append(raw_event_data)
                    
                    event_info = parse_event(event)
                    if event_info:
                        print(f"标题: {event_info['name']}")
                        print(f"开始时间: {event_info['start']}")
                        print(f"结束时间: {event_info['end']}")
                        print(f"地点: {event_info['location'] if event_info['location'] else '未指定'}")
                        if event_info['description']:
                            print(f"描述: {event_info['description'][:100]}{'...' if len(event_info['description']) > 100 else ''}")
                        else:
                            print("描述: 未指定")
                        print("-" * 50)
                        
                        # 将事件数据添加到列表中
                        all_events_data.append(event_info)
                
                # 保存原始事件数据
                with open(f"raw_events_{config_id}_{timestamp}.json", 'w', encoding='utf-8') as f:
                    json.dump(raw_events_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"原始事件数据已保存到: raw_events_{config_id}_{timestamp}.json")
                
                # 将所有事件数据保存到JSON文件中
                output_filename = f"caldav_events_{config_id}_{timestamp}.json"
                
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_events_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"\n解析后的事件数据已保存到文件: {output_filename}")
                print(f"共保存了 {len(all_events_data)} 个事件的数据")
                
            except caldav.lib.error.AuthorizationError as e:
                print(f"授权错误 - 请检查您的凭据: {str(e)}")
            except caldav.lib.error.NotFoundError as e:
                print(f"资源未找到: {str(e)}")
            except caldav.lib.error.DAVError as e:
                print(f"DAV 错误: {str(e)}")
            except Exception as e:
                print(f"处理配置 {i+1} 时发生意外错误: {str(e)}")
                import traceback
                traceback.print_exc()
    
    except FileNotFoundError:
        print("错误: 未找到 cal_setting.json 文件!")
    except Exception as e:
        print(f"发生意外错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()