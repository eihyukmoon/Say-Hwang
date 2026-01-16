# 1. 라이브러리 설치 (Restart 후 꼭 다시 실행해야 함)
!pip install -q yt-dlp
!pip install -q git+https://github.com/m-bain/whisperx.git 
!pip install -q jamo
!pip install -q g2pk
!apt-get update -qq && apt-get install -y ffmpeg
#여기 까지가 설치



import os
import json
import yt_dlp
import whisperx
import torch
import gc
from jamo import h2j, j2hcj
from g2pk import G2p

# ==========================================
# ⚙️ 1. 환경 설정 (Settings)
# ==========================================
# 분석할 유튜브 링크 리스트
YOUTUBE_LINKS = [
    "https://youtube.com/shorts/BSZHxXzF9wU?si=vIhoy6uEf4H0eKSm", 
]

BASE_DIR = "/kaggle/working"
OUTPUT_DIR = os.path.join(BASE_DIR, "video_source")
DB_FILE = os.path.join(BASE_DIR, "master_index.json")

# GPU/모델 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 16 
COMPUTE_TYPE = "float16" 

# PyTorch 2.6+ 보안 패치 (무게 중심 무시)
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "true"

# ==========================================
# 🔧 2. 유틸리티 함수
# ==========================================
def get_jamo_context(pronounce_word):
    """단어의 발음에서 각 음절의 앞/뒤 문맥(Triphone) 추출"""
    syllables = list(pronounce_word)
    context_list = []
    
    for i, char in enumerate(syllables):
        current_jamo = j2hcj(h2j(char))
        
        prev_char = None
        if i > 0:
            prev_jamo = j2hcj(h2j(syllables[i-1]))
            prev_char = prev_jamo[-1] # 앞 글자의 종성
            
        next_char = None
        if i < len(syllables) - 1:
            next_jamo = j2hcj(h2j(syllables[i+1]))
            next_char = next_jamo[0] # 뒷 글자의 초성
            
        context_list.append({
            "sound": char,
            "prev": prev_char,
            "next": next_char
        })
    return context_list

# ==========================================
# 🚀 3. 메인 분석 프로세스
# ==========================================
def run_main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"⚙️ Running on: {DEVICE}")
    print("🚀 WhisperX 모델 로딩 중...")
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, language="ko")
    g2p = G2p()
    
    all_records = []

    for url in YOUTUBE_LINKS:
        try:
            print(f"\n▶️ Processing: {url}")
            
            # [1] 다운로드 (yt-dlp)
            ydl_opts = {
                'outtmpl': f'{OUTPUT_DIR}/%(id)s.%(ext)s',
                'quiet': True,
                'format': 'bestaudio/best'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                ext = info['ext']
                filepath = os.path.join(OUTPUT_DIR, f"{video_id}.{ext}")
                print(f"   - 다운로드 완료: {filepath}")

            # [2] 음성 인식 (Transcribe)
            audio = whisperx.load_audio(filepath)
            result = model.transcribe(audio, batch_size=BATCH_SIZE)
            
            # [3] 정밀 정렬 (Align) - 글자 단위 활성화
            print("   - 강제 정렬(Aligning) 중...")
            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
            aligned_result = whisperx.align(
                result["segments"], model_a, metadata, audio, DEVICE, 
                return_char_alignments=True 
            )
            
            # [4] 데이터 구조화 (정밀 추출 로직)
            print("   - 데이터 구조화 및 G2P 변환 중...")
            for segment in aligned_result["segments"]:
                if "chars" not in segment: continue

                segment_chars = segment["chars"]
                char_ptr = 0 # 글자 포인터

                for word_info in segment["words"]:
                    if "start" not in word_info or "end" not in word_info: continue
                    
                    word_text = word_info["word"]
                    try:
                        pronounced = g2p(word_text)
                    except:
                        pronounced = word_text
                    
                    context_data = get_jamo_context(pronounced)
                    
                    # 부모 노드 (단어 단위)
                    parent_entry = {
                        "type": "word",
                        "text": word_text,
                        "pronounce": pronounced,
                        "start": word_info["start"],
                        "end": word_info["end"],
                        "duration": round(word_info["end"] - word_info["start"], 3),
                        "video_id": video_id,
                        "file_path": f"video_source/{video_id}.{ext}",
                        "children": [] 
                    }
                    
                    # 단어 시간대에 걸친 글자 조각 수집 (정밀 매칭)
                    while char_ptr < len(segment_chars):
                        c_info = segment_chars[char_ptr]
                        c_start = c_info.get("start")
                        
                        # 글자 시작 시간이 단어 끝 시간 근처라면 다음 단어로 넘김
                        if c_start is not None and c_start >= word_info["end"] - 0.02:
                            break
                        
                        # 공백이 아닌 실제 글자만 추가
                        if c_info["char"] != " " and c_start is not None:
                            # 현재 단어의 발음 조각들과 순서대로 매칭
                            idx = len(parent_entry["children"])
                            if idx < len(context_data):
                                ctx = context_data[idx]
                                parent_entry["children"].append({
                                    "char": c_info["char"],
                                    "sound": ctx["sound"],
                                    "start": c_info["start"],
                                    "end": c_info["end"],
                                    "context_prev": ctx["prev"],
                                    "context_next": ctx["next"]
                                })
                        char_ptr += 1

                    if parent_entry["children"]:
                        all_records.append(parent_entry)

            # 메모리 비우기
            del model_a
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    # [5] 최종 결과 저장
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 완료! 총 {len(all_records)}개의 단어(글자 포함)를 처리했습니다.")
    print(f"📁 저장 위치: {DB_FILE}")

if __name__ == "__main__":
    run_main()
