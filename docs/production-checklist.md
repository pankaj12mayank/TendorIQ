# Production Readiness Checklist

## Pre-Deployment

### Environment Configuration
- [ ] All required environment variables set
- [ ] DATABASE_URL configured (production instance)
- [ ] REDIS_URL configured (production instance)
- [ ] SECRET_KEY set (min 32 chars, random)
- [ ] CORS_ORIGINS configured for production domain
- [ ] SENTRY_DSN configured for error tracking

### Security
- [ ] API keys rotated (not using dev keys)
- [ ] Rate limiting enabled and tested
- [ ] RBAC permissions validated
- [ ] Tenant isolation verified
- [ ] JWT validation working
- [ ] Audit logging enabled

### Database
- [ ] Migrations tested on staging
- [ ] Connection pooling configured
- [ ] Backup strategy in place
- [ ] Indexes created for performance

### Monitoring
- [ ] Health endpoints responding
- [ ] Sentry capturing errors
- [ ] Metrics collection working
- [ ] Alerting configured
- [ ] Logging level set to INFO

## Build & Deploy

### Linting & Formatting
- [ ] `ruff check` passes (Python)
- [ ] `ruff format` passes (Python)
- [ ] `eslint` passes (TypeScript)
- [ ] `prettier` passes (TypeScript)

### Type Checking
- [ ] `mypy` passes (Python)
- [ ] `tsc --noEmit` passes (TypeScript)

### Testing
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing

### Build
- [ ] Frontend builds successfully
- [ ] Backend builds successfully
- [ ] No security vulnerabilities (npm audit)
- [ ] No known CVEs

## Post-Deployment

### Health Checks
- [ ] `/health` returns 200
- [ ] `/health/ready` returns 200
- [ ] Database connection working
- [ ] Redis connection working

### Functionality
- [ ] User authentication working
- [ ] API endpoints responding
- [ ] Queue processing working
- [ ] AI features working
- [ ] File uploads/downloads working

### Monitoring
- [ ] Errors appearing in Sentry
- [ ] Metrics visible in dashboard
- [ ] Logs flowing correctly
- [ ] Alerts triggering correctly

## Rollback Plan
- [ ] Database rollback procedure documented
- [ ] Previous version tagged
- [ ] Rollback script tested

## Contacts
- Primary On-Call: _____________
- Secondary On-Call: _____________
- Security Contact: _____________