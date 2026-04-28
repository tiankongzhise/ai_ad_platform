"""
Redis 客户端管理
职责:
  - 提供全局异步 Redis 连接池（aioredis）
  - OAuth state 存取（防 CSRF）
  - Celery 同步任务进度跟踪
  - API 缓存 / JWT 黑名单

用途说明:
  - OAuth state: oauth_state:{state} -> {tenant_id}:{user_id}  TTL=10分钟
  - 同步状态:   ad_sync_status:{account_id} -> JSON           TTL=24小时
  - JWT黑名单:  jwt_blacklist:{jti} -> 1                      TTL=token剩余有效期
"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

# ---------------------------------------------------------------------------
# 连接池（模块级单例）
# ---------------------------------------------------------------------------

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 异步客户端（懒初始化，全局连接池）"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    """关闭 Redis 连接（应用关闭时调用）"""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


# ---------------------------------------------------------------------------
# OAuth State 管理（防 CSRF）
# ---------------------------------------------------------------------------

_OAUTH_STATE_PREFIX = "oauth_state:"
_OAUTH_STATE_TTL = 600  # 10 分钟


async def save_oauth_state(state: str, tenant_id: str, user_id: str) -> None:
    """
    将 OAuth state 与当前用户绑定，存入 Redis
    
    广告平台回调时携带原始 state，通过本函数反查 tenant_id
    
    Args:
        state:     前端发起 OAuth 时生成的随机字符串（防 CSRF）
        tenant_id: 当前用户所属租户 ID
        user_id:   当前用户 ID
    """
    redis = await get_redis()
    value = json.dumps({"tenant_id": tenant_id, "user_id": user_id})
    await redis.setex(f"{_OAUTH_STATE_PREFIX}{state}", _OAUTH_STATE_TTL, value)


async def consume_oauth_state(state: str) -> Optional[dict]:
    """
    验证并消费 OAuth state（一次性使用）
    
    Args:
        state: 广告平台回调 URL 中携带的 state 参数
    
    Returns:
        {"tenant_id": ..., "user_id": ...} 或 None（state 无效/已过期）
    """
    redis = await get_redis()
    key = f"{_OAUTH_STATE_PREFIX}{state}"

    # 读取后立即删除（原子操作：GET + DEL）
    value = await redis.getdel(key)
    if value is None:
        return None

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 广告同步任务状态跟踪
# ---------------------------------------------------------------------------

_SYNC_STATUS_PREFIX = "ad_sync_status:"
_SYNC_STATUS_TTL = 86400  # 24 小时


async def set_sync_status(account_id: str, status_data: dict) -> None:
    """
    记录广告同步任务状态，供前端轮询使用
    
    Args:
        account_id:  广告账户 ID
        status_data: 状态字典，建议包含:
                     {
                       "status": "running"|"success"|"error",
                       "progress": 0-100,
                       "synced_count": int,
                       "error_msg": str | None,
                       "started_at": ISO datetime str,
                       "finished_at": ISO datetime str | None,
                     }
    """
    redis = await get_redis()
    await redis.setex(
        f"{_SYNC_STATUS_PREFIX}{account_id}",
        _SYNC_STATUS_TTL,
        json.dumps(status_data, ensure_ascii=False),
    )


async def get_sync_status(account_id: str) -> Optional[dict]:
    """
    获取广告同步任务状态
    
    Args:
        account_id: 广告账户 ID
    
    Returns:
        状态字典 或 None（从未同步）
    """
    redis = await get_redis()
    value = await redis.get(f"{_SYNC_STATUS_PREFIX}{account_id}")
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# JWT 黑名单（登出后使 Token 失效）
# ---------------------------------------------------------------------------

_JWT_BLACKLIST_PREFIX = "jwt_blacklist:"


async def add_token_to_blacklist(jti: str, ttl_seconds: int) -> None:
    """
    将 Token 加入黑名单（用户登出时调用）
    
    Args:
        jti:         JWT 的唯一标识（Payload 中的 jti 字段）
        ttl_seconds: Token 剩余有效秒数（过期后自动从 Redis 清除）
    """
    redis = await get_redis()
    await redis.setex(f"{_JWT_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """
    检查 Token 是否在黑名单中
    
    Args:
        jti: JWT 唯一标识
    
    Returns:
        True = 已注销，False = 有效
    """
    redis = await get_redis()
    return await redis.exists(f"{_JWT_BLACKLIST_PREFIX}{jti}") > 0


# ---------------------------------------------------------------------------
# 通用缓存辅助
# ---------------------------------------------------------------------------

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """通用缓存写入（JSON 序列化）"""
    redis = await get_redis()
    await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))


async def cache_get(key: str) -> Optional[Any]:
    """通用缓存读取（JSON 反序列化）"""
    redis = await get_redis()
    raw = await redis.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
