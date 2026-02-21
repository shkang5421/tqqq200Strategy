import yfinance as yf
import pandas_ta as ta
import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

def get_trading_signal():
    # 1. 데이터 다운로드
    tickers = ['QQQ', 'TQQQ']
    data = yf.download(tickers, period='300d', interval='1d', auto_adjust=True)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [f"{col[0]}_{col[1]}" for col in data.columns]

    # 데이터 정리
    qqq = data['Close_QQQ']
    ma_intervals = [5, 20, 50, 100, 200]
    mas = {f"{i}일선": ta.sma(qqq, length=i).iloc[-1] for i in ma_intervals}
    
    qqq_curr = qqq.iloc[-1]
    tqqq_rsi = ta.rsi(data['Close_TQQQ'], length=14).iloc[-1]
    
    # 2. 텍스트 리포트 생성 (글자 간격 맞춤)
    ma_table = "\n".join([f"{name.ljust(6)}: ${val:>8.2f}" for name, val in mas.items()])
    
    ma200 = mas['200일선']
    ma200_plus_5 = ma200 * 1.05
    
    # 전략 판단
    if qqq_curr < ma200:
        action, detail = "🚨 전량 매도 / SGOV 매수", "QQQ가 200일선 아래에 있습니다. 대피하세요!"
    elif ma200 <= qqq_curr <= ma200_plus_5:
        action, detail = "🚀 TQQQ 풀매수 / 유지", "200일선 위 안정적인 상승 구간입니다."
    else:
        action, detail = "🔥 TQQQ 유지 / SPYM 추가", "과열 구간입니다. 추가 매수는 SPYM을 권장합니다."

    report = (
        f"📅 **오늘의 TQQQ 전략 리포트**\n"
        f"```\n"
        f"[QQQ 현재가] : ${qqq_curr:.2f}\n\n"
        f"[주요 이동평균선]\n"
        f"{ma_table}\n"
        f"```\n"
        f"**TQQQ RSI(14):** `{tqqq_rsi:.2f}`\n\n"
        f"**💡 오늘의 행동 지침:**\n"
        f"**{action}**\n"
        f"_{detail}_\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ *수익률별 계단식 익절 원칙을 준수하세요!*"
    )

    # 3. 차트 이미지 생성 (들여쓰기 교정 완료)
    plt.figure(figsize=(10, 6))
    
    qqq_recent = qqq.tail(150)
    sma200_recent = ta.sma(qqq, length=200).tail(150)
    envelope_upper = sma200_recent * 1.05 

    plt.plot(qqq_recent, label='QQQ Price', color='#3498db', linewidth=1.5)
    plt.plot(sma200_recent, label='200MA', color='#f39c12', linestyle='--')
    plt.plot(envelope_upper, label='200MA +5% (Overheat)', color='#e74c3c', linestyle=':', alpha=0.7)

    plt.fill_between(sma200_recent.index, sma200_recent, envelope_upper, color='#f1c40f', alpha=0.1, label='Normal Growth Zone')
    
    plt.title('QQQ vs 200-Day Moving Average & Envelope +5%', fontsize=14)
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.2)
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()

    return report, img_buffer

def send_to_discord(msg, img_buffer):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        print(msg)
        return

    payload = {"content": msg}
    files = {"file": ("chart.png", img_buffer, "image/png")}
    requests.post(webhook_url, data=payload, files=files)

if __name__ == "__main__":
    report_text, chart_img = get_trading_signal()
    send_to_discord(report_text, chart_img)
