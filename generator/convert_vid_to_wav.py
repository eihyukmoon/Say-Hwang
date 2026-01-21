import ffmpeg
import os

def batch_convert_with_library(folder_path):
    # 1. 폴더 내 mp4 파일 목록 필터링
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
    
    if not files:
        print("❌ 변환할 MP4 파일이 없습니다.")
        return

    print(f"🚀 ffmpeg-python을 사용하여 {len(files)}개 파일 변환을 시작합니다.")

    for filename in files:
        input_path = os.path.join(folder_path, filename)
        output_path = os.path.join(folder_path, os.path.splitext(filename)[0] + ".wav")

        print(f"🔄 변환 중: {filename}...")

        try:
            # ffmpeg-python 스타일의 체이닝 방식
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path, 
                                   ar='16000', # 16kHz
                                   ac='1',     # Mono
                                   acodec='pcm_s16le') # PCM 16-bit
            
            # overwrite_output=True는 기존에 같은 이름의 wav가 있으면 덮어씁니다.
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            print(f"✅ 변환 완료: {output_path}")
            
        except ffmpeg.Error as e:
            print(f"❌ {filename} 변환 중 에러 발생!")
            # 에러 상세 내용을 출력하여 문제를 파악하기 쉽게 합니다.
            print(e.stderr.decode())

if __name__ == "__main__":
    # 경로 앞에 r을 붙여 백슬래시 에러 방지
    target_dir = r"./youtube_downloads"
    batch_convert_with_library(target_dir)