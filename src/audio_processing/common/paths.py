from pathlib import Path


def ensure_directory(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_source_output_dir(source, module_name: str) -> Path:
    return ensure_directory( source.output_path / module_name  )
        
   