import time
import psycopg2

DB_CONFIG = "host=localhost dbname=stressdb user=postgres password=test1234 port=5432"
BATCH_SIZE = 100000  # 每批次處理 10 萬筆，避免記憶體溢出
TOTAL_LIMIT = 1000000 # 總共遷移 100 萬筆

def run_migration():
    print(f"🚀 開始執行資料遷移 (Data Migration) 實驗...")
    print(f"目標：從舊表遷移 {TOTAL_LIMIT:,} 筆資料至精簡版新表結構\n")
    
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()
    
    # 1. 建立全新優化結構的目標表 (v2)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS taxi_trips_v2 (
        id SERIAL PRIMARY KEY,
        passenger_count INT,
        trip_distance NUMERIC(10, 2),
        fare_amount NUMERIC(10, 2)
    );
    """)
    cur.execute("TRUNCATE TABLE taxi_trips_v2;") # 清空舊資料
    conn.commit()
    
    start_time = time.time()
    migrated_rows = 0
    
    # 2. 批次 (Batch) 寫入資料
    while migrated_rows < TOTAL_LIMIT:
        batch_start = time.time()
        
        insert_sql = """
        INSERT INTO taxi_trips_v2 (passenger_count, trip_distance, fare_amount)
        SELECT 
            passenger_count, 
            trip_distance, 
            fare_amount
        FROM taxi_trips
        OFFSET %s LIMIT %s;
        """
        cur.execute(insert_sql, (migrated_rows, BATCH_SIZE))
        conn.commit()
        
        migrated_rows += BATCH_SIZE
        batch_end = time.time()
        print(f"📦 已成功遷移 {migrated_rows:,} / {TOTAL_LIMIT:,} 筆資料 (本批次耗時: {batch_end - batch_start:.2f} 秒)")

    total_time = time.time() - start_time
    throughput = TOTAL_LIMIT / total_time
    
    print("\n======== 📊 資料遷移 (Data Migration) 結果 ========")
    print(f"遷移總筆數    : {TOTAL_LIMIT:,} 筆")
    print(f"遷移總耗時    : {total_time:.2f} 秒")
    print(f"遷移吞吐量    : {throughput:,.2f} 筆/秒 (Rows/sec)")
    print("====================================================")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_migration()