import json
import os
import numpy as np
from pydub import AudioSegment
from jamo import h2j, j2hcj
from g2pk import G2p

AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

class KoreanPhoneticVectorizer:
    def __init__(self):
        # 1. 초성 유사 그룹 (같은 줄에 있는 것끼리 교체 가능성 높음)
        self.CHO_GROUPS = [
            {'ㄱ', 'ㄲ', 'ㅋ'},  # 연구개음
            {'ㄷ', 'ㄸ', 'ㅌ'},  # 치조음 (파열)
            {'ㅂ', 'ㅃ', 'ㅍ'},  # 양순음
            {'ㅈ', 'ㅉ', 'ㅊ'},  # 경구개음
            {'ㅅ', 'ㅆ'},       # 치조음 (마찰)
            {'ㅇ', 'ㅎ'},       # 후음 (ㅎ는 ㅇ과 가깝게 처리)
            {'ㄴ', 'ㄹ', 'ㅁ'}   # 비음/유음 (울림소리)
        ]
        
        # 2. 중성(모음) 유사 그룹 (청각적으로 매우 유사한 것들)
        self.JUNG_GROUPS = [
            {'ㅏ', 'ㅑ'}, 
            {'ㅓ', 'ㅕ'},
            {'ㅗ', 'ㅛ'}, 
            {'ㅜ', 'ㅠ'},
            {'ㅡ', 'ㅣ'}, 
            {'ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'}, # 현대 국어에서 구분이 모호함
            {'ㅘ', 'ㅚ', 'ㅙ', 'ㅞ'}, # 와/웨 계열
            {'ㅝ', 'ㅟ', 'ㅢ'}
        ]

    def decompose(self, char):
        """한글 자모 분리 (초, 중, 종)"""
        if '가' <= char <= '힣':
            return j2hcj(h2j(char))
        return None

    def calculate_distance(self, target_char, db_char):
        """
        두 음절 사이의 거리를 계산 (점수가 낮을수록 유사함)
        0점: 완전 일치
        """
        t_parts = self.decompose(target_char)
        d_parts = self.decompose(db_char)

        # 한글이 아닌 경우 패널티 최대
        if not t_parts or not d_parts: return 999
        
        # 길이 보정 (종성이 없는 경우 처리)
        t_cho, t_jung, t_jong = (t_parts + ' ')[0:3]
        d_cho, d_jung, d_jong = (d_parts + ' ')[0:3]

        score = 0

        # --- 가중치 로직 (Hierarchy) ---
        
        # 1. 중성(모음) 비교 - 가장 중요 [가중치: 50]
        if t_jung != d_jung:
            if self._is_same_group(t_jung, d_jung, self.JUNG_GROUPS):
                score += 10 # 비슷한 모음 (예: ㅐ vs ㅔ)
            else:
                score += 50 # 완전히 다른 모음 (이러면 거의 탈락)

        # 2. 초성(자음) 비교 - 두 번째 중요 [가중치: 20]
        if t_cho != d_cho:
            if self._is_same_group(t_cho, d_cho, self.CHO_GROUPS):
                score += 5  # 같은 계열 (예: ㅂ vs ㅍ) -> 대체로 자연스러움
            else:
                score += 20 # 다른 계열 (예: ㅂ vs ㅅ)

        # 3. 종성(받침) 비교 - 덜 중요함 [가중치: 10]
        # 받침은 연음법칙 등으로 인해 자주 변하거나 생략됨
        if t_jong != d_jong:
            # 종성 유무가 다른 경우 (하나는 있고 하나는 없음) -> 큰 차이
            if (t_jong == ' ') != (d_jong == ' '):
                score += 15
            # 종성은 다르지만 비슷한 소리 (ㄴ vs ㅁ 등)
            elif self._is_same_group(t_jong, d_jong, self.CHO_GROUPS):
                score += 5
            else:
                score += 10

        return score

    def _is_same_group(self, c1, c2, groups):
        for group in groups:
            if c1 in group and c2 in group:
                return True
        return False

# --- FeatureVectorAssembler 클래스 내부 메서드 수정 ---
# 기존 클래스 안의 _find_best_match를 아래로 교체하세요.

    def _find_best_match(self, target_char):
        """유사도 점수(Penalty)가 가장 낮은 음절 탐색"""
        best_char = None
        min_score = 999
        
        # 성능 최적화를 위해 후보군을 무작위로 섞거나, 
        # 너무 많은 데이터가 있다면 여기서 1차 필터링을 할 수도 있습니다.
        
        candidates = []

        for db_char in self.syllable_map.keys():
            score = self.vectorizer.calculate_distance(target_char, db_char)
            
            # 완전 일치는 아니지만 쓸만한 후보 (점수 임계값 설정 가능)
            if score < min_score:
                min_score = score
                best_char = db_char
                candidates = [db_char] # 신규 1등
            elif score == min_score:
                candidates.append(db_char) # 동점자 처리

        # 동점자가 있다면 길이가 가장 긴(오디오 품질이 좋을 확률이 높은) 샘플 보유 음절 선택
        if candidates:
            # 후보들 중 보유한 오디오 클립의 평균 길이가 긴 것을 선택 (노이즈/짧은 발음 회피)
            best_char = max(candidates, key=lambda c: sum(x['dur'] for x in self.syllable_map[c]) / len(self.syllable_map[c]))
            
        return best_char
class FeatureVectorAssembler:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.syllable_map = {}
        self.loaded_audios = {}
        self.g2p = G2p() 
        self.vectorizer = KoreanPhoneticVectorizer() # 수정된 새 클래스 사용
        self._initialize_database()

    def _initialize_database(self):
        # 폴더 내 모든 json 파일 리스트업
        files = [f for f in os.listdir(self.data_folder) if f.endswith('.json')]
        
        for json_file in files:
            file_name = os.path.splitext(json_file)[0]
            base_name = file_name.split('_syllables')[0]

            audio_exts = ['.mp3', '.wav', '.m4a']
            audio_path = None
            
            for ext in audio_exts:
                path = os.path.join(self.data_folder, base_name + ext)
                if os.path.exists(path):
                    audio_path = path
                    break
            
            if not audio_path:
                print(f"경고: {json_file}에 해당하는 오디오 파일을 찾을 수 없습니다.")
                continue

            # 오디오 로드 (캐싱)
            if audio_path not in self.loaded_audios:
                self.loaded_audios[audio_path] = AudioSegment.from_file(audio_path)
            
            # JSON 파싱
            json_path = os.path.join(self.data_folder, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    for syll in entry.get('syllables', []):
                        char = syll['text']
                        if syll['duration_ms'] < 100: continue # 너무 짧은 건 제외
                        if char not in self.syllable_map:
                            self.syllable_map[char] = []
                        
                        self.syllable_map[char].append({
                            'audio': self.loaded_audios[audio_path],
                            'start': syll['start_ms'],
                            'dur': syll['duration_ms'],
                            'source': json_file
                        })
        
        print(f"인덱싱 완료: 총 {len(self.syllable_map)}개의 고유 음절 확보")
        

    def _find_best_match(self, target_char):
        """유사도 점수(Penalty)가 가장 낮은 음절 탐색"""
        best_char = None
        min_score = 999
        candidates = []

        # DB에 있는 모든 음절과 비교 (데이터가 너무 많으면 여기서 속도 저하 가능성 있음)
        for db_char in self.syllable_map.keys():
            score = self.vectorizer.calculate_distance(target_char, db_char)
            
            if score < min_score:
                min_score = score
                best_char = db_char
                candidates = [db_char] # 새로운 1등
            elif score == min_score:
                candidates.append(db_char) # 동점자

        # 동점자가 있다면 보유한 샘플들의 평균 길이가 긴(품질이 좋을 확률이 높은) 음절 선택
        if candidates:
            best_char = max(candidates, key=lambda c: sum(x['dur'] for x in self.syllable_map[c]) / len(self.syllable_map[c]))
            
        return best_char

    def assemble(self, text, output_path="phonetic_assembled.mp3"):
        # 1. 실제 발음 정규화
        pronunciation = self.g2p(text)
        print(f"분석된 발음: {pronunciation}")
        
        combined = AudioSegment.empty()
        for char in pronunciation:
            if char == " ":
                combined += AudioSegment.silent(duration=150); continue
            
            # 2. 매칭 수행 (직접 보유 or 대체 찾기)
            if char in self.syllable_map:
                curr = char
            else:
                curr = self._find_best_match(char)
            
            if not curr: 
                print(f"[{char}] -> 대체 불가 (건너뜀)")
                continue

            # 3. 최장 음절 선택 및 페이드 보정
            choice = max(self.syllable_map[curr], key=lambda x: x['dur'])
            
            # 너무 길면 자르기 (최대 350ms)
            save_dur = min(choice['dur'], 300)
            
            # 로그 출력
            match_msg = f"[{char}]"
            if curr != char:
                match_msg += f" -> 대체: [{curr}]"
            print(f"{match_msg} : {choice['source']} ({choice['start']} 부터 {save_dur}ms)")

            clip = choice['audio'][choice['start'] : choice['start'] + save_dur]
            clip = clip.fade_in(10).fade_out(10)

            if len(combined) > 0:
                combined = combined.append(clip, crossfade=10)
            else:
                combined = clip
            
        combined.export(output_path, format="mp3")
        print(f"--- 저장 완료: {output_path} ---")

# --- 실행 ---
assembler = FeatureVectorAssembler(data_folder="./youtube_audio")
assembler.assemble("리그 오브 레전드")