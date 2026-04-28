"""
巨量引擎 API 服务封装
官方文档: https://open.oceanengine.com/lubianks
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import AdPlatformError


@dataclass
class JuliangOAuthToken:
    """巨量引擎 OAuth Token 响应"""
    access_token: str
    refresh_token: str
    expires_in: int  # 有效期（秒）
    advertiser_ids: list[str]  # 授权的广告主ID列表
    request_id: str


@dataclass
class JuliangAdvertiser:
    """巨量引擎广告账户信息"""
    advertiser_id: str
    advertiser_name: str
    advertiser_type: str
    country: str
    status: str
    balance: float


@dataclass
class JuliangCampaign:
    """巨量引擎广告计划"""
    campaign_id: str
    campaign_name: str
    budget: float
    budget_mode: str
    status: str
    bid_type: str


@dataclass
class JuliangAdDailyStat:
    """巨量引擎广告数据（每日汇总）"""
    date: str  # YYYY-MM-DD
    campaign_id: str
    campaign_name: str
    impressions: int
    clicks: int
    spend: float  # 花费（元）
    form_submit: int  # 表单提交数
    ctr: float  # 点击率
    cpc: float  # 点击单价
    cpm: float  # 千次展示成本


class JuliangService:
    """
    巨量引擎 API 服务封装
    
    功能:
    1. OAuth 2.0 授权
    2. 获取广告账户列表
    3. 获取广告数据报告
    4. 自动 Token 刷新
    """
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        callback_url: Optional[str] = None,
    ):
        self.app_id = app_id or settings.JULIANG_APP_ID
        self.app_secret = app_secret or settings.JULIANG_APP_SECRET
        self.callback_url = callback_url or settings.JULIANG_CALLBACK_URL
        self.api_base = settings.JULIANG_API_BASE_URL
        self.oauth_url = settings.JULIANG_OAUTH_URL
        self.token_url = settings.JULIANG_TOKEN_URL
        
        # 缓存的 Token
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
    
    def build_oauth_url(self, state: str) -> str:
        """
        构建巨量引擎 OAuth 授权 URL
        
        Args:
            state: 随机状态字符串，用于防止 CSRF
        
        Returns:
            授权跳转 URL
        """
        params = {
            "app_id": self.app_id,
            "redirect_uri": self.callback_url,
            "state": state,
            "scope": "ad_report advert_management",
        }
        return f"{self.oauth_url}?{urlencode(params)}"
    
    async def exchange_token(self, auth_code: str) -> JuliangOAuthToken:
        """
        通过授权码换取 Access Token
        
        Args:
            auth_code: OAuth 回调返回的授权码
        
        Returns:
            OAuthToken 对象
        
        Raises:
            AdPlatformError: Token 交换失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret,
                        "grant_type": "authorization_code",
                        "authorization_code": auth_code,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("code", 0) != 0:
                    raise AdPlatformError(
                        platform="juliang",
                        detail=data.get("message", "Token 交换失败"),
                        platform_code=str(data.get("code")),
                    )
                
                return JuliangOAuthToken(
                    access_token=data["data"]["access_token"],
                    refresh_token=data["data"]["refresh_token"],
                    expires_in=data["data"]["expires_in"],
                    advertiser_ids=data["data"].get("advertiser_ids", []),
                    request_id=data.get("request_id", ""),
                )
                
            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="juliang",
                    detail=f"Token 交换请求失败: {str(e)}",
                )
    
    async def refresh_access_token(self, refresh_token: str) -> JuliangOAuthToken:
        """
        刷新 Access Token
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的 OAuthToken 对象
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("code", 0) != 0:
                    raise AdPlatformError(
                        platform="juliang",
                        detail=data.get("message", "Token 刷新失败"),
                        platform_code=str(data.get("code")),
                    )
                
                return JuliangOAuthToken(
                    access_token=data["data"]["access_token"],
                    refresh_token=data["data"]["refresh_token"],
                    expires_in=data["data"]["expires_in"],
                    advertiser_ids=data["data"].get("advertiser_ids", []),
                    request_id=data.get("request_id", ""),
                )
                
            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="juliang",
                    detail=f"Token 刷新请求失败: {str(e)}",
                )
    
    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        """设置 Token（用于数据库恢复）"""
        self._access_token = access_token
        self._refresh_token = refresh_token
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        access_token: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        通用 API 请求方法
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            access_token: 访问令牌
            **kwargs: 传递给 httpx 的其他参数
        
        Returns:
            API 响应数据
        """
        token = access_token or self._access_token
        if not token:
            raise AdPlatformError(
                platform="juliang",
                detail="缺少 Access Token",
            )
        
        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Access-Token"] = token
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("code", 0) != 0:
                    raise AdPlatformError(
                        platform="juliang",
                        detail=data.get("message", "API 请求失败"),
                        platform_code=str(data.get("code")),
                    )
                
                return data.get("data", {})
                
            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="juliang",
                    detail=f"API 请求失败: {str(e)}",
                )
    
    async def get_advertiser_list(
        self,
        access_token: Optional[str] = None,
    ) -> list[JuliangAdvertiser]:
        """
        获取广告主账户列表
        
        Args:
            access_token: 访问令牌
        
        Returns:
            广告账户列表
        """
        data = await self._request(
            "GET",
            "/advertiser/v2/info/",
            access_token=access_token,
        )
        
        advertisers = []
        for item in data if isinstance(data, list) else []:
            advertisers.append(JuliangAdvertiser(
                advertiser_id=str(item.get("advertiser_id", "")),
                advertiser_name=item.get("advertiser_name", ""),
                advertiser_type=item.get("advertiser_type", ""),
                country=item.get("country", ""),
                status=item.get("status", ""),
                balance=float(item.get("balance", 0)) / 100,  # 转换为元
            ))
        
        return advertisers
    
    async def get_campaign_list(
        self,
        advertiser_id: str,
        access_token: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[JuliangCampaign], int]:
        """
        获取广告计划列表
        
        Args:
            advertiser_id: 广告主ID
            access_token: 访问令牌
            page: 页码
            page_size: 每页数量
        
        Returns:
            (广告计划列表, 总数)
        """
        data = await self._request(
            "GET",
            "/campaign/v2/list/",
            access_token=access_token,
            params={
                "advertiser_id": advertiser_id,
                "page": page,
                "page_size": page_size,
            },
        )
        
        campaigns = []
        for item in data.get("list", []):
            campaigns.append(JuliangCampaign(
                campaign_id=str(item.get("campaign_id", "")),
                campaign_name=item.get("campaign_name", ""),
                budget=float(item.get("budget", 0)) / 100,
                budget_mode=item.get("budget_mode", ""),
                status=item.get("status", ""),
                bid_type=item.get("bid_type", ""),
            ))
        
        total = data.get("page_info", {}).get("total", len(campaigns))
        return campaigns, total
    
    async def get_report(
        self,
        advertiser_id: str,
        start_date: str,
        end_date: str,
        access_token: Optional[str] = None,
        level: str = "CAMPAIGN",  # CAMPAIGN | ADGROUP | AD
        page: int = 1,
        page_size: int = 1000,
    ) -> list[dict]:
        """
        获取广告数据报告
        
        Args:
            advertiser_id: 广告主ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            access_token: 访问令牌
            level: 报告层级 (CAMPAIGN=计划级, ADGROUP=单元级, AD=广告级)
            page: 页码
            page_size: 每页数量
        
        Returns:
            报告数据列表
        """
        data = await self._request(
            "POST",
            "/report/v2/ad/",
            access_token=access_token,
            json={
                "advertiser_id": advertiser_id,
                "start_date": start_date,
                "end_date": end_date,
                "level": level,
                "page": page,
                "page_size": page_size,
                "fields": [
                    "date", "campaign_id", "campaign_name",
                    "impressions", "clicks", "cost",
                    "form_submit", "ctr", "cpc", "cpm",
                ],
            },
        )
        
        return data.get("list", [])
    
    async def get_daily_stats(
        self,
        advertiser_id: str,
        days: int = 7,
        access_token: Optional[str] = None,
    ) -> list[JuliangAdDailyStat]:
        """
        获取最近N天的广告数据
        
        Args:
            advertiser_id: 广告主ID
            days: 天数（默认7天）
            access_token: 访问令牌
        
        Returns:
            每日统计数据列表
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 巨量引擎限制单次查询最多90天
        if days > 90:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        report_data = await self.get_report(
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            access_token=access_token,
            level="CAMPAIGN",
        )
        
        stats = []
        for item in report_data:
            stats.append(JuliangAdDailyStat(
                date=item.get("date", ""),
                campaign_id=str(item.get("campaign_id", "")),
                campaign_name=item.get("campaign_name", ""),
                impressions=int(item.get("impressions", 0)),
                clicks=int(item.get("clicks", 0)),
                spend=float(item.get("cost", 0)) / 100,  # 分转元
                form_submit=int(item.get("form_submit", 0)),
                ctr=float(item.get("ctr", 0)),
                cpc=float(item.get("cpc", 0)) / 100,  # 分转元
                cpm=float(item.get("cpm", 0)) / 100,  # 分转元
            ))
        
        return stats
    
    async def get_balance(
        self,
        advertiser_id: str,
        access_token: Optional[str] = None,
    ) -> float:
        """
        获取广告账户余额
        
        Args:
            advertiser_id: 广告主ID
            access_token: 访问令牌
        
        Returns:
            余额（元）
        """
        data = await self._request(
            "GET",
            "/advertiser/v2/info/",
            access_token=access_token,
            params={"advertiser_ids": advertiser_id},
        )
        
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0].get("balance", 0)) / 100
        
        return 0.0


# 全局单例（懒加载）
_juliang_service: Optional[JuliangService] = None


def get_juliang_service() -> JuliangService:
    """获取巨量引擎服务单例"""
    global _juliang_service
    if _juliang_service is None:
        _juliang_service = JuliangService()
    return _juliang_service
