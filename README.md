# py-memory-manager

This library implements a thread-safe virtual memory manager for allocating and
freeing writable memory in a provided buffer.

It currently only supports `bytearray` and writable `memoryview` buffers. Other
types such as `list` are implemented as linked lists internally, and so are not
suitable for this use case.

Thread safety is provided via read and write locks, which may not be performant
in highly contested environments. There is no lock pre-emption, so be aware that
it may be possible to deadlock the memory manager. There is no attempt to
provide thread safety for allocated memoryview objects, that is left to the
user.

It is technically possible to use multiple memory managers on the same buffer,
but it is not recommended.

## Installation

Install directly via GitHub using uv:

```bash
uv add git+https://github.com/shakefu/py-memory-manager
```

## Usage

This section describes how to use the py-memory-manager library.

### Basic Usage Example

```python
from py_memory_manager import MemoryManager, create_buffer

# Use helper function to create a buffer
buf = create_buffer(1024)

# Create a memory manager for the buffer
mm = MemoryManager(buf)

# Allocate 100 bytes of memory
alloc = mm.alloc(100)

# Use the allocated memory
alloc[:10] = b"Hello, World!"

# Free the allocated memory
mm.free(alloc)

# The buffer is now free
print(buf)

```

## Contributing

Follow these guidelines for development and contributing.

### Committing

This repository uses
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) for
commit messages. This is enforced by the pre-commit hook.

### Pre-commit Hooks

This repository uses pre-commit hooks to ensure code quality and consistency.

**Running pre-commit against all files:**

```bash
uv run pre-commit run --all-files
```

### Running Tests

This repository uses pytest for testing. We aim for 100% coverage, due to the
simple nature of the library.

**Running the full test suite:**

```bash
uv run pytest
```

**Running tests with coverage output:**

```bash
uv run pytest --cov --cov-report term-missing
```

## License

This project is licensed under the GPL-3.0 license. See [LICENSE](LICENSE) for
the full license text.

## Notes

Repository supporting files borrowed from my open source project
[HumbleDB](https://github.com/shakefu/humbledb) for convenience and development
speed.

- `.gitignore` - Standard gitignore file.
- `.pre-commit-config.yaml` - Standard linting and formatting hooks for Python.
- `.releaserc.json` - Semantic Release configuration.
- `.github/` - GitHub Actions workflows for CI/CD, with support for Semantic
  Release and Renovatebot.
