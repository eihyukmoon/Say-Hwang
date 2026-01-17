import os
import json
from pydub import AudioSegment
from assemble_v2 import FeatureVectorAssembler 

class SyllableReviewer(FeatureVectorAssembler):
    def review_character(self, target_char, limit=30):
        """
        후보 리스트를 보여줄 때 '원본 길이'를 눈으로 확인할 수 있게 출력합니다.
        """
        if target_char not in self.syllable_map:
            print(f"❌ '{target_char}'는 데이터에 없습니다.")
            return []

        candidates = self.syllable_map[target_char]
        # 길이(duration) 긴 순서대로 정렬
        sorted_candidates = sorted(candidates, key=lambda x: x['dur'], reverse=True)
        
        print(f"\n🔍 '{target_char}' 검색 결과: 총 {len(sorted_candidates)}개 발견")
        print(f"--- 상위 {min(len(sorted_candidates), limit)}개 리스트 (길이순) ---")
        # [수정] 사용자가 고르기 전에 참고할 수 있도록 여기서 '원본 길이'를 보여줍니다.
        print(f"{'ID':<4} | {'원본 길이':<10} | {'출처 (src)':<20} | {'시작 시간'}")
        print("-" * 65)

        review_audio = AudioSegment.empty()
        
        for idx, cand in enumerate(sorted_candidates[:limit]):
            src_clean = cand['source'].replace('_syllables.json', '').replace('.json', '')
            
            # 리스트 출력
            print(f"{idx:<4} | {cand['dur']:<10} | {src_clean[:20]:<20} | {cand['start']}ms")
            
            # 듣기 파일 생성 (구분 묵음 0.4초)
            clip = cand['audio'][cand['start'] : cand['start'] + cand['dur']]
            review_audio += clip + AudioSegment.silent(duration=400)

        output_filename = f"review_{target_char}.mp3"
        review_audio.export(output_filename, format="mp3")
        print("-" * 65)
        print(f"🎧 듣기 파일 생성됨: {output_filename}")
        
        return sorted_candidates

    def save_best_json(self, target_char, index, candidates, custom_dur=None, json_path="single_best.json"):
        """
        [수정] JSON 파일에는 'original_duration_ms'를 저장하지 않고,
        실제 합성 때 필요한 핵심 정보만 저장합니다.
        """
        if index >= len(candidates):
            print("❌ 잘못된 ID 번호입니다.")
            return

        selected = candidates[index]
        clean_src = selected['source'].replace('_syllables.json', '').replace('.json', '')

        # 사용자가 입력한 길이가 있으면 그것을, 없으면 원본 길이를 사용
        final_dur = custom_dur if custom_dur else selected['dur']

        new_entry = {
            "src": clean_src,
            "word": target_char,
            "start_ms": selected['start'],
            "duration_ms": int(final_dur)  # 이것이 실제 합성에 쓰일 길이입니다.
        }

        # 1. JSON 로드
        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = []

        # 2. 중복 제거 (덮어쓰기)
        data = [item for item in data if item['word'] != target_char]
        
        # 3. 추가 및 저장
        data.append(new_entry)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"💾 저장 완료! [{target_char}] -> {json_path}")
        print(f"   (설정 길이: {final_dur}ms / 원본 길이: {selected['dur']}ms)")


# --- 실행 로직 ---
if __name__ == "__main__":
    reviewer = SyllableReviewer(data_folder="./youtube_audio")
    
    while True:
        target = input("\n검수할 글자를 입력하세요 (종료: q): ").strip()
        if target == 'q': break
        if not target: continue
        
        candidates = reviewer.review_character(target)
        
        if candidates:
            sel = input(f"'{target}' 중 가장 좋은 소리의 ID 번호는? (없으면 엔터): ")
            
            if sel.isdigit():
                idx = int(sel)
                # 범위 체크
                if idx < 0 or idx >= len(candidates):
                    print("❌ 범위를 벗어난 번호입니다.")
                    continue
                
                # 선택한 후보의 원본 길이 확인
                original_dur = candidates[idx]['dur']
                
                # 길이 변경 여부 질문 (여기서 원본 길이를 한 번 더 상기시켜 줌)
                dur_input = input(f"👉 길이를 변경할까요? (엔터 = 원본 {original_dur}ms 사용 / 숫자 입력 = 변경): ")
                
                custom_dur = int(dur_input) if dur_input.isdigit() else None
                
                reviewer.save_best_json(target, idx, candidates, custom_dur=custom_dur)