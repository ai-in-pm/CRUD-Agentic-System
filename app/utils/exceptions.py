class BaseError(Exception):
    """Base error class for all custom exceptions"""
    pass

class ValidationError(BaseError):
    """Raised when data validation fails"""
    pass

class QueryError(BaseError):
    """Raised when query processing fails"""
    pass

class UpdateError(BaseError):
    """Raised when update processing fails"""
    pass

class SecurityError(BaseError):
    """Raised when security checks fail"""
    pass

class AnalyticsError(BaseError):
    """Raised when analytics processing fails"""
    pass

class OrchestrationError(BaseError):
    """Raised when orchestration fails"""
    pass
