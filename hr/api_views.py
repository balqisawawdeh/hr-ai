from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class AIAssistantThrottle(UserRateThrottle):
    """Custom throttle for AI assistant queries"""
    scope = 'ai_assistant'


class SecureLocationThrottle(UserRateThrottle):
    """Custom throttle for location-sensitive operations"""
    scope = 'location_updates'
    rate = '200/hour'

from .models import (
    Employee, CheckInLocation, LocationHistory, 
    EmployeeStatus, Geofence
)
from .serializers import (
    EmployeeLocationSerializer, CheckInLocationSerializer,
    LocationHistorySerializer, EmployeeStatusSerializer,
    GeofenceSerializer, AIQuerySerializer, AIResponseSerializer,
    LocationUpdateSerializer, CheckInRequestSerializer,
    CheckOutRequestSerializer
)
from .services import LocationService, AIAssistantService


class CheckInLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for check-in/out locations"""
    queryset = CheckInLocation.objects.all()
    serializer_class = CheckInLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CheckInLocation.objects.select_related('employee')
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by check type
        check_type = self.request.query_params.get('check_type')
        if check_type in ['in', 'out']:
            queryset = queryset.filter(check_type=check_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's check-ins/outs"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(timestamp__date=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get check-in/out summary"""
        today = timezone.now().date()
        
        summary = {
            'total_employees': Employee.objects.count(),
            'checked_in_today': CheckInLocation.objects.filter(
                timestamp__date=today,
                check_type='in'
            ).count(),
            'checked_out_today': CheckInLocation.objects.filter(
                timestamp__date=today,
                check_type='out'
            ).count(),
            'currently_online': EmployeeStatus.objects.filter(
                status='checked_in',
                last_update__gte=timezone.now() - timedelta(minutes=10)
            ).count()
        }
        
        return Response(summary)


class EmployeeStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for employee status"""
    queryset = EmployeeStatus.objects.select_related('employee', 'current_geofence')
    serializer_class = EmployeeStatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by online status
        online_only = self.request.query_params.get('online_only')
        if online_only and online_only.lower() == 'true':
            cutoff_time = timezone.now() - timedelta(minutes=10)
            queryset = queryset.filter(last_update__gte=cutoff_time)
        
        return queryset.order_by('employee__first_name', 'employee__last_name')
    
    @action(detail=False, methods=['get'])
    def online(self, request):
        """Get currently online employees"""
        cutoff_time = timezone.now() - timedelta(minutes=10)
        queryset = self.get_queryset().filter(last_update__gte=cutoff_time)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get employees grouped by location/geofence"""
        queryset = self.get_queryset()
        
        # Group by geofence
        locations = {}
        for status in queryset:
            location_name = status.current_geofence.name if status.current_geofence else 'Unknown'
            if location_name not in locations:
                locations[location_name] = []
            
            locations[location_name].append({
                'employee_id': status.employee.id,
                'employee_name': status.employee.full_name,
                'status': status.status,
                'last_update': status.last_update,
                'is_online': status.is_online
            })
        
        return Response(locations)


class GeofenceViewSet(viewsets.ModelViewSet):
    """ViewSet for geofences"""
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get employees currently in this geofence"""
        geofence = self.get_object()
        statuses = EmployeeStatus.objects.filter(current_geofence=geofence)
        serializer = EmployeeStatusSerializer(statuses, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([SecureLocationThrottle])
@ratelimit(key='user', rate='100/h', method='POST')
@csrf_exempt
def check_in(request):
    """API endpoint for employee check-in with enhanced security"""
    
    # Log check-in attempt
    logger.info(f"Check-in attempt from user {request.user.username}")
    
    # Validate location data
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    
    if latitude is None or longitude is None:
        return Response({
            'error': 'Location coordinates are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate coordinate ranges
    try:
        lat = float(latitude)
        lng = float(longitude)
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return Response({
                'error': 'Invalid coordinates'
            }, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({
            'error': 'Invalid coordinate format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CheckInRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            result = LocationService.process_check_in(
                employee_id=serializer.validated_data['employee_id'],
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                notes=serializer.validated_data.get('notes', ''),
                user=request.user
            )
            
            # Log successful check-in
            if result.get('success'):
                logger.info(f"Check-in successful for user {request.user.username}")
            else:
                logger.warning(f"Check-in failed for user {request.user.username}: {result.get('message')}")
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Check-in error for user {request.user.username}: {str(e)}")
            return Response({
                'error': 'Check-in processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_out(request):
    """API endpoint for employee check-out"""
    serializer = CheckOutRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        result = LocationService.process_check_out(
            employee_id=serializer.validated_data['employee_id'],
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            notes=serializer.validated_data.get('notes', '')
        )
        
        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location(request):
    """API endpoint for real-time location updates"""
    serializer = LocationUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        result = LocationService.update_employee_location(
            employee_id=serializer.validated_data['employee_id'],
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            accuracy=serializer.validated_data.get('accuracy')
        )
        
        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIAssistantThrottle])
@ratelimit(key='user', rate='50/h', method='POST')
@csrf_exempt
def ai_assistant_query(request):
    """API endpoint for AI assistant queries with enhanced security"""
    
    # Log the query attempt
    logger.info(f"AI Assistant query from user {request.user.username}: {request.data.get('query', 'No query')}")
    
    # Validate request size
    if len(str(request.data)) > 10000:  # 10KB limit
        return Response({
            'error': 'Query too large. Maximum size is 10KB.'
        }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    
    serializer = AIQuerySerializer(data=request.data)
    
    if serializer.is_valid():
        query = serializer.validated_data['query']
        context = serializer.validated_data.get('context', {})
        
        # Sanitize query input
        if len(query) > 1000:
            return Response({
                'error': 'Query too long. Maximum length is 1000 characters.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add user context with security information
        context.update({
            'user_id': request.user.id,
            'user_name': request.user.get_full_name() or request.user.username,
            'user_groups': [group.name for group in request.user.groups.all()],
            'is_staff': request.user.is_staff,
            'timestamp': timezone.now().isoformat(),
            'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
        })
        
        try:
            result = AIAssistantService.process_query(query, context)
            
            response_data = {
                'query': query,
                'response': result['response'],
                'data': result.get('data', {}),
                'confidence': result.get('confidence', 0.0),
                'timestamp': timezone.now(),
                'user': request.user.username
            }
            
            # Log successful query
            logger.info(f"AI Assistant query successful for user {request.user.username}")
            
            response_serializer = AIResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            logger.error(f"AI Assistant query error for user {request.user.username}: {str(e)}")
            
            return Response({
                'error': f'Error processing query: {str(e)}',
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_current_location(request, employee_id):
    """Get current location of a specific employee"""
    try:
        employee = Employee.objects.get(id=employee_id)
        status_obj = EmployeeStatus.objects.get(employee=employee)
        
        data = {
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'status': status_obj.status,
            'current_latitude': status_obj.current_latitude,
            'current_longitude': status_obj.current_longitude,
            'last_update': status_obj.last_update,
            'is_online': status_obj.is_online,
            'geofence': status_obj.current_geofence.name if status_obj.current_geofence else None
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except EmployeeStatus.DoesNotExist:
        return Response({'error': 'Employee status not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def location_analytics(request):
    """Get location analytics and insights"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    analytics = {
        'daily_checkins': CheckInLocation.objects.filter(
            timestamp__date=today,
            check_type='in'
        ).count(),
        
        'weekly_checkins': CheckInLocation.objects.filter(
            timestamp__date__gte=week_ago,
            check_type='in'
        ).count(),
        
        'active_geofences': Geofence.objects.filter(is_active=True).count(),
        
        'employees_by_status': dict(
            EmployeeStatus.objects.values('status').annotate(
                count=Count('status')
            ).values_list('status', 'count')
        ),
        
        'top_locations': list(
            EmployeeStatus.objects.filter(
                current_geofence__isnull=False
            ).values(
                'current_geofence__name'
            ).annotate(
                count=Count('current_geofence')
            ).order_by('-count')[:5]
        )
    }
    
    return Response(analytics, status=status.HTTP_200_OK)

