# http://stackoverflow.com/a/14364249/1457005

from pathlib import Path


def ensure_dir_exists(path: str) -> None:
    """
    Simplified directory checking function
    - handles nested folder creation
    - natively replaces try-except for OSError 
    - still raises FileExistsError, identical to original implementation
    Parameters
    ----------
    path : str
        Path of directory intended to be used/created
    """
    Path(path).mkdir(parents=True, exist_ok=True)
