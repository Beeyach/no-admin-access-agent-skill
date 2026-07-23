# Contributing

Contributions are welcome, especially for platform-specific command detection and safe user-space alternatives.

## Before opening a pull request

1. Keep the skill useful on Windows, macOS, and Linux.
2. Do not add instructions that bypass security policy or organizational controls.
3. Add or update tests for behavior changes.
4. Run:

```bash
python -m unittest discover -s tests -v
python install.py --target both --home .test-home
```

5. Remove `.test-home` after the installer check.

## Good issue reports

Include the operating system, proposed command, expected result, actual result, and whether the tool was already installed. Remove usernames, company names, tokens, internal paths, and other sensitive information.

