# Contributing to KrishiMitra

Thank you for your interest in contributing! 🌾

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add crop price comparison chart
   fix: resolve Hindi voice note transcription error
   docs: update API endpoint documentation
   security: patch XSS vulnerability in chat input
   ```
6. Push to your fork: `git push origin feat/your-feature`
7. Open a Pull Request against `main`

## Branch Naming Convention

| Prefix       | Use Case                          |
| ------------ | --------------------------------- |
| `feat/`      | New features                      |
| `fix/`       | Bug fixes                         |
| `security/`  | Security patches                  |
| `docs/`      | Documentation only                |
| `refactor/`  | Code refactoring                  |
| `test/`      | Adding or updating tests          |

## Code Standards

- Follow PEP 8 for Python
- Type hints on all function signatures
- Docstrings on all public functions
- No hardcoded secrets — use `.env`

## Security

- **NEVER** commit API keys, tokens, or credentials
- Use `.env.example` as the template
- Report vulnerabilities via `SECURITY.md`
