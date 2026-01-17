import json
import os
from pydub import AudioSegment
import random

AudioSegment.converter=r"C:\ffmpeg\bin\ffmpeg.exe"

class MultiVoiceAssembler:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.syllable_map = {}  # 음절: [(오디오객체, 시작시간, 길이), ...]
        self.loaded_audios = {} # 오디오 파일 캐싱 (중복 로드 방지)
        
        self._initialize_database()

    def _initialize_database(self):
        # 폴더 내 모든 json 파일 리스트업
        files = [f for f in os.listdir(self.data_folder) if f.endswith('.json')]
        
        for json_file in files:
            file_name = os.path.splitext(json_file)[0]
            base_name=file_name.split('_syllables')[0]

            # JSON 파일명과 대응되는 mp3/wav 파일이 있다고 가정
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

            # 오디오 로드 및 저장
            if audio_path not in self.loaded_audios:
                self.loaded_audios[audio_path] = AudioSegment.from_file(audio_path)
            
            # JSON 파싱 및 음절 맵 추가
            json_path = os.path.join(self.data_folder, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    for syll in entry.get('syllables', []):
                        char = syll['text']
                        if char not in self.syllable_map:
                            self.syllable_map[char] = []
                        
                        self.syllable_map[char].append({
                            'audio': self.loaded_audios[audio_path],
                            'start': syll['start_ms'],
                            'dur': syll['duration_ms'],
                            'source': json_file # 디버깅용
                        })
        print(f"인덱싱 완료: 총 {len(self.syllable_map)}개의 고유 음절 확보")

    def assemble(self, text, output_path="longest_output.mp3", crossfade=20):
        """
        랜덤 선택 대신, DB 내에서 해당 음절의 'duration'이 가장 긴 샘플을 선택합니다.
        """
        combined = AudioSegment.empty()
        
        print(f"\n--- 최장 음소 기반 문장 생성: '{text}' ---")
        
        for char in text:
            if char == " ":
                # 공백은 약 100ms의 무음으로 처리
                combined += AudioSegment.silent(duration=100)
                continue
                
            if char in self.syllable_map:
                # 해당 음절의 샘플 리스트 중 'dur' 값이 가장 큰 것을 선택
                # 람다 함수를 사용하여 dict의 'dur' 값을 기준으로 비교합니다.
                choice = max(self.syllable_map[char], key=lambda x: x['dur'])
                
                if choice['dur']>300:
                    save_dur=300
                else:
                    save_dur=choice['dur'] 
                
                source_id = choice['source'].split('_syllables')[0]
                print(f"[{char}] : {source_id} ({choice['start']}ms부터  {choice['start'] + save_dur}ms까지) {save_dur}ms 선택됨")
                
                # 선택된 구간 추출
                clip = choice['audio'][choice['start'] : choice['start'] + save_dur]

                if len(combined) > 0:
                    combined = combined.append(clip, crossfade=crossfade)
                else:
                    combined = clip
            else:
                print(f"[{char}] : 음절이 없어 건너뜁니다.")

        combined.export(output_path, format="mp3")
        print(f"--- 저장 완료: {output_path} ---")

# --- 실행부 ---
# 'data' 폴더 안에 json과 mp3 파일들을 모아두고 실행하세요.
# 파일명은 'voice1.json', 'voice1.mp3' 처럼 짝이 맞아야 합니다.
random.seed()
assembler = MultiVoiceAssembler(data_folder="./youtube_audio")
assembler.assemble("서버가 안돼")