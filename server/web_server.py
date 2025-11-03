from flask import Flask, Response, request, jsonify, render_template_string
import logging
from datetime import datetime
from merger.calendar_merger import CalendarMerger
from config import Config

# HTML 模板
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .stats { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .button { background: #007cba; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; }
        .endpoints { margin-top: 20px; }
        .endpoint { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #007cba; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
    </div>
    
    <div class="stats">
        <h3>统计信息</h3>
        <p>总事件数: {{ stats.total_events }}</p>
        <p>最后更新: {{ stats.last_updated or '未知' }}</p>
        {% if stats.events_by_source %}
        <p>事件来源分布:</p>
        <ul>
            {% for source, count in stats.events_by_source.items() %}
            <li>{{ source }}: {{ count }} 个事件</li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
    
    <div>
        <a href="javascript:void(0)" class="button" onclick="copyCalendarURL()">订阅日历</a>
        <a href="/calendar.ics" class="button">下载日历文件 (.ics)</a>
        <a href="/api/events" class="button">查看事件 API</a>
        <a href="/api/sync" class="button" onclick="return confirm('确定要立即同步吗？')">立即同步</a>
    </div>
    
    <div class="endpoints">
        <h3>API 端点</h3>
        <div class="endpoint">
            <strong>GET /calendar.ics</strong> - 订阅/下载 iCalendar 文件
        </div>
        <div class="endpoint">
            <strong>GET /api/events</strong> - 获取事件列表 (JSON)
        </div>
        <div class="endpoint">
            <strong>POST /api/sync</strong> - 手动触发同步
        </div>
        <div class="endpoint">
            <strong>GET /api/stats</strong> - 获取统计信息
        </div>
    </div>
    
    <script>
        function copyCalendarURL() {
            // 获取完整的订阅地址
            const protocol = window.location.protocol;
            const host = window.location.host;
            const calendarPath = '/calendar.ics';
            const calendarURL = protocol + '//' + host + calendarPath;
            
            // 尝试使用 Clipboard API 复制到剪贴板
            navigator.clipboard.writeText(calendarURL).then(function() {
                // 复制成功，显示提示信息
                alert('日历订阅地址已复制到剪贴板！\\n\\n' + calendarURL + '\\n\\n您可以将此地址添加到您的日历应用中进行订阅。');
            }).catch(function(err) {
                // 如果 Clipboard API 不可用，使用备用方法
                try {
                    const textArea = document.createElement('textarea');
                    textArea.value = calendarURL;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    alert('日历订阅地址已复制到剪贴板！\\n\\n' + calendarURL + '\\n\\n您可以将此地址添加到您的日历应用中进行订阅。');
                } catch (err) {
                    // 如果复制失败，显示地址让用户手动复制
                    alert('请手动复制以下日历订阅地址：\\n\\n' + calendarURL + '\\n\\n您可以将此地址添加到您的日历应用中进行订阅。');
                }
            });
        }
    </script>
</body>
</html>
"""

class CalendarWebServer:
    """日历 Web 服务器"""
    
    def __init__(self, storage, merger):
        self.storage = storage
        self.merger = merger
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            stats = self.storage.get_stats()
            return render_template_string(
                INDEX_HTML,
                title=Config.WEB_TITLE,
                description=Config.WEB_DESCRIPTION,
                stats=stats
            )
        
        @self.app.route('/calendar.ics')
        def download_calendar():
            """下载 iCalendar 文件"""
            ical_data = self.merger.generate_icalendar()
            return Response(
                ical_data,
                mimetype='text/calendar',
                headers={
                    'Content-Disposition': 'attachment; filename=merged_calendar.ics'
                }
            )
        
        @self.app.route('/api/events')
        def get_events():
            """获取事件列表 API"""
            try:
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                source = request.args.get('source')
                
                events = self.storage.load_events(
                    start_date=start_date,
                    end_date=end_date,
                    source_calendar=source
                )
                
                return jsonify({
                    'success': True,
                    'data': events,
                    'count': len(events),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sync', methods=['POST'])
        def sync_calendars():
            """手动触发同步"""
            try:
                success = self.merger.merge_all_events()
                return jsonify({
                    'success': success,
                    'message': '同步完成' if success else '同步失败',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """获取统计信息 API"""
            try:
                stats = self.storage.get_stats()
                return jsonify({
                    'success': True,
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
    
    def run(self, host=None, port=None, debug=None, use_reloader=None):
        """运行服务器"""
        host = host or Config.HOST
        port = port or Config.PORT
        debug = debug or Config.DEBUG
        use_reloader = use_reloader if use_reloader is not None else Config.DEBUG  # Only use reloader in debug mode by default
        
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=use_reloader,
            threaded=True
        )