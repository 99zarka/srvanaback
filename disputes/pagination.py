from rest_framework.pagination import PageNumberPagination

class DisputePagination(PageNumberPagination):
    page_size = 20  # Default page size
    page_size_query_param = 'page_size'  # Allow frontend to override page size
    max_page_size = 100  # Maximum page size allowed
