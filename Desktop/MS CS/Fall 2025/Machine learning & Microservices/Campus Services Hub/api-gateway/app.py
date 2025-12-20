"""
API Gateway for Campus Services Hub
Routes requests to appropriate microservices
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import jwt
import os
import time
import logging
from datetime import datetime
from functools import wraps
from config import Config
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
app.config.from_object(Config)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a session with retry logic
def create_session():
    """Create requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

session = create_session()

# Service URLs
SERVICES = {
    'user': app.config['USER_SERVICE_URL'],
    'request': app.config['REQUEST_SERVICE_URL'],
    'booking': app.config['BOOKING_SERVICE_URL'],
    'notification': app.config['NOTIFICATION_SERVICE_URL']
}

# Rate limiting (simple in-memory implementation)
request_counts = {}
RATE_LIMIT = 100  # requests per minute
RATE_WINDOW = 60  # seconds

def check_rate_limit(client_id):
    """Simple rate limiting check"""
    current_time = time.time()
    
    if client_id not in request_counts:
        request_counts[client_id] = []
    
    # Remove old requests outside the window
    request_counts[client_id] = [
        req_time for req_time in request_counts[client_id]
        if current_time - req_time < RATE_WINDOW
    ]
    
    # Check if limit exceeded
    if len(request_counts[client_id]) >= RATE_LIMIT:
        return False
    
    # Add current request
    request_counts[client_id].append(current_time)
    return True

def rate_limit_middleware(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Use IP address as client identifier
        client_id = request.remote_addr
        
        if not check_rate_limit(client_id):
            return jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated

def extract_token():
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

def validate_token(token):
    """Validate JWT token"""
    try:
        decoded = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"]
        )
        return True, decoded
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"
    except Exception as e:
        return False, str(e)

def forward_request(service_url, path='', method='GET', **kwargs):
    """
    Forward request to a microservice
    
    Args:
        service_url: Base URL of the service
        path: Additional path to append
        method: HTTP method
        **kwargs: Additional arguments for requests
    """
    try:
        url = f"{service_url}{path}"
        
        # Forward headers (except Host)
        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in ['host', 'content-length']
        }
        
        # Add timeout
        kwargs.setdefault('timeout', 30)
        kwargs['headers'] = headers
        
        # Make request
        response = session.request(method, url, **kwargs)
        
        # Create response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [
            (name, value) for name, value in response.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        
        return Response(
            response.content,
            response.status_code,
            response_headers
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout to {service_url}{path}")
        return jsonify({
            'success': False,
            'message': 'Service request timed out'
        }), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {service_url}{path}")
        return jsonify({
            'success': False,
            'message': 'Service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error forwarding request: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Gateway error',
            'error': str(e)
        }), 500

# ============================
# HEALTH & STATUS
# ============================

@app.route('/health', methods=['GET'])
def health_check():
    """Gateway health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/services/health', methods=['GET'])
@rate_limit_middleware
def check_all_services():
    """Check health of all services"""
    service_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = session.get(f"{service_url}/health", timeout=5)
            service_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            service_status[service_name] = {
                'status': 'unreachable',
                'error': str(e)
            }
    
    all_healthy = all(s['status'] == 'healthy' for s in service_status.values())
    
    return jsonify({
        'success': True,
        'gateway': 'healthy',
        'services': service_status,
        'overall': 'healthy' if all_healthy else 'degraded'
    }), 200 if all_healthy else 503

# ============================
# AUTHENTICATION ROUTES
# ============================

@app.route('/api/auth/register', methods=['POST'])
@rate_limit_middleware
def register():
    """Register new user"""
    return forward_request(
        SERVICES['user'],
        '/register',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/auth/login', methods=['POST'])
@rate_limit_middleware
def login():
    """User login"""
    return forward_request(
        SERVICES['user'],
        '/login',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/auth/validate-token', methods=['POST'])
@rate_limit_middleware
def validate_token_route():
    """Validate JWT token"""
    return forward_request(
        SERVICES['user'],
        '/validate-token',
        method='POST',
        json=request.get_json()
    )

# ============================
# USER ROUTES
# ============================

@app.route('/api/users/me', methods=['GET'])
@rate_limit_middleware
def get_current_user():
    """Get current user profile"""
    return forward_request(SERVICES['user'], '/users/me', method='GET')

@app.route('/api/users/me', methods=['PUT'])
@rate_limit_middleware
def update_current_user():
    """Update current user profile"""
    return forward_request(
        SERVICES['user'],
        '/users/me',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/users/me/password', methods=['PUT'])
@rate_limit_middleware
def change_password():
    """Change user password"""
    return forward_request(
        SERVICES['user'],
        '/users/me/password',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/users/<int:user_id>', methods=['GET'])
@rate_limit_middleware
def get_user(user_id):
    """Get user by ID"""
    return forward_request(SERVICES['user'], f'/users/{user_id}', method='GET')

@app.route('/api/users', methods=['GET'])
@rate_limit_middleware
def get_all_users():
    """Get all users (admin/staff only)"""
    return forward_request(SERVICES['user'], '/users', method='GET')

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
@rate_limit_middleware
def update_user_role(user_id):
    """Update user role (admin only)"""
    return forward_request(
        SERVICES['user'],
        f'/users/{user_id}/role',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@rate_limit_middleware
def delete_user(user_id):
    """Delete user (admin only)"""
    return forward_request(SERVICES['user'], f'/users/{user_id}', method='DELETE')

# ============================
# REQUEST SERVICE ROUTES
# ============================

@app.route('/api/requests', methods=['POST'])
@rate_limit_middleware
def create_request():
    """Create new service request"""
    return forward_request(
        SERVICES['request'],
        '/requests',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/requests', methods=['GET'])
@rate_limit_middleware
def get_requests():
    """Get service requests"""
    return forward_request(SERVICES['request'], '/requests', method='GET')

@app.route('/api/requests/<int:request_id>', methods=['GET'])
@rate_limit_middleware
def get_request(request_id):
    """Get specific request"""
    return forward_request(SERVICES['request'], f'/requests/{request_id}', method='GET')

@app.route('/api/requests/<int:request_id>', methods=['PUT'])
@rate_limit_middleware
def update_request(request_id):
    """Update request"""
    return forward_request(
        SERVICES['request'],
        f'/requests/{request_id}',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
@rate_limit_middleware
def delete_request(request_id):
    """Delete request"""
    return forward_request(SERVICES['request'], f'/requests/{request_id}', method='DELETE')

@app.route('/api/requests/<int:request_id>/status', methods=['PUT'])
@rate_limit_middleware
def update_request_status(request_id):
    """Update request status"""
    return forward_request(
        SERVICES['request'],
        f'/requests/{request_id}/status',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/requests/<int:request_id>/priority', methods=['PUT'])
@rate_limit_middleware
def update_request_priority(request_id):
    """Update request priority"""
    return forward_request(
        SERVICES['request'],
        f'/requests/{request_id}/priority',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/requests/<int:request_id>/assign', methods=['PUT'])
@rate_limit_middleware
def assign_request(request_id):
    """Assign request to staff"""
    return forward_request(
        SERVICES['request'],
        f'/requests/{request_id}/assign',
        method='PUT',
        json=request.get_json()
    )

@app.route('/api/requests/stats', methods=['GET'])
@rate_limit_middleware
def get_request_statistics():
    """Get request statistics"""
    return forward_request(SERVICES['request'], '/requests/stats', method='GET')

# ============================
# BOOKING SERVICE ROUTES
# ============================

@app.route('/api/rooms', methods=['GET'])
@rate_limit_middleware
def get_rooms():
    """Get available rooms"""
    return forward_request(SERVICES['booking'], '/rooms', method='GET')

@app.route('/api/rooms/<int:room_id>/availability', methods=['GET'])
@rate_limit_middleware
def check_availability(room_id):
    """Check room availability"""
    return forward_request(SERVICES['booking'], f'/rooms/{room_id}/availability', method='GET')

@app.route('/api/bookings', methods=['POST'])
@rate_limit_middleware
def create_booking():
    """Create new booking"""
    return forward_request(
        SERVICES['booking'],
        '/bookings',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/bookings', methods=['GET'])
@rate_limit_middleware
def get_bookings():
    """Get bookings"""
    return forward_request(SERVICES['booking'], '/bookings', method='GET')

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@rate_limit_middleware
def cancel_booking(booking_id):
    """Cancel booking"""
    return forward_request(SERVICES['booking'], f'/bookings/{booking_id}', method='DELETE')

# ============================
# NOTIFICATION SERVICE ROUTES
# ============================

@app.route('/api/notifications', methods=['POST'])
@rate_limit_middleware
def create_notification():
    """Create notification (internal use)"""
    return forward_request(
        SERVICES['notification'],
        '/notifications',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/notifications/user/<int:user_id>', methods=['GET'])
@rate_limit_middleware
def get_user_notifications(user_id):
    """Get user notifications"""
    return forward_request(SERVICES['notification'], f'/notifications/user/{user_id}', method='GET')

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@rate_limit_middleware
def mark_as_read(notification_id):
    """Mark notification as read"""
    return forward_request(
        SERVICES['notification'],
        f'/notifications/{notification_id}/read',
        method='PUT'
    )

@app.route('/api/notifications/unread/count/<int:user_id>', methods=['GET'])
@rate_limit_middleware
def get_unread_count(user_id):
    """Get unread notification count"""
    return forward_request(
        SERVICES['notification'],
        f'/notifications/unread/count/{user_id}',
        method='GET'
    )

@app.route('/api/notifications/mark-all-read', methods=['PUT'])
@rate_limit_middleware
def mark_all_as_read():
    """Mark all notifications as read"""
    return forward_request(
        SERVICES['notification'],
        '/notifications/mark-all-read',
        method='PUT'
    )

# ============================
# ANNOUNCEMENT ROUTES
# ============================

@app.route('/api/announcements', methods=['POST'])
@rate_limit_middleware
def create_announcement():
    """Create announcement"""
    return forward_request(
        SERVICES['notification'],
        '/announcements',
        method='POST',
        json=request.get_json()
    )

@app.route('/api/announcements', methods=['GET'])
@rate_limit_middleware
def get_announcements():
    """Get announcements"""
    return forward_request(SERVICES['notification'], '/announcements', method='GET')

@app.route('/api/announcements/<int:announcement_id>', methods=['GET'])
@rate_limit_middleware
def get_announcement(announcement_id):
    """Get specific announcement"""
    return forward_request(
        SERVICES['notification'],
        f'/announcements/{announcement_id}',
        method='GET'
    )

@app.route('/api/announcements/recent', methods=['GET'])
@rate_limit_middleware
def get_recent_announcements():
    """Get recent announcements"""
    return forward_request(SERVICES['notification'], '/announcements/recent', method='GET')

@app.route('/api/notifications/stats', methods=['GET'])
@rate_limit_middleware
def get_notification_statistics():
    """Get notification statistics"""
    return forward_request(SERVICES['notification'], '/notifications/stats', method='GET')

# ============================
# ERROR HANDLERS
# ============================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@app.errorhandler(503)
def service_unavailable(error):
    """Handle 503 errors"""
    return jsonify({
        'success': False,
        'message': 'Service temporarily unavailable'
    }), 503

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ============================
# APPLICATION STARTUP
# ============================

if __name__ == '__main__':
    try:
        logger.info("Starting API Gateway...")
        logger.info(f"User Service: {SERVICES['user']}")
        logger.info(f"Request Service: {SERVICES['request']}")
        logger.info(f"Booking Service: {SERVICES['booking']}")
        logger.info(f"Notification Service: {SERVICES['notification']}")
        
        app.run(
            host='0.0.0.0',
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("API Gateway stopped by user")
    except Exception as e:
        logger.error(f"Failed to start API Gateway: {str(e)}")
