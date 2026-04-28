"""
巨量引擎服务测试
"""
import pytest

from app.services.juliang_service import JuliangService, JuliangOAuthToken


class TestJuliangService:
    """巨量引擎服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return JuliangService(
            app_id="test_app_id",
            app_secret="test_app_secret",
            callback_url="http://localhost:8000/callback",
        )
    
    def test_build_oauth_url(self, service):
        """测试构建 OAuth URL"""
        state = "test_state_123"
        url = service.build_oauth_url(state)
        
        assert "app_id=test_app_id" in url
        assert "redirect_uri=" in url
        assert "state=test_state_123" in url
        assert "scope=" in url
    
    def test_set_tokens(self, service):
        """测试设置 Token"""
        service.set_tokens("access_token", "refresh_token")
        
        assert service._access_token == "access_token"
        assert service._refresh_token == "refresh_token"


class TestJuliangOAuthToken:
    """OAuth Token 数据类测试"""
    
    def test_token_creation(self):
        """测试 Token 创建"""
        token = JuliangOAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_in=86400,
            advertiser_ids=["123456"],
            request_id="req_123",
        )
        
        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.expires_in == 86400
        assert "123456" in token.advertiser_ids


class TestJuliangAdDailyStat:
    """广告数据统计测试"""
    
    def test_daily_stat_creation(self):
        """测试每日统计数据创建"""
        from app.services.juliang_service import JuliangAdDailyStat
        
        stat = JuliangAdDailyStat(
            date="2024-04-01",
            campaign_id="12345",
            campaign_name="测试计划",
            impressions=10000,
            clicks=500,
            spend=1000.50,
            form_submit=50,
            ctr=5.0,
            cpc=2.0,
            cpm=100.05,
        )
        
        assert stat.date == "2024-04-01"
        assert stat.spend == 1000.50
        assert stat.ctr == 5.0