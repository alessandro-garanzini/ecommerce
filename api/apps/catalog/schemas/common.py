from typing import List
from ninja import Schema


class MessageSchema(Schema):
    """Generic message response."""
    message: str


class PaginationSchema(Schema):
    """Pagination metadata."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class BulkOperationResultSchema(Schema):
    """Result of bulk operations."""
    success_count: int
    failed_count: int
    failed_ids: List[int]
    message: str
