import asyncio
import json
import os
import edge_tts
from pydub import AudioSegment
from jamo import h2j, j2hcj
from g2pk import G2p
import re  # 정규표현식 (특수문자 제거용)

# ffmpeg 경로 설정 (사용자 환경에 맞게 수정)
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

# ---------------------------------------------------------
# 1. 유사 발음 찾기 엔진 (Phonetic Vectorizer)
# ---------------------------------------------------------
class KoreanPhoneticVectorizer:
    def __init__(self):
        # 발음 기관이 비슷한 그룹끼리 묶음
        self.CHO_GROUPS = [{'ㄱ', 'ㄲ', 'ㅋ'}, {'ㄷ', 'ㄸ', 'ㅌ'}, {'ㅂ', 'ㅃ', 'ㅍ'}, {'ㅈ', 'ㅉ', 'ㅊ'}, {'ㅅ', 'ㅆ'}, {'ㅇ', 'ㅎ'}, {'ㄴ', 'ㄹ', 'ㅁ'}]
        self.JUNG_GROUPS = [{'ㅘ','ㅏ', 'ㅑ'}, {'ㅝ','ㅓ', 'ㅕ'}, {'ㅚ','ㅗ', 'ㅛ'}, {'ㅜ', 'ㅠ','ㅡ'}, {'ㅟ','ㅣ', 'ㅢ'}, {'ㅐ', 'ㅔ', 'ㅒ', 'ㅖ','ㅙ', 'ㅞ'}]
    
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
        
        if t_jung != d_jung:
            score += 10 if self._is_same_group(t_jung, d_jung, self.JUNG_GROUPS) else 90

        if t_cho != d_cho:
            score += 5 if self._is_same_group(t_cho, d_cho, self.CHO_GROUPS) else 40

        if t_jong != d_jong:
            if (t_jong == ' ') != (d_jong == ' '):
                score += 15
            elif self._is_same_group(t_jong, d_jong, self.CHO_GROUPS):
                score += 5
            else:
                score += 10
                
        return score


class GoldenAssembler:
    def __init__(self, audio_folder, json_path="./single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        self.golden_map = {}
        self.audio_cache = {}
        self.g2p = G2p()
        
        # 엔진 탑재
        self.vectorizer = KoreanPhoneticVectorizer()
        
        self._initialize_database()

    def _initialize_database(self):
        if not os.path.exists(self.json_path): return
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data: self.golden_map[entry['word']] = entry
        
        required = {d['src'] for d in data}
        for src in required:
            for ext in ['.mp3', '.wav', '.m4a']:
                path = os.path.join(self.audio_folder, src + ext)
                if os.path.exists(path):
                    self.audio_cache[src] = AudioSegment.from_file(path)
                    break
        print(f"✅ DB 로드 완료: {len(self.golden_map)}개 글자 보유")

    def _find_best_substitute(self, target_char):
        """ DB에 없는 글자일 경우, 가장 비슷한 글자를 찾아서 반환 """
        best_char = None
        min_score = 999
        
        for db_char in self.golden_map.keys():
            score = self.vectorizer.calculate_distance(target_char, db_char)
            if score < min_score:
                min_score = score
                best_char = db_char
            if min_score == 0: return best_char # 완벽 일치
            
        return best_char

    def match_target_amplitude(self, sound, target_dBFS=-18.0):
        change = target_dBFS - sound.dBFS
        return sound.apply_gain(change)

    def _apply_smart_speed(self, sound, target_ms):
        import subprocess
        import tempfile
        
        current_ms = len(sound)
        if current_ms == 0 or target_ms < 10: return sound
        
        ratio = current_ms / target_ms
        
        ratio = max(0.5, min(ratio, 2.0))
        
        if 0.95 <= ratio <= 1.05:
            if len(sound) > target_ms:
                return sound[:target_ms]
            else:
                return sound + AudioSegment.silent(duration=target_ms - len(sound))

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_in:
            sound.export(temp_in.name, format="wav")
            temp_in_path = temp_in.name
            
        # 임시 파일 생성 (출력용)
        temp_out_path = temp_in_path.replace(".wav", "_out.wav")

        try:
            ffmpeg_path = AudioSegment.converter 
            cmd = [
                ffmpeg_path, 
                "-y",              # 덮어쓰기 허용
                "-v", "error",     # 에러만 출력 (로그 숨김)
                "-i", temp_in_path,
                "-filter:a", f"atempo={ratio}",
                "-vn",             # 비디오 정보 제외 (오디오만)
                temp_out_path
            ]
            
            # 실행
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(temp_out_path):
                processed_sound = AudioSegment.from_file(temp_out_path)
                return processed_sound
            else:
                return sound[:target_ms]

        except Exception as e:
            print(f"⚠️ FFmpeg 처리 중 오류: {e}")
            return sound[:target_ms]
            
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

    def _get_char_weight(self,char, is_last_char=False):
        if not ('가' <= char <= '힣'): return 1.0
        jamo = j2hcj(h2j(char))
        weight = 1.0
        if len(jamo) == 3: weight += 0.4  # 받침 있음
        if is_last_char: weight += 0.9    # 어절 끝
        return weight

    def assemble(self, text, output_path="final_output.mp3"):
        text=re.sub(r'[^\w\s]', '', text)
        # 1. 발음 변환 (G2P)
        pronunciation = self.g2p(text)
        pronun_clean = re.sub(r'[^\w]', '', text)
        
        print(f"\n📢 입력: '{text}'")
        print(f"🔄 발음: {pronunciation}")

        combined = AudioSegment.empty()
        
        # 3. 합성 루프
        for i,char in enumerate(pronunciation):
            if char==' ':
                combined+=AudioSegment.silent(duration=200)
                continue
            target_ms = 200*self._get_char_weight(char,i==0 or i== len(pronunciation)-1 or pronunciation[i-1]==' ' or pronunciation[i+1]==' ' )
            
            # --- [핵심] 유사 단어 검색 메커니즘 ---
            final_char = char
            is_substitute = False
            
            if char not in self.golden_map:
                final_char = self._find_best_substitute(char)
                is_substitute = True
                
            if not final_char or final_char not in self.golden_map:
                print(f"❌ '{char}' -> 대체 실패 (무음 처리)")
                combined += AudioSegment.silent(duration=target_ms)
                continue

            # 오디오 처리
            info = self.golden_map[final_char]
            full_audio = self.audio_cache.get(info['src'])
            
            if full_audio:
                start, dur = info['start_ms'], info['duration_ms']
                if start + dur > len(full_audio): dur = len(full_audio) - start
                
                clip = full_audio[start : start + dur]
                clip = self.match_target_amplitude(clip)
                clip = self._apply_smart_speed(clip, target_ms)
                clip = clip.fade_in(2).fade_out(2)
                
                # 로그 출력
                log_msg = f"[{char}]"
                if is_substitute:
                    log_msg += f" -> 🔄대체: [{final_char}]"
                else:
                    log_msg += f" -> ✅정확"
                print(f"{log_msg} ({dur}ms -> {len(clip)}ms)")
                
                if len(combined) > 0:
                    combined = combined.append(clip, crossfade=10)
                else:
                    combined = clip
            else:
                combined += AudioSegment.silent(duration=target_ms)

        combined.export(output_path, format="mp3")
        print(f"🎉 합성 완료: {output_path}")

if __name__ == "__main__":
    assembler = GoldenAssembler(audio_folder="./youtube_audio")
    assembler.assemble("고생하셨습니다")