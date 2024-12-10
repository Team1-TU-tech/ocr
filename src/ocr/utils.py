import redis

def connect_to_redis():
    """
    Redis 서버에 연결하는 함수
    :return: Redis 클라이언트 객체
    """
    try:
        return redis.StrictRedis(
            host='redis',  # Redis 컨테이너의 호스트 이름
            port=6379,
            decode_responses=True
        )
    except redis.ConnectionError as e:
        print(f"Redis 연결 오류: {e}")
        raise

def get_last_id_from_redis(name, default_id=49640):
    r = connect_to_redis()
    key = f'{name}_last_processed_id' 
    last_id = r.get(key)
    if last_id is None:
        r.set(key, default_id)  # Redis에 기본값 설정
        return default_id
    return int(last_id)

def update_last_id_in_redis(name, new_id):
    r = connect_to_redis()
    key = f'{name}_last_processed_id'
    r.set(key, new_id)
    print(f"마지막 처리된 ID를 Redis에 업데이트했습니다. {name}: {new_id}")
