"""
Custom Exception Handler
Returns standardized error responses for all API errors.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('edoc_hms')


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler with a consistent JSON envelope:
    { "success": false, "message": "...", "errors": {...} }
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        message = 'An error occurred.'
        errors = response.data

        # Extract a clean message from common error formats
        if isinstance(errors, dict):
            if 'detail' in errors:
                message = str(errors['detail'])
                errors = {}
            elif 'non_field_errors' in errors:
                message = str(errors['non_field_errors'][0])
        elif isinstance(errors, list):
            message = str(errors[0]) if errors else message

        response.data = {
            'success': False,
            'message': message,
            'errors': errors if errors else {},
        }

        logger.warning(
            f"API Error {response.status_code}: {message} "
            f"| View: {context.get('view', 'unknown')}"
        )

    return response
