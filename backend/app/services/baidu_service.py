"""
百度营销 API 服务封装
官方文档: https://developer.baidu.com/wiki/index.php?title=docs/cplat/rm/api
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import AdPlatformError


@dataclass
class BaiduOAuthToken:
    """百度营销 OAuth Token 响应"""
    access_token: str
    refresh_token: str
    expires_in: int       # 有效期（秒）
    session_key: str      # 百度特有：会话密钥
    scope: str


@dataclass
class BaiduAccount:
    """百度营销广告账户信息"""
    user_id: str
    username: str
    status: str
    balance: float        # 账户余额（元）


@dataclass
class BaiduAdDailyStat:
    """百度营销广告数据（每日汇总）"""
    date: str
    campaign_id: str
    campaign_name: str
    impressions: int
    clicks: int
    spend: float          # 花费（元）
    form_submit: int      # 转化数
    ctr: float
    cpc: float


class BaiduService:
    """
    百度营销 API 服务封装

    功能:
    1. OAuth 2.0 授权
    2. 获取广告账户信息
    3. 获取广告数据报告
    4. 自动 Token 刷新
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        callback_url: Optional[str] = None,
    ):
        self.app_id = app_id or settings.BAIDU_APP_ID
        self.app_secret = app_secret or settings.BAIDU_APP_SECRET
        self.callback_url = callback_url or settings.BAIDU_CALLBACK_URL
        self.api_base = settings.BAIDU_API_BASE_URL
        self.oauth_url = settings.BAIDU_OAUTH_URL
        self.token_url = settings.BAIDU_TOKEN_URL

        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    def build_oauth_url(self, state: str) -> str:
        """
        构建百度营销 OAuth 授权 URL

        Args:
            state: 随机状态字符串，防止 CSRF

        Returns:
            授权跳转 URL
        """
        params = {
            "response_type": "code",
            "client_id": self.app_id,
            "redirect_uri": self.callback_url,
            "state": state,
            "scope": "basic",
            "display": "popup",
        }
        return f"{self.oauth_url}?{urlencode(params)}"

    async def exchange_token(self, auth_code: str) -> BaiduOAuthToken:
        """
        通过授权码换取 Access Token

        Args:
            auth_code: OAuth 回调返回的授权码

        Returns:
            BaiduOAuthToken 对象

        Raises:
            AdPlatformError: Token 交换失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": auth_code,
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "redirect_uri": self.callback_url,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise AdPlatformError(
                        platform="baidu",
                        detail=data.get("error_description", "Token 交换失败"),
                        platform_code=data.get("error"),
                    )

                return BaiduOAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", ""),
                    expires_in=int(data.get("expires_in", 2592000)),
                    session_key=data.get("session_key", ""),
                    scope=data.get("scope", ""),
                )

            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="baidu",
                    detail=f"Token 交换请求失败: {str(e)}",
                )

    async def refresh_access_token(self, refresh_token: str) -> BaiduOAuthToken:
        """刷新 Access Token"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise AdPlatformError(
                        platform="baidu",
                        detail=data.get("error_description", "Token 刷新失败"),
                        platform_code=data.get("error"),
                    )

                return BaiduOAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", refresh_token),
                    expires_in=int(data.get("expires_in", 2592000)),
                    session_key=data.get("session_key", ""),
                    scope=data.get("scope", ""),
                )

            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="baidu",
                    detail=f"Token 刷新请求失败: {str(e)}",
                )

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        """设置 Token（从数据库恢复时使用）"""
        self._access_token = access_token
        self._refresh_token = refresh_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        access_token: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """通用 API 请求方法"""
        token = access_token or self._access_token
        if not token:
            raise AdPlatformError(platform="baidu", detail="缺少 Access Token")

        url = f"{self.api_base}{endpoint}"
        params = kwargs.pop("params", {})
        params["access_token"] = token

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    **kwargs,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("header", {}).get("desc", "") not in ("", "success"):
                    raise AdPlatformError(
                        platform="baidu",
                        detail=data.get("header", {}).get("desc", "API 请求失败"),
                        platform_code=str(data.get("header", {}).get("failures", "")),
                    )

                return data.get("body", data)

            except httpx.HTTPError as e:
                raise AdPlatformError(
                    platform="baidu",
                    detail=f"API 请求失败: {str(e)}",
                )

    async def get_account_info(
        self,
        access_token: Optional[str] = None,
    ) -> BaiduAccount:
        """
        获取账户基本信息

        Args:
            access_token: 访问令牌

        Returns:
            BaiduAccount 对象
        """
        data = await self._request(
            "GET",
            "/baidu/sem/account/v13/account/info/get",
            access_token=access_token,
        )

        account_info = data.get("accountinfo", {})
        return BaiduAccount(
            user_id=str(account_info.get("userid", "")),
            username=account_info.get("username", "百度推广账户"),
            status=account_info.get("status", "unknown"),
            balance=float(account_info.get("budget", 0)),
        )

    async def get_daily_stats(
        self,
        advertiser_id: str,
        days: int = 7,
        access_token: Optional[str] = None,
    ) -> list[BaiduAdDailyStat]:
        """
        获取最近 N 天的广告数据（计划级）

        Args:
            advertiser_id: 广告主 ID（百度营销中即用户 ID）
            days:          天数
            access_token:  访问令牌

        Returns:
            每日统计数据列表
        """
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        data = await self._request(
            "POST",
            "/baidu/sem/report/v13/reportrecord/getReportFile",
            access_token=access_token,
            json={
                "reportFileId": None,
                "reportFileFormat": "json",
                "reportType": "PLAN",
                "unitOfTime": "DAY",
                "startDate": start_date,
                "endDate": end_date,
                "performanceIndex": [
                    "date", "planId", "planName",
                    "impression", "click", "cost",
                    "ctr", "avgCpc",
                ],
            },
        )

        stats = []
        for item in data.get("reportFileList", []):
            stats.append(BaiduAdDailyStat(
                date=str(item.get("date", ""))[:10],  # YYYYMMDD → YYYY-MM-DD
                campaign_id=str(item.get("planId", "")),
                campaign_name=item.get("planName", ""),
                impressions=int(item.get("impression", 0)),
                clicks=int(item.get("click", 0)),
                spend=float(item.get("cost", 0)),
                form_submit=int(item.get("conversion", 0)),
                ctr=float(item.get("ctr", 0)),
                cpc=float(item.get("avgCpc", 0)),
            ))

        return stats


# 全局单例（懒加载）
_baidu_service: Optional[BaiduService] = None


def get_baidu_service() -> BaiduService:
    """获取百度营销服务单例"""
    global _baidu_service
    if _baidu_service is None:
        _baidu_service = BaiduService()
    return _baidu_service
