# SimpleDirectoryScanner

A high-performance Python utility for scanning directory structures and saving all discovered paths to a file, optimized for large file systems.

## Features

- **Multi-process scanning**: Utilizes multiple CPU cores for parallel directory traversal
- **Memory efficient**: Processes directories in chunks with proper file buffering
- **Path normalization**: Handles Windows long paths (UNC) and platform-specific path formats
- **Resilient error handling**: Continues scanning even when encountering permission errors
- **Memory-mapped file operations**: Uses memory mapping for efficient file merging

## Installation

Simply download the `main-pathOS-optimized.py` file to your project directory.

## Requirements

- Python 3.6+
- Standard library packages only (no external dependencies)

## Usage

### Basic Usage

```python
from main-pathOS-optimized import write_paths_to_file

# Scan a directory and write all paths to a file
write_paths_to_file("E:\\", "Data\\output.txt", 4)
```

### Parameters

- `base_path`: The root directory to scan
- `output_file`: File path where the list of all discovered paths will be saved
- `num_processes`: Number of parallel processes to use (defaults to CPU count if not specified)

### Running as a Script

You can also run the module directly:

```bash
python main-pathOS-optimized.py
```

By default, it will scan "E:\" and save results to "Data\output.txt" using 4 processes.

## How It Works

1. The scanner divides the top-level directories among multiple processes
2. Each process scans its assigned directories recursively
3. Results are written to temporary files
4. When all processes complete, temporary files are efficiently merged into the final output file

## Performance Considerations

- Increasing `num_processes` generally improves performance on multi-core systems, but too many processes can cause diminishing returns
- The default chunk size (8192 bytes) is optimized for most file systems
- For very large scans, ensure adequate disk space for temporary files

## Error Handling

- The scanner logs errors but continues operation when encountering inaccessible directories
- Permission issues are gracefully handled with appropriate logging

## License

[MIT License](LICENSE)
