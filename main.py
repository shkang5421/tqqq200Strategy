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
    data = yf.download(tickers, period='400d', interval='1d', auto_adjust=True)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [f"{col[0]}_{col[1]}" for col in data.columns]

    # 기초 데이터 정리
    qqq_close = data['Close_QQQ']
    tqqq_close = data['Close_TQQQ']
    
    # QQQ 지표 계산
    ma_intervals = [5, 20, 50, 100, 200]
    qqq_mas = {f"{i}일선": ta.sma(qqq_close, length=i).iloc[-1] for i in ma_intervals}
    qqq_rsi = ta.rsi(qqq_close, length=14).iloc[-1]
    
    # TQQQ 지표 계산
    tqqq_curr = tqqq_close.iloc[-1]
    tqqq_ma200 = ta.sma(tqqq_close, length=200).iloc[-1]
    tqqq_ma200_plus_5 = tqqq_ma200 * 1.05
    tqqq_rsi = ta.rsi(tqqq_close, length=14).iloc[-1]
    
    # 2. 텍스트 리포트 구성
    qqq_ma_table = "\n".join([f"{name.ljust(6)}: ${val:>8.2f}" for name, val in qqq_mas.items()])
    
    # 전략 판단 (QQQ 200일선 기준 추세 필터)
    qqq_curr_val = qqq_close.iloc[-1]
    qqq_ma200_val = qqq_mas['200일선']
    qqq_ma200_plus_5 = qqq_ma200_val * 1.05
    
    if qqq_curr_val < qqq_ma200_val:
        action, detail = "🚨 전량 매도 / SGOV 매수", "QQQ가 200일선 아래입니다. 리스크 관리 모드!"
    elif qqq_ma200_val <= qqq_curr_val <= qqq_ma200_plus_5:
        action, detail = "🚀 TQQQ 풀매수 / 유지", "상승 추세 구간입니다. 전략대로 보유하세요."
    else:
        action, detail = "🔥 TQQQ 유지 / SPYM 추가 매수", "과열 구간입니다. 신규 자금은 SPYM으로!"

    report = (
        f"📊 **나스닥(QQQ) 현황 리포트**\n"
        f"```\n"
        f"[QQQ 현재가] : ${qqq_curr_val:.2f}\n"
        f"[QQQ RSI]    : {qqq_rsi:.2f}\n\n"
        f"[주요 이동평균선]\n"
        f"{qqq_ma_table}\n"
        f"```\n"
        f"📈 **TQQQ 매수·매도 전략 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"• **TQQQ 현재가:** `${tqqq_curr:.2f}`\n"
        f"• **TQQQ RSI(14):** `{tqqq_rsi:.2f}`\n"
        f"• **TQQQ 200일선:** `${tqqq_ma200:.2f}`\n"
        f"• **엔벨로프(+5%):** `${tqqq_ma200_plus_5:.2f}` (과열 기준선)\n\n"
        f"**💡 오늘의 행동 지침:**\n"
        f"**{action}**\n"
        f"_{detail}_\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ *수익률별 계단식 익절 원칙 준수 필수!*"
    )

    # 3. TQQQ 전용 차트 생성
    plt.figure(figsize=(10, 6))
    tqqq_recent = tqqq_close.tail(150)
    t_sma200_recent = ta.sma(tqqq_close, length=200).tail(150)
    t_envelope_upper = t_sma200_recent * 1.05 

    plt.plot(tqqq_recent.index, tqqq_recent, label='TQQQ Price', color='#00cf95', linewidth=2)
    plt.plot(t_sma200_recent.index, t_sma200_recent, label='TQQQ 200MA', color='#f39c12', linestyle='--')
    plt.plot(t_envelope_upper.index, t_envelope_upper, label='Env +5%', color='#ff4757', linestyle=':', alpha=0.8)
    plt.fill_between(t_sma200_recent.index, t_sma200_recent, t_envelope_upper, color='#1dd1a1', alpha=0.1)
    
    plt.title('TQQQ Price vs 200-Day Moving Average & Env +5%', fontsize=14)
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.15)
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()

    return report, img_buffer

def send_to_discord(msg, img_buffer):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        print("Webhook URL not found.")
        return

    try:
        # 1. 텍스트 메시지 전송
        requests.post(webhook_url, json={"content": msg})
        
        # 2. 이미지 파일 전송
        img_buffer.seek(0)
        files = {"file": ("chart.png",
