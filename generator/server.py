from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from assemble_v3 import GoldenAssembler
import os

app = Flask(__name__)
CORS(app)  # CORS 허용

# 서버 시작 시 한 번만 초기화 (JSON 로딩)
print("[서버 초기화] GoldenAssembler 로딩 중...")
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
        
        # 오디오 생성
        output_path = "final_output_hybrid.mp3"
        assembler.assemble(text, output_path)
        
        # 파일 존재 확인
        if not os.path.exists(output_path):
            return jsonify({'error': '오디오 파일 생성 실패'}), 500
        
        print(f"[응답 전송] {output_path}\n")
        return send_file(output_path, mimetype='audio/mpeg')
    
    except Exception as e:
        print(f"[오류 발생] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Python 서버 정상 작동 중'})

if __name__ == '__main__':
    # 5000번 포트 충돌 방지 및 사용자 요청으로 4000으로 변경
    app.run(host='0.0.0.0', port=4000, debug=False)
