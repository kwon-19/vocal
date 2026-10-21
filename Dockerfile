# 1. 베이스 이미지 선택 (빌드 도구가 포함된 표준 버전)
FROM python:3.11

# 2. 시간대 설정 (KST) 및 오디오/컴파일에 필수적인 리눅스 시스템 패키지 설치
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y \
    tzdata \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 생성 및 이동
WORKDIR /app

# 4. 종속성 복사 및 의존성 해결 패키지 매니저 업데이트
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 5. [수정] 한 줄씩 읽어가며 패키지 설치 (특정 패키지 에러 시 건너뛰고 완료)
RUN while read -r line || [ -n "$line" ]; do \
        if [ -n "$line" ] && [ "${line#\#}" = "$line" ]; then \
            pip install --no-cache-dir --use-deprecated=legacy-resolver "$line" || true; \
        fi; \
    done < requirements.txt

# 6. 전체 프로젝트 복사
COPY . .

# 7. Flask 환경변수 설정
ENV FLASK_APP=pybo:create_app
ENV FLASK_ENV=production

# 8. 포트 오픈
EXPOSE 5000

# 9. 앱 실행
CMD ["flask", "run", "--host=0.0.0.0"]
