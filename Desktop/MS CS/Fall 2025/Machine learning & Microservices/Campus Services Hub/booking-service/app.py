from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime, timedelta
import logging
import requests
from config import Config
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

def get_db_connection():
    """Create and return a database connection with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
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
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
    except mysql.connector.Error as e:
        raise DatabaseError(f"Cannot connect to MySQL server: {str(e)}")

def validate_user(token):
    """Validate user token with user service"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f'{Config.USER_SERVICE_URL}/users/me',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return True, response.json()['data']
        else:
            return False, None
    except Exception as e:
        logger.error(f"User validation error: {str(e)}")
        return False, None

@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'service': 'booking-service',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'booking-service',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected'
        }), 500

@app.route('/rooms', methods=['GET'])
def get_rooms():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM rooms WHERE is_available = TRUE")
        rooms = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': rooms
        }), 200
        
    except Exception as e:
        logger.error(f"Get rooms error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get rooms',
            'error': str(e)
        }), 500

@app.route('/rooms/<int:room_id>/availability', methods=['GET'])
def check_availability(room_id):
    try:
        date = request.args.get('date', datetime.now().date().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT start_time, end_time FROM bookings 
            WHERE room_id = %s AND DATE(start_time) = %s AND status != 'cancelled'
        """, (room_id, date))
        
        bookings = cursor.fetchall()
        
        # Convert datetime to ISO format
        for booking in bookings:
            if booking.get('start_time'):
                booking['start_time'] = booking['start_time'].isoformat()
            if booking.get('end_time'):
                booking['end_time'] = booking['end_time'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {'bookings': bookings}
        }), 200
        
    except Exception as e:
        logger.error(f"Check availability error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check availability',
            'error': str(e)
        }), 500

@app.route('/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        is_valid, user_data = validate_user(token)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        room_id = data.get('room_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        purpose = data.get('purpose', '')
        
        if not all([room_id, start_time, end_time]):
            return jsonify({
                'success': False,
                'message': 'room_id, start_time, and end_time are required'
            }), 400
        
        # Validate time
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        if end_dt <= start_dt:
            return jsonify({
                'success': False,
                'message': 'End time must be after start time'
            }), 400
        
        if (end_dt - start_dt).total_seconds() > 4 * 3600:
            return jsonify({
                'success': False,
                'message': 'Booking cannot exceed 4 hours'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check room availability
        cursor.execute("""
            SELECT id FROM bookings 
            WHERE room_id = %s AND status != 'cancelled' AND (
                (start_time < %s AND end_time > %s) OR
                (start_time >= %s AND start_time < %s)
            )
        """, (room_id, end_time, start_time, start_time, end_time))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Room is already booked for this time slot'
            }), 409
        
        # Create booking
        cursor.execute("""
            INSERT INTO bookings (user_id, room_id, start_time, end_time, purpose, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_data['id'], room_id, start_time, end_time, purpose, 'confirmed'))
        
        booking_id = cursor.lastrowid
        
        # Get room name for notification
        cursor.execute("SELECT name FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        
        # Send notification (non-blocking)
        try:
            notification_data = {
                'user_id': user_data['id'],
                'message': f'Your booking for {room["name"]} has been confirmed.',
                'type': 'booking_confirmed'
            }
            requests.post(
                f'{Config.NOTIFICATION_SERVICE_URL}/notifications',
                json=notification_data,
                timeout=2
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Booking created: {booking_id}")
        return jsonify({
            'success': True,
            'message': 'Booking created successfully',
            'data': {'booking_id': booking_id}
        }), 201
        
    except Exception as e:
        logger.error(f"Create booking error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create booking',
            'error': str(e)
        }), 500

@app.route('/bookings', methods=['GET'])
def get_bookings():
    try:
        token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        is_valid, user_data = validate_user(token)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if user_data['role'] in ['staff', 'admin']:
            cursor.execute("""
                SELECT b.*, r.name as room_name, r.type as room_type 
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                ORDER BY b.start_time DESC
            """)
        else:
            cursor.execute("""
                SELECT b.*, r.name as room_name, r.type as room_type 
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.user_id = %s
                ORDER BY b.start_time DESC
            """, (user_data['id'],))
        
        bookings = cursor.fetchall()
        
        # Convert datetime to ISO format
        for booking in bookings:
            for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                if booking.get(field):
                    booking[field] = booking[field].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': bookings
        }), 200
        
    except Exception as e:
        logger.error(f"Get bookings error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get bookings',
            'error': str(e)
        }), 500

@app.route('/bookings/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    try:
        token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        is_valid, user_data = validate_user(token)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Check authorization
        if user_data['role'] not in ['staff', 'admin'] and booking['user_id'] != user_data['id']:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Unauthorized access'
            }), 403
        
        # Check if booking can be cancelled (at least 1 hour before)
        start_time = booking['start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        if datetime.now() + timedelta(hours=1) > start_time:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Booking can only be cancelled at least 1 hour before start time'
            }), 400
        
        cursor.execute("""
            UPDATE bookings SET status = 'cancelled', updated_at = %s 
            WHERE id = %s
        """, (datetime.now(), booking_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Booking cancelled: {booking_id}")
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Cancel booking error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to cancel booking',
            'error': str(e)
        }), 500

def init_database():
    """Initialize database and tables"""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            # Create database if not exists
            root_conn = get_root_connection()
            root_cursor = root_conn.cursor()
            root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            root_cursor.close()
            root_conn.close()
            
            # Connect to specific database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type ENUM('classroom', 'lab', 'meeting_room', 'auditorium', 'other') DEFAULT 'classroom',
                    capacity INT NOT NULL,
                    location VARCHAR(255),
                    equipment TEXT,
                    is_available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    room_id INT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    purpose VARCHAR(255),
                    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms(id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_room_id (room_id),
                    INDEX idx_status (status),
                    INDEX idx_start_time (start_time)
                )
            """)
            
            # Insert sample rooms
            cursor.execute("SELECT COUNT(*) FROM rooms")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO rooms (name, type, capacity, location, equipment) VALUES
                    ('Room 101', 'classroom', 30, 'Main Building - First Floor', 'Projector, Whiteboard'),
                    ('Computer Lab A', 'lab', 25, 'Tech Building - Ground Floor', '25 Computers, Projector'),
                    ('Conference Room', 'meeting_room', 10, 'Admin Building - Second Floor', 'TV, Whiteboard, Phone'),
                    ('Chemistry Lab', 'lab', 20, 'Science Building - First Floor', 'Lab Equipment, Fume Hood'),
                    ('Auditorium', 'auditorium', 200, 'Main Building - Ground Floor', 'Stage, Sound System, Projector')
                """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except mysql.connector.Error as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Database initialization failed: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {str(e)}")
            return False
    
    return False

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'message': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        if init_database():
            app.run(
                host='0.0.0.0',
                port=5001,  # Fixed port to match Dockerfile
                debug=Config.DEBUG if hasattr(Config, 'DEBUG') else False,
                threaded=True
            )
        else:
            print("Database initialization failed. Exiting.")
    except KeyboardInterrupt:
        print("Service stopped by user")
    except Exception as e:
        print(f"Failed to start service: {str(e)}")
