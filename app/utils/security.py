from flask import request, current_app, render_template
from functools import wraps
import logging
from datetime import datetime
import os
import json

def force_https():
    """تأكد من استخدام HTTPS"""
    if not request.is_secure and current_app.config.get('ENV') == 'production':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

def secure_url(url):
    """تحويل الروابط إلى HTTPS في بيئة الإنتاج"""
    if current_app.config.get('ENV') == 'production' and url.startswith('http://'):
        return url.replace('http://', 'https://', 1)
    return url

def log_security_event(event_type, details):
    """تسجيل أحداث الأمان"""
    log_file = os.path.join(current_app.root_path, '..', 'logs', 'security.log')
    timestamp = datetime.utcnow().isoformat()
    
    log_entry = {
        'timestamp': timestamp,
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string,
        'details': details
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def monitor_errors():
    """مراقبة الأخطاء وإرسال تنبيهات"""
    logger = logging.getLogger('error_monitor')
    
    if not logger.handlers:
        # إعداد تسجيل الأخطاء
        log_file = os.path.join(current_app.root_path, '..', 'logs', 'errors.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        logger.addHandler(file_handler)
        
        # إعداد إرسال البريد الإلكتروني للأخطاء الحرجة
        if current_app.config.get('MAIL_SERVER'):
            mail_handler = logging.handlers.SMTPHandler(
                mailhost=(current_app.config['MAIL_SERVER'],
                         current_app.config['MAIL_PORT']),
                fromaddr=f"error-monitor@{current_app.config['MAIL_SERVER']}",
                toaddrs=[current_app.config.get('ADMIN_EMAIL', 'admin@example.com')],
                subject='خطأ حرج في تطبيق Sultan Prints'
            )
            mail_handler.setLevel(logging.ERROR)
            logger.addHandler(mail_handler)
    
    return logger

def error_handler(f):
    """مزخرف للتعامل مع الأخطاء وتسجيلها"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger = monitor_errors()
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            
            # تسجيل حدث أمان
            log_security_event('error', {
                'function': f.__name__,
                'error': str(e),
                'args': str(args),
                'kwargs': str(kwargs)
            })
            
            # إعادة توجيه المستخدم إلى صفحة الخطأ
            return current_app.error_handlers.get(500)(e)
    
    return decorated_function

def setup_security_monitoring(app):
    """إعداد مراقبة الأمان للتطبيق"""
    @app.before_request
    def before_request():
        # تأكد من استخدام HTTPS
        if app.config.get('ENV') == 'production' and not request.is_secure:
            return force_https()
        
        # تسجيل محاولات الوصول المشبوهة
        if request.headers.get('X-Forwarded-For') or \
           request.headers.get('X-Real-IP') or \
           'curl' in request.user_agent.string.lower():
            log_security_event('suspicious_access', {
                'headers': dict(request.headers),
                'url': request.url
            })
    
    @app.after_request
    def after_request(response):
        # إضافة رؤوس الأمان
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' https:; font-src 'self' https:;"
        
        return response
    
    # إعداد معالجات الأخطاء
    @app.errorhandler(404)
    def not_found_error(error):
        log_security_event('404_error', {'url': request.url})
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger = monitor_errors()
        logger.error('Server Error: %s', error, exc_info=True)
        log_security_event('500_error', {'error': str(error)})
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        log_security_event('403_error', {'url': request.url})
        return render_template('errors/403.html'), 403 