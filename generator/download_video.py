import yt_dlp
import os

# [1] 저장 폴더 설정
OUTPUT_DIR = './youtube_downloads'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# [2] 추출된 유튜브 링크 리스트
youtube_links = [
    "https://www.youtube.com/shorts/-d-P7D0jPAc?si=yM9mawaVKY9voHvc",
    "https://www.youtube.com/shorts/5zCgDPxZPvI?si=ffijq58FbjP8cOiy",
    "https://www.youtube.com/shorts/B-bNigfnoTs?si=lUBEHxBE2MEXK2zU",
    "https://www.youtube.com/shorts/KgHYsw3ghnQ?si=vzxI9-644qt8Z40A",
    "https://www.youtube.com/shorts/LEcpTw1Fh10?si=shl1Lu4hfhdpQe5J",
    "https://www.youtube.com/shorts/NzXLKDKfAqw?si=Qr1oK9_W1iY_r4aV",
    "https://www.youtube.com/shorts/WPN_phPy9aA?si=2EJwiCHuDkbrfKMl",
    "https://www.youtube.com/shorts/gpVFMvLyqQs?si=F1Qfnjty2FHUPOQT",
    "https://www.youtube.com/shorts/lE5ZcbgCxuQ?si=MtKZAqSERlEbmRd8",
    "https://www.youtube.com/shorts/m4qCZ6jAfaw?si=5S64s5_mAlSpX_35",
    "https://www.youtube.com/shorts/n4B14Nx8UXI?si=GyZ4TG9dSywXk9Vd",
    "https://www.youtube.com/shorts/oOMuTNi2_4Q",
    "https://www.youtube.com/shorts/vZN6TTgGZGs",
    "https://youtu.be/87EJhX6NfK4?si=eYfEb6VoiunzrPLZ",
    "https://youtu.be/gdCa9j9wEs8?si=kFKgM4vIA-DNgemC",
    "https://youtube.com/shorts/-vR4GyI0xTk?si=8XS9NeQ3k0dLRrpw",
    "https://youtube.com/shorts/5ZqHdPgFZFg?si=LS_CjS1CDbS-y6Nz",
    "https://youtube.com/shorts/BSZHxXzF9wU?si=M1IUD9B6cZcAQBCF",
    "https://youtube.com/shorts/K21IML4SDik?si=JAUk-IG41HXormy7",
    "https://youtube.com/shorts/KC4R8nSBsNs?si=2Nsxu9TOtlu7FzFI",
    "https://youtube.com/shorts/Kdgg9NMIiFE?si=7yZlamPITk0iGBPk",
    "https://youtube.com/shorts/VXlAOE_ZSq0?si=PvqM8OI0V3feTfMK",
    "https://youtube.com/shorts/Za0FplVc4m0?si=YnLsAeMOk5W7DiRa",
    "https://youtube.com/shorts/kCezfvy-7nc?si=P7YsAYIgaqfXNa6o",
    "https://youtube.com/shorts/o4ZMG18vdEk?si=YVaFpVtNGySrHYCA",
    "https://youtube.com/shorts/py2ZU4SqtgM?si=aEHZoduu9AXCxiys",
    "https://youtube.com/shorts/uMN95bmCMq0?si=thUkCEBng2-ei9vL",
    "https://youtube.com/shorts/v3tx455RTfw?si=JaotVesRociejL16",
    "https://youtube.com/shorts/xkIlbNvuUvQ?si=jkF-5nUSCkVU9LD9"
]

# [3] 다운로드 옵션 설정
ydl_opts = {
    'cookiefile': 'youtube_cookies.txt',
    
    # 수정된 부분: %(title)s 대신 %(id)s를 사용하여 링크의 고유ID로 저장
    'outtmpl': f'{OUTPUT_DIR}/%(id)s.%(ext)s',
    
    'format': 'ba/bestaudio/best',
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['dash', 'hls'],
        }
    },
    'socket_timeout': 30,
    'retries': 10,
    'fragment_retries': 15,
    'ignoreerrors': True,
    'no_warnings': False,
    'quiet': False,
}

# [4] 실행
def main():
    print(f"총 {len(youtube_links)}개의 영상을 ID 기반 파일명으로 다운로드합니다.")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(youtube_links)

    print("\n작업이 완료되었습니다.")
    print(f"저장 위치: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()