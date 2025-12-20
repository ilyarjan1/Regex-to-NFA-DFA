"""
User Service for Campus Services Hub
Authentication and User Management Microservice
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import jwt
import bcrypt
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from config import Config

# Initialize Flask app
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
        
        try:
            # Decode token
            data = jwt.decode(
                token, 
                app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            request.current_user = data
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Token validation failed'
            }), 401
        
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

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter"
    return True, "Password is valid"

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
            'service': 'user-service',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'user-service',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected'
        }), 500

# ============================
# AUTHENTICATION ENDPOINTS
# ============================

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Request body: {email, password, name, role}
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
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({
                    'success': False,
                    'message': f'{field} is required and cannot be empty'
                }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        name = data['name'].strip()
        role = data.get('role', 'student').lower()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Validate password strength
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({
                'success': False,
                'message': password_message
            }), 400
        
        # Validate role
        valid_roles = ['student', 'staff', 'admin']
        if role not in valid_roles:
            return jsonify({
                'success': False,
                'message': f'Role must be one of: {", ".join(valid_roles)}'
            }), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User with this email already exists'
            }), 409
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (email, password, name, role, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (email, hashed_password, name, role, datetime.now()))
        
        user_id = cursor.lastrowid
        
        # Generate JWT token
        token_payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'])
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'token': token,
                'user': {
                    'id': user_id,
                    'email': email,
                    'name': name,
                    'role': role
                }
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
            'message': 'Registration failed',
            'error': str(e)
        }), 500

@app.route('/login', methods=['POST'])
def login():
    """
    User login
    Request body: {email, password}
    """
    try:
        data = request.get_json()
        
        # Validate request
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user by email
        cursor.execute("""
            SELECT id, email, password, name, role, created_at 
            FROM users 
            WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Verify password
        if not bcrypt.checkpw(
            password.encode('utf-8'), 
            user['password'].encode('utf-8')
        ):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Generate JWT token
        token_payload = {
            'user_id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None
                }
            }
        }), 200
        
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'message': 'Database error',
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Login failed',
            'error': str(e)
        }), 500

@app.route('/validate-token', methods=['POST'])
def validate_token():
    """
    Validate a JWT token
    Request body: {token}
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'message': 'Token is required'
            }), 400
        
        token = data['token']
        
        try:
            # Decode and validate token
            decoded = jwt.decode(
                token, 
                app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            
            # Check if user still exists
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s", (decoded['user_id'],))
            user_exists = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            
            if not user_exists:
                return jsonify({
                    'success': False,
                    'valid': False,
                    'message': 'User no longer exists'
                }), 200
            
            return jsonify({
                'success': True,
                'valid': True,
                'user': decoded
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': True,
                'valid': False,
                'message': 'Token expired'
            }), 200
        except jwt.InvalidTokenError:
            return jsonify({
                'success': True,
                'valid': False,
                'message': 'Invalid token'
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Token validation failed',
            'error': str(e)
        }), 500

# ============================
# USER MANAGEMENT ENDPOINTS
# ============================

@app.route('/users/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get current user's profile
    """
    try:
        user_id = request.current_user['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, email, name, role, created_at, updated_at
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Convert datetime to ISO format
        user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
        user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
        
        return jsonify({
            'success': True,
            'data': user
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve user profile',
            'error': str(e)
        }), 500

@app.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """
    Get user by ID
    """
    try:
        current_user = request.current_user
        
        # Check permissions
        if current_user['user_id'] != user_id and current_user['role'] not in ['staff', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Unauthorized access'
            }), 403
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, email, name, role, created_at, updated_at
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Convert datetime to ISO format
        user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
        user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
        
        return jsonify({
            'success': True,
            'data': user
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve user',
            'error': str(e)
        }), 500

@app.route('/users/me', methods=['PUT'])
@token_required
def update_current_user():
    """
    Update current user's profile
    Request body: {name}
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        # Extract updatable fields
        name = data.get('name')
        
        # Validate at least one field to update
        if not name:
            return jsonify({
                'success': False,
                'message': 'At least one field (name) is required for update'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update user
        cursor.execute("""
            UPDATE users 
            SET name = %s, updated_at = %s
            WHERE id = %s
        """, (name, datetime.now(), user_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User profile updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update user profile',
            'error': str(e)
        }), 500

@app.route('/users/me/password', methods=['PUT'])
@token_required
def change_password():
    """
    Change current user's password
    Request body: {current_password, new_password}
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Both current_password and new_password are required'
            }), 400
        
        # Validate new password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current password hash
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Verify current password
        if not bcrypt.checkpw(
            current_password.encode('utf-8'),
            user['password'].encode('utf-8')
        ):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 401
        
        # Hash new password
        new_hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Update password
        cursor.execute("""
            UPDATE users 
            SET password = %s, updated_at = %s
            WHERE id = %s
        """, (new_hashed_password, datetime.now(), user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to change password',
            'error': str(e)
        }), 500

# ============================
# ADMIN ENDPOINTS
# ============================

@app.route('/users', methods=['GET'])
@token_required
@role_required('admin', 'staff')
def get_all_users():
    """
    Get all users (admin/staff only)
    Query parameters: page, limit, role, search
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        role_filter = request.args.get('role')
        search = request.args.get('search', '')
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        query = """
            SELECT id, email, name, role, created_at, updated_at
            FROM users 
            WHERE 1=1
        """
        params = []
        
        if role_filter:
            query += " AND role = %s"
            params.append(role_filter)
        
        if search:
            query += " AND (email LIKE %s OR name LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        # Convert datetime to ISO format
        for user in users:
            user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
        
        cursor.close()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
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
            'message': 'Failed to retrieve users',
            'error': str(e)
        }), 500

@app.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@role_required('admin')
def update_user_role(user_id):
    """
    Update user role (admin only)
    Request body: {role}
    """
    try:
        data = request.get_json()
        
        if not data or 'role' not in data:
            return jsonify({
                'success': False,
                'message': 'Role is required'
            }), 400
        
        new_role = data['role'].lower()
        valid_roles = ['student', 'staff', 'admin']
        
        if new_role not in valid_roles:
            return jsonify({
                'success': False,
                'message': f'Role must be one of: {", ".join(valid_roles)}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update role
        cursor.execute("""
            UPDATE users 
            SET role = %s, updated_at = %s
            WHERE id = %s
        """, (new_role, datetime.now(), user_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User role updated to {new_role}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update user role',
            'error': str(e)
        }), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(user_id):
    """
    Delete a user (admin only - soft delete)
    """
    try:
        # Prevent admin from deleting themselves
        if user_id == request.current_user['user_id']:
            return jsonify({
                'success': False,
                'message': 'Cannot delete your own account'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Soft delete - set is_active to false (add this column to users table)
        # For now, we'll do a hard delete since we don't have is_active column
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to delete user',
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
            # Create database
            root_conn = get_root_connection()
            root_cursor = root_conn.cursor()
            root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']}")
            root_cursor.close()
            root_conn.close()
            
            # Connect to specific database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    role ENUM('student', 'staff', 'admin') DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Check if we need to insert test data
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                test_users = [
                    ('admin@campus.edu', 'admin123', 'Admin User', 'admin'),
                    ('student@campus.edu', 'student123', 'John Student', 'student'),
                    ('staff@campus.edu', 'staff123', 'Jane Staff', 'staff')
                ]
                
                for email, password, name, role in test_users:
                    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute(
                        "INSERT INTO users (email, password, name, role) VALUES (%s, %s, %s, %s)",
                        (email, hashed, name, role)
                    )
            
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
                port=5000,
                debug=False,
                threaded=True
            )
        else:
            print("Database initialization failed. Exiting.")
            
    except KeyboardInterrupt:
        print("Service stopped by user")
    except Exception as e:
        print(f"Failed to start service: {str(e)}")