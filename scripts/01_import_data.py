import csv
import time
import psycopg2

# 1. 連線至 Docker 內的 PostgreSQL
conn = psycopg2.connect("host=localhost dbname=stressdb user=postgres password=test1234 port=5432")
cur = conn.cursor()

csv_file_path = 'taxi_data.csv'

print("開始建立資料表並匯入數據...")
start_time = time.time()

with open(csv_file_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    
    # 根據 CSV 標頭動態建立資料表
    columns = [f'"{h}" TEXT' for h in headers]
    create_table_query = f"CREATE TABLE IF NOT EXISTS taxi_trips ({', '.join(columns)});"
    cur.execute(create_table_query)
    conn.commit()

# 2. 使用 PostgreSQL 的 COPY 指令超高速匯入（免通過 NumPy/Pandas）
with open(csv_file_path, 'r', encoding='utf-8') as f:
    cur.copy_expert("COPY taxi_trips FROM STDIN WITH CSV HEADER", f)
    conn.commit()

end_time = time.time()

# 查詢總筆數
cur.execute("SELECT count(*) FROM taxi_trips;")
total_rows = cur.fetchone()[0]

print(f"\n✅ 成功！共匯入 {total_rows:,} 筆數據到 'taxi_trips' 資料表！")
print(f"總耗時: {end_time - start_time:.2f} 秒")

cur.close()
conn.close()