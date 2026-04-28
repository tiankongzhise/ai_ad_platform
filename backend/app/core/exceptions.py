"""
统一异常处理
"""
from typing import Any, Optional

from fastapi import HTTPException, status


class EduAdCRMException(HTTPException):
    """业务异常基类"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: Optional[str] = None,
        extra: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.extra = extra or {}


class AuthenticationError(EduAdCRMException):
    """认证错误"""
    
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="AUTH_ERROR",
        )


class AuthorizationError(EduAdCRMException):
    """授权错误"""
    
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="AUTHZ_ERROR",
        )


class ResourceNotFoundError(EduAdCRMException):
    """资源不存在"""
    
    def __init__(self, resource: str = "资源", resource_id: Optional[str] = None):
        detail = f"{resource}不存在"
        if resource_id:
            detail = f"{resource} [{resource_id}] 不存在"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code="NOT_FOUND",
        )


class ValidationError(EduAdCRMException):
    """数据验证错误"""
    
    def __init__(self, detail: str = "数据验证失败", field: Optional[str] = None):
        extra = {"field": field} if field else {}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code="VALIDATION_ERROR",
            extra=extra,
        )


class AdPlatformError(EduAdCRMException):
    """广告平台API错误"""
    
    def __init__(
        self,
        platform: str,
        detail: str,
        platform_code: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"[{platform}] {detail}",
            code=f"AD_PLATFORM_ERROR_{platform.upper()}",
            extra={"platform": platform, "platform_code": platform_code},
        )


class TokenExpiredError(AuthenticationError):
    """Token 过期"""
    
    def __init__(self):
        super().__init__(detail="Token 已过期，请重新登录")


class DuplicateResourceError(EduAdCRMException):
    """资源重复"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} [{identifier}] 已存在",
            code="DUPLICATE_RESOURCE",
        )
