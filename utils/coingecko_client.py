import requests
import time
from datetime import datetime, timedelta
import click
from utils.local_cache import LocalCache

# 核心封装类保持不变
class CoinGeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, retry=3, timeout=10, cache_ttl=300):
        self.session = requests.Session()
        self.retry = retry
        self.timeout = timeout
        self.cache = LocalCache(ttl=cache_ttl)

    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        # 创建缓存键
        cache_key = (url, tuple(sorted((params or {}).items())))
        
        # 尝试从缓存获取
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        for i in range(self.retry):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    result = resp.json()
                    # 将结果存入缓存
                    self.cache.set(cache_key, result)
                    return result
                else:
                    click.secho(
                        f"[WARN] Request failed ({resp.status_code}): {resp.text}",
                        fg="yellow",
                    )
            except Exception as e:
                click.secho(f"[ERROR] Attempt {i + 1}/{self.retry} failed: {e}", fg="red")
            time.sleep(1)
        raise ConnectionError(f"Failed to fetch data from {url}")

    def get_price(self, ids, vs_currencies="usd"):
        params = {"ids": ids, "vs_currencies": vs_currencies}
        return self._get("simple/price", params=params)

    def get_market(self, vs_currency="usd", per_page=10, page=1):
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": False,
        }
        return self._get("coins/markets", params=params)

    def get_history(self, coin_id, date):
        try:
            target_date = datetime.strptime(date, "%d-%m-%Y")
            if target_date < datetime.now() - timedelta(days=365):
                click.secho("❌ 免费API只能访问过去365天的数据，请选择更近的日期。", fg="red")
                return None
        except ValueError:
            click.secho("⚠️ 日期格式错误，应为 'dd-mm-yyyy'，例如 '01-01-2025'", fg="yellow")
            return None

        params = {"date": date}
        return self._get(f"coins/{coin_id}/history", params=params)

client = CoinGeckoClient()