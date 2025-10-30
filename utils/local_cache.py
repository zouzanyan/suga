from diskcache import Cache
from threading import RLock
import os

class LocalCache:
    """
    本地磁盘缓存工具类，基于 diskcache 实现，支持 TTL、最大条目数
    """
    def __init__(self, maxsize=1000, ttl=60, cache_dir=None):
        """
        :param maxsize: 最大缓存条目数
        :param ttl: 默认过期时间（秒）
        :param cache_dir: 缓存目录路径，默认为项目目录下的 .cache
        """
        if cache_dir is None:
            # 默认使用项目目录下的 .cache 目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cache_dir = os.path.join(project_root, '.cache')
            
        self.cache = Cache(cache_dir)
        self.lock = RLock()  # 保证线程安全
        
        # 设置默认的 TTL 和最大大小
        self.default_ttl = ttl
        self.maxsize = maxsize
        
        # 配置缓存大小限制
        self.cache.reset('cull_limit', 0)  # 不自动清理
        self.cache.reset('size_limit', int(1e9))  # 1GB 大小限制
        self.cache.reset('eviction_policy', 'least-recently-stored')

    def set(self, key, value, ttl=None):
        """设置缓存，支持单条目 TTL"""
        with self.lock:
            expire_time = ttl if ttl is not None else self.default_ttl
            self.cache.set(key, value, expire_time)

    def get(self, key, default=None):
        """获取缓存"""
        with self.lock:
            return self.cache.get(key, default)

    def delete(self, key):
        """删除缓存"""
        with self.lock:
            self.cache.delete(key)

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

# 使用示例
if __name__ == "__main__":
    cache = LocalCache(maxsize=100, ttl=5)  # TTL 5 秒
    cache.set("foo", "bar")
    print(cache.get("foo"))  # bar
    import time
    time.sleep(6)
    print(cache.get("foo"))  # None