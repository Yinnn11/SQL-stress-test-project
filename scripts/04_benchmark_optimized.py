import time  # 匯入時間模組：用來記錄程式跑了多久（計算秒數）
import psycopg2  # 匯入 PostgreSQL 資料庫的連接套件：負責讓 Python 與 Docker 裡面的資料庫對話
from concurrent.futures import (
    ThreadPoolExecutor,
)  # 匯入多執行緒模組：用來模擬「多個使用者同時造訪」

# ==========================================
# 1. 基本設定區
# ==========================================

# 資料庫連線設定字串：包含主機位置(localhost)、資料庫名稱(stressdb)、帳號(postgres)、密碼(test1234)、連接埠(5432)
DB_CONFIG = (
    "host=localhost dbname=stressdb user=postgres password=test1234 port=5432"
)

# 併發使用者數量：設定為 20，代表模擬 20 個人「在同一時間」按下按鈕發送查詢
CONCURRENT_USERS = 20

# 測試用的 SQL 查詢語法：
# 這段 SQL 的意思是：「請幫我從 1,270 萬筆資料中，找出『乘客數>=2 人』且『搭乘距離>5 英哩』的資料，
# 並按照『人數』分組，計算出他們的平均距離與平均車資。」
# 💡 觀念說明：因為現在資料庫『沒有建立索引』，資料庫為了算出結果，必須把 1,270 萬筆資料「從頭到尾每一筆都翻過一次」，
# 這在資料庫術語中稱為「全表掃描 (Sequential Scan)」，是非常消耗 CPU 與時間的操作！
# 修正後的 TEST_QUERY：加上 ::numeric 轉型，並加上 ::integer 做比較
TEST_QUERY = """
SELECT 
    passenger_count, 
    AVG(trip_distance) as avg_dist, 
    AVG(fare_amount) as avg_fare
FROM taxi_trips
WHERE passenger_count = 2 
  AND trip_distance > 50.0
GROUP BY passenger_count;
"""


# ==========================================
# 2. 模擬「單一使用者」發送請求的函數 (Function)
# ==========================================
def run_query(user_id):
    """這個函式代表『一個使用者』打開網頁、向資料庫發送查詢、並拿到結果的完整過程"""

    start = time.time()  # 記錄這個使用者「開始查詢」的時間點

    try:
        # 步驟 A: 建立與 PostgreSQL 資料庫的連線
        conn = psycopg2.connect(DB_CONFIG)

        # 步驟 B: 建立游標 (Cursor)，這是用來執行 SQL 語法的工具
        cur = conn.cursor()

        # 步驟 C: 將 SQL 語法送到資料庫執行
        cur.execute(TEST_QUERY)

        # 步驟 D: 抓取資料庫傳回來的查詢結果
        cur.fetchall()

        # 步驟 E: 查詢完畢，把游標與連線關閉，釋放記憶體資源
        cur.close()
        conn.close()

        # 計算這個使用者總共花了多少秒才收到結果
        duration = time.time() - start

        # 回傳：(耗時秒數, 是否成功)
        return duration, True

    except Exception as e:
        # 如果查詢過程中發生錯誤（例如資料庫塞爆斷線），印出錯誤訊息
        print(f"使用者 {user_id} 查詢失敗: {e}")
        return 0, False


# ==========================================
# 3. 主程式執行區（壓力測試核心）
# ==========================================
if __name__ == "__main__":
    print(
        f"🔥 開始執行壓力測試！模擬 {CONCURRENT_USERS} 個使用者同時衝進資料庫..."
    )

    # 記錄整個壓力測試開始的時間
    total_start_time = time.time()

    # 使用 ThreadPoolExecutor (線程池) 來實作「同時併發」
    # max_workers=20 代表開 20 個平行通道，同時讓 20 個 run_query 函式一起執行
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        # map 會把 0~19 這 20 個使用者 ID 分別交給 20 個通道同時執行，並蒐集他們的執行結果
        results = list(executor.map(run_query, range(CONCURRENT_USERS)))

    # 計算 20 個使用者「全部查詢完畢」的總共耗時
    total_duration = time.time() - total_start_time

    # 數據整理與統計：
    # 1. 整理出所有成功的查詢所花費的時間
    durations = [r[0] for r in results if r[1]]

    # 2. 算出一共有幾個使用者成功拿到資料
    success_count = sum(1 for r in results if r[1])

    # 3. 平均響應時間 (Avg Latency)：把所有人的耗時加起來除以成功人數，代表「平均每個使用者要等幾秒」
    avg_latency = sum(durations) / len(durations) if durations else 0

    # 4. 吞吐量 (TPS / Transactions Per Second)：計算「資料庫平均每秒能處理幾個請求」
    tps = success_count / total_duration if total_duration > 0 else 0

    # ==========================================
    # 4. 印出壓測報告
    # ==========================================
    print("\n======== 📊 壓力測試結果 (有索引 Baseline) ========")
    print(f"總成功請求數        : {success_count} / {CONCURRENT_USERS}")
    print(f"總共耗費時間        : {total_duration:.2f} 秒")
    print(
        f"平均響應時間(Latency): {avg_latency:.2f} 秒 (代表使用者平均要等這麼久)"
    )
    print(
        f"每秒處理請求數 (TPS) : {tps:.2f} req/sec (數字越高代表資料庫效能越強)"
    )
    print("====================================================")