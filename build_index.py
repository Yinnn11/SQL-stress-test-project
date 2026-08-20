import time
import psycopg2

DB_CONFIG = {
    "dbname": "stressdb",
    "user": "postgres",
    "password": "test1234",
    "host": "localhost",
    "port": "5432",
}

print("🚀 開始連線至 PostgreSQL 並建立複合索引...")
start_time = time.time()

try:
    conn = psycopg2.connect(**DB_CONFIG)
    # 設定 autocommit=True，CREATE INDEX 不可在交易區塊內執行
    conn.autocommit = True
    cur = conn.cursor()

    sql = """
    CREATE INDEX IF NOT EXISTS idx_trips_pickup_datetime_dist 
    ON taxi_trips (tpep_pickup_datetime DESC, trip_distance);
    """

    print("⏳ 正在對 12,700,000+ 筆資料建立 (tpep_pickup_datetime, trip_distance) 複合索引，請稍候...")
    cur.execute(sql)

    end_time = time.time()
    print(
        f"✅ 複合索引建立成功！耗時: {end_time - start_time:.2f} 秒"
    )

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ 建立索引失敗，錯誤訊息: {e}")