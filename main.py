# ... (기존 상단 코드 동일)

    # 2. 차트 이미지 생성
    plt.figure(figsize=(10, 6)) # 세로 길이를 조금 늘려 가독성 확보
    
    # 데이터 준비
    qqq_recent = qqq.tail(150)
    sma200_recent = ta.sma(qqq, length=200).tail(150)
    envelope_upper = sma200_recent * 1.05 # 엔벨로프 +5% 계산

    # 그래프 그리기
    plt.plot(qqq_recent, label='QQQ Price', color='#3498db', linewidth=1.5) # QQQ 종가
    plt.plot(sma200_recent, label='200MA', color='#f39c12', linestyle='--') # 200일선
    plt.plot(envelope_upper, label='200MA +5% (Overheat)', color='#e74c3c', linestyle=':', alpha=0.7) # 엔벨로프 +5%

    # 현재가 위치에 점 찍기 (선택 사항)
    plt.scatter(qqq_recent.index[-1], qqq_curr, color='#2c3e50', zorder=5)
    
    # 그래프 꾸미기
    plt.title('QQQ vs 200-Day Moving Average & Envelope +5%', fontsize=14)
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.2)
    plt.fill_between(sma200_recent.index, sma200_recent, envelope_upper, color='#f1c40f', alpha=0.1, label='Normal Growth Zone') # 구간 색칠

    # 이미지 저장 및 반환
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()

    return report, img_buffer

# ... (기존 하단 코드 동일)
