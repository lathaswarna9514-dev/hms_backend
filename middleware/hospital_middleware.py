import logging
from hospitals.models import Hospital

logger = logging.getLogger('edoc_hms')

class HospitalScopeMiddleware:
    """
    Middleware that reads the X-Hospital-ID header from incoming requests.
    Validates it against existing active hospitals and scopes the request object
    with request.hospital_id and request.hospital.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.hospital_id = None
        request.hospital = None

        hospital_header = request.headers.get('X-Hospital-ID')
        
        # If user is authenticated, we can fallback to their account hospital if scoped
        if not hospital_header and request.user and request.user.is_authenticated:
            if request.user.hospital:
                request.hospital_id = request.user.hospital.id
                request.hospital = request.user.hospital

        if hospital_header:
            try:
                hospital_id = int(hospital_header)
                hospital = Hospital.objects.get(id=hospital_id, is_active=True)
                request.hospital_id = hospital.id
                request.hospital = hospital
            except (ValueError, Hospital.DoesNotExist):
                logger.warning(f"Invalid or inactive X-Hospital-ID header supplied: {hospital_header}")

        response = self.get_response(request)
        return response
