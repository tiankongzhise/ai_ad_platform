"""
SQLite Mock 数据层
使用 aiosqlite 提供异步 SQLite 连接，用于快速联调
"""
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

# Mock 数据库文件路径
MOCK_DB_PATH = Path(__file__).parent.parent.parent / "mock_data.sqlite3"


@asynccontextmanager
async def get_mock_db():
    """
    获取 SQLite Mock 数据库连接（上下文管理器）

    Usage:
        async with get_mock_db() as db:
            cursor = await db.execute("SELECT * FROM mock_dashboard_trend")
            rows = await cursor.fetchall()
    """
    async with aiosqlite.connect(MOCK_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_mock_db():
    """
    初始化 Mock 数据库

    1. 创建表结构（执行 schema.sql）
    2. 生成初始数据（星海教育演示数据）
    """
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema 文件不存在: {schema_path}")

    async with get_mock_db() as db:
        # 执行建表语句
        with open(schema_path, "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()

    # 生成演示数据
    await seed_demo_data()


async def seed_demo_data():
    """生成"星海教育"演示数据"""
    from .seed import generate_all_demo_data
    await generate_all_demo_data()


def is_mock_mode() -> bool:
    """检查是否启用 Mock 模式"""
    import os
    return os.getenv("MOCK_MODE", "false").lower() == "true"
