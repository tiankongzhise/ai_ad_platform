"""
广告账户 API 测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app


class TestAdAccountsAPI:
    """广告账户 API 测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth(self):
        """模拟认证"""
        with patch("app.core.tenant.get_current_user") as mock:
            mock.return_value = {
                "user_id": "test_user",
                "tenant_id": "test_tenant",
            }
            yield mock
    
    def test_get_oauth_url_requires_auth(self, client):
        """测试获取 OAuth URL 需要认证"""
        # 不带 Token 的请求应该返回 401
        response = client.get("/api/v1/ad/juliang/oauth-url")
        assert response.status_code == 401
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        assert "version" in response.json()


class TestOAuthCallback:
    """OAuth 回调测试"""
    
    @pytest.fixture
    def mock_juliang_service(self):
        """模拟巨量引擎服务"""
        with patch("app.services.juliang_service.get_juliang_service") as mock:
            service = MagicMock()
            service.exchange_token = AsyncMock(
                return_value=MagicMock(
                    access_token="test_token",
                    refresh_token="test_refresh",
                    expires_in=86400,
                    advertiser_ids=["123456"],
                    request_id="req_123",
                )
            )
            service.get_advertiser_list = AsyncMock(
                return_value=[
                    MagicMock(
                        advertiser_id="123456",
                        advertiser_name="测试账户",
                        balance=1000.0,
                    )
                ]
            )
            mock.return_value = service
            yield service


class TestSyncStatus:
    """同步状态测试"""
    
    def test_sync_status_requires_auth(self):
        """测试同步状态需要认证"""
        client = TestClient(app)
        response = client.get("/api/v1/ad/sync-status")
        assert response.status_code == 401