"""
缓存处理
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

from httpx import Client

from .config import Config
from .log import logger


class FileCache:
    """文件缓存"""

    def __init__(self) -> None:
        self._seq: int = 1
        self._client = Client(
            headers={
                "User-Agent": "Mozilla/5.0(X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0"
            }
        )

    def get_seq(self) -> str:
        s = self._seq
        self._seq = (self._seq + 1) % sys.maxsize
        return f"{str(s)}.file"

    def _save(self, file: bytes, path: Path):
        """储存文件"""
        with open(path, mode="wb") as f:
            f.write(file)

    def get(self, url: str) -> bytes:
        """请求获取图片"""
        res = self._client.get(url)
        return res.content

    def save_file(self, chache_path: Path, file: bytes) -> Path:
        """储存文件，返回路径"""
        seq = self.get_seq()
        path = chache_path / seq
        self._save(file, path)
        return path


def scheduler_job(config: Config):
    """定时工作"""
    logger.info("开始清理文件缓存...")
    path = Path(config.cache_path)
    days = timedelta(days=config.cache_days)
    now = datetime.now()
    count = 0
    delete_count = 0
    for file in path.iterdir():
        count += 1
        file_info = file.stat()
        file_time = datetime.fromtimestamp(file_info.st_ctime)
        if file_time + days > now:
            file.unlink()
            delete_count += 1
    logger.debug(f"共有缓存文件 {count} 个，清理 {delete_count} 个...")
    logger.info("缓存文件清理完毕...")