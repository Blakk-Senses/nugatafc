from django.utils import timezone
import uuid
import user_agents
from .models import PageView, VisitorSession

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only track specific paths you want to monitor
        if self.should_track(request):
            self.track_page_view(request)
        
        response = self.get_response(request)
        return response

    def should_track(self, request):
        """Determine if the request should be tracked - only your specified paths"""
        included_paths = [
            '/',           # Home page
            '/news/',      # News section
            '/players/',   # Players section
            '/standings/', # Standings section
        ]
        
        current_path = request.path
        
        # Track if path starts with any of the included paths
        return any(current_path.startswith(path) for path in included_paths)

    def track_page_view(self, request):
        # Get or create session
        session_key = request.session.session_key or str(uuid.uuid4())
        if not request.session.session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Parse user agent
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        ua = user_agents.parse(user_agent_string)
        
        # Get or create visitor session
        session, created = VisitorSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'ip_address': self.get_client_ip(request),
                'user_agent': user_agent_string,
                'device_type': self.get_device_type(ua),
                'browser': ua.browser.family,
                'operating_system': ua.os.family,
            }
        )
        
        if not created:
            # Update session end time
            session.end_time = timezone.now()
            session.save()
        
        # Create page view with foreign key relationship
        PageView.objects.create(
            url=request.path,
            ip_address=self.get_client_ip(request),
            user_agent=user_agent_string,
            referrer=request.META.get('HTTP_REFERER'),
            session_key=session_key,
            visitor_session=session
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_device_type(self, ua):
        if ua.is_mobile:
            return 'Mobile'
        elif ua.is_tablet:
            return 'Tablet'
        elif ua.is_pc:
            return 'Desktop'
        else:
            return 'Other'