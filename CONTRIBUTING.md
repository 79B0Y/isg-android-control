# Contributing to Android TV Box Integration

Thank you for your interest in contributing to the Android TV Box Home Assistant Integration! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.9+
- Home Assistant development environment
- Android device with ADB enabled
- Basic knowledge of Home Assistant custom components

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/bobo/android-tv-box.git
   cd android-tv-box
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Test your changes**
   ```bash
   # Run validation script
   bash release.sh
   ```

## Contribution Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Use meaningful variable and function names

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add new sensor for battery level
fix: resolve ADB connection timeout issue
docs: update installation guide
refactor: improve error handling in adb_service.py
```

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests if applicable
   - Update documentation as needed

3. **Test your changes**
   - Test on a real Android device
   - Verify all existing functionality still works
   - Check for any new issues

4. **Submit a pull request**
   - Provide a clear description of changes
   - Reference any related issues
   - Include screenshots if UI changes are involved

### Testing

Before submitting a pull request, please:

- [ ] Test on a real Android device
- [ ] Verify all entities work correctly
- [ ] Check Home Assistant logs for errors
- [ ] Test web interface functionality
- [ ] Verify HACS compatibility

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Home Assistant version
- Integration version
- Android device information
- Configuration details
- Relevant logs
- Steps to reproduce

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for consistency.

### Feature Requests

For feature requests, please:

- Describe the use case
- Explain why it would be useful
- Consider implementation complexity
- Check if similar features exist

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## Development Areas

### High Priority

- **Performance improvements**: Optimize ADB command execution
- **Error handling**: Better error messages and recovery
- **Documentation**: Improve user guides and API docs
- **Testing**: Add automated tests

### Medium Priority

- **New entities**: Additional sensor types
- **Web interface**: Enhanced management features
- **MQTT integration**: Better MQTT support
- **Automation**: More automation examples

### Low Priority

- **UI improvements**: Better web interface design
- **Advanced features**: Complex automation scenarios
- **Platform support**: Additional Android versions

## Code Structure

```
custom_components/android_tv_box/
├── __init__.py              # Main component initialization
├── manifest.json            # Component metadata
├── config.py                # Configuration schema
├── config_flow.py           # Configuration UI flow
├── adb_service.py           # ADB communication service
├── media_player.py          # Media player entity
├── switch.py                # Switch entities
├── camera.py                # Camera entity
├── sensor.py                # Sensor entities
├── remote.py                # Remote entity
├── select.py                # Select entity
├── binary_sensor.py         # Binary sensor entity
├── services.py              # Custom services
├── web_server.py            # Web management interface
└── web/                     # Web interface files
    ├── index.html
    ├── style.css
    └── script.js
```

## Release Process

### Version Bumping

When making changes that require a version bump:

1. Update version in `custom_components/android_tv_box/manifest.json`
2. Update version in `hacs.json`
3. Update changelog
4. Create release notes

### HACS Release

1. **Prepare release**
   ```bash
   bash release.sh
   ```

2. **Create GitHub release**
   - Tag the release: `git tag v1.2.1`
   - Push tags: `git push origin main --tags`
   - Create GitHub release with notes

3. **Update HACS**
   - HACS will automatically detect the new release
   - Users can update through HACS interface

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

### Be Collaborative

- Help others when possible
- Share knowledge and experience
- Provide constructive feedback
- Work together to solve problems

### Be Patient

- Remember that contributors are volunteers
- Allow time for responses and reviews
- Be understanding of different time zones
- Show appreciation for contributions

## Getting Help

### Documentation

- [README.md](custom_components/android_tv_box/README.md) - Main documentation
- [HACS Installation Guide](HACS_INSTALLATION.md) - HACS setup
- [Web Interface Guide](WEB_INTERFACE_GUIDE.md) - Web management
- [Project Overview](PROJECT_OVERVIEW.md) - Architecture details

### Community

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and ideas
- **Home Assistant Community**: For Home Assistant related questions

### Development Help

- **Home Assistant Developer Docs**: https://developers.home-assistant.io/
- **HACS Documentation**: https://hacs.xyz/docs/
- **ADB Documentation**: https://developer.android.com/studio/command-line/adb

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

By contributing, you agree that your contributions will be licensed under the same license.

---

Thank you for contributing to the Android TV Box Integration! 🎉
