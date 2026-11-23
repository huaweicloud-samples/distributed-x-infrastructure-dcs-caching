"""数据库查询缓存（Database Caching）示例。

演示「缓存旁路（cache-aside）」模式：查询先查 DCS（Redis）缓存，
未命中则回源 RDS（MySQL），并把结果写入缓存设置 TTL。
"""

import os
import json

import redis
import pymysql


class DB:
    def __init__(self, **params):
        params.setdefault("charset", "utf8mb4")
        params.setdefault("cursorclass", pymysql.cursors.DictCursor)
        self.mysql = pymysql.connect(**params)

    def query(self, sql):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def record(self, sql, values):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.fetchone()


# 缓存数据的存活时间（秒）；设 3600 便于从容验证，演示过期可改回 10
TTL = 3600

# 缓存连接：从 REDIS_URL 读取（DCS Redis 连接串，形如 redis://:password@host:6379/0）
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# 回源数据库：从 DB_* 环境变量读取（RDS MySQL）
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "tutorial")

Database = DB(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
Cache = redis.Redis.from_url(REDIS_URL)


def fetch(sql):
    """整表查询：先查缓存，未命中回源数据库并回填。"""
    res = Cache.get(sql)
    if res:
        return json.loads(res)

    res = Database.query(sql)
    Cache.setex(sql, TTL, json.dumps(res))
    return res


def planet(planet_id):
    """单条记录查询：缓存用 hash 结构存储行星记录。"""
    key = f"planet:{planet_id}"
    res = Cache.hgetall(key)
    if res:
        return res

    sql = "SELECT `id`, `name` FROM `planet` WHERE `id`=%s"
    res = Database.record(sql, (planet_id,))

    if res:
        # hset(mapping=...) 兼容 redis-py 4.x / 5.x
        Cache.hset(key, mapping=res)
        Cache.expire(key, TTL)

    return res


if __name__ == "__main__":
    print(fetch("SELECT * FROM planet"))
    print(planet(1))
    print(planet(2))
    print(planet(3))