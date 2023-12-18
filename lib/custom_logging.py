from threading import local
import logging

logger = logging.getLogger('watchtower')


_thread_locals = local()

class CustomLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        try:
            clarity_id = get_current_clarity_id()
            user_session_id = get_current_user_session_id()
            logger.info('Adding ClarityID and CUSTOM_USER_SESSION_ID to each log record')
            return '[ClarityID: %s] [CUSTOM_USER_SESSION_ID: %s] %s' % (clarity_id, user_session_id, msg), kwargs
        except Exception as Error:
            logger.error(f'An error occurred while processing the log at CustomLoggerAdapter : {str(Error)}')
            return '', kwargs

def get_current_clarity_id():
    try:
        clarity_id = getattr(_thread_locals, 'clarity_token', None)
        logger.info(f'In get_current_clarity_id method Retrieved ClarityID : {clarity_id}')
        return clarity_id
    except Exception as Error:
        logger.error(f'An error occurred while retrieving the ClarityID at get_current_clarity_id: {str(Error)}')
        return None

def get_current_user_session_id():
    try:
        user_session_id = getattr(_thread_locals, 'custom_user_session_id', None)    
        logger.info(f'In get_current_user_session_id method Retrieved CustomUserSessionID : {user_session_id}')
        return user_session_id
    except Exception as Error:
        logger.error(f'An error occurred while retrieving the custom_user_session_id at get_current_user_session_id: {str(Error)}')
        return None


class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.clarity_token = request.session.get('clarity_token', None)
        _thread_locals.custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        # logger.info('LoggingMiddleware: Request received - ClarityID: %s, CustomUserSessionID: %s', get_current_clarity_id(), get_current_user_session_id())
        return self.get_response(request)
