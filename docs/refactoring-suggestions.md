# Refactoring Suggestions

## Code Duplication

### 1. Base Service Class

**Problem:** 15+ services with similar patterns

**Current:**
```python
class TenderService:
    async def get(self, id):
        return await self.db.get(Tender, id)
    
    async def list(self, filter):
        return await self.db.query(Tender, filter)
    
class DocumentService:
    async def get(self, id):
        return await self.db.get(Document, id)
    
    async def list(self, filter):
        return await self.db.query(Document, filter)
```

**Refactor:**
```python
# core/services/base.py
class BaseService(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model
    
    async def get(self, id: UUID) -> Optional[ModelType]:
        return await self.db.get(self.model, id)
    
    async def list(self, filters: dict, pagination: Pagination) -> list[ModelType]:
        query = select(self.model)
        # Apply filters, pagination, tenant isolation
        return await self.db.execute(query)
    
    async def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        return instance
    
    async def update(self, id: UUID, data: dict) -> Optional[ModelType]:
        instance = await self.get(id)
        for key, value in data.items():
            setattr(instance, key, value)
        await self.db.commit()
        return instance

# Now services are simple:
class TenderService(BaseService[Tender]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Tender)
```

### 2. Validation Utils

**Problem:** 20+ validate functions scattered across modules

**Refactor:**
```python
# core/validation/__init__.py
class Validator:
    @staticmethod
    def email(email: str) -> bool: ...
    @staticmethod
    def uuid(uuid_str: str) -> bool: ...
    @staticmethod
    def pagination(page: int, size: int) -> tuple[bool, Optional[str]]: ...
    
    @staticmethod
    def tender(data: dict) -> tuple[bool, Optional[TenderCreate], Optional[str]]: ...
    @staticmethod
    def document(data: dict) -> tuple[bool, Optional[DocumentCreate], Optional[str]]: ...

# Remove individual functions, use Validator class
```

### 3. Similar Response Schemas

**Problem:** 10+ schemas with same fields (id, created_at, updated_at)

**Refactor:**
```python
# api/schemas/base.py
class BaseSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Then inherit:
class TenderResponse(BaseSchema):
    title: str
    status: TenderStatus
    # ... only tender-specific fields
```

---

## Structural Improvements

### 1. Router Organization

**Current:** All endpoints in single router files

**Refactor:**
```
api/routers/
├── tenders/
│   ├── __init__.py  # Router with all tenders endpoints
│   ├── schemas.py   # Tenders-specific schemas
│   └── deps.py      # Tenders-specific dependencies
├── documents/
│   ├── __init__.py
│   ├── schemas.py
│   └── deps.py
├── analysis/
│   ├── __init__.py
│   ├── schemas.py
│   └── deps.py
```

### 2. Service Layer Structure

**Current:** Services mixed with routers

**Refactor:**
```
core/services/
├── __init__.py          # Export all services
├── base.py              # BaseService class
├── tender_service.py
├── document_service.py
├── analysis_service.py
└── mixins/
    ├── tenant_aware.py  # Tenant isolation mixin
    ├── audit_logging.py # Audit logging mixin
    └── caching.py       # Caching mixin
```

### 3. Error Handling

**Current:** Try-except in each endpoint

**Refactor:**
```python
# core/exceptions.py
class TenderIQException(Exception):
    def __init__(self, message: str, code: str = "ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(TenderIQException):
    def __init__(self, resource: str, id: UUID):
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)

class PermissionError(TenderIQException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED", 403)

# api/exceptions.py - FastAPI handler
@app.exception_handler(TenderIQException)
async def tenderiq_exception_handler(request, exc: TenderIQException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code}
    )
```

---

## Performance Refactoring

### 1. N+1 Query Fix

**Current:**
```python
# In tender list endpoint
tenders = await db.query(Tender).all()
for tender in tenders:
    tender.documents = await db.query(Document).filter(Document.tender_id == tender.id).all()
```

**Refactor:**
```python
# Use joinedload
from sqlalchemy.orm import joinedload

tenders = await db.execute(
    select(Tender)
    .options(joinedload(Tender.documents))
    .where(Tender.tenant_id == tenant_id)
)
```

### 2. Pagination Pattern

**Current:** Inconsistent pagination across endpoints

**Refactor:**
```python
# api/dependencies/pagination.py
async def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Pagination:
    return Pagination(offset=(page-1)*page_size, limit=page_size)

class Pagination:
    def __init__(self, offset: int, limit: int):
        self.offset = offset
        self.limit = limit
```

---

## Testing Improvements

### 1. Fixtures

**Refactor:**
```python
# tests/fixtures/__init__.py
@pytest.fixture
async def db_session():
    async with create_test_db() as session:
        yield session

@pytest.fixture
async def auth_user(db_session):
    user = User(email="test@tenderiq.com", role="admin")
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
def mock_tenant():
    return {"id": "tenant-123", "name": "Test Tenant"}
```

---

## Migration Steps

### Step 1: Base Service (1 week)
1. Create `BaseService` class
2. Migrate one service (TenderService)
3. Test thoroughly
4. Migrate remaining services

### Step 2: Validation (1 week)
1. Create Validator class
2. Update endpoints to use Validator
3. Remove duplicate functions
4. Add comprehensive tests

### Step 3: Exception Handling (2 days)
1. Create exception hierarchy
2. Add global exception handler
3. Update endpoints to use new exceptions
4. Document error codes

### Step 4: Schemas (1 week)
1. Create base schemas
2. Update response schemas
3. Remove duplicate field definitions
4. Add schema tests

---

## Time Estimate

| Refactoring | Days | Risk |
|-------------|------|------|
| Base Service | 3 | Low |
| Validation | 2 | Low |
| Exceptions | 1 | Medium |
| Schemas | 2 | Low |
| Error Handling | 2 | Medium |
| **Total** | **10** | - |