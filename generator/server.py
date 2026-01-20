from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from assemble_v4 import GoldenAssembler
import os
import base64

app = Flask(__name__)
CORS(app)  # CORS 허용

# 서버 시작 시 한 번만 초기화 (JSON 로딩)
print("[서버 초기화] GoldenAssembler V4 로딩 중...")
assembler = GoldenAssembler(audio_folder="./youtube_audio")
print("[서버 준비 완료] 요청 대기 중...\n")

@app.route('/api/generate', methods=['POST'])
def generate_audio():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': '텍스트가 비어있습니다'}), 400
        
        print(f"\n[요청 수신] '{text}'")
        
        # 오디오 생성 (메모리에서 처리)
        audio_base64, timing_data = assembler.assemble(text)
        
        response = {
            "audio_base64": audio_base64,
            "timing_data": timing_data
        }
        
        print(f"[응답 전송] 오디오(Base64) + 타이밍 데이터\n")
        return jsonify(response)
    
    except Exception as e:
        print(f"[오류 발생] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Python 서버 정상 작동 중'})

if __name__ == '__main__':
    # 5000번 포트 충돌 방지 및 사용자 요청으로 4000으로 변경
    app.run(host='0.0.0.0', port=4000, debug=False)
