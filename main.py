import yfinance as yf
import pandas_ta as ta
import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
import pytz

def get_trading_signal():
    print("1. 환경 설정 및 데이터 다운로드 시작...")
    kst = pytz.timezone('Asia/Seoul')
    now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')

    tickers = ['QQQ', 'TQQQ']
    try:
        # 데이터 누락 방지를 위해 넉넉하게 500일치 다운로드
        data = yf.download(tickers, period='500d', interval='1d', auto_adjust=True)
        
        # 멀티 인덱스 정리
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [f"{col[0]}_{col[1]}" for col in data.columns]
        
        # 데이터가 비어있는 행(주말 등) 제거하여 nan 방지
        data = data.dropna()
        
        if data.empty or len(data) < 200:
            print("❌ 에러: 계산 가능한 충분한 데이터가 없습니다.")
            return None, None
            
    except Exception as e:
        print(f"❌ 데이터 처리 중 예외 발생: {e}")
        return None, None

    print("2. 기술적 지표 계산 중...")
    qqq_close = data['Close_QQQ']
    tqqq_close = data['Close_TQQQ']
    
    # QQQ 지표
    ma_intervals = [5, 20, 50, 100, 200]
    qqq_mas = {f"{i}일선": ta.sma(qqq_close, length=i).iloc[-1] for i in ma_intervals}
    qqq_rsi = ta.rsi(qqq_close, length=14).iloc[-1]
    
    # TQQQ 지표
    tqqq_curr = tqqq_close.iloc[-1]
    tqqq_ma200 = ta.sma(tqqq_close, length=200).iloc[-1]
    tqqq_ma200_plus_5 = tqqq_ma200 * 1.05
    tqqq_rsi = ta.rsi(tqqq_close, length=14).iloc[-1]
    
    # 전략 판단
    qqq_curr_val = qqq_close.iloc[-1]
    qqq_ma200_val = qqq_mas['200일선']
    
    if qqq_curr_val < qqq_ma200_val:
        action, detail = "🚨 전량 매도 / SGOV 매수", "QQQ가 200일선 아래입니다. 리스크 관리 모드!"
    elif qqq_ma200_val <= qqq_curr_val <= (qqq_ma200_val * 1.05):
        action, detail = "🚀 TQQQ 풀매수 / 유지", "상승 추세 구간입니다. 전략대로 보유하세요."
    else:
        action, detail = "🔥 TQQQ 유지 / SPYM 추가 매수", "과열 구간입니다. 신규 자금은 SPYM으로!"

    ma_table = "\n".join([f"{name.ljust(6)}: ${val:>8.2f}" for name, val in qqq_mas.items()])
    
    report = (
        f"📅 **리포트 생성 일시 (KST):** `{now_str}`\n"
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
        f"• **엔벨로프(+5%):** `${tqqq_ma200_plus_5:.2f}`\n\n"
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
    plt.plot(t_envelope_upper.index, t_envelope_upper, label='Env +5%', color='#ff4757', linestyle=':', alpha=0.8)
    plt.fill_between(t_sma200_recent.index, t_sma200_recent, t_envelope_upper, color='#1dd1a1', alpha=0.1)
    
    plt.title(f'TQQQ Analysis ({now_str})', fontsize=14)
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.15)
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return report, img_buffer

def send_to_discord(msg, img_buffer):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url: return

    try:
        payload = {"content": msg}
        files = {"file": ("chart.png", img_buffer, "image/png")}
        requests.post(webhook_url, data=payload, files=files)
        print("✅ 전송 완료!")
    except Exception as e:
        print(f"❌ 전송 에러: {e}")

if __name__ == "__main__":
    report_text, chart_img = get_trading_signal()
    if report_text:
        send_to_discord(report_text, chart_img)
