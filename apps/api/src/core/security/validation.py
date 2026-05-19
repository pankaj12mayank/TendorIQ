"""Request Validation Middleware"""

import re
import html
from typing import Any, Callable, Optional
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from ..logging import get_logger

logger = get_logger('validation')


class ValidationRules:
    """Common validation rules for inputs"""
    
    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """Remove HTML tags and escape special characters"""
        return html.escape(re.sub(r'<[^>]+>', '', input_str))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        try:
            UUID(uuid_str)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        pattern = r'^https?://'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        pattern = r'^\+?[\d\s\-()]+$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_alphanumeric(text: str, allow_spaces: bool = True) -> bool:
        pattern = r'^[a-zA-Z0-9\s]+$' if allow_spaces else r'^[a-zA-Z0-9]+$'
        return bool(re.match(pattern, text))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        return sanitized[:255]
    
    @staticmethod
    def validate_json_structure(data: dict, required_keys: list[str]) -> tuple[bool, Optional[str]]:
        """Validate JSON has required keys"""
        missing = [key for key in required_keys if key not in data]
        if missing:
            return False, f"Missing required keys: {', '.join(missing)}"
        return True, None


class InputValidator:
    """Validator for common input types"""
    
    @staticmethod
    def validate_tender_title(title: str) -> tuple[bool, Optional[str]]:
        if not title or len(title.strip()) < 3:
            return False, "Title must be at least 3 characters"
        if len(title) > 200:
            return False, "Title must not exceed 200 characters"
        return True, None
    
    @staticmethod
    def validate_tender_description(desc: str) -> tuple[bool, Optional[str]]:
        if len(desc) > 10000:
            return False, "Description must not exceed 10000 characters"
        return True, None
    
    @staticmethod
    def validate_amount(amount: float) -> tuple[bool, Optional[str]]:
        if amount < 0:
            return False, "Amount cannot be negative"
        if amount > 1_000_000_000:
            return False, "Amount exceeds maximum allowed"
        return True, None
    
    @staticmethod
    def validate_date_range(start: datetime, end: datetime) -> tuple[bool, Optional[str]]:
        if end <= start:
            return False, "End date must be after start date"
        return True, None
    
    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple[bool, Optional[str]]:
        if page < 1:
            return False, "Page must be at least 1"
        if page_size < 1 or page_size > 100:
            return False, "Page size must be between 1 and 100"
        return True, None


class RequestValidationMiddleware:
    """Middleware for request validation"""
    
    @staticmethod
    def validate_pagination_params(request: Request) -> None:
        """Validate pagination query parameters"""
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
        
        if page:
            try:
                page_int = int(page)
                if page_int < 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Page must be at least 1"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid page parameter"
                )
        
        if page_size:
            try:
                size_int = int(page_size)
                if size_int < 1 or size_int > 100:
                    raise HTTPException(
                        status_code=400,
                        detail="Page size must be between 1 and 100"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid page_size parameter"
                )
    
    @staticmethod
    def validate_uuid_params(request: Request, param_names: list[str]) -> None:
        """Validate UUID path/query parameters"""
        for param_name in param_names:
            param_value = request.path_params.get(param_name) or request.query_params.get(param_name)
            if param_value and not ValidationRules.validate_uuid(param_value):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {param_name} format"
                )
    
    @staticmethod
    def sanitize_user_input(data: dict) -> dict:
        """Sanitize user input to prevent XSS and injection"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = ValidationRules.sanitize_html(value.strip())
            elif isinstance(value, dict):
                sanitized[key] = RequestValidationMiddleware.sanitize_user_input(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    ValidationRules.sanitize_html(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


class APIKeyValidator:
    """Validate API keys"""
    
    @staticmethod
    def validate_format(api_key: str) -> bool:
        if not api_key:
            return False
        if len(api_key) < 20:
            return False
        return True
    
    @staticmethod
    def generate_api_key(prefix: str = 'tq') -> str:
        import secrets
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def validate_scopes(scopes: list[str], required_scopes: list[str]) -> tuple[bool, Optional[str]]:
        for scope in required_scopes:
            if scope not in scopes:
                return False, f"Missing required scope: {scope}"
        return True, None


class PydanticValidator:
    """Validate request bodies using Pydantic models"""
    
    @staticmethod
    def validate_with_model(data: dict, model: type[BaseModel]) -> tuple[bool, Optional[BaseModel], Optional[str]]:
        try:
            validated = model(**data)
            return True, validated, None
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                errors.append(f"{field}: {error['msg']}")
            return False, None, '; '.join(errors)
    
    @staticmethod
    def validate_partial(data: dict, model: type[BaseModel]) -> tuple[bool, Optional[BaseModel], Optional[str]]:
        try:
            validated = model.partial(**data)
            return True, validated, None
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                errors.append(f"{field}: {error['msg']}")
            return False, None, '; '.join(errors)


validation_rules = ValidationRules()
input_validator = InputValidator()
api_key_validator = APIKeyValidator()
pydantic_validator = PydanticValidator()


def get_validation_rules() -> ValidationRules:
    return validation_rules


def get_input_validator() -> InputValidator:
    return input_validator


def get_api_key_validator() -> APIKeyValidator:
    return api_key_validator


def get_pydantic_validator() -> PydanticValidator:
    return pydantic_validator