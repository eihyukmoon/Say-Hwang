import json
import os
import subprocess
import sys
from pydub import AudioSegment
from pydub.generators import Sine  # 소리 생성을 위해 추가됨

# ffmpeg 경로 설정 (사용자 환경에 맞게 수정)
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPLAY_PATH = r"C:\ffmpeg\bin\ffplay.exe"

class GoldenRefiner:
    def __init__(self, audio_folder, json_path="single_best.json"):
        self.audio_folder = audio_folder
        self.json_path = json_path
        self.data = []
        self.audio_cache = {}
        
        # '삐' 소리 미리 만들어두기 (1000Hz, 50ms)
        # -10dB로 줄여서 너무 시끄럽지 않게 설정
        self.beep = Sine(1000).to_audio_segment(duration=50).apply_gain(-10)
        self.silence = AudioSegment.silent(duration=100) # 삐 소리 후 0.1초 대기

        self.load_data()

    def load_data(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            # 단어 가나다순 정렬
            self.data.sort(key=lambda x: x['word'])
            print(f"📂 데이터 로드 완료: {len(self.data)}개 항목")
        else:
            print("❌ single_best.json 파일이 없습니다.")
            sys.exit()

    def save_data(self):
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def match_target_amplitude(self, sound, target_dBFS=-20.0):
        """
        현재 사운드의 dBFS(Decibels relative to Full Scale)를 확인하고,
        Target 볼륨과의 차이만큼 게인(Gain)을 조절하여 리턴합니다.
        """
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    def play_once(self, clip):
        """삐 소리를 붙여서 재생"""
        temp_file = "temp_refine.mp3"
        
        # [수정됨] 삐 + 침묵 + 실제오디오 합치기
        final_sound = self.beep + clip
        
        final_sound = self.match_target_amplitude(final_sound, target_dBFS=-20.0)
        
        final_sound.export(temp_file, format="mp3")
        
        # -nodisp: 화면 없음, -autoexit: 재생 후 종료, -loglevel quiet: 로그 숨김
        cmd = f'"{FFPLAY_PATH}" -nodisp -autoexit -loglevel quiet "{temp_file}"'
        subprocess.run(cmd, shell=True)
        try: os.remove(temp_file)
        except: pass

    def refine_item(self, index):
        """하나의 아이템을 편집하는 루프"""
        entry = self.data[index]
        src_id = entry['src']
        word = entry['word']
        
        # 오디오 캐싱
        if src_id not in self.audio_cache:
            found = False
            for ext in ['.mp3', '.wav', '.m4a']:
                path = os.path.join(self.audio_folder, src_id + ext)
                if os.path.exists(path):
                    print(f"\n🎵 오디오 로딩 중... ({src_id})")
                    self.audio_cache[src_id] = AudioSegment.from_file(path)
                    found = True
                    break
            if not found:
                print(f"❌ 오디오 파일 없음: {src_id}")
                return "DELETE"

        full_audio = self.audio_cache[src_id]
        
        # 편집 변수 초기화
        start = entry['start_ms']
        dur = entry['duration_ms']
        end = start + dur
        
        # UI 안내
        print("\n" + "="*60)
        print(f"🔥 편집 중: [{word}] (진행: {index+1} / {len(self.data)})")
        print("="*60)
        print(" [숫자 숫자] : 시작 끝 시간 직접 입력 (예: 1200 1500)")
        print(" [p] : 다시 듣기 (삐~ 소리 포함)")
        print(" [s] : 저장 & 다음")
        print(" [x] : 🗑️ 삭제")
        print(" [q] : 종료")
        print("-" * 60)

        # 진입 시 1회 자동 재생
        print(f"   현재 구간: {start} ~ {end} (길이: {end-start}ms)")
        self.play_once(full_audio[start:end])

        while True:
            user_input = input(f"👉 입력 ({start} {end}): ").strip().lower()

            if user_input == 'q':
                return "QUIT"

            elif user_input == 's':
                entry['start_ms'] = int(start)
                entry['duration_ms'] = int(end - start)
                return "NEXT"

            elif user_input == 'x':
                return "DELETE"

            elif user_input == 'p' or user_input == '':
                print(f"   🔊 재생 중...")
                self.play_once(full_audio[start:end])

            else:
                try:
                    parts = user_input.split()
                    if len(parts) == 2:
                        new_start = int(parts[0])
                        new_end = int(parts[1])
                        
                        if new_end > new_start:
                            start = new_start
                            end = new_end
                            print(f"   ✅ 변경됨! -> {start} ~ {end} (길이: {end-start}ms)")
                            self.play_once(full_audio[start:end])
                        else:
                            print("   ⚠️ 끝 시간이 시작 시간보다 커야 합니다.")
                    else:
                        print("   ⚠️ 형식이 틀렸습니다. '시작 끝' 순서로 입력하세요.")
                except ValueError:
                    print("   ⚠️ 숫자 또는 명령어만 입력하세요.")

    def run(self):
        index = 0
        while index < len(self.data):
            action = self.refine_item(index)
            
            if action == "QUIT":
                print("\n👋 종료합니다.")
                break
            
            elif action == "NEXT":
                self.save_data()
                print(" -> 💾 저장됨")
                index += 1
            
            elif action == "DELETE":
                deleted_word = self.data[index]['word']
                del self.data[index]
                self.save_data()
                print(f"\n -> 🗑️ [{deleted_word}] 삭제 완료")
        
        print("\n🎉 모든 데이터 검수 완료!")

if __name__ == "__main__":
    refiner = GoldenRefiner(audio_folder="./youtube_audio")
    refiner.run()