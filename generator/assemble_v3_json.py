import json
import os
import glob
from pydub import AudioSegment
from jamo import h2j, j2hcj
from g2pk import G2p
import re
import math

# ffmpeg 경로 설정
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

# ---------------------------------------------------------
# 1. 유사 발음 찾기 엔진 (기존과 동일)
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

    def calculate_string_distance(self, target_str, db_str, cut=9999):
        if len(target_str) != len(db_str): return 9999
        total_score = 0
        for t, d in zip(target_str, db_str):
            eval = self.calculate_distance(t, d)
            total_score = max(eval, total_score) # Max pooling distance
        return total_score

# ---------------------------------------------------------
# 2. 메인 시퀀서 (JSON 생성기)
# ---------------------------------------------------------
class GoldenAssemblerJSON:
    def __init__(self, audio_folder, json_path="./single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        
        self.golden_map = {}
        self.chunk_prefix = {}
        self.chunk_suffix = {}
        self.audio_cache = {} # dBFS 계산을 위해 로딩은 필요함
        
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
            
        print(f"✅ 싱글 DB 로드 완료: {len(self.golden_map)}개")

    def _load_chunk_db(self):
        json_files = glob.glob(os.path.join(self.audio_folder, "*_syllables.json"))
        print(f"📂 덩어리(Chunk) 데이터 분석 중... ({len(json_files)}개 파일)")
        
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
                pronunciation = self.g2p(entry['word'])
                
                # 검증
                if len(pronunciation) != total_len: continue 
                if total_len < 2: continue
                
                # Prefix 등록
                for length in range(2, total_len + 1):
                    chunk = syllables[0 : length]
                    chunk_text = pronunciation[0:length]
                    
                    start_ms = chunk[0]['start_ms']
                    end_ms = chunk[-1]['start_ms'] + chunk[-1]['duration_ms']
                    
                    chunk_info = {
                        "text": chunk_text,
                        "src": src_id,
                        "start_ms": start_ms,
                        "duration_ms": end_ms - start_ms,
                        "length": length
                    }
                    if length not in self.chunk_prefix: self.chunk_prefix[length] = []
                    self.chunk_prefix[length].append(chunk_info)
                    chunk_count += 1

                # Suffix 등록
                for length in range(2, total_len + 1):
                    chunk = syllables[total_len - length : total_len]
                    chunk_text = pronunciation[total_len - length : total_len]
                    
                    start_ms = chunk[0]['start_ms']
                    end_ms = chunk[-1]['start_ms'] + chunk[-1]['duration_ms']
                    
                    chunk_info = {
                        "text": chunk_text,
                        "src": src_id,
                        "start_ms": start_ms,
                        "duration_ms": end_ms - start_ms,
                        "length": length
                    }
                    if length not in self.chunk_suffix: self.chunk_suffix[length] = []
                    self.chunk_suffix[length].append(chunk_info)
                    chunk_count += 1

        self._cache_audio_files(required_srcs)
        print(f"✅ 덩어리 DB 구축 완료: {chunk_count}개")

    def _cache_audio_files(self, src_ids):
        # 볼륨(dBFS) 측정을 위해 오디오 로딩은 필요합니다.
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

    # --- 검색 로직 ---
    def _find_best_chunk(self, db, target_text):
        length = len(target_text)
        if length not in db: return None
        
        candidates = db[length]
        best_chunk = None
        min_score = 20
        
        for chunk in candidates:
            if chunk['text'] == target_text: return chunk
            score = self.vectorizer.calculate_string_distance(target_text, chunk['text'], 9999)
            if score <= 20 and score < min_score:
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

    def _get_char_weight(self, char, is_last_char=False):
        if not ('가' <= char <= '힣'): return 1.0
        jamo = j2hcj(h2j(char))
        weight = 1.0
        if len(jamo) == 3: weight += 0.3
        if is_last_char: weight += 0.9
        return weight

    # --- 계산 로직 (오디오 조작 X, 값 계산 O) ---

    def calculate_volume_adjustment(self, info, target_dBFS=-18.0):
        """해당 구간의 현재 볼륨을 측정하여 필요한 Gain 값을 반환"""
        src_id = info['src']
        if src_id not in self.audio_cache: return 0.0
        
        full_audio = self.audio_cache[src_id]
        start = info['start_ms']
        dur = info['duration_ms']
        
        # 안전 장치
        if start >= len(full_audio): return 0.0
        if start + dur > len(full_audio): dur = len(full_audio) - start
        
        clip = full_audio[start : start + dur]
        if len(clip) == 0: return 0.0
        
        # 차이값 계산
        needed_gain = target_dBFS - clip.dBFS
        return round(needed_gain, 2)

    def calculate_speed_rate(self, current_ms, target_ms):
        """목표 시간 대비 배속률 계산"""
        if current_ms == 0 or target_ms < 10: return 1.0
        
        # target_ms가 더 짧으면 빨리 재생해야 함 (ratio > 1)
        # target_ms가 더 길면 느리게 재생해야 함 (ratio < 1)
        ratio = current_ms / target_ms
        
        # 제한 (0.5배 ~ 2.0배)
        ratio = max(0.5, min(ratio, 2.0))
        
        # 5% 이내 오차는 그냥 1.0 처리
        if 0.95 <= ratio <= 1.05:
            return 1.0
        
        return round(ratio, 3)

    # --- 메인 생성 메서드 ---

    def generate_sequence(self, text, output_path="output_sequence.json"):
        clean_text_input = re.sub(r'[^\w\s]', '', text)
        print(f"\n📢 시퀀스 생성 시작: '{clean_text_input}'")

        sequence = [] # 최종 JSON 리스트
        
        words = clean_text_input.split(" ")
        
        for word in words:
            pronunciation = self.g2p(word)
            total_len = len(pronunciation)
            
            print(f"\n🔹 단어: '{word}' -> [{pronunciation}]")

            prefix_chunk = None
            suffix_chunk = None
            prefix_len = 0
            suffix_len = 0

            # 1. Prefix 검색
            max_search_len = min(5, total_len)
            for length in range(max_search_len, 1, -1):
                target_sub = pronunciation[0:length]
                chunk_match = self._find_best_chunk(self.chunk_prefix, target_sub)
                if chunk_match:
                    prefix_chunk = chunk_match
                    prefix_len = length
                    print(f"  👉 Prefix: '{target_sub}' (len={length})")
                    break
            
            # 2. Suffix 검색
            remaining_len = total_len - prefix_len
            if remaining_len >= 2:
                max_search_len = min(5, remaining_len)
                for length in range(max_search_len, 1, -1):
                    target_sub = pronunciation[total_len - length : total_len]
                    chunk_match = self._find_best_chunk(self.chunk_suffix, target_sub)
                    if chunk_match:
                        suffix_chunk = chunk_match
                        suffix_len = length
                        print(f"  👈 Suffix: '{target_sub}' (len={length})")
                        break

            # --- 시퀀스 작성 ---

            # A. Prefix
            if prefix_chunk:
                vol_adj = self.calculate_volume_adjustment(prefix_chunk)
                
                # 파일 확장자 찾기
                for e in ['.mp3', '.wav', '.m4a']:
                    if os.path.exists(os.path.join(self.audio_folder, prefix_chunk['src'] + e)):
                        ext = e
                        break
                        
                sequence.append({
                    "text": prefix_chunk['text'],
                    "file_name": prefix_chunk['src'],
                    "start_ms": prefix_chunk['start_ms'],
                    "duration_ms": prefix_chunk['duration_ms'],
                    "speed": 1.0, # 덩어리는 보통 원본 속도
                    "volume_gain_db": vol_adj
                })

            # B. Middle (낱글자)
            start_mid = prefix_len
            end_mid = total_len - suffix_len
            
            for i in range(start_mid, end_mid):
                char = pronunciation[i]
                islast = (i == 0) or (i == total_len - 1)
                
                target_char = char
                is_substitute = False
                
                if char not in self.golden_map:
                    target_char = self._find_best_substitute(char)
                    is_substitute = True

                info = self.golden_map[target_char]
                vol_adj = self.calculate_volume_adjustment(info)
                
                # 속도 계산
                current_len = info['duration_ms']
                target_len = 200 * self._get_char_weight(target_char, islast)
                speed_rate = self.calculate_speed_rate(current_len, target_len)
                
                # 파일 확장자 찾기
                ext = ".mp3"
                for e in ['.mp3', '.wav', '.m4a']:
                    if os.path.exists(os.path.join(self.audio_folder, info['src'] + e)):
                        ext = e
                        break
                
                log = f"    🧩 Middle: '{char}'"
                if is_substitute: log += f" (->{target_char})"
                print(log)

                sequence.append({
                    "text": char, # 디버깅용
                    "substitute_text": target_char if is_substitute else None,
                    "file_name": info['src'],
                    "start_ms": info['start_ms'],
                    "duration_ms": info['duration_ms'],
                    "speed": speed_rate,
                    "volume_gain_db": vol_adj
                })

            # C. Suffix
            if suffix_chunk:
                vol_adj = self.calculate_volume_adjustment(suffix_chunk)
                
                ext = ".mp3"
                for e in ['.mp3', '.wav', '.m4a']:
                    if os.path.exists(os.path.join(self.audio_folder, suffix_chunk['src'] + e)):
                        ext = e
                        break

                sequence.append({
                    "text": suffix_chunk['text'],
                    "file_name": suffix_chunk['src'],
                    "start_ms": suffix_chunk['start_ms'],
                    "duration_ms": suffix_chunk['duration_ms'],
                    "speed": 1.0,
                    "volume_gain_db": vol_adj
                })
            
            # 단어 사이 묵음
            sequence.append({
                "type": "silence",
                "duration_ms": 200
            })

        # JSON 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sequence, f, indent=4, ensure_ascii=False)
        
        print(f"\n🎉 시퀀스 JSON 저장 완료: {output_path}")

if __name__ == "__main__":
    assembler = GoldenAssemblerJSON(audio_folder="./youtube_audio")
    assembler.generate_sequence("누구세요? 뚱인데요 할렐루야")