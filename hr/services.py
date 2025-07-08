from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import re
import openai
from django.conf import settings

from .models import (
    Employee, CheckInLocation, LocationHistory, 
    EmployeeStatus, Geofence
)


class LocationService:
    """Service class for location-related operations"""
    
    @staticmethod
    def process_check_in(employee_id, latitude, longitude, notes=''):
        """Process employee check-in"""
        try:
            employee = Employee.objects.get(id=employee_id)
            
            # Check if already checked in today
            today = timezone.now().date()
            existing_checkin = CheckInLocation.objects.filter(
                employee=employee,
                check_type='in',
                timestamp__date=today
            ).first()
            
            if existing_checkin:
                return {
                    'success': False,
                    'message': 'Already checked in today',
                    'data': {
                        'existing_checkin': existing_checkin.timestamp.isoformat()
                    }
                }
            
            # Check geofences
            geofences = Geofence.objects.filter(is_active=True)
            within_geofence = False
            geofence_obj = None
            
            for geofence in geofences:
                if geofence.contains_point(latitude, longitude):
                    within_geofence = True
                    geofence_obj = geofence
                    break
            
            # Create check-in record
            checkin = CheckInLocation.objects.create(
                employee=employee,
                latitude=latitude,
                longitude=longitude,
                check_type='in',
                is_within_geofence=within_geofence,
                notes=notes
            )
            
            # Update employee status
            status_obj, created = EmployeeStatus.objects.get_or_create(
                employee=employee,
                defaults={
                    'status': 'checked_in',
                    'current_latitude': latitude,
                    'current_longitude': longitude,
                    'last_check_in': checkin.timestamp,
                    'current_geofence': geofence_obj
                }
            )
            
            if not created:
                status_obj.status = 'checked_in'
                status_obj.current_latitude = latitude
                status_obj.current_longitude = longitude
                status_obj.last_check_in = checkin.timestamp
                status_obj.current_geofence = geofence_obj
                status_obj.save()
            
            return {
                'success': True,
                'message': f'Checked in successfully{" at " + geofence_obj.name if geofence_obj else ""}',
                'data': {
                    'checkin_id': checkin.id,
                    'timestamp': checkin.timestamp.isoformat(),
                    'location': f"{latitude}, {longitude}",
                    'geofence': geofence_obj.name if geofence_obj else None,
                    'within_geofence': within_geofence
                }
            }
            
        except Employee.DoesNotExist:
            return {
                'success': False,
                'message': 'Employee not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing check-in: {str(e)}'
            }
    
    @staticmethod
    def process_check_out(employee_id, latitude, longitude, notes=''):
        """Process employee check-out"""
        try:
            employee = Employee.objects.get(id=employee_id)
            
            # Check if checked in today
            today = timezone.now().date()
            checkin = CheckInLocation.objects.filter(
                employee=employee,
                check_type='in',
                timestamp__date=today
            ).first()
            
            if not checkin:
                return {
                    'success': False,
                    'message': 'No check-in found for today'
                }
            
            # Check if already checked out
            checkout = CheckInLocation.objects.filter(
                employee=employee,
                check_type='out',
                timestamp__date=today
            ).first()
            
            if checkout:
                return {
                    'success': False,
                    'message': 'Already checked out today',
                    'data': {
                        'existing_checkout': checkout.timestamp.isoformat()
                    }
                }
            
            # Create check-out record
            checkout = CheckInLocation.objects.create(
                employee=employee,
                latitude=latitude,
                longitude=longitude,
                check_type='out',
                notes=notes
            )
            
            # Update employee status
            status_obj = EmployeeStatus.objects.get(employee=employee)
            status_obj.status = 'checked_out'
            status_obj.current_latitude = latitude
            status_obj.current_longitude = longitude
            status_obj.last_check_out = checkout.timestamp
            status_obj.current_geofence = None
            status_obj.save()
            
            # Calculate work duration
            work_duration = checkout.timestamp - checkin.timestamp
            
            return {
                'success': True,
                'message': 'Checked out successfully',
                'data': {
                    'checkout_id': checkout.id,
                    'timestamp': checkout.timestamp.isoformat(),
                    'location': f"{latitude}, {longitude}",
                    'work_duration': str(work_duration),
                    'work_hours': round(work_duration.total_seconds() / 3600, 2)
                }
            }
            
        except Employee.DoesNotExist:
            return {
                'success': False,
                'message': 'Employee not found'
            }
        except EmployeeStatus.DoesNotExist:
            return {
                'success': False,
                'message': 'Employee status not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing check-out: {str(e)}'
            }
    
    @staticmethod
    def update_employee_location(employee_id, latitude, longitude, accuracy=None):
        """Update employee's real-time location"""
        try:
            employee = Employee.objects.get(id=employee_id)
            
            # Save to location history
            LocationHistory.objects.create(
                employee=employee,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy
            )
            
            # Update employee status
            status_obj, created = EmployeeStatus.objects.get_or_create(
                employee=employee,
                defaults={
                    'status': 'offline',
                    'current_latitude': latitude,
                    'current_longitude': longitude
                }
            )
            
            if not created:
                status_obj.current_latitude = latitude
                status_obj.current_longitude = longitude
                status_obj.last_update = timezone.now()
                
                # Check geofences
                geofences = Geofence.objects.filter(is_active=True)
                within_geofence = None
                
                for geofence in geofences:
                    if geofence.contains_point(latitude, longitude):
                        within_geofence = geofence
                        break
                
                status_obj.current_geofence = within_geofence
                status_obj.save()
            
            return {
                'success': True,
                'message': 'Location updated successfully',
                'data': {
                    'employee_id': employee_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timezone.now().isoformat(),
                    'geofence': within_geofence.name if within_geofence else None
                }
            }
            
        except Employee.DoesNotExist:
            return {
                'success': False,
                'message': 'Employee not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating location: {str(e)}'
            }


class AIAssistantService:
    """Service class for AI assistant functionality"""
    
    @staticmethod
    def process_query(query, context=None):
        """Process natural language query and return structured response"""
        if context is None:
            context = {}
        
        # Analyze query to determine intent
        intent = AIAssistantService._analyze_query_intent(query)
        
        # Get relevant data based on intent
        data = AIAssistantService._get_query_data(intent, query)
        
        # Generate natural language response
        response = AIAssistantService._generate_response(query, intent, data, context)
        
        return {
            'response': response,
            'data': data,
            'intent': intent,
            'confidence': 0.9  # Placeholder confidence score
        }
    
    @staticmethod
    def _analyze_query_intent(query):
        """Analyze query to determine user intent"""
        query_lower = query.lower()
        
        # Location queries
        if any(word in query_lower for word in ['where is', 'location of', 'find']):
            return 'location_query'
        
        # Status queries
        elif any(word in query_lower for word in ['who is', 'status of', 'checked in']):
            return 'status_query'
        
        # Time-based queries
        elif any(word in query_lower for word in ['today', 'yesterday', 'this week']):
            return 'time_based_query'
        
        # Attendance queries
        elif any(word in query_lower for word in ['attendance', 'present', 'absent']):
            return 'attendance_query'
        
        # List queries
        elif any(word in query_lower for word in ['list', 'show me', 'all']):
            return 'list_query'
        
        else:
            return 'general_query'
    
    @staticmethod
    def _get_query_data(intent, query):
        """Get relevant data based on query intent"""
        data = {}
        
        try:
            if intent == 'location_query':
                # Extract employee name from query
                employee_name = AIAssistantService._extract_employee_name(query)
                if employee_name:
                    employee = Employee.objects.filter(
                        Q(first_name__icontains=employee_name) |
                        Q(last_name__icontains=employee_name) |
                        Q(first_name__icontains=employee_name.split()[0]) |
                        Q(last_name__icontains=employee_name.split()[-1])
                    ).first()
                    
                    if employee:
                        try:
                            status_obj = EmployeeStatus.objects.get(employee=employee)
                            data = {
                                'employee_id': employee.id,
                                'employee_name': f"{employee.first_name} {employee.last_name}",
                                'status': status_obj.status,
                                'current_location': status_obj.current_location_string,
                                'geofence': status_obj.current_geofence.name if status_obj.current_geofence else None,
                                'last_update': status_obj.last_update.isoformat() if status_obj.last_update else None,
                                'is_online': status_obj.is_online
                            }
                        except EmployeeStatus.DoesNotExist:
                            data = {'error': 'Employee status not found'}
                    else:
                        data = {'error': 'Employee not found'}
            
            elif intent == 'status_query':
                # Get all employee statuses
                statuses = EmployeeStatus.objects.select_related('employee', 'current_geofence')
                data = {
                    'employees': [
                        {
                            'name': f"{status.employee.first_name} {status.employee.last_name}",
                            'status': status.status,
                            'location': status.current_geofence.name if status.current_geofence else 'Unknown',
                            'is_online': status.is_online
                        }
                        for status in statuses
                    ]
                }
            
            elif intent == 'time_based_query':
                today = timezone.now().date()
                
                if 'today' in query.lower():
                    checkins = CheckInLocation.objects.filter(
                        timestamp__date=today,
                        check_type='in'
                    ).select_related('employee')
                    
                    data = {
                        'date': today.isoformat(),
                        'checkins': [
                            {
                                'employee_name': f"{checkin.employee.first_name} {checkin.employee.last_name}",
                                'time': checkin.timestamp.strftime('%H:%M'),
                                'location': f"{checkin.latitude}, {checkin.longitude}"
                            }
                            for checkin in checkins
                        ]
                    }
            
            elif intent == 'attendance_query':
                today = timezone.now().date()
                total_employees = Employee.objects.count()
                checked_in = CheckInLocation.objects.filter(
                    timestamp__date=today,
                    check_type='in'
                ).count()
                
                data = {
                    'total_employees': total_employees,
                    'checked_in_today': checked_in,
                    'attendance_rate': round((checked_in / total_employees) * 100, 1) if total_employees > 0 else 0
                }
            
            elif intent == 'list_query':
                # Get current employee statuses
                statuses = EmployeeStatus.objects.select_related('employee', 'current_geofence')
                data = {
                    'employees': [
                        {
                            'name': f"{status.employee.first_name} {status.employee.last_name}",
                            'status': status.status,
                            'location': status.current_geofence.name if status.current_geofence else 'Unknown',
                            'last_update': status.last_update.isoformat() if status.last_update else None
                        }
                        for status in statuses
                    ]
                }
        
        except Exception as e:
            data = {'error': f'Error retrieving data: {str(e)}'}
        
        return data
    
    @staticmethod
    def _extract_employee_name(query):
        """Extract employee name from query"""
        # Simple name extraction - look for capitalized words
        words = query.split()
        potential_names = []
        
        for i, word in enumerate(words):
            if word[0].isupper() and word.lower() not in ['where', 'is', 'the', 'location', 'of']:
                potential_names.append(word)
                # Check if next word is also capitalized (full name)
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    potential_names.append(words[i + 1])
                    break
        
        return ' '.join(potential_names) if potential_names else None
    
    @staticmethod
    def _generate_response(query, intent, data, context):
        """Generate natural language response"""
        if 'error' in data:
            return f"I'm sorry, but {data['error'].lower()}."
        
        if intent == 'location_query' and 'employee_name' in data:
            employee_name = data['employee_name']
            status = data['status']
            location = data.get('geofence', 'an unknown location')
            
            if status == 'checked_in':
                return f"{employee_name} is currently checked in at {location}."
            elif status == 'checked_out':
                return f"{employee_name} has checked out and is not currently at work."
            else:
                return f"{employee_name}'s current status is {status}."
        
        elif intent == 'time_based_query' and 'checkins' in data:
            checkins = data['checkins']
            if checkins:
                count = len(checkins)
                names = [checkin['employee_name'] for checkin in checkins[:3]]
                response = f"{count} employees checked in today"
                if count <= 3:
                    response += f": {', '.join(names)}"
                else:
                    response += f", including {', '.join(names)} and {count - 3} others"
                return response + "."
            else:
                return "No employees have checked in today yet."
        
        elif intent == 'attendance_query' and 'total_employees' in data:
            total = data['total_employees']
            checked_in = data['checked_in_today']
            rate = data['attendance_rate']
            return f"Today's attendance: {checked_in} out of {total} employees ({rate}%) have checked in."
        
        elif intent == 'status_query' and 'employees' in data:
            employees = data['employees']
            online_count = sum(1 for emp in employees if emp['is_online'])
            return f"Currently {online_count} employees are online and active."
        
        else:
            return "I understand your query, but I don't have enough information to provide a specific answer."

