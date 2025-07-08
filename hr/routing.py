from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/location/$', consumers.LocationConsumer.as_asgi()),
    re_path(r'ws/employee/(?P<employee_id>\w+)/$', consumers.EmployeeLocationConsumer.as_asgi()),
]

