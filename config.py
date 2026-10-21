import os

BASE_DIR = os.path.dirname(__file__)

# 파일 업로드 관련 설정
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'pybo', 'static', 'uploads')
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # AI 모델 처리를 위해 30MB로 확장
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a'}

# 업로드 폴더가 없으면 자동 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
