# 1. 라이브러리 설치 (Restart 후 꼭 다시 실행해야 함)
!pip install -q yt-dlp
!pip install -q git+https://github.com/m-bain/whisperx.git 
!pip install -q jamo
!pip install -q g2pk
!apt-get update -qq && apt-get install -y ffmpeg


import os
import json
import yt_dlp
import whisperx
import torch
import gc
from jamo import h2j, j2hcj
from g2pk import G2p

# ==========================================
# 🛡️ [안전 패치 V2] PyTorch 2.6 호환성 문제 해결
# ==========================================
# RecursionError 방지를 위한 강력한 중복 체크 로직
try:
    # 1. 이미 패치된 흔적(_is_patched)이 있거나, 
    # 2. torch.load가 파이썬 기본 함수가 아니라 우리가 만든 함수라면 패치 건너뜀
    if hasattr(torch.load, "_is_patched"):
        print("✅ 이미 보안 패치가 적용되어 있습니다. (Skiped)")
    else:
        print("🔧 PyTorch 보안 설정을 수정합니다...")
        _original_load = torch.load
        
        def patched_load(*args, **kwargs):
            # 강제로 weights_only=False 설정 (보안 경고 무시)
            kwargs['weights_only'] = False
            return _original_load(*args, **kwargs)
        
        # 패치되었다는 표식 남기기
        patched_load._is_patched = True
        torch.load = patched_load
        print("✅ PyTorch 패치 완료.")
        
except Exception as e:
    print(f"⚠️ 패치 중 경고 발생 (무시 가능): {e}")

# ==========================================
# ⚙️ 설정 (Settings)
# ==========================================
YOUTUBE_LINKS = [
    "https://youtube.com/shorts/BSZHxXzF9wU?si=vIhoy6uEf4H0eKSm", 
]

BASE_DIR = "/kaggle/working"
OUTPUT_DIR = os.path.join(BASE_DIR, "video_source")
DB_FILE = os.path.join(BASE_DIR, "master_index.json")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 16 
COMPUTE_TYPE = "float16" 

print(f"⚙️ Running on: {DEVICE}")

# ==========================================
# 🔧 유틸리티
# ==========================================
def get_jamo_context(pronounce_word):
    syllables = list(pronounce_word)
    context_list = []
    
    for i, char in enumerate(syllables):
        current_jamo = j2hcj(h2j(char))
        prev_char = None
        if i > 0:
            prev_jamo = j2hcj(h2j(syllables[i-1]))
            prev_char = prev_jamo[-1]
        next_char = None
        if i < len(syllables) - 1:
            next_jamo = j2hcj(h2j(syllables[i+1]))
            next_char = next_jamo[0]
        context_list.append({
            "sound": char,
            "prev": prev_char,
            "next": next_char
        })
    return context_list

# ==========================================
# 🚀 메인 로직
# ==========================================
def process_videos():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("🚀 WhisperX 모델 로딩 중... (시간이 조금 걸릴 수 있습니다)")
    
    # 모델 로드
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, language="ko")
    g2p = G2p()
    
    all_records = []

    for url in YOUTUBE_LINKS:
        try:
            print(f"\n▶️ Processing: {url}")
            
            # [1] 다운로드
            ydl_opts = {
                'outtmpl': f'{OUTPUT_DIR}/%(id)s.%(ext)s',
                'quiet': True,
                'format': 'bestaudio/best',
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                ext = info['ext']
                filepath = f"{OUTPUT_DIR}/{video_id}.{ext}"
                print(f"   - 다운로드 완료: {filepath}")

            # [2] 전사
            print("   - 음성 인식(Transcribing) 중...")
            audio = whisperx.load_audio(filepath)
            result = model.transcribe(audio, batch_size=BATCH_SIZE)
            
            # [3] 정렬
            print("   - 강제 정렬(Aligning) 중...")
            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
            
            aligned_result = whisperx.align(
                result["segments"], model_a, metadata, audio, DEVICE, 
                return_char_alignments=True 
            )
            
            # [4] 데이터 구조화
            print("   - 데이터 구조화 및 G2P 변환 중...")
            for segment in aligned_result["segments"]:
                if "words" not in segment: continue

                for word_info in segment["words"]:
                    if "start" not in word_info: continue
                    
                    word_text = word_info["word"]
                    pronounced = g2p(word_text)
                    context_data = get_jamo_context(pronounced)
                    
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
                    
                    if "chars" in word_info:
                        min_len = min(len(word_info["chars"]), len(context_data))
                        for i in range(min_len):
                            char_data = word_info["chars"][i]
                            ctx = context_data[i]
                            if "start" in char_data:
                                child_entry = {
                                    "char": char_data["char"],
                                    "sound": ctx["sound"],
                                    "start": char_data["start"],
                                    "end": char_data["end"],
                                    "context_prev": ctx["prev"],
                                    "context_next": ctx["next"]
                                }
                                parent_entry["children"].append(child_entry)
                    
                    all_records.append(parent_entry)

            del model_a
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            continue

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 완료! 총 {len(all_records)}개의 단어가 처리되었습니다.")
    print(f"파일 위치: {DB_FILE}")

if __name__ == "__main__":
    process_videos()
