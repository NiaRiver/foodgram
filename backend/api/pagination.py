from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 100


class SubLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 100

def paginate_list(items, page_size):
    return [items[i:i + page_size] for i in range(0, len(items), page_size)]