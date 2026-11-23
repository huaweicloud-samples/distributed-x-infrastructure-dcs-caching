"""读取电影推荐（FunctionGraph 函数）。

从 DCS（Redis）按 userId + rank 读取推荐电影，通过 redis.Redis 连接（REDIS_URL 连接串）。
"""

import os

import redis


def handler(event, context):
    try:
        if "queryStringParameters" not in event:
            raise Exception("userId and rank is not in the input provided")
        params = event["queryStringParameters"]
        if "userId" not in params:
            raise Exception("UserId is not in the input provided")
        if "rank" not in params:
            raise Exception("Movie rank is not in the input provided")

        user_id = params["userId"]
        rank = params["rank"]
        r = connect()

        result = r.hget(user_id, rank)
        if result is None:
            return {
                "statusCode": 200,
                "body": f"There is no number {rank} recommended movie for user {user_id} ",
            }
        return {
            "statusCode": 200,
            "body": f"The number {rank} recommended movie for user {user_id} is {result}",
        }
    except Exception as e:
        return {"statusCode": 500, "body": f"Found an exception: '{e}'"}


def connect():
    return redis.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )