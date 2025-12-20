"""
Request Service for Campus Services Hub
Service Request Management Microservice
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import jwt
import requests
import os
import time
from datetime import datetime
from functools import wraps
from config import Config

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

def get_db_connection():
    """
    Create and return a database connection with retry logic
    """
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB'],
                connection_timeout=5
            )
            return conn
        except mysql.connector.Error as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise DatabaseError(f"Failed to connect to database after {max_retries} attempts: {str(e)}")

def get_root_connection():
    """Get connection without database for initialization"""
    try:
        return mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD']
        )
    except mysql.connector.Error as e:
        raise DatabaseError(f"Cannot connect to MySQL server: {str(e)}")

def validate_token(token):
    """
    Validate JWT token and return user data
    """
    try:
        # Decode token using shared secret
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
        return False, f"Token validation failed: {str(e)}"

def token_required(f):
    """
    Decorator to protect routes with JWT authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing'
            }), 401
        
        # Validate token
        is_valid, result = validate_token(token)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': result
            }), 401
        
        # Store user data in request context
        request.current_user = result
        return f(*args, **kwargs)
    
    return decorated

def role_required(*roles):
    """
    Decorator to require specific user roles
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            user_role = request.current_user.get('role')
            
            if user_role not in roles:
                return jsonify({
                    'success': False,
                    'message': f'Access denied. Required roles: {roles}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def send_notification(user_id, message, notification_type="request_update"):
    """
    Send notification to user via notification service
    """
    try:
        notification_data = {
            'user_id': user_id,
            'message': message,
            'type': notification_type
        }
        
        response = requests.post(
            f"{app.config['NOTIFICATION_SERVICE_URL']}/notifications",
            json=notification_data,
            timeout=2
        )
        return response.status_code == 201
    except Exception:
        # Silent fail - notification is optional
        return False

# ============================
# HEALTH & STATUS ENDPOINTS
# ============================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint with database connectivity test
    """
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'service': 'request-service',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'request-service',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected'
        }), 500

# ============================
# REQUEST MANAGEMENT ENDPOINTS
# ============================

@app.route('/requests', methods=['POST'])
@token_required
def create_request():
    """
    Create a new service request
    Request body: {title, description, category, location, priority}
    """
    try:
        data = request.get_json()
        
        # Validate request
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        # Extract and validate required fields
        required_fields = ['title', 'description', 'category']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({
                    'success': False,
                    'message': f'{field} is required and cannot be empty'
                }), 400
        
        title = data['title'].strip()
        description = data['description'].strip()
        category = data['category'].lower()
        location = data.get('location', '').strip()
        priority = data.get('priority', app.config['DEFAULT_PRIORITY']).lower()
        
        # Validate category
        if category not in app.config['VALID_CATEGORIES']:
            return jsonify({
                'success': False,
                'message': f'Category must be one of: {", ".join(app.config["VALID_CATEGORIES"])}'
            }), 400
        
        # Validate priority
        if priority not in app.config['VALID_PRIORITIES']:
            return jsonify({
                'success': False,
                'message': f'Priority must be one of: {", ".join(app.config["VALID_PRIORITIES"])}'
            }), 400
        
        # Only staff/admin can set high/urgent priority
        user_role = request.current_user.get('role')
        if priority in ['high', 'urgent'] and user_role not in ['staff', 'admin']:
            priority = 'medium'  # Downgrade to medium for students
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Insert new request
        cursor.execute("""
            INSERT INTO service_requests 
            (user_id, title, description, category, location, priority, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.current_user['user_id'],
            title,
            description,
            category,
            location,
            priority,
            app.config['DEFAULT_STATUS'],
            datetime.now()
        ))
        
        request_id = cursor.lastrowid
        
        # Send notification to user
        send_notification(
            user_id=request.current_user['user_id'],
            message=f'Your service request "{title}" has been submitted successfully.'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Service request created successfully',
            'data': {
                'request_id': request_id,
                'title': title,
                'status': app.config['DEFAULT_STATUS']
            }
        }), 201
        
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'message': 'Database error',
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to create request',
            'error': str(e)
        }), 500

@app.route('/requests', methods=['GET'])
@token_required
def get_requests():
    """
    Get service requests with optional filters
    Query parameters: status, category, priority, user_id, page, limit
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        category = request.args.get('category')
        priority = request.args.get('priority')
        user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        offset = (page - 1) * limit
        
        user_role = request.current_user.get('role')
        current_user_id = request.current_user['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query based on user role
        query = "SELECT * FROM service_requests WHERE 1=1"
        params = []
        
        # Regular users can only see their own requests
        if user_role not in ['staff', 'admin']:
            query += " AND user_id = %s"
            params.append(current_user_id)
        # Staff/admins can filter by user_id if provided
        elif user_id:
            query += " AND user_id = %s"
            params.append(int(user_id))
        
        # Apply filters
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if priority:
            query += " AND priority = %s"
            params.append(priority)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        requests_list = cursor.fetchall()
        
        # Convert datetime to ISO format
        for req in requests_list:
            for field in ['created_at', 'updated_at', 'estimated_completion_date', 'actual_completion_date']:
                if req.get(field):
                    req[field] = req[field].isoformat()
        
        cursor.close()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            'success': True,
            'data': {
                'requests': requests_list,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve requests',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>', methods=['GET'])
@token_required
def get_request(request_id):
    """
    Get specific service request by ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (request_id,))
        request_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not request_data:
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        # Check permissions
        user_role = request.current_user.get('role')
        current_user_id = request.current_user['user_id']
        
        if user_role not in ['staff', 'admin'] and request_data['user_id'] != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized access'
            }), 403
        
        # Convert datetime to ISO format
        for field in ['created_at', 'updated_at', 'estimated_completion_date', 'actual_completion_date']:
            if request_data.get(field):
                request_data[field] = request_data[field].isoformat()
        
        return jsonify({
            'success': True,
            'data': request_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve request',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>/status', methods=['PUT'])
@token_required
@role_required('staff', 'admin')
def update_request_status(request_id):
    """
    Update request status (staff/admin only)
    Request body: {status, admin_notes}
    """
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400
        
        new_status = data['status'].lower()
        admin_notes = data.get('admin_notes', '').strip()
        
        # Validate status
        if new_status not in app.config['VALID_STATUSES']:
            return jsonify({
                'success': False,
                'message': f'Status must be one of: {", ".join(app.config["VALID_STATUSES"])}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current request data
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        # Prepare update data
        update_data = {
            'status': new_status,
            'admin_notes': admin_notes,
            'updated_at': datetime.now(),
            'assigned_to': request.current_user['user_id']
        }
        
        # Set completion date if status is completed
        if new_status == 'completed':
            update_data['actual_completion_date'] = datetime.now()
        
        # Update request
        cursor.execute("""
            UPDATE service_requests 
            SET status = %s, admin_notes = %s, updated_at = %s, 
                assigned_to = %s, actual_completion_date = %s
            WHERE id = %s
        """, (
            update_data['status'],
            update_data['admin_notes'],
            update_data['updated_at'],
            update_data['assigned_to'],
            update_data.get('actual_completion_date'),
            request_id
        ))
        
        # Send notification to requester
        send_notification(
            user_id=request_data['user_id'],
            message=f'Your request "{request_data["title"]}" status has been updated to {new_status}.'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Request status updated to {new_status}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update request status',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>', methods=['PUT'])
@token_required
def update_request(request_id):
    """
    Update request details
    Users can update their own pending requests
    Staff/Admin can update any request
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current request data
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        # Check permissions
        user_role = request.current_user.get('role')
        current_user_id = request.current_user['user_id']
        
        # Users can only update their own pending requests
        if user_role not in ['staff', 'admin']:
            if request_data['user_id'] != current_user_id:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Unauthorized access'
                }), 403
            
            if request_data['status'] != 'pending':
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Only pending requests can be updated'
                }), 400
        
        # Extract and validate updatable fields
        title = data.get('title')
        description = data.get('description')
        location = data.get('location')
        
        if not any([title, description, location]):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'At least one field (title, description, location) is required for update'
            }), 400
        
        # Build update query
        update_fields = []
        update_values = []
        
        if title:
            update_fields.append("title = %s")
            update_values.append(title.strip())
        
        if description:
            update_fields.append("description = %s")
            update_values.append(description.strip())
        
        if location:
            update_fields.append("location = %s")
            update_values.append(location.strip())
        
        update_fields.append("updated_at = %s")
        update_values.append(datetime.now())
        
        update_values.append(request_id)  # For WHERE clause
        
        update_query = f"""
            UPDATE service_requests 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        cursor.execute(update_query, update_values)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Request updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update request',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>', methods=['DELETE'])
@token_required
def delete_request(request_id):
    """
    Delete/cancel a service request
    Users can delete their own pending requests
    Admin can delete any request
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current request data
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        # Check permissions
        user_role = request.current_user.get('role')
        current_user_id = request.current_user['user_id']
        
        # Users can only delete their own pending requests
        if user_role not in ['staff', 'admin']:
            if request_data['user_id'] != current_user_id:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Unauthorized access'
                }), 403
            
            if request_data['status'] != 'pending':
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Only pending requests can be deleted'
                }), 400
        
        # Staff can only delete if they are admin or assigned to the request
        if user_role == 'staff':
            if request_data['assigned_to'] != current_user_id:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'You can only delete requests assigned to you'
                }), 403
        
        # Delete the request
        cursor.execute("DELETE FROM service_requests WHERE id = %s", (request_id,))
        
        # Send notification if request was not pending
        if request_data['status'] != 'pending':
            send_notification(
                user_id=request_data['user_id'],
                message=f'Your request "{request_data["title"]}" has been deleted.'
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Request deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to delete request',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>/priority', methods=['PUT'])
@token_required
@role_required('staff', 'admin')
def update_request_priority(request_id):
    """
    Update request priority (staff/admin only)
    Request body: {priority}
    """
    try:
        data = request.get_json()
        
        if not data or 'priority' not in data:
            return jsonify({
                'success': False,
                'message': 'Priority is required'
            }), 400
        
        new_priority = data['priority'].lower()
        
        # Validate priority
        if new_priority not in app.config['VALID_PRIORITIES']:
            return jsonify({
                'success': False,
                'message': f'Priority must be one of: {", ".join(app.config["VALID_PRIORITIES"])}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update priority
        cursor.execute("""
            UPDATE service_requests 
            SET priority = %s, updated_at = %s
            WHERE id = %s
        """, (new_priority, datetime.now(), request_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Request priority updated to {new_priority}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update request priority',
            'error': str(e)
        }), 500

@app.route('/requests/<int:request_id>/assign', methods=['PUT'])
@token_required
@role_required('staff', 'admin')
def assign_request(request_id):
    """
    Assign request to staff member (staff/admin only)
    Request body: {assigned_to}
    """
    try:
        data = request.get_json()
        
        if not data or 'assigned_to' not in data:
            return jsonify({
                'success': False,
                'message': 'assigned_to is required'
            }), 400
        
        assigned_to = int(data['assigned_to'])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current request data
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404
        
        # Update assignment
        cursor.execute("""
            UPDATE service_requests 
            SET assigned_to = %s, updated_at = %s, status = 'in_progress'
            WHERE id = %s
        """, (assigned_to, datetime.now(), request_id))
        
        # Send notification to assignee
        send_notification(
            user_id=assigned_to,
            message=f'You have been assigned to request: "{request_data["title"]}"'
        )
        
        # Send notification to requester
        send_notification(
            user_id=request_data['user_id'],
            message=f'Your request "{request_data["title"]}" has been assigned to a staff member.'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Request assigned to user {assigned_to}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to assign request',
            'error': str(e)
        }), 500

# ============================
# STATISTICS ENDPOINTS
# ============================

@app.route('/requests/stats', methods=['GET'])
@token_required
@role_required('staff', 'admin')
def get_request_statistics():
    """
    Get request statistics (staff/admin only)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get basic statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                MIN(created_at) as oldest_request,
                MAX(created_at) as newest_request
            FROM service_requests
        """)
        stats = cursor.fetchone()
        
        # Get category statistics
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                AVG(TIMESTAMPDIFF(HOUR, created_at, COALESCE(actual_completion_date, NOW()))) as avg_hours_to_complete
            FROM service_requests
            GROUP BY category
        """)
        category_stats = cursor.fetchall()
        
        # Get priority statistics
        cursor.execute("""
            SELECT 
                priority,
                COUNT(*) as count
            FROM service_requests
            GROUP BY priority
        """)
        priority_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime to ISO format
        if stats['oldest_request']:
            stats['oldest_request'] = stats['oldest_request'].isoformat()
        if stats['newest_request']:
            stats['newest_request'] = stats['newest_request'].isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'overall': stats,
                'by_category': category_stats,
                'by_priority': priority_stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve statistics',
            'error': str(e)
        }), 500

# ============================
# DATABASE INITIALIZATION
# ============================

def init_database():
    """Initialize database and tables"""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            # Create database if not exists
            root_conn = get_root_connection()
            root_cursor = root_conn.cursor()
            root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']}")
            root_cursor.close()
            root_conn.close()
            
            # Connect to specific database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create service_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    category ENUM('maintenance', 'cleaning', 'it_support', 'facilities', 'other') DEFAULT 'maintenance',
                    location VARCHAR(255),
                    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
                    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
                    admin_notes TEXT,
                    assigned_to INT,
                    estimated_completion_date DATE,
                    actual_completion_date TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    INDEX idx_category (category),
                    INDEX idx_priority (priority),
                    INDEX idx_assigned_to (assigned_to),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            # Check if we need to insert test data
            cursor.execute("SELECT COUNT(*) FROM service_requests")
            request_count = cursor.fetchone()[0]
            
            if request_count == 0:
                # Insert sample requests
                sample_requests = [
                    (1, 'Leaking faucet', 'Faucet in bathroom keeps dripping all night', 'maintenance', 'Science Building, Room 201', 'medium', 'completed', 'Fixed by maintenance team', 2, '2025-12-05', '2025-12-04 14:30:00'),
                    (3, 'Broken chair', 'Office chair in room 105 is broken', 'maintenance', 'Admin Building, Room 105', 'low', 'in_progress', 'Waiting for replacement parts', 2, '2025-12-10', None),
                    (2, 'Room cleaning needed', 'Classroom needs cleaning after lab session', 'cleaning', 'Main Building, Room 301', 'medium', 'pending', None, None, None, None),
                    (1, 'Projector not working', 'Projector in lecture hall shows no display', 'it_support', 'Lecture Hall A', 'high', 'pending', None, None, None, None),
                    (4, 'Printer paper needed', 'Printer in library out of paper', 'facilities', 'Library, 2nd floor', 'low', 'completed', 'Restocked paper', 3, '2025-12-03', '2025-12-03 10:15:00'),
                    (5, 'Window broken', 'Window pane cracked in lab', 'maintenance', 'Chemistry Lab, Room 204', 'urgent', 'in_progress', 'Safety issue - needs immediate attention', 2, '2025-12-05', None)
                ]
                
                for req in sample_requests:
                    cursor.execute("""
                        INSERT INTO service_requests 
                        (user_id, title, description, category, location, priority, status, admin_notes, assigned_to, estimated_completion_date, actual_completion_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, req)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except mysql.connector.Error as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False
        except Exception as e:
            return False
    
    return False

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

# ============================
# APPLICATION STARTUP
# ============================

if __name__ == '__main__':
    try:
        # Initialize database
        if init_database():
            # Start Flask app
            app.run(
                host='0.0.0.0',
                port=app.config['PORT'],
                debug=app.config['DEBUG'],
                threaded=True
            )
        else:
            print("Database initialization failed. Exiting.")
            
    except KeyboardInterrupt:
        print("Service stopped by user")
    except Exception as e:
        print(f"Failed to start service: {str(e)}")