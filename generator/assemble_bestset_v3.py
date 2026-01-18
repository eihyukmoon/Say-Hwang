import json
import os
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine
from jamo import h2j, j2hcj
from g2pk import G2p

# ffmpeg 경로 (사용자 환경에 맞게 수정)
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

class KoreanPhoneticVectorizer:
    # (기존과 동일하여 생략 가능하지만, 실행을 위해 포함)
    def __init__(self):
        self.CHO_GROUPS = [{'ㄱ', 'ㄲ', 'ㅋ'}, {'ㄷ', 'ㄸ', 'ㅌ'}, {'ㅂ', 'ㅃ', 'ㅍ'}, {'ㅈ', 'ㅉ', 'ㅊ'}, {'ㅅ', 'ㅆ'}, {'ㅇ', 'ㅎ'}, {'ㄴ', 'ㄹ', 'ㅁ'}]
        self.JUNG_GROUPS = [{'ㅏ', 'ㅑ'}, {'ㅓ', 'ㅕ'}, {'ㅗ', 'ㅛ'}, {'ㅜ', 'ㅠ'}, {'ㅡ', 'ㅣ'}, {'ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'}, {'ㅘ', 'ㅚ', 'ㅙ', 'ㅞ'}, {'ㅝ', 'ㅟ', 'ㅢ'}]

    def decompose(self, char):
        if '가' <= char <= '힣': return j2hcj(h2j(char))
        return None

class GoldenAssembler:
    def __init__(self, audio_folder, json_path="./single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        self.audio_cache = {}
        self._initialize_database()

    def _initialize_database(self):
        if not os.path.exists(self.json_path):
            print(f"❌ 오류: {self.json_path} 파일을 찾을 수 없습니다.")
            return

        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f) # 전체 리스트 저장
        
        print(f"📂 데이터베이스 로딩 중... ({len(self.raw_data)}개 데이터)")
        
        required_sources = set()
        for entry in self.raw_data:
            required_sources.add(entry['src'])
            
        print(f"🎵 오디오 소스 {len(required_sources)}개 로드 시작...")
        for src in required_sources:
            audio_path = None
            for ext in ['.mp3', '.wav', '.m4a']:
                path = os.path.join(self.audio_folder, src + ext)
                if os.path.exists(path):
                    audio_path = path
                    break
            
            if audio_path:
                try:
                    self.audio_cache[src] = AudioSegment.from_file(audio_path)
                except Exception as e:
                    print(f"   ⚠️ 오디오 로드 실패 ({src}): {e}")
            else:
                print(f"   ⚠️ 오디오 파일 없음: {src}")
        print(f"✅ 초기화 완료")

    def match_target_amplitude(self, sound, target_dBFS=-20.0):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    def export_all_clips(self, output_path="all_clips_inventory.mp3"):
        """
        DB에 있는 모든 클립을 가나다순으로 정렬하여 비프음과 함께 출력합니다.
        """
        print(f"\n📢 모든 오디오 클립 추출 시작 (총 {len(self.raw_data)}개)")
        
        # 1. 가나다 순으로 정렬 (검수하기 편하게)
        sorted_data = sorted(self.raw_data, key=lambda x: x['word'])
        
        # 2. 비프음 생성 (뚜- 소리, 100ms)
        beep = Sine(1000).to_audio_segment(duration=100).apply_gain(-5)
        
        combined = AudioSegment.empty()
        
        count = 0
        for info in sorted_data:
            word = info['word']
            src_id = info['src']
            start = info['start_ms']
            dur = info['duration_ms']
            
            if src_id in self.audio_cache:
                full_audio = self.audio_cache[src_id]
                
                # 범위 체크
                if start + dur > len(full_audio):
                    dur = len(full_audio) - start
                
                # 오디오 자르기
                clip = full_audio[start : start + dur]
                
                # 볼륨 평준화 (검수용이라도 귀 아프지 않게)
                clip = self.match_target_amplitude(clip, target_dBFS=-20.0)
                
                # 페이드 살짝
                clip = clip.fade_in(5).fade_out(5)
                
                # 합치기: [공백] + [단어] + [공백] + [비프음]
                combined += clip + beep
                
                count += 1
                print(f"[{count}] '{word}' 완료 (src: {src_id}, {dur}ms)")
            else:
                print(f"❌ '{word}' 스킵됨 (소스 오디오 없음: {src_id})")
                
        # 내보내기
        combined.export(output_path, format="mp3")
        print(f"\n🎉 전체 클립 저장 완료: {output_path}")
        print("💡 팁: 이 파일을 들으면서 이상한 발음이 나오면 해당 단어를 JSON에서 찾아 수정하거나 삭제하세요.")

if __name__ == "__main__": 
    assembler = GoldenAssembler(audio_folder="./youtube_audio", json_path="./single_best.json")
    
    # 이 함수를 호출하면 됩니다.
    assembler.export_all_clips("all_clips_inventory.mp3")