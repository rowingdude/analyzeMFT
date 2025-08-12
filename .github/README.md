# GitHub Configuration

This directory contains the GitHub-specific configuration files for the analyzeMFT project, implementing a comprehensive DevOps and community management strategy.

## Workflows

### Core CI/CD Pipeline

**`ci.yml`** - Main continuous integration workflow
- Cross-platform testing (Ubuntu, Windows, macOS)
- Multi-version Python support (3.8-3.12)
- Code quality checks (flake8, mypy)
- Security scanning (bandit, safety)
- Test coverage reporting with Codecov integration
- Concurrent execution with cancellation support

**`release.yml`** - Automated release management
- Version validation across all project files
- Multi-platform build testing
- Automated GitHub release creation with changelog
- PyPI publishing for stable releases
- Artifact management and distribution

**`pr-validation.yml`** - Pull request validation
- Change detection with path filtering
- Conventional commit title validation
- Quick smoke tests for faster feedback
- Security scanning for code changes
- Documentation link checking
- Coverage differential analysis
- Dependabot auto-approval workflow

**`maintenance.yml`** - Scheduled maintenance tasks
- Weekly dependency security audits
- Comprehensive code quality analysis
- Test coverage reporting
- Artifact cleanup (30-day retention)
- Dynamic badge generation for repository status

## Issue Templates

**`bug_report.yml`** - Structured bug reporting
- Environment details collection
- Reproduction steps capture
- Error output formatting
- Command-line information gathering

**`feature_request.yml`** - Feature proposal workflow
- Problem and solution documentation
- Priority and use case classification
- Implementation idea collection
- Contribution willingness assessment

**`question.yml`** - User support and Q&A
- Question categorization (usage, troubleshooting, best practices)
- Context gathering for better support
- Pre-submission checklist to reduce duplicates

## Community Management

**`pull_request_template.md`** - Standardized PR submissions
- Change type classification
- Testing requirement checklist
- Documentation update tracking
- Code quality verification

**`CONTRIBUTING.md`** - Comprehensive contributor guide
- Development environment setup
- Coding standards and style guide
- Testing requirements and strategies
- Security considerations for forensic tools
- Performance optimization guidelines
- Documentation standards

**`SECURITY.md`** - Security policy and reporting
- Vulnerability disclosure process
- Supported version matrix
- Security best practices for users
- Development security practices
- Contact information for security issues

## Dependency Management

**`dependabot.yml`** - Automated dependency updates
- Weekly Python package updates
- GitHub Actions version management
- Dependency grouping (testing, security, linting)
- Review assignment and auto-approval for trusted updates

## Project Maintenance Features

### Automated Quality Assurance
- **Code Quality**: Continuous monitoring with flake8, mypy, bandit
- **Security**: Regular vulnerability scanning of dependencies
- **Performance**: Memory and complexity analysis
- **Coverage**: Automated test coverage tracking and reporting

### Release Management
- **Version Consistency**: Automated validation across setup.py, constants.py, and README.md
- **Multi-Platform Testing**: Ensures compatibility across operating systems
- **Artifact Security**: Build verification and integrity checking
- **Changelog Generation**: Automated release notes from commit history

### Community Support
- **Issue Triage**: Structured templates for efficient issue resolution
- **Contribution Workflow**: Clear guidelines for new contributors
- **Security Response**: Responsible disclosure process for vulnerabilities
- **Documentation**: Comprehensive guides for users and developers

### Development Experience
- **Fast Feedback**: Quick validation for common changes
- **Concurrent Execution**: Optimized CI/CD pipeline performance
- **Artifact Management**: Organized build and test result storage
- **Badge Integration**: Real-time project health indicators

## Badge Integration

The maintenance workflow supports dynamic badge generation for:
- Test coverage percentage
- Build status
- Python version support
- Security audit status
- Latest release version

Badges are stored in GitHub Gists and updated automatically through the maintenance workflow.

## Security Considerations

All workflows implement security best practices:
- Minimal permission scopes
- Secure artifact handling
- Dependency vulnerability monitoring
- Private vulnerability reporting support
- Automated security scanning integration

## Customization Notes

Key areas for project-specific customization:
- **Reviewer Assignment**: Update reviewers/assignees in dependabot.yml and issue templates
- **Badge Gist ID**: Configure BADGE_GIST_ID secret for dynamic badges
- **PyPI Credentials**: Set PYPI_API_TOKEN secret for automated publishing
- **Security Contacts**: Update security contact information in SECURITY.md
- **Funding**: Configure funding platforms in FUNDING.yml if applicable

This configuration provides a production-ready foundation for maintaining a high-quality open source forensic analysis tool with comprehensive automation, security, and community support.