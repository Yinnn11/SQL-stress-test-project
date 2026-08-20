import concurrent.futures
import time
import requests

# 測試目標 API URL
API_URL = "http://127.0.0.1:8000/trips?limit=10"

# 設定併發參數
TOTAL_REQUESTS = 200  # 總請求次數
CONCURRENT_USERS = 20  # 同時併發的使用者數


def send_request():
    start_time = time.time()
    try:
        response = requests.get(API_URL)
        latency = time.time() - start_time
        return response.status_code == 200, latency
    except Exception:
        return False, time.time() - start_time


def run_stress_test():
    print(
        f"🚀 開始壓力測試：模擬 {CONCURRENT_USERS} 個併發使用者發送 {TOTAL_REQUESTS} 次請求..."
    )

    start_time = time.time()
    results = []

    # 使用 ThreadPoolExecutor 模擬併發發送 HTTP 請求
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=CONCURRENT_USERS
    ) as executor:
        futures = [
            executor.submit(send_request) for _ in range(TOTAL_REQUESTS)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    total_time = time.time() - start_time

    # 統計結果
    successes = sum(1 for success, _ in results if success)
    failures = TOTAL_REQUESTS - successes
    latencies = [lat for _, lat in results]
    avg_latency = sum(latencies) / len(latencies)
    rps = TOTAL_REQUESTS / total_time

    print("\n" + "=" * 40)
    print("📊 壓力測試結果報告 (Stress Test Results)")
    print("=" * 40)
    print(f"總執行時間: {total_time:.2f} 秒")
    print(f"成功請求數: {successes} / {TOTAL_REQUESTS}")
    print(f"失敗請求數: {failures}")
    print(f"每秒處理請求數 (RPS): {rps:.2f} req/sec")
    print(f"平均延遲時間 (Latency): {avg_latency * 1000:.2f} ms")
    print("=" * 40)


if __name__ == "__main__":
    run_stress_test()