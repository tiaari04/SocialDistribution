from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination class that follows the project spec: uses `page` and `size` query params."""
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'size'
    max_page_size = 200
