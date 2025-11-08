# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-09

### Added
- Initial release of OpenCode Context Filter Proxy
- HTTP proxy server for filtering repository context
- Automatic wrapper script for OpenCode integration
- Installation script with interactive setup
- Comprehensive documentation (SETUP, USAGE, TROUBLESHOOTING, TECHNICAL)
- Test suite (basic, realistic, extreme context tests)
- Support for llama3.2:1b and qwen2.5:1.5b models
- Performance monitoring via logging
- MIT License

### Features
- 99% context token reduction (45,000 → 200 tokens)
- 8× faster inference (8s → 1s)
- Transparent operation (no OpenCode modifications)
- Automatic startup via wrapper script
- Real-time filtering logs
- Minimal dependencies (Python stdlib only)

### Performance
- Tested on 16 subagents
- Aggregate time savings: ~112 seconds per invocation cycle
- Memory usage: ~20MB RSS
- Latency overhead: <50ms

### Documentation
- README.md - Quick start and overview
- docs/SETUP.md - Installation and configuration
- docs/USAGE.md - Daily usage guide
- docs/TROUBLESHOOTING.md - Common issues and solutions
- docs/TECHNICAL.md - Architecture and implementation
- CONTRIBUTING.md - Contribution guidelines
- LICENSE - MIT License

### Testing
- Basic functionality tests
- Realistic context tests
- Extreme context tests
- All tests passing on Python 3.6+

## [Unreleased]

### Planned
- Configuration file support
- Multi-threaded request handling
- Prometheus metrics export
- Dynamic model detection
- Adaptive context sizing
- Docker image
- PyPI package

### Upstream
- Native context control in OpenCode (issue #4096)
- Per-agent context limits
- Context templates

---

**Status**: Production-ready workaround  
**Tested on**: OpenCode 1.x with llama3.2:1b and qwen2.5:1.5b  
**Performance verified**: 8× inference improvement, 99% context reduction
