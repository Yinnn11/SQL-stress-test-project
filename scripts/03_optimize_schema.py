import time
import psycopg2

DB_CONFIG = (
    "host=localhost dbname=stressdb user=postgres password=test1234 port=5432"
)

print("🔧 開始修復欄位資料型態 (將 TEXT 轉為 INTEGER 與 NUMERIC)...")
start_time = time.time()

conn = psycopg2.connect(DB_CONFIG)
cur = conn.cursor()

# 1. 移除舊的表達式索引
cur.execute("DROP INDEX IF EXISTS idx_passenger_distance;")

# 2. 修改欄位型態為原生數字 (這會花費約 10~20 秒)
print("⏳ 正在將 1,270 萬筆資料的欄位轉型為原生數字...")
alter_sql = """
ALTER TABLE taxi_trips 
  ALTER COLUMN passenger_count TYPE INTEGER USING (passenger_count::integer),
  ALTER COLUMN trip_distance TYPE NUMERIC USING (trip_distance::numeric),
  ALTER COLUMN fare_amount TYPE NUMERIC USING (fare_amount::numeric);
"""
cur.execute(alter_sql)
conn.commit()

# 3. 建立原生的標準 B-Tree 複合索引
print("⚡ 正在建立標準原生 B-Tree 複合索引...")
create_idx_sql = """
CREATE INDEX idx_passenger_distance_native 
ON taxi_trips (passenger_count, trip_distance);
"""
cur.execute(create_idx_sql)
conn.commit()

# 4. 更新統計數據
cur.execute("ANALYZE taxi_trips;")
conn.commit()

end_time = time.time()
print(f"✅ 修復成功！欄位型態與原生 B-Tree 索引已設定完畢，耗時: {end_time - start_time:.2f} 秒")

cur.close()
conn.close()