import asyncio
import json
import os
import glob
import edge_tts
from pydub import AudioSegment
from jamo import h2j, j2hcj
from g2pk import G2p
import re
import subprocess
import tempfile

# ffmpeg 경로 설정
# ffmpeg 경로 설정
# AudioSegment.converter = "ffmpeg" # 기본적으로 PATH에 있으면 주석 처리해도 됨


# ---------------------------------------------------------
# 1. 유사 발음 찾기 엔진
# ---------------------------------------------------------
class KoreanPhoneticVectorizer:
    def __init__(self):
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
            score += 30 if self._is_same_group(t_jung, d_jung, self.JUNG_GROUPS) else 90
        if t_cho != d_cho:
            score += 5 if self._is_same_group(t_cho, d_cho, self.CHO_GROUPS) else 50
        if t_jong != d_jong:
            if (t_jong == ' ') != (d_jong == ' '): score += 15
            elif self._is_same_group(t_jong, d_jong, self.CHO_GROUPS): score += 5
            else: score += 10
        return score

    def calculate_string_distance(self, target_str, db_str,cut=9999):
        if len(target_str) != len(db_str): return 9999
        total_score = 0
        for t, d in zip(target_str, db_str):
            eval=self.calculate_distance(t, d)
            total_score = max(eval,total_score)
        return total_score

# ---------------------------------------------------------
# 2. 메인 합성기
# ---------------------------------------------------------
class GoldenAssembler:
    def __init__(self, audio_folder, json_path="./single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        
        self.golden_map = {}
        self.chunk_prefix = {}
        self.chunk_suffix = {}
        self.audio_cache = {}
        
        self.g2p = G2p()
        self.vectorizer = KoreanPhoneticVectorizer()
        
        self._initialize_database()
        self._load_chunk_db()

    def _initialize_database(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data: self.golden_map[entry['word']] = entry
            
            required = {d['src'] for d in data}
            self._cache_audio_files(required)
            
        print(f"[INFO] 싱글 DB 로드 완료: {len(self.golden_map)}개")

    def _load_chunk_db(self):
        json_files = glob.glob(os.path.join(self.audio_folder, "*_syllables.json"))
        print(f"[INFO] 덩어리(Chunk) 데이터 분석 중... ({len(json_files)}개 파일)")
        
        chunk_count = 0
        required_srcs = set()

        for jf in json_files:
            src_id = os.path.basename(jf).replace("_syllables.json", "")
            required_srcs.add(src_id)
            
            with open(jf, 'r', encoding='utf-8') as f:
                words_data = json.load(f)
                
            for entry in words_data:
                syllables = entry.get('syllables', [])
                total_len = len(syllables)
                
                if total_len!=len(entry['word']):
                    print(f"conflict in {entry['word']} in {jf}")
                    return
                
                pronunciation=self.g2p(entry['word'])

                # 2글자 미만은 덩어리가 아님
                if total_len < 2: continue
                
                for length in range(2, total_len + 1):
                    chunk = syllables[0 :length]
                        
                    chunk_text = pronunciation[0:length]
                    
                    start_ms = chunk[0]['start_ms']
                    end_ms = chunk[-1]['start_ms'] + chunk[-1]['duration_ms']
                    duration_ms = end_ms - start_ms
                    
                    chunk_info = {
                        "text": chunk_text,
                        "src": src_id,
                        "start_ms": start_ms,
                        "duration_ms": duration_ms,
                        "length": length
                    }
                    
                    if length not in self.chunk_prefix:
                        self.chunk_prefix[length] = []
                    self.chunk_prefix[length].append(chunk_info)
                    chunk_count += 1

                    chunk = syllables[-length :]
                        
                    chunk_text = "".join([s['text'] for s in chunk])
                    
                    start_ms = chunk[0]['start_ms']
                    end_ms = chunk[-1]['start_ms'] + chunk[-1]['duration_ms']
                    duration_ms = end_ms - start_ms
                    
                    chunk_info = {
                        "text": chunk_text,
                        "src": src_id,
                        "start_ms": start_ms,
                        "duration_ms": duration_ms,
                        "length": length
                    }
                    
                    if length not in self.chunk_suffix:
                        self.chunk_suffix[length] = []
                    self.chunk_suffix[length].append(chunk_info)
                    chunk_count += 1

        self._cache_audio_files(required_srcs)
        print(f" 덩어리 DB 구축 완료 (Prefix/Suffix Only): {chunk_count}개 패턴 확보")

    def _cache_audio_files(self, src_ids):
        for src in src_ids:
            if src in self.audio_cache: continue
            audio_path = None
            for ext in ['.mp3', '.wav', '.m4a']:
                path = os.path.join(self.audio_folder, src + ext)
                if os.path.exists(path):
                    audio_path = path
                    break
            if audio_path:
                try:
                    self.audio_cache[src] = AudioSegment.from_file(audio_path)
                except: pass

    def _find_best_chunk(self,db, target_text):
        length = len(target_text)
        if length not in db: return None
        
        candidates = db[length]
        best_chunk = None
        max_cut = 20
        min_score=max_cut

        for chunk in candidates:
            if chunk['text'] == target_text:
                return chunk
            
            score = self.vectorizer.calculate_string_distance(target_text, chunk['text'],max_cut)
            
            if score < min_score and score < max_cut:
                min_score = score
                best_chunk = chunk
                
        return best_chunk

    def _find_best_substitute(self, target_char):
        best_char = None
        min_score = 999
        for db_char in self.golden_map.keys():
            score = self.vectorizer.calculate_distance(target_char, db_char)
            if score < min_score:
                min_score = score
                best_char = db_char
            if min_score == 0: return best_char
        return best_char

    def match_target_amplitude(self, sound, target_dBFS=-18.0):
        change = target_dBFS - sound.dBFS
        return sound.apply_gain(change)

    def _apply_smart_speed(self, sound, target_ms):
        current_ms = len(sound)
        if current_ms == 0 or target_ms < 10: return sound
        ratio = max(0.5, min(current_ms / target_ms, 2.0))
        if 0.95 <= ratio <= 1.05:
            if len(sound) > target_ms: return sound[:target_ms]
            else: return sound + AudioSegment.silent(duration=target_ms - len(sound))

        import subprocess, io, tempfile
        # 메모리 방식 사용
        try:
            input_buffer = io.BytesIO()
            sound.export(input_buffer, format="wav")
            input_data = input_buffer.getvalue()
            ffmpeg_path = AudioSegment.converter
            cmd = [ffmpeg_path, "-y", "-v", "error", "-f", "wav", "-i", "pipe:0", "-filter:a", f"atempo={ratio}", "-f", "wav", "pipe:1"]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_data, _ = process.communicate(input=input_data)
            output_buffer = io.BytesIO(out_data)
            processed_sound = AudioSegment.from_file(output_buffer, format="wav")
            if len(processed_sound) > target_ms: processed_sound = processed_sound[:target_ms]
            else: processed_sound += AudioSegment.silent(duration=target_ms - len(processed_sound))
            return processed_sound
        except: return sound[:target_ms]

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
            print(f"[ERROR] FFmpeg 처리 중 오류: {e}")
            return sound[:target_ms]
            
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

    def _get_char_weight(self, char, is_last_char=False):
        if not ('가' <= char <= '힣'): return 1.0
        jamo = j2hcj(h2j(char))
        weight = 1.0
        if len(jamo) == 3: weight += 0.3
        if is_last_char: weight += 0.9
        return weight

    def _get_clip_from_info(self, info):
        """
        info 딕셔너리({'src', 'start_ms', 'duration_ms'})를 받아
        오디오를 자르고, 볼륨을 평준화하고, 페이드 처리를 해서 반환합니다.
        """
        src_id = info['src']
        
        # 1. 오디오 소스 확인
        if src_id not in self.audio_cache:
            # 혹시 캐시에 없으면 로드 시도 (경로 추론)
            audio_path = None
            for ext in ['.mp3', '.wav', '.m4a']:
                path = os.path.join(self.audio_folder, src_id + ext)
                if os.path.exists(path):
                    audio_path = path
                    break
            
            if audio_path:
                try:
                    self.audio_cache[src_id] = AudioSegment.from_file(audio_path)
                except:
                    return None
            else:
                return None

        full_audio = self.audio_cache[src_id]
        start = info['start_ms']
        dur = info['duration_ms']

        # 2. 범위 안전 장치 (오디오 길이 초과 방지)
        if start >= len(full_audio):
            return None
        
        if start + dur > len(full_audio):
            dur = len(full_audio) - start

        # 3. 자르기 (Trimming)
        clip = full_audio[start : start + dur]

        # 4. 볼륨 평준화 (Normalization)
        # Prefix/Suffix 처리를 위해 여기서 수행해야 함 (-20dBfs 기준)
        clip = self.match_target_amplitude(clip)

        # 5. 클릭음 방지 페이드 (De-clicking)
        # 뚝뚝 끊기는 소리를 방지하기 위해 아주 짧게 페이드 처리
        clip = clip.fade_in(5).fade_out(5)

        return clip

    def assemble(self, text, output_path="final_output_hybrid.mp3"):
        # 1. 텍스트 정리
        clean_text_input = re.sub(r'[^\w\s]', '', text)
        print(f"\n 입력: '{clean_text_input}'")

        combined = AudioSegment.empty()
        # 타이밍 정보 저장용 리스트
        # 구조: { "char": "가", "start": 0, "end": 200, "type": "prefix"/"middle"/"suffix"/"silence" }
        timing_data = []

        # 단어 단위 분리
        words = clean_text_input.split(" ")
        
        current_time_ms = 0

        for word in words:
            pronunciation = self.g2p(word)
            total_len = len(pronunciation)
            
            print(f"\n 단어 처리: '{word}' -> [{pronunciation}]")

            prefix_chunk = None
            suffix_chunk = None
            prefix_len = 0
            suffix_len = 0

            # -------------------------------------------------------------
            # Step 1: Prefix (앞부분) 검색
            # -------------------------------------------------------------
            max_search_len = min(5, total_len)
            for length in range(max_search_len, 1, -1):
                target_sub = pronunciation[0:length]
                chunk_match = self._find_best_chunk(self.chunk_prefix,target_sub)
                
                if chunk_match:
                    prefix_chunk = chunk_match
                    prefix_len = length
                    src= prefix_chunk["src"]
                    print(f"  Prefix 발견: '{target_sub} -> '{chunk_match['text']}' : {src} {self.vectorizer.calculate_string_distance(target_sub,chunk_match['text'])}")
                    break
            
            
            remaining_len = total_len - prefix_len
            max_search_len = min(5, remaining_len)
            
            for length in range(max_search_len, 1, -1):
                # 뒤에서부터 검색
                target_sub = pronunciation[total_len - length : total_len]
                chunk_match = self._find_best_chunk(self.chunk_suffix,target_sub)
                
                if chunk_match:
                    suffix_chunk = chunk_match
                    suffix_len = length
                    src=suffix_chunk["src"]
                    print(f"  Suffix 발견: '{target_sub} -> '{chunk_match['text']}' : {src} {self.vectorizer.calculate_string_distance(target_sub,chunk_match['text'])}")
                    break

            if prefix_chunk:
                clip = self._get_clip_from_info(prefix_chunk)
                if clip:
                    duration = len(clip)
                    timing_data.append({
                        "char": prefix_chunk['text'],
                        "start": current_time_ms,
                        "end": current_time_ms + duration,
                        "type": "prefix"
                    })
                    
                    if len(combined) > 0: 
                        # crossfade가 있으면 길이가 줄어들 수 있음. 계산 단순화를 위해 단순히 더함 (crossfade 고려 필요시 수정)
                        # 여기서는 정확한 타이밍을 위해 crossfade가 적용된 후 길이를 측정하는게 좋지만, 일단 duration 기반으로 계산
                        combined = combined.append(clip, crossfade=10)
                        # crossfade 적용 시 실제 길이는 (기존 + 새클립 - crossfade)
                        # 단, combined += clip 인 경우는 그대로.
                        # 여기서는 변동폭이 작으므로 duration 그대로 더하고 보정은 추후 고려
                        current_time_ms += duration - 10 # crossfade 만큼 뺌
                    else: 
                        combined += clip
                        current_time_ms += duration

            # B. Middle (한 글자씩)
            start_mid = prefix_len
            end_mid = total_len - suffix_len
            
            for i in range(start_mid, end_mid):
                char = pronunciation[i]
                islast=i==0 or i==total_len-1
                
                target_char = char
                is_substitute = False
                
                # 대체 글자 찾기
                if char not in self.golden_map:
                    target_char = self._find_best_substitute(char)
                    is_substitute = True

                info = self.golden_map[target_char]
                clip = self._get_clip_from_info(info) 
                clip = self._apply_smart_speed(clip, 200*self._get_char_weight(target_char,islast))
                
                src=info["src"]
                
                if clip:
                    duration = len(clip)
                    timing_data.append({
                        "char": char,
                        "start": current_time_ms,
                        "end": current_time_ms + duration,
                        "type": "middle"
                    })

                    if len(combined) > 0: 
                        combined = combined.append(clip, crossfade=10)
                        current_time_ms += duration - 10
                    else: 
                        combined+=clip
                        current_time_ms += duration

            # C. Suffix 추가
            if suffix_chunk:
                clip = self._get_clip_from_info(suffix_chunk)
                if clip:
                    duration = len(clip)
                    timing_data.append({
                        "char": suffix_chunk['text'],
                        "start": current_time_ms,
                        "end": current_time_ms + duration,
                        "type": "suffix"
                    })

                    if len(combined) > 0: 
                        combined = combined.append(clip, crossfade=10)
                        current_time_ms += duration - 10
                    else: 
                        combined += clip
                        current_time_ms += duration
            
            # 단어 사이 묵음
            silence_dur = 200
            combined += AudioSegment.silent(duration=silence_dur)
            current_time_ms += silence_dur
            timing_data.append({
                "char": " ",
                "start": current_time_ms - silence_dur,
                "end": current_time_ms,
                "type": "space"
            })

        combined.export(output_path, format="mp3")
        print(f"\n 저장 완료: {output_path}")
        return timing_data

if __name__ == "__main__":
    import sys
    text_to_speak = "감사합니다"
    if len(sys.argv) > 1:
        text_to_speak = sys.argv[1]
    
    assembler = GoldenAssembler(audio_folder="./youtube_audio")
    assembler.assemble(text_to_speak)   