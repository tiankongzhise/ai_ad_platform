"""
应用配置管理
遵循参数 > 类属性 > 全局配置 的优先级逻辑
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量大小写不敏感
        extra="ignore"  # 忽略额外字段
    )
    
    # ==================== 应用基础配置 ====================
    APP_NAME: str = "EduAdCRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # ==================== 数据库配置 ====================
    DATABASE_URL: str = "mysql+aiomysql://user:pass@localhost:3306/eduadcrm"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    
    # ==================== Redis 配置 ====================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5分钟
    
    # ==================== JWT 配置 ====================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ==================== Celery 配置 ====================
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # ==================== 巨量引擎 OAuth 配置 ====================
    JULIANG_APP_ID: str = ""
    JULIANG_APP_SECRET: str = ""
    JULIANG_OAUTH_URL: str = "https://open.oceanengine.com/authorize"
    JULIANG_TOKEN_URL: str = "https://open.oceanengine.com/oauth/access_token"
    JULIANG_API_BASE_URL: str = "https://ad.oceanengine.com"
    JULIANG_CALLBACK_URL: str = "http://localhost:8000/api/v1/ad/juliang/callback"
    
    # ==================== 百度营销 OAuth 配置 ====================
    BAIDU_APP_ID: str = ""
    BAIDU_APP_SECRET: str = ""
    BAIDU_OAUTH_URL: str = "https://exam.baidu.com/oauth.html"
    BAIDU_TOKEN_URL: str = "https://exam.baidu.com/oauth/token"
    BAIDU_API_BASE_URL: str = "https://exam.baidu.com/rest/2.0"
    BAIDU_CALLBACK_URL: str = "http://localhost:8000/api/v1/ad/baidu/callback"
    
    # ==================== 文件存储配置 ====================
    STORAGE_TYPE: str = "local"  # local | cos | minio
    LOCAL_STORAGE_PATH: str = "./uploads"
    COS_SECRET_ID: Optional[str] = None
    COS_SECRET_KEY: Optional[str] = None
    COS_BUCKET: Optional[str] = None
    COS_REGION: Optional[str] = None
    
    # ==================== 邮件配置 ====================
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"
    
    # ==================== CORS 配置 ====================
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # ==================== 限流配置 ====================
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # ==================== 管理员密钥 (初始化用) ====================
    ADMIN_INIT_KEY: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    """获取单例配置实例"""
    return Settings()


# 全局配置实例
settings = get_settings()
