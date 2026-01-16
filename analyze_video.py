import os
import json
import yt_dlp
import whisperx
import torch
import gc
from jamo import h2j, j2hcj
from g2pk import G2p

# ==========================================
# ⚙️ 설정 (Settings)
# ==========================================
# 분석할 유튜브 링크 리스트
YOUTUBE_LINKS = [
    # 예시: 아이유 쇼츠, 뉴스 클립 등 테스트하고 싶은 영상 링크 입력
    "https://www.youtube.com/shorts/3iM_06QeZD8", 
]

# 캐글의 작업용 디렉토리 (Output 탭에서 다운로드 가능)
BASE_DIR = "/kaggle/working"
OUTPUT_DIR = os.path.join(BASE_DIR, "video_source")
DB_FILE = os.path.join(BASE_DIR, "master_index.json")

# GPU 설정 확인
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 16 # GPU 메모리에 따라 조절 (T4 x2라면 16~32도 가능)
COMPUTE_TYPE = "float16" # 메모리 효율을 위해 float16 사용

print(f"⚙️ Running on: {DEVICE}")

# ==========================================
# 🔧 유틸리티: Triphone 문맥 추출기
# ==========================================
def get_jamo_context(pronounce_word):
    """
    단어의 발음(예: '학꾜')을 받아서, 각 글자의 앞(Prev)/뒤(Next) 자모 소리를 추출
    """
    syllables = list(pronounce_word) # ['학', '꾜']
    context_list = []
    
    for i, char in enumerate(syllables):
        # 현재 글자 자모 분해 (학 -> ㅎ,ㅏ,ㄱ)
        current_jamo = j2hcj(h2j(char))
        
        # 1. Previous Context (앞 글자의 종성)
        prev_char = None
        if i > 0:
            prev_jamo = j2hcj(h2j(syllables[i-1]))
            prev_char = prev_jamo[-1] # 앞 글자의 마지막 자모(받침)
            
        # 2. Next Context (뒷 글자의 초성)
        next_char = None
        if i < len(syllables) - 1:
            next_jamo = j2hcj(h2j(syllables[i+1]))
            next_char = next_jamo[0] # 뒷 글자의 첫 자모(초성)
            
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
    # 폴더 생성
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. WhisperX 모델 로드 (Alignment 모델 포함)
    print("🚀 WhisperX 모델 로딩 중...")
    # 캐글 T4 GPU에서는 large-v2가 무난하게 잘 돌아갑니다.
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
                'format': 'bestaudio/best',
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                ext = info['ext']
                filepath = f"{OUTPUT_DIR}/{video_id}.{ext}"
                print(f"   - 다운로드 완료: {filepath}")

            # [2] 전사 (Transcribe)
            print("   - 음성 인식(Transcribing) 중...")
            audio = whisperx.load_audio(filepath)
            result = model.transcribe(audio, batch_size=BATCH_SIZE)
            
            # [3] 정렬 (Align) - 글자 단위 타임스탬프 추출
            print("   - 강제 정렬(Aligning) 중...")
            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
            
            # 핵심: return_char_alignments=True
            aligned_result = whisperx.align(
                result["segments"], model_a, metadata, audio, DEVICE, 
                return_char_alignments=True 
            )
            
            # [4] 데이터 구조화 (Parent-Child)
            print("   - 데이터 구조화 및 G2P 변환 중...")
            for segment in aligned_result["segments"]:
                if "words" not in segment: continue

                for word_info in segment["words"]:
                    if "start" not in word_info: continue
                    
                    word_text = word_info["word"]
                    pronounced = g2p(word_text) # G2P 변환 (학교 -> 학꾜)
                    
                    # 문맥 분석 (Triphone context)
                    context_data = get_jamo_context(pronounced)
                    
                    # 부모 노드 (Parent) 생성
                    parent_entry = {
                        "type": "word",
                        "text": word_text,
                        "pronounce": pronounced,
                        "start": word_info["start"],
                        "end": word_info["end"],
                        "duration": round(word_info["end"] - word_info["start"], 3),
                        "video_id": video_id,
                        # 캐글 Output 경로 문제 방지를 위해 파일명만 저장하거나 상대경로 권장
                        "file_path": f"video_source/{video_id}.{ext}", 
                        "children": [] 
                    }
                    
                    # 자식 노드 (Children) 생성
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

            # 메모리 정리 (다음 루프를 위해)
            del model_a
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            continue

    # JSON 저장
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 완료! 총 {len(all_records)}개의 단어가 처리되었습니다.")
    print(f"파일 위치: {DB_FILE}")

if __name__ == "__main__":
    process_videos()
