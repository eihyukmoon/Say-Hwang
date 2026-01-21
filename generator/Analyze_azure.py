import azure.cognitiveservices.speech as speechsdk
import json
import os
import time

# 1. 인증 정보
AZURE_KEY = ""
AZURE_REGION = "koreacentral"
TARGET_DIR = r"C:\Say-Hwang\Say-Hwang\youtube_audio"

def analyze_with_pronunciation(wav_path, output_json, config):
    audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)

    pron_config = speechsdk.PronunciationAssessmentConfig(
        reference_text="", 
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True
    )
    pron_config.phoneme_system = "Syllable" 
    pron_config.apply_to(recognizer)

    all_results = []
    done = False

    def recognized_cb(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            raw_json = json.loads(evt.result.json)
            if 'NBest' in raw_json:
                words = raw_json['NBest'][0].get('Words', [])
                for w in words:
                    word_text = w.get('Word')
                    # 특수문자 제거 후 순수 글자 리스트 (예: "일에" -> ['일', '에'])
                    chars = [c for c in word_text if c.isalnum()]
                    raw_phonemes = w.get('Phonemes', [])
                    
                    if not chars or not raw_phonemes:
                        continue

                    num_chars = len(chars)
                    num_segments = len(raw_phonemes)
                    repaired_syllables = []

                    # [핵심 로직] Azure가 쪼갠 구간들을 글자 수(chars)에 맞춰 병합
                    # 예: 구간 3개, 글자 2개면 구간을 1개 / 2개로 묶어서 글자 시간을 할당
                    step = max(1, num_segments // num_chars)
                    for i in range(num_chars):
                        start_idx = i * step
                        # 마지막 글자는 남은 모든 구간을 가져감
                        end_idx = (i + 1) * step if i < num_chars - 1 else num_segments
                        
                        group = raw_phonemes[start_idx:end_idx]
                        if group:
                            start_ms = group[0].get('Offset') / 10000
                            duration_ms = sum(seg.get('Duration') for seg in group) / 10000
                            
                            repaired_syllables.append({
                                "text": chars[i], # 비어있던 text 필드에 실제 글자를 채움
                                "start_ms": start_ms,
                                "duration_ms": duration_ms
                            })

                    all_results.append({
                        "word": word_text,
                        "start_ms": w.get('Offset', 0) / 10000,
                        "syllables": repaired_syllables
                    })
                    print(f"✨ {word_text} -> {len(repaired_syllables)}글자 타임라인 보정 완료")

    def stop_cb(evt):
        nonlocal done
        done = True

    recognizer.recognized.connect(recognized_cb)
    recognizer.session_stopped.connect(stop_cb)
    recognizer.canceled.connect(stop_cb)

    recognizer.start_continuous_recognition_async()
    while not done: time.sleep(0.5)
    recognizer.stop_continuous_recognition_async()

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

def run_batch():
    wav_files = [f for f in os.listdir(TARGET_DIR) if f.endswith('.wav')]
    config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    config.speech_recognition_language = "ko-KR"
    config.output_format = speechsdk.OutputFormat.Detailed
    
    for filename in wav_files:
        path = os.path.join(TARGET_DIR, filename)
        out = os.path.join(TARGET_DIR, os.path.splitext(filename)[0] + "_syllables.json")
        print(f"📡 정밀 분석 및 글자 매칭 중: {filename}...")
        analyze_with_pronunciation(path, out, config)

if __name__ == "__main__":
    run_batch()