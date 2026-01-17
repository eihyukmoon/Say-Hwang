import json
import os
import numpy as np
from pydub import AudioSegment
from jamo import h2j, j2hcj
from g2pk import G2p

# ffmpeg 경로 (사용자 환경에 맞게 수정)
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

class KoreanPhoneticVectorizer:
    def __init__(self):
        self.CHO_GROUPS = [{'ㄱ', 'ㄲ', 'ㅋ'}, {'ㄷ', 'ㄸ', 'ㅌ'}, {'ㅂ', 'ㅃ', 'ㅍ'}, {'ㅈ', 'ㅉ', 'ㅊ'}, {'ㅅ', 'ㅆ'}, {'ㅇ', 'ㅎ'}, {'ㄴ', 'ㄹ', 'ㅁ'}]
        self.JUNG_GROUPS = [{'ㅏ', 'ㅑ'}, {'ㅓ', 'ㅕ'}, {'ㅗ', 'ㅛ'}, {'ㅜ', 'ㅠ'}, {'ㅡ', 'ㅣ'}, {'ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'}, {'ㅘ', 'ㅚ', 'ㅙ', 'ㅞ'}, {'ㅝ', 'ㅟ', 'ㅢ'}]

    def decompose(self, char):
        if '가' <= char <= '힣': return j2hcj(h2j(char))
        return None

    def _is_same_group(self, c1, c2, groups):
        for group in groups:
            if c1 in group and c2 in group: return True
        return False

    def calculate_distance(self, target_char, db_char):
        t_parts, d_parts = self.decompose(target_char), self.decompose(db_char)
        if not t_parts or not d_parts: return 999
        t_cho, t_jung, t_jong = (t_parts + '   ')[:3]
        d_cho, d_jung, d_jong = (d_parts + '   ')[:3]

        score = 0
        if t_jung != d_jung: score += 10 if self._is_same_group(t_jung, d_jung, self.JUNG_GROUPS) else 50
        if t_cho != d_cho: score += 5 if self._is_same_group(t_cho, d_cho, self.CHO_GROUPS) else 20
        if t_jong != d_jong:
            if (t_jong == ' ') != (d_jong == ' '): score += 15
            elif self._is_same_group(t_jong, d_jong, self.CHO_GROUPS): score += 5
            else: score += 10
        return score

class GoldenAssembler:
    def __init__(self, audio_folder, json_path="./single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        self.golden_map = {}
        self.audio_cache = {}
        self.g2p = G2p()
        self.vectorizer = KoreanPhoneticVectorizer()
        self._initialize_database()

    def _initialize_database(self):
        if not os.path.exists(self.json_path):
            print(f"❌ 오류: {self.json_path} 파일을 찾을 수 없습니다.")
            return

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📂 골든 셋 로딩 중... ({len(data)}개 데이터)")
        
        required_sources = set()
        for entry in data:
            self.golden_map[entry['word']] = entry
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

    def _find_best_substitute(self, target_char):
        best_char, min_score = None, 999
        for db_char in self.golden_map.keys():
            score = self.vectorizer.calculate_distance(target_char, db_char)
            if score < min_score:
                min_score = score
                best_char = db_char
            if min_score == 0: return best_char
        return best_char

    # --- [추가된 메서드] 볼륨 평준화 ---
    def match_target_amplitude(self, sound, target_dBFS=-20.0):
        """
        현재 사운드의 dBFS(Decibels relative to Full Scale)를 확인하고,
        Target 볼륨과의 차이만큼 게인(Gain)을 조절하여 리턴합니다.
        """
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    def assemble(self, text, output_path="final_output.mp3"):
        pronunciation = self.g2p(text)
        print(f"\n📢 합성 시작: '{text}' -> [{pronunciation}]")
        
        combined = AudioSegment.empty()
        
        for char in pronunciation:
            if char == " ":
                combined += AudioSegment.silent(duration=200)
                continue
            
            target = char
            match_type = "정확"
            
            if char not in self.golden_map:
                target = self._find_best_substitute(char)
                match_type = "대체"
                
            if not target or target not in self.golden_map:
                print(f"❌ 실패: '{char}' (대체 불가)")
                continue

            info = self.golden_map[target]
            src_id = info['src']
            
            if src_id in self.audio_cache:
                full_audio = self.audio_cache[src_id]
                start = info['start_ms']
                dur = info['duration_ms']
                
                # 안전 장치
                if start + dur > len(full_audio):
                    dur = len(full_audio) - start
                
                # 1. 오디오 자르기
                clip = full_audio[start : start + dur]
                
                # 2. [핵심] 볼륨 평준화 적용 (-20dB로 통일)
                # 페이드 처리 전에 해야 볼륨이 맞춰진 상태에서 자연스럽게 줄어듭니다.
                clip = self.match_target_amplitude(clip, target_dBFS=-20.0)
                
                # 3. 페이드 처리
                clip = clip.fade_in(5).fade_out(5)
                
                log = f"[{char}]"
                if match_type == "대체":
                    log += f" -> 🔄대체: [{target}]"
                print(f"{log} : {src_id} ({dur}ms) [Vol Normalized]")
                
                if len(combined) > 0:
                    combined = combined.append(clip, crossfade=10)
                else:
                    combined = clip
            else:
                print(f"❌ 오디오 데이터 누락: {src_id}")

        combined.export(output_path, format="mp3")
        print(f"\n🎉 저장 완료: {output_path}")

if __name__ == "__main__":
    assembler = GoldenAssembler(audio_folder="./youtube_audio", json_path="./single_best.json")
    assembler.assemble("리그 오브 레전드")