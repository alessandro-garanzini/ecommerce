from ninja import Schema


class MessageSchema(Schema):
    """Generic message response schema"""
    message: str
