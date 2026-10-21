import os
import gc
from flask import Blueprint, render_template, request, current_app
from werkzeug.utils import secure_filename
import librosa
import numpy as np
from scipy.signal import butter, lfilter
# ★ FFmpeg 의존성이 없는 순수 내장 디코더 탑재
import miniaudio

bp = Blueprint('main', __name__, url_prefix='/')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def filter_vocal_frequency(y, sr):
    b, a = butter_bandpass(80, 1100, sr, order=4)
    return lfilter(b, a, y)


def analyze_vocal(y, sr):
    if y is None or len(y) == 0:
        raise ValueError("오디오 데이터가 비어있거나 읽을 수 없습니다.")

    rms = librosa.feature.rms(y=y)
    rms_mean = np.mean(rms)
    rms_std = np.std(rms)
    shimmer_ratio = (rms_std / rms_mean) if rms_mean > 0 else 0.5

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    voiced_pitches = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if 80 < pitch < 1100:
            voiced_pitches.append(pitch)

    if len(voiced_pitches) > 1:
        pitch_diffs = np.abs(np.diff(voiced_pitches))
        pitch_mean = np.mean(voiced_pitches)
        jitter_ratio = (np.mean(pitch_diffs) / pitch_mean) if pitch_mean > 0 else 0.5
    else:
        jitter_ratio = 0.5

    stability_score = max(55, min(98, int(100 - (jitter_ratio * 120))))
    volume_score = max(50, min(97, int(100 - (shimmer_ratio * 70))))

    if stability_score < 60 and len(voiced_pitches) > 10:
        stability_score = 68

    total_score = int((stability_score + volume_score) / 2)

    return {
        'total': total_score,
        'stability': stability_score,
        'volume': volume_score
    }


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        if 'vocal_file' not in request.files:
            return render_template('index.html', error="파일이 접수되지 않았습니다.")

        file = request.files['vocal_file']
        if file.filename == '':
            return render_template('index.html', error="선택된 파일이 없습니다.")

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"temp_vocal_file.{ext}"

            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            y, sr = None, 22050

            try:
                # --- [★ miniaudio를 활용한 독자적 오디오 디코딩 스트림] ---
                try:
                    # 외부 코덱 프로그램 없이 m4a/mp3 원시 바이너리를 직접 오디오 프레임 배열로 변환
                    info = miniaudio.get_file_info(file_path)
                    decoded = miniaudio.decode_file(file_path, sample_rate=22050, dither=miniaudio.DitherMode.NONE)

                    # 1차원 numpy array float32 형태로 정규화 변환
                    y = np.array(decoded.samples, dtype=np.float32)
                    sr = 22050

                    # 다채널(스테레오 등)인 경우 채널 평균을 내어 모노 변환
                    if decoded.nchannels > 1:
                        y = y.reshape((-1, decoded.nchannels)).mean(axis=1)

                    del decoded
                except Exception:
                    # 만약의 경우를 대비한 백업용 기본 로드
                    y, sr = librosa.load(file_path, sr=22050)
                # --- [우회 로직 끝] ---

                # 가창 주파수 필터링 및 분석 진행
                vocal_y = filter_vocal_frequency(y, sr)
                result = analyze_vocal(vocal_y, sr)

                # 가비지 컬렉션으로 메모리를 비워 윈도우 파일 잠금 강제 해제
                del y
                gc.collect()

                # 임시 파일 삭제
                if os.path.exists(file_path):
                    os.remove(file_path)

                return render_template('index.html', result=result)

            except Exception as e:
                if 'y' in locals():
                    del y
                gc.collect()

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                return render_template('index.html', error=f"음원 분석 실패: {str(e)}")

    return render_template('index.html')
