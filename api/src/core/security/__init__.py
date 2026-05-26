"""Security Module - Production-Grade Security Components"""

from .signed_urls import (
    SignedURLGenerator,
    SecureFileHandler,
    signed_url_generator,
    secure_file_handler,
    get_signed_url_generator,
    get_secure_file_handler
)

from .validation import (
    ValidationRules,
    InputValidator,
    RequestValidationMiddleware,
    APIKeyValidator,
    PydanticValidator,
    validation_rules,
    input_validator,
    get_validation_rules,
    get_input_validator,
    get_api_key_validator,
    get_pydantic_validator
)

from .encrypted_secrets import (
    SecretEncryptor,
    SecretsManager,
    APIKeyManager,
    secret_encryptor,
    secrets_manager,
    api_key_manager,
    get_secret_encryptor,
    get_secrets_manager,
    get_api_key_manager
)

__all__ = [
    # Signed URLs
    'SignedURLGenerator',
    'SecureFileHandler',
    'signed_url_generator',
    'secure_file_handler',
    'get_signed_url_generator',
    'get_secure_file_handler',
    
    # Validation
    'ValidationRules',
    'InputValidator',
    'RequestValidationMiddleware',
    'APIKeyValidator',
    'PydanticValidator',
    'validation_rules',
    'input_validator',
    'get_validation_rules',
    'get_input_validator',
    'get_api_key_validator',
    'get_pydantic_validator',
    
    # Encrypted Secrets
    'SecretEncryptor',
    'SecretsManager',
    'APIKeyManager',
    'secret_encryptor',
    'secrets_manager',
    'api_key_manager',
    'get_secret_encryptor',
    'get_secrets_manager',
    'get_api_key_manager',
]