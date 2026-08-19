import matplotlib.pyplot as plt

# 壓測數據
categories = ['Baseline (Seq Scan)', 'Optimized (Index Scan)']
latency = [7.81, 0.07]  # 平均響應時間 (秒)
tps = [2.28, 117.52]    # 每秒處理請求數 (TPS)

# 設置畫布
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 圖 1: Latency 對比 (越低越好)
bars1 = ax1.bar(categories, latency, color=['#e74c3c', '#2ecc71'])
ax1.set_title('Average Latency (Lower is Better)')
ax1.set_ylabel('Seconds')
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# 在長條圖上標示數值
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval:.2f}s', ha='center', va='bottom', fontweight='bold')

# 圖 2: TPS 對比 (越高越好)
bars2 = ax2.bar(categories, tps, color=['#e74c3c', '#2ecc71'])
ax2.set_title('Throughput - TPS (Higher is Better)')
ax2.set_ylabel('Requests / Sec')
ax2.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.2f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('performance_comparison.png', dpi=300)
print("✅ 效能對比圖已成功產生並儲存為 'performance_comparison.png'！")