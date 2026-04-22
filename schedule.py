from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Schedule, Site
from datetime import datetime, timedelta

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('', methods=['GET'])
@jwt_required()
def get_schedules():
    """Get all schedules for user"""
    user_id = get_jwt_identity()
    schedules = Schedule.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'schedules': [
            {
                'id': s.id,
                'site_id': s.site_id,
                'site_name': s.site.site_name,
                'frequency': s.frequency,
                'day_of_week': s.day_of_week,
                'hour_of_day': s.hour_of_day,
                'enabled': s.enabled,
                'next_run': s.next_run.isoformat() if s.next_run else None,
                'last_run': s.last_run.isoformat() if s.last_run else None,
                'topic': s.topic,
                'tone': s.tone,
                'length': s.length
            }
            for s in schedules
        ]
    }), 200

@schedule_bp.route('', methods=['POST'])
@jwt_required()
def create_schedule():
    """Create new schedule"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate
    required_fields = ['site_id', 'frequency']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check site exists
    site = Site.query.filter_by(id=data['site_id'], user_id=user_id).first()
    if not site:
        return jsonify({'error': 'Site not found'}), 404
    
    # Check if schedule already exists
    existing = Schedule.query.filter_by(
        user_id=user_id,
        site_id=data['site_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Schedule already exists for this site'}), 409
    
    # Calculate next run
    now = datetime.utcnow()
    day_of_week = data.get('day_of_week', 0)  # 0 = Monday
    hour_of_day = data.get('hour_of_day', 9)  # 9am
    
    next_run = calculate_next_run(now, day_of_week, hour_of_day)
    
    # Create schedule
    schedule = Schedule(
        user_id=user_id,
        site_id=data['site_id'],
        frequency=data['frequency'],
        day_of_week=day_of_week,
        hour_of_day=hour_of_day,
        enabled=data.get('enabled', False),
        next_run=next_run,
        topic=data.get('topic', 'disassembly'),
        tone=data.get('tone', 'helpful'),
        length=data.get('length', 'medium')
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    return jsonify({
        'message': 'Schedule created',
        'schedule': {
            'id': schedule.id,
            'site_id': schedule.site_id,
            'frequency': schedule.frequency,
            'enabled': schedule.enabled,
            'next_run': schedule.next_run.isoformat()
        }
    }), 201

@schedule_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    """Update schedule"""
    user_id = get_jwt_identity()
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'frequency' in data:
        schedule.frequency = data['frequency']
    if 'day_of_week' in data:
        schedule.day_of_week = data['day_of_week']
    if 'hour_of_day' in data:
        schedule.hour_of_day = data['hour_of_day']
    if 'enabled' in data:
        schedule.enabled = data['enabled']
    if 'topic' in data:
        schedule.topic = data['topic']
    if 'tone' in data:
        schedule.tone = data['tone']
    if 'length' in data:
        schedule.length = data['length']
    
    # Recalculate next run if time changed
    if any(field in data for field in ['frequency', 'day_of_week', 'hour_of_day']):
        now = datetime.utcnow()
        schedule.next_run = calculate_next_run(
            now,
            schedule.day_of_week,
            schedule.hour_of_day
        )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Schedule updated',
        'schedule': {
            'id': schedule.id,
            'enabled': schedule.enabled,
            'next_run': schedule.next_run.isoformat()
        }
    }), 200

@schedule_bp.route('/<int:schedule_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_schedule(schedule_id):
    """Enable/disable schedule"""
    user_id = get_jwt_identity()
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    schedule.enabled = not schedule.enabled
    db.session.commit()
    
    return jsonify({
        'message': f'Schedule {"enabled" if schedule.enabled else "disabled"}',
        'enabled': schedule.enabled
    }), 200

@schedule_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    """Delete schedule"""
    user_id = get_jwt_identity()
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': 'Schedule deleted'}), 200

def calculate_next_run(now, day_of_week, hour_of_day):
    """Calculate next run time based on day and hour"""
    # day_of_week: 0=Monday, 6=Sunday
    # hour_of_day: 0-23
    
    current_day = now.weekday()
    target_time = now.replace(hour=hour_of_day, minute=0, second=0, microsecond=0)
    
    # If target time is in the past today, move to next week
    if current_day == day_of_week and now > target_time:
        days_ahead = 7
    elif current_day < day_of_week:
        days_ahead = day_of_week - current_day
    else:
        days_ahead = 7 - (current_day - day_of_week)
    
    return target_time + timedelta(days=days_ahead)
