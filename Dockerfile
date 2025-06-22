# 1. Python 3.9.13이 설치된 경량 리눅스 이미지 사용
FROM python:3.9.13-slim

# 2. 캐시 비활성화 및 로그 즉시 출력 설정
# - PYTHONDONTWRITEBYTECODE: .pyc 파일 생성 방지
# - PYTHONUNBUFFERED: print 로그가 즉시 출력되도록 설정 (버퍼링 X)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. 컨테이너 내 작업 디렉토리 지정 (이후 COPY, RUN 등이 이 위치 기준)
WORKDIR /app

# 4. 시스템 패키지 설치
# - wkhtmltopdf: PDF 출력용
# - build-essential: 일부 파이썬 패키지 컴파일 시 필요
# - curl: 네트워크 요청 테스트용
# - rm: 설치 후 패키지 캐시 삭제 → 이미지 최적화
RUN apt-get update && apt-get install -y \
    build-essential \
    wkhtmltopdf \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. 현재 디렉토리(호스트) 파일 전체를 컨테이너의 /app 디렉토리로 복사
COPY . .

# 6. pip 업그레이드 후, requirements.txt에 따라 파이썬 의존성 설치
# - --no-cache-dir: 설치 후 캐시 제거 → 이미지 사이즈 최소화
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. 컨테이너 외부에서 접근할 수 있도록 포트 5000 노출
EXPOSE 5000

# 8. Gunicorn으로 Flask 앱 실행
# - -w 4: 워커 프로세스 4개 (멀티코어 처리)
# - -b 0.0.0.0:5000: 컨테이너 내부 모든 IP에서 포트 5000 수신
# - app:app → app.py 파일 안의 `app = Flask(__name__)` 실행
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
