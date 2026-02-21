import yfinance as yf
import pandas_ta as ta
import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
import pytz # 시간대 변환을 위해 필요

def get_trading_signal():
    print("1. 데이터 다운로드 시작...")
    # 한국 시간 설정
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')

    tickers = ['QQQ', 'TQQQ']
    try:
        data = yf.download(tickers, period='400d', interval='1d', auto_adjust=True)
        if data.empty:
            print("❌ 에러: 데이터를 가져오지 못했습니다.")
            return None, None
    except Exception as e:
        print(f"❌ 데이터 다운로드 중 예외 발생: {e}")
        return None, None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [f"{col[0]}_{col[1]}" for col in data.columns]

    print("2. 지표 계산 중...")
    qqq_close = data['Close_QQQ']
    tqqq_close = data['Close_TQQQ']
    
    ma_intervals = [5, 20, 50, 100, 200]
    qqq_mas = {f"{i}일선": ta.sma(qqq_close, length=i).iloc[-1] for i in ma_intervals}
    qqq_rsi = ta.rsi(qqq_close, length=14).iloc[-1]
    
    tqqq_curr = tqqq_close.iloc[-1]
    tqqq_ma200 = ta.sma(tqqq_close, length=200).iloc[-1]
    tqqq_ma200_plus_5 = tqqq_ma200 * 1.05
    tqqq_rsi = ta.rsi(tqqq_close, length=14).iloc[-1]
    
    qqq_curr_val = qqq_close.iloc[-1]
    qqq_ma200_val = qqq_mas['200일선']
    qqq_ma200_plus_5_val = qqq_ma200_val * 1.05
    
    # 전략 판단
    if qqq_curr_val < qqq_ma200_val:
        action, detail = "🚨 전량 매도 / SGOV 매수", "QQQ가 200일선 아래입니다. 리스크 관리 모드!"
    elif qqq_ma200_val <= qqq_curr_val <= qqq_ma200_plus_5_val:
        action, detail = "🚀 TQQQ 풀매수 / 유지", "상승 추세 구간입니다. 전략대로 보유하세요."
    else:
        action, detail = "🔥 TQQQ 유지 / SPYM 추가 매수", "과열 구간입니다. 신규 자금은 SPYM으로!"

    ma_table = "\n".join([f"{name.ljust(6)}: ${val:>8.2f}" for name, val in qqq_mas.items()])
    
    # 리포트 생성 (상단에 한국 시간 추가)
    report = (
        f"📅 **리포트 생성 일시 (KST):** `{now}`\n"
        f"📊 **나스닥(QQQ) 현황 리포트**\n"
        f"```\n"
        f"[QQQ 현재가] : ${qqq_curr_val:.2f}\n"
        f"[QQQ RSI]    : {qqq_rsi:.2f}\n\n"
        f"[주요 이동평균선]\n"
        f"{ma_table}\n"
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

    print("3. 차트 생성 중...")
    plt.figure(figsize=(10, 6))
    tqqq_recent = tqqq_close.tail(150)
    t_sma200_recent = ta.sma(tqqq_close, length=200).tail(150)
    t_envelope_upper = t_sma200_recent * 1.05 

    plt.plot(tqqq_recent.index, tqqq_recent, label='TQQQ Price', color='#00cf95', linewidth=2)
    plt.plot(t_sma200_recent.index, t_sma200_recent, label='TQQQ 200MA', color='#f39c12', linestyle='--')
    plt.plot(t_envelope
