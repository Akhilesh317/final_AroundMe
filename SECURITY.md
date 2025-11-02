# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please do not disclose security vulnerabilities publicly until they have been addressed.

### 2. Report Privately

Send details to: **security@aroundme.example.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity

### Severity Levels

**Critical**
- Remote code execution
- Authentication bypass
- Data breach potential
- Fix: Within 24-48 hours

**High**
- SQL injection
- XSS vulnerabilities
- Privilege escalation
- Fix: Within 7 days

**Medium**
- Information disclosure
- CSRF vulnerabilities
- Fix: Within 30 days

**Low**
- Minor issues
- Fix: Next release

## Security Best Practices

### For Users

1. **API Keys**: Never commit API keys to version control
2. **Environment Files**: Keep `.env` files private
3. **Updates**: Keep dependencies up to date
4. **Passwords**: Use strong, unique passwords
5. **HTTPS**: Always use HTTPS in production

### For Developers

1. **Input Validation**: Always validate user input
2. **SQL Injection**: Use parameterized queries (ORM)
3. **XSS Prevention**: Sanitize output (React auto-escapes)
4. **Authentication**: Implement proper auth (future)
5. **Rate Limiting**: Enable rate limiting
6. **CORS**: Configure CORS properly
7. **Secrets**: Use environment variables
8. **Dependencies**: Run `npm audit` and `pip check`

## Security Features

### Current Implementation

- ✅ Input validation with Pydantic
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ XSS prevention (React auto-escaping)
- ✅ Rate limiting (slowapi)
- ✅ CORS configuration
- ✅ Environment-based secrets
- ✅ HTTPS support (deployment)
- ✅ Structured logging (no sensitive data)

### Planned Enhancements

- [ ] OAuth2 authentication
- [ ] API key rotation
- [ ] Request signing
- [ ] Audit logging
- [ ] WAF integration
- [ ] Security headers (CSP, HSTS)
- [ ] Secrets management (Vault)

## Known Security Considerations

### API Keys

**Issue**: API keys stored in environment variables
**Mitigation**: 
- Never commit `.env` files
- Use secrets management in production
- Rotate keys quarterly

### Rate Limiting

**Issue**: IP-based rate limiting can be bypassed
**Mitigation**:
- Implement user-based limiting (future)
- Use CDN rate limiting
- Monitor for abuse

### Personalization Data

**Issue**: User preferences stored in database
**Mitigation**:
- Opt-in only (default off)
- User can delete anytime
- No PII stored
- No cross-user data sharing

### Provider APIs

**Issue**: Dependent on external API security
**Mitigation**:
- HTTPS only
- Validate responses
- Error handling
- No sensitive data in logs

## Compliance

### GDPR (Future)

When user authentication is added:
- Right to access data
- Right to deletion
- Data portability
- Consent management

### Data Storage

**Currently Stored**:
- Search logs (anonymous)
- User preferences (opt-in)
- Feedback (anonymous)

**NOT Stored**:
- Personal identifiable information (PII)
- Payment information
- Location tracking (search only)

## Security Checklist

### Before Deployment

- [ ] All dependencies updated
- [ ] Security audit performed
- [ ] API keys rotated
- [ ] HTTPS configured
- [ ] Rate limiting enabled
- [ ] Error messages sanitized
- [ ] Logging configured (no secrets)
- [ ] Backups configured
- [ ] Monitoring enabled
- [ ] Incident response plan ready

### Regular Maintenance

- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Quarterly API key rotation
- [ ] Review access logs
- [ ] Update security policies

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Initial response and triage
3. **Day 3-7**: Investigation and fix development
4. **Day 7-14**: Testing and review
5. **Day 14-30**: Coordinated disclosure
6. **Day 30+**: Public disclosure (if resolved)

## Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

<!-- Contributors will be listed here -->

## Contact

- **Security Issues**: security@aroundme.example.com
- **General Questions**: support@aroundme.example.com
- **GitHub Issues**: For non-security bugs only

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Security Headers](https://securityheaders.com/)

---

Last Updated: 2024-01-15