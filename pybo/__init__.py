from flask import Flask
import config


def create_app():
    # 1. 플라스크 앱 인스턴스 생성
    app = Flask(__name__)

    # 2. config.py 환경 설정 로드
    app.config.from_object(config)

    # 3. 블루프린트(라우팅 설정) 등록
    from .views import main_views
    app.register_blueprint(main_views.bp)

    return app
