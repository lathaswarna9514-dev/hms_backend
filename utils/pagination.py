from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom PageNumberPagination class that embeds 'success': True
    and supports page_size query parameter override.
    """
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

def paginate_queryset_response(queryset, request, serializer_class, page_size=15):
    """
    Helper function to paginate querysets in custom APIViews.
    """
    paginator = StandardResultsSetPagination()
    paginator.page_size = page_size
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = serializer_class(queryset, many=True)
    return Response({
        'success': True,
        'count': queryset.count(),
        'results': serializer.data
    })
