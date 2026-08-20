from fastapi.testclient import TestClient
from API.main import app

# 1. 測試根目錄端點
def test_read_main():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API 服務正常運作中！"}

# 2. 測試取得行程列表端點 (/trips)
def test_get_trips():
    with TestClient(app) as client:
        response = client.get("/trips?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

# 3. 測試統計摘要端點 (/stats/analytics)
def test_get_summary():
    with TestClient(app) as client:
        response = client.get("/stats/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "total_trips" in data