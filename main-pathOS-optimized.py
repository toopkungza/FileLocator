import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import logging
from contextlib import contextmanager
import tempfile
import platform
from typing import List, Iterator, Set
import mmap
from itertools import islice

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectoryScanner:
    def __init__(self, base_path: str, output_file: str, chunk_size: int = 8192):
        self.base_path = Path(base_path).resolve()
        self.output_file = Path(output_file).resolve()
        self.chunk_size = chunk_size
        self._seen_paths: Set[str] = set()
        
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _is_accessible(path: Path) -> bool:
        try:
            os.access(path, os.R_OK)
            return True
        except (PermissionError, OSError):
            return False

    def _normalize_path(self, path: Path) -> str:
        try:
            path_str = str(path.absolute())
            if platform.system() == 'Windows':
                if path_str.startswith('\\\\'):
                    return f"\\\\?\\UNC\\{path_str[2:]}\n"
                return f"\\\\?\\{path_str}\n"
            return f"{path_str}\n"
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return f"{path}\n"

    def _scan_directory(self, directory: Path) -> Iterator[str]:
        if not self._is_accessible(directory):
            return

        try:
            for entry in directory.rglob("*"):
                if self._is_accessible(entry):
                    normalized_path = self._normalize_path(entry)
                    if normalized_path not in self._seen_paths:
                        self._seen_paths.add(normalized_path)
                        yield normalized_path
        except Exception as e:
            logger.error(f"Scan error in {directory}: {e}")

    def _process_chunk(self, dirs: List[Path], temp_file: Path) -> None:
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_file, 'wb', buffering=self.chunk_size) as f:
            for directory in dirs:
                for path in self._scan_directory(directory):
                    f.write(path.encode('utf-8'))

    def _get_subdirectories(self) -> List[Path]:
        return [d for d in self.base_path.iterdir() 
                if d.is_dir() and self._is_accessible(d)]

    @contextmanager
    def _temp_file_manager(self):
        temp_dir = Path(tempfile.gettempdir()) / "directory_scanner"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_files = []
        
        try:
            yield temp_files
        finally:
            for tf in temp_files:
                try:
                    if tf.exists():
                        tf.unlink()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

    def _merge_files(self, temp_files: List[Path]) -> None:
        with open(self.output_file, 'wb', buffering=self.chunk_size) as outfile:
            for temp_file in temp_files:
                if not temp_file.exists():
                    continue
                    
                with open(temp_file, 'rb') as infile:
                    with mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        for chunk in iter(lambda: mm.read(self.chunk_size), b''):
                            outfile.write(chunk)

    def scan(self, num_processes: int = None) -> None:
        num_processes = num_processes or os.cpu_count() or 1
        subdirs = self._get_subdirectories()
        
        if not subdirs:
            logger.warning(f"No accessible subdirectories in {self.base_path}")
            return

        chunks = [list(islice(subdirs, i, None, num_processes)) 
                 for i in range(num_processes)]

        with self._temp_file_manager() as temp_files:
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                futures = []
                
                for i, chunk in enumerate(chunks):
                    temp_file = Path(tempfile.gettempdir()) / f"scan_{i}"
                    temp_files.append(temp_file)
                    futures.append(executor.submit(self._process_chunk, chunk, temp_file))

                for future in futures:
                    future.result()

            self._merge_files(temp_files)

def write_paths_to_file(base_path: str, output_file: str, num_processes: int = None) -> None:
    scanner = DirectoryScanner(base_path, output_file)
    scanner.scan(num_processes)

if __name__ == '__main__':
    write_paths_to_file(r"E:\", "Data\output.txt", 4)