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
    qqq_ma200_plus_5_val = qqq_ma200_val * 1.05
    
    if qqq_curr_val < qqq_ma200_val:
        action, detail = "🚨 전량 매도 / SGOV 매수", "QQQ가 200일선 아래입니다. 리스크 관리 모드!"
    elif qqq_ma200_val <= qqq_curr_val <= qqq_ma200_plus_5_val:
        action, detail
