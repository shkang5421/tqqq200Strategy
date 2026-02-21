import yfinance as yf
import pandas_ta as ta
import requests
import os
import pandas as pd

def get_trading_signal():
    # 1. 데이터 다운로드 (분석에 필요한 충분한 기간)
    tickers = ['QQQ', 'TQQQ', 'SPYM']
    data = yf.download(tickers, period='300d', interval='1d', auto_adjust=True)

    # Multi-index 처리
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [f"{col[0]}_{col[1]}" for col in data.columns]

    # 2. QQQ 데이터 및 이동평균선 계산
    qqq_close = data['Close_QQQ'].iloc[-1]
    ma_intervals = [5, 20, 50, 100, 200]
    ma_values = {f"MA{i}": ta.sma(data['Close_QQQ'], length=i).iloc[-1] for i in ma_intervals}
    
    # 3. TQQQ RSI 계산
    tqqq_rsi = ta.rsi(data['Close_TQQQ'], length=14).iloc[-1]
    
    # 4. 전략 판단 로직
    ma200 = ma_values['MA200']
    ma200_plus_5 = ma200 * 1.05
    
    action = ""
    status_detail = ""

    # [매매 전략 로직 적용]
    if qqq_close < ma200:
        action = "🚨 전량 매도 및 SGOV 풀매수 (하락장 대피)"
        status_detail = "현재 QQQ가 200일선 아래에 있습니다. 자산 보호가 최우선입니다."
    elif ma200 <= qqq_close <= ma200_plus_5:
        action = "🚀 TQQQ 풀매수 / 유지 (상승장 진입)"
        status_detail = "QQQ가 200일선 위에서 안정적인 상승 추세에 있습니다."
    elif qqq_close > ma200_plus_5:
        action = "🔥 TQQQ 유지 + 신규 자금 SPYM 추가 매수 (과열 구간)"
        status_detail = "200일선 대비 5% 초과 상승한 과열 구간입니다. 추가 성장은 SPYM으로 방어하세요."

    # 리포트 구성
    report = (
        f"📅 **오늘의 TQQQ 전략 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"**1. QQQ 현재가:** `${qqq_close:.2f}`\n\n"
        f"**2. QQQ 주요 이동평균선:**\n"
        f"   - 5일선: `${ma_values['MA5']:.2f}`\n"
        f"   - 20일선: `${ma_values['MA20']:.2f}`\n"
        f"   - 50일선: `${ma_values['MA5']:.2f}`\n"
        f"   - 100일선: `${ma_values['MA100']:.2f}`\n"
        f"   - 200일선: `${ma_values['MA200']:.2f}`\n\n"
        f"**3. TQQQ RSI(14):** `{tqqq_rsi:.2f}`\n\n"
        f"**4. 💡 오늘의 행동 지침:**\n"
        f"**{action}**\n"
        f"_{status_detail}_\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ *수익률에 따른 계단식 익절(+10%, 25%, 50% 시 10% / 100%배수 시 50%)을 잊지 마세요!*"
    )
    return report

def send_discord(message):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if webhook_url:
        requests.post(webhook_url, json={"content": message})
    else:
        print(message)

if __name__ == "__main__":
    msg = get_trading_signal()
    send_discord(msg)
