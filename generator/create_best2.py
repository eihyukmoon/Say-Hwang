import os
import json
import subprocess
import operator
from pydub import AudioSegment
from assemble_v2 import FeatureVectorAssembler 

class AutoReviewer(FeatureVectorAssembler):
    def play_sound(self, audio_segment):
        """ffmpeg의 ffplay를 이용해 즉시 재생"""
        # [수정] ffplay.exe의 절대 경로를 직접 지정합니다.
        ffplay_path = r"C:\ffmpeg\bin\ffplay.exe" 
        
        # 파일이 실제로 있는지 확인 (없으면 에러 메시지 출력)
        if not os.path.exists(ffplay_path):
            print(f"\n❌ 오류: {ffplay_path} 파일을 찾을 수 없습니다.")
            print("ffmpeg 폴더 안에 ffplay.exe가 있는지 확인해주세요.")
            return

        temp_file = "temp_preview.mp3"
        audio_segment.export(temp_file, format="mp3")
        
        # -nodisp: 화면없음, -autoexit: 종료시 닫힘, -loglevel quiet: 로그숨김
        # 경로에 공백이 있을 수 있으므로 따옴표(")로 감싸줍니다.
        cmd = f'"{ffplay_path}" -nodisp -autoexit -loglevel quiet "{temp_file}"'
        
        subprocess.run(cmd, shell=True)
        
        if os.path.exists(temp_file):
            os.remove(temp_file)

    def load_completed_chars(self, json_path="single_best.json"):
        """이미 작업한 글자 목록을 불러옵니다."""
        if not os.path.exists(json_path):
            return set()
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(item['word'] for item in data)
        except:
            return set()

    def save_selection(self, target_char, candidate):
        """선택한 후보를 JSON에 저장"""
        original_dur = candidate['dur']
        
        while True:
            val = input(f"   ✂️ 길이 조절 (엔터 = 원본 {original_dur}ms / 숫자 = 변경할 ms): ").strip()
            if not val:
                final_dur = original_dur
                break
            if val.isdigit():
                final_dur = int(val)
                break
            print("   숫자만 입력하세요.")

        clean_src = candidate['source'].replace('_syllables.json', '').replace('.json', '')
        
        new_entry = {
            "src": clean_src,
            "word": target_char,
            "start_ms": candidate['start'],
            "duration_ms": final_dur
        }

        json_path = "single_best.json"
        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = []

        data = [item for item in data if item['word'] != target_char]
        data.append(new_entry)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"   ✅ 저장됨: [{target_char}]")

    def review_loop(self, target_char, current_idx, total_chars):
        """한 글자에 대한 검수 루프"""
        candidates = self.syllable_map[target_char]
        # 샘플 길이 긴 순서로 정렬
        sorted_candidates = sorted(candidates, key=lambda x: x['dur'], reverse=True)
        
        cand_count = len(sorted_candidates)
        print("\n" + "="*60)
        print(f"🎯 전체 진행: {current_idx}/{total_chars} | 현재 글자: [{target_char}] (후보 {cand_count}개)")
        print("="*60)
        print(" [Enter]: 다음 후보 (패스)")
        print(" [y]: 채택 (이걸로 결정하고 다음 글자로)")
        print(" [r]: 다시 듣기")
        print(" [n]: 이 글자 건너뛰기 (Next Char)")
        print(" [q]: 프로그램 전체 종료")
        print("-" * 60)

        for i, cand in enumerate(sorted_candidates):
            src_clean = cand['source'].replace('_syllables.json', '').replace('.json', '')
            
            while True:
                print(f"▶ 후보 {i+1}/{cand_count} | 원본: {cand['dur']}ms | 출처: {src_clean}")
                
                # 소리 재생
                clip = cand['audio'][cand['start'] : cand['start'] + cand['dur']]
                self.play_sound(clip)

                choice = input("   👉 명령 [Enter/y/r/n/q]: ").strip().lower()

                if choice == 'r':
                    continue # 다시 듣기
                
                elif choice == 'y':
                    self.save_selection(target_char, cand)
                    return "NEXT_CHAR" # 저장했으니 다음 글자로
                
                elif choice == 'n':
                    print(f"   💨 '{target_char}' 건너뜀.")
                    return "NEXT_CHAR" # 저장 안 하고 다음 글자로
                
                elif choice == 'q':
                    return "QUIT_ALL" # 전체 종료
                
                else:
                    break # Enter: 다음 후보 재생

        print(f"\n🚫 '{target_char}'의 쓸만한 후보가 더 없습니다. 다음 글자로 넘어갑니다.")
        return "NEXT_CHAR"

    def run_full_review(self):
        # 1. 작업해야 할 모든 글자 가져오기
        all_chars = list(self.syllable_map.keys())
        
        # 2. 정렬 전략: 샘플이 많은(자주 쓰이는) 글자부터 먼저 검수
        print("📊 데이터 분석 및 정렬 중...")
        all_chars.sort(key=lambda char: len(self.syllable_map[char]), reverse=True)
        
        total_chars = len(all_chars)
        
        # 3. 메인 루프
        for idx, char in enumerate(all_chars):
            # 이미 완료했는지 체크
            completed = self.load_completed_chars()
            if char in completed:
                continue # 이미 했으면 스킵

            # 검수 실행
            result = self.review_loop(char, idx + 1, total_chars)
            
            if result == "QUIT_ALL":
                print("\n👋 검수를 종료합니다. (진행 상황은 single_best.json에 저장됨)")
                break

# --- 실행 ---
if __name__ == "__main__":
    reviewer = AutoReviewer(data_folder="./youtube_audio")
    print("\n🚀 전체 자동 검수 모드를 시작합니다.")
    print("   - 이미 single_best.json에 있는 글자는 자동으로 건너뜁니다.")
    print("   - 샘플이 많은(중요한) 글자부터 순서대로 나옵니다.")
    
    reviewer.run_full_review()