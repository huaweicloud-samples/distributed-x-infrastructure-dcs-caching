"""写入电影推荐（FunctionGraph 函数）。

从 OBS 拉取批量预测结果，写入 DCS（Redis），使用 OBS SDK（esdk-obs-python，FunctionGraph 运行期内置）。
"""

import json
import os

import redis
from obs import ObsClient


def handler(event, context):
    try:
        bucket = os.environ["OBS_BUCKET"]
        key = os.environ.get("PREDICTIONS_KEY", "batchpredictions.json")

        user_predictions = _read_predictions_from_obs(bucket, key)
        users = user_predictions["data"]

        r = connect()
        for user in users:
            mapping = {}
            for idx, movie_id in enumerate(user["movieId"], start=1):
                mapping[idx] = movie_id
            r.hset(user["userId"], mapping=mapping)

        return "Successfully inserted the user recommendations"
    except Exception as e:
        return f"Failed to insert the user recommendations due to {e}"


def _read_predictions_from_obs(bucket, key):
    obs_client = ObsClient(
        access_key_id=os.environ.get("HW_ACCESS_KEY"),
        secret_access_key=os.environ.get("HW_SECRET_KEY"),
        server=f"https://obs.{os.environ.get('REGION', 'cn-north-4')}.myhuaweicloud.com",
    )
    resp = obs_client.getObject(bucket, key, loadStreamInMemory=True)
    if resp.status >= 300:
        raise RuntimeError(f"OBS getObject failed: {resp.errorCode} {resp.errorMessage}")
    return json.loads(resp.body.buffer.decode("utf-8"))


def connect():
    return redis.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )