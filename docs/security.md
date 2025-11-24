# Security Best Practices

Security guidelines and best practices for the Trading Manager application.

## Overview

This document covers security considerations for:
- Authentication and authorization
- Password management
- Database security
- API security
- Secrets management

## Authentication

### Password Hashing

The application uses **bcrypt** for password hashing, which is secure and resistant to brute-force attacks.

**Implementation:**
```python
import bcrypt

# Hashing a password
password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')

# Verifying a password
is_valid = bcrypt.checkpw(
    password.encode('utf-8'),
    password_hash.encode('utf-8')
)
```

**Password Requirements:**
- Minimum 8 characters (recommended: implement in validation)
- Mix of uppercase, lowercase, numbers, and symbols (recommended)
- No common passwords (consider using password strength library)

### JWT Token Management

The application uses **flask-jwt-extended** for JWT token authentication.

**Token Types:**
1. **Access Token**: Short-lived (1 hour default), used for API requests
2. **Refresh Token**: Long-lived, used to obtain new access tokens

**Security Features:**
- Tokens are signed with SECRET_KEY
- Token expiration is enforced
- Tokens include user claims for authorization

**Best Practices:**
1. **Never store tokens in localStorage** (vulnerable to XSS)
   - Use httpOnly cookies (preferred)
   - Use sessionStorage as fallback
   
2. **Always use HTTPS in production**

3. **Implement token refresh logic:**
```javascript
// Client-side token refresh
async function refreshToken() {
  const refreshToken = getRefreshToken();
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshToken}`
    }
  });
  const data = await response.json();
  saveAccessToken(data.access_token);
}
```

4. **Implement token revocation** (future enhancement)
   - Store revoked tokens in Redis
   - Check against revoked list before accepting token

### Session Management

**Recommendations:**
1. Set secure session configuration:
```python
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=3600   # 1 hour
)
```

2. Implement session invalidation on logout

3. Track last login time to detect suspicious activity

## Secrets Management

### Environment Variables

**Never commit secrets to version control!**

1. Use `.env` file for local development (add to .gitignore)
2. Use environment variables in production

**Required Secrets:**
```bash
SECRET_KEY=<random-256-bit-key>
JWT_SECRET_KEY=<random-256-bit-key>
DB_PASSWORD=<strong-password>
```

**Generate Strong Keys:**
```python
import secrets
print(secrets.token_urlsafe(32))  # Generates 256-bit key
```

Or use command line:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
openssl rand -base64 32
```

### Key Rotation

**Best Practice:** Rotate secrets periodically

1. Generate new secret
2. Update environment variable
3. Restart application
4. Invalidate old tokens (if JWT_SECRET_KEY changed)

## Database Security

### Connection Security

1. **Use SSL/TLS** for database connections:
```python
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

2. **Use connection pooling** with limits:
```python
engine = create_engine(
    database_uri,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verify connections
)
```

3. **Never expose database directly** to the internet
   - Use firewall rules
   - Allow only backend servers
   - Use VPN for admin access

### Database User Privileges

**Principle of Least Privilege:**

1. **Application User** (trading_user):
```sql
-- Grant only necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO trading_user;

-- No DROP, CREATE, or ALTER privileges
```

2. **Admin User** (separate):
```sql
-- For migrations and schema changes
CREATE USER trading_admin WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE trading_manager TO trading_admin;
```

3. **Read-Only User** (for analytics):
```sql
CREATE USER trading_readonly WITH PASSWORD 'strong-password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO trading_readonly;
```

### SQL Injection Prevention

**Always use parameterized queries:**

✅ **Secure:**
```python
# Using SQLAlchemy ORM (automatically parameterized)
user = session.query(User).filter_by(username=username).first()

# Using raw SQL with parameters
session.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {'username': username}
)
```

❌ **Insecure:**
```python
# Never use string formatting
query = f"SELECT * FROM users WHERE username = '{username}'"
session.execute(query)
```

### Sensitive Data Protection

1. **Never log passwords or tokens:**
```python
# Bad
logger.info(f"Login attempt: {username} / {password}")

# Good
logger.info(f"Login attempt for user: {username}")
```

2. **Mask sensitive data in API responses:**
```python
def to_dict(self):
    return {
        'email': self.email,
        # Never include password_hash
    }
```

3. **Encrypt sensitive fields** (if needed):
```python
from cryptography.fernet import Fernet

# Encrypt API keys, etc.
cipher_suite = Fernet(encryption_key)
encrypted = cipher_suite.encrypt(data.encode())
```

## API Security

### CORS Configuration

**Development:**
```python
CORS(app)  # Allow all origins
```

**Production:**
```python
CORS(app, origins=[
    'https://trading-manager.com',
    'https://app.trading-manager.com'
])
```

### Rate Limiting

**Recommended:** Implement rate limiting to prevent abuse

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/auth/login')
@limiter.limit("5 per minute")
def login():
    pass
```

### Input Validation

**Always validate and sanitize input:**

```python
from flask import request
from werkzeug.exceptions import BadRequest

def validate_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        raise BadRequest('Invalid email format')
    return email

# In route
email = validate_email(request.json.get('email'))
```

### HTTPS/TLS

**Production Requirements:**
1. Use HTTPS for all connections
2. Use TLS 1.2 or higher
3. Use strong cipher suites
4. Implement HSTS header:
```python
@app.after_request
def set_secure_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### Content Security Policy

```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = \
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response
```

## Authorization

### Role-Based Access Control (RBAC)

**Check user permissions:**
```python
from functools import wraps
from flask_jwt_extended import get_jwt_identity

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        with session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/admin/users')
@admin_required
def admin_users():
    pass
```

### Resource Ownership

**Verify user owns resource:**
```python
@app.route('/api/watchlists/<watchlist_id>')
@jwt_required()
def get_watchlist(watchlist_id):
    user_id = get_jwt_identity()
    
    with session_scope() as session:
        watchlist = session.query(Watchlist).filter_by(
            id=watchlist_id,
            user_id=user_id  # Ensure ownership
        ).first()
        
        if not watchlist:
            return jsonify({'error': 'Not found'}), 404
```

## Celery Security

### Secure Task Communication

1. **Use secure Redis connection:**
```python
CELERY_BROKER_URL = 'rediss://user:password@host:6379/0'  # SSL
```

2. **Don't pass sensitive data** through task arguments:
```python
# Bad
@celery_app.task
def send_email(user_id, password):
    pass

# Good
@celery_app.task
def send_email(user_id):
    # Fetch password from secure storage in task
    pass
```

3. **Validate task input:**
```python
@celery_app.task
def process_data(data_id):
    # Validate data_id
    if not isinstance(data_id, str):
        raise ValueError('Invalid data_id')
```

## Docker Security

### Container Security

1. **Run as non-root user:**
```dockerfile
# In Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

2. **Use specific image versions:**
```dockerfile
# Good
FROM python:3.11-slim

# Avoid
FROM python:latest
```

3. **Scan images for vulnerabilities:**
```bash
docker scan trading-backend:latest
```

4. **Limit container resources:**
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Monitoring and Logging

### Security Logging

**Log security events:**
```python
import logging

security_logger = logging.getLogger('security')

# Log failed login attempts
security_logger.warning(f"Failed login attempt for user: {username}")

# Log privilege escalation attempts
security_logger.critical(f"Unauthorized admin access attempt by user: {user_id}")

# Log data access
security_logger.info(f"User {user_id} accessed sensitive data: {resource_id}")
```

### Audit Trail

**Track important actions:**
```python
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID)
    action = Column(String(100))  # 'login', 'create', 'update', 'delete'
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

## Compliance

### GDPR Considerations

If handling EU users' data:

1. **Data minimization**: Only collect necessary data
2. **Right to erasure**: Implement account deletion
3. **Data portability**: Provide data export
4. **Consent management**: Track user consent
5. **Privacy policy**: Clear and accessible

### Data Retention

**Implement retention policies:**
```sql
-- TimescaleDB retention policy
SELECT add_retention_policy('audit_logs', INTERVAL '90 days');
```

## Security Checklist

### Development
- [ ] All secrets in .env file (not in code)
- [ ] .env file in .gitignore
- [ ] Input validation on all endpoints
- [ ] Parameterized SQL queries
- [ ] Password hashing with bcrypt
- [ ] JWT token expiration configured

### Pre-Production
- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Set up security headers
- [ ] Database backups configured
- [ ] Monitoring and logging in place

### Production
- [ ] All secrets in environment variables
- [ ] Database SSL/TLS enabled
- [ ] Firewall rules configured
- [ ] Regular security updates
- [ ] Vulnerability scanning
- [ ] Incident response plan
- [ ] Security audit completed

## Incident Response

### If a Security Breach Occurs

1. **Immediate Actions:**
   - Isolate affected systems
   - Revoke compromised credentials
   - Change all secrets
   - Lock affected accounts

2. **Investigation:**
   - Review logs
   - Identify scope of breach
   - Document findings

3. **Remediation:**
   - Patch vulnerabilities
   - Restore from clean backups
   - Notify affected users (if required)

4. **Prevention:**
   - Update security measures
   - Conduct security training
   - Review and update policies

## Resources

- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [JWT Security Best Practices](https://tools.ietf.org/html/rfc8725)

## Security Contact

Report security vulnerabilities to: security@your-domain.com
