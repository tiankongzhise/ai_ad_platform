"""
SQLite Mock 数据层
用于快速联调和演示
"""

from .mock_db import get_mock_db, init_mock_db, is_mock_mode

__all__ = ["get_mock_db", "init_mock_db", "is_mock_mode"]
