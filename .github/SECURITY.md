# Security Policy

## Supported Versions

We actively support the following versions of analyzeMFT with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 3.1.x   | :white_check_mark: |
| 3.0.x   | :x:                |
| < 3.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in analyzeMFT, please report it responsibly:

### Private Disclosure

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please:

1. Email the security team at: [security contact - update as needed]
2. Or use GitHub's private vulnerability reporting feature
3. Or contact the maintainer directly

### What to Include

Please include the following information in your security report:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity assessment
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Environment**: Version, OS, Python version, and configuration details
- **Proof of Concept**: Example code or commands demonstrating the issue
- **Suggested Fix**: If you have ideas for remediation

### Response Timeline

- **Initial Response**: Within 48 hours of receiving the report
- **Investigation**: Within 7 days we'll provide an initial assessment
- **Resolution**: Security fixes will be prioritized and released as soon as possible

## Security Considerations

### Input Validation

analyzeMFT processes binary MFT files which could potentially contain malicious data:

- All file inputs are validated before processing
- Buffer overflows are prevented through bounds checking
- Invalid data structures are handled gracefully

### File System Access

The tool requires read access to MFT files:

- Only reads from explicitly specified files
- Does not modify input files
- Output files are created with appropriate permissions

### Memory Management

Large MFT files require careful memory handling:

- Processing occurs in configurable chunks to prevent memory exhaustion
- Temporary data is cleared appropriately
- Resource cleanup is implemented with context managers

### Dependencies

We monitor dependencies for security vulnerabilities:

- Regular dependency scanning with `safety` and `pip-audit`
- Dependabot automatically creates PRs for security updates
- Dependencies are pinned to known-good versions

### Data Privacy

analyzeMFT may process sensitive forensic data:

- No data is transmitted over networks by default
- No telemetry or analytics data is collected
- Users are responsible for securing their MFT files and output

## Security Best Practices for Users

### Safe Usage

1. **Verify Sources**: Only analyze MFT files from trusted sources
2. **Isolated Environment**: Run analysis in isolated/sandboxed environments when processing untrusted data
3. **Output Security**: Secure output files containing forensic data appropriately
4. **Version Management**: Keep analyzeMFT updated to the latest secure version

### Recommended Environment

```bash
# Use virtual environments
python -m venv forensic-env
source forensic-env/bin/activate

# Install from official sources
pip install analyzeMFT

# Verify installation
python -c "import analyzeMFT; print('Installation verified')"
```

### File Handling

```bash
# Set appropriate file permissions
chmod 600 sensitive_mft.raw
chmod 700 output_directory/

# Use secure temporary directories
export TMPDIR=/secure/tmp

# Clean up after analysis
shred -vfz -n 3 output.csv  # If data is sensitive
```

## Vulnerability Disclosure

### Public Disclosure Timeline

After a security issue is resolved:

1. **Fix Released**: Security patch is included in a new release
2. **Advisory Published**: GitHub Security Advisory is published
3. **Public Discussion**: After 90 days, technical details may be shared publicly

### Security Advisories

Security advisories are published at:
- GitHub Security Advisories tab
- Release notes for security releases
- Security section of the README

## Security Development Practices

### Code Review

All code changes undergo security review:

- Automated security scanning with Bandit
- Manual review of security-sensitive changes
- Dependency vulnerability scanning

### Testing

Security testing includes:

- Fuzzing with malformed MFT files
- Boundary condition testing
- Input validation testing
- Memory safety testing

### Continuous Monitoring

- Automated dependency scanning in CI/CD
- Regular security audits
- Monitoring of security advisories for dependencies

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged in:

- Security advisories (with permission)
- Release notes
- Hall of Fame (if established)

## Contact

For security-related questions or concerns:

- Security Email: [To be established]
- Maintainer: rowingdude
- GitHub Security: Use private vulnerability reporting

## Legal

This security policy is subject to the project's overall license and terms of use. Users are responsible for compliance with applicable laws and regulations when using analyzeMFT for forensic analysis.