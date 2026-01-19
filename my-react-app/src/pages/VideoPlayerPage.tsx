import { useEffect, useRef, useState } from 'react';

type SequenceItem = {
  text?: string;
  substitute_text?: string;
  file_name?: string;
  start_ms?: number;
  duration_ms: number;
  speed?: number;
  volume_gain_db?: number;
  type?: string;
};

export default function VideoPlayerPage() {
  const [sequence, setSequence] = useState<SequenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioBuffersRef = useRef<Map<string, AudioBuffer>>(new Map());
  const startTimeRef = useRef<number>(0);

  // JSON 로드 및 오디오 파일 준비
  useEffect(() => {
    const loadSequence = async () => {
      try {
        const res = await fetch('http://localhost:4000/api/output-sequence');
        const data = await res.json();
        setSequence(data);
        
        // AudioContext 초기화
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        audioContextRef.current = audioContext;

        // 고유한 파일들 로드
        const fileNames = [...new Set(data
          .filter((item: SequenceItem) => item.file_name)
          .map((item: SequenceItem) => item.file_name))];

        for (const fileName of fileNames) {
          try {
            const audioRes = await fetch(`/youtube_audio/${fileName}.wav`);
            const arrayBuffer = await audioRes.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            audioBuffersRef.current.set(fileName as string, audioBuffer);
          } catch (err) {
            console.warn(`오디오 파일 로드 실패: ${fileName}`, err);
          }
        }

        setLoading(false);
      } catch (err) {
        setError('시퀀스 로드 실패: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
        setLoading(false);
      }
    };

    loadSequence();
  }, []);

  // 재생 함수
  const playSequence = async () => {
    if (!audioContextRef.current || sequence.length === 0) return;

    const audioContext = audioContextRef.current;
    setIsPlaying(true);
    startTimeRef.current = audioContext.currentTime;

    let currentTime = 0;

    for (let i = 0; i < sequence.length; i++) {
      if (!isPlaying) break;

      const item = sequence[i];
      setCurrentIndex(i);

      if (item.type === 'silence') {
        // 무음 재생
        await sleep(item.duration_ms);
        currentTime += item.duration_ms;
      } else if (item.file_name) {
        // 오디오 재생
        const audioBuffer = audioBuffersRef.current.get(item.file_name);
        if (audioBuffer) {
          const source = audioContext.createBufferSource();
          const gainNode = audioContext.createGain();

          source.buffer = audioBuffer;
          source.playbackRate.value = item.speed || 1.0;
          
          // 볼륨 조정 (dB를 선형 값으로 변환)
          const volumeGainDb = item.volume_gain_db || 0;
          gainNode.gain.value = Math.pow(10, volumeGainDb / 20);

          source.connect(gainNode);
          gainNode.connect(audioContext.destination);

          source.start(audioContext.currentTime, (item.start_ms || 0) / 1000);
          
          await sleep(item.duration_ms);
          currentTime += item.duration_ms;
        }
      }
    }

    setIsPlaying(false);
    setCurrentIndex(0);
  };

  const stopPlayback = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto"></div>
          <p>오디오 로드 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        <div className="text-center space-y-4">
          <p className="text-red-400 text-lg font-semibold">오류</p>
          <p className="text-zinc-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-8">
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">영상 재생기</h1>
          <p className="text-zinc-400">총 {sequence.length}개 항목</p>
        </div>

        {/* 컨트롤 버튼 */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={playSequence}
            disabled={isPlaying}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-semibold transition"
          >
            {isPlaying ? '재생 중...' : '재생'}
          </button>
          <button
            onClick={stopPlayback}
            disabled={!isPlaying}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded-lg font-semibold transition"
          >
            중지
          </button>
        </div>

        {/* 시퀀스 표시 */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {sequence.map((item, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg border transition ${
                idx === currentIndex
                  ? 'bg-blue-600/30 border-blue-500'
                  : 'bg-white/5 border-white/10'
              } ${idx < currentIndex ? 'opacity-50' : ''}`}
            >
              {item.type === 'silence' ? (
                <p className="text-gray-400">🔇 무음 {item.duration_ms}ms</p>
              ) : (
                <div className="space-y-1">
                  <p className="font-bold text-lg">{item.text}</p>
                  {item.substitute_text && (
                    <p className="text-sm text-yellow-300">대체: {item.substitute_text}</p>
                  )}
                  <div className="text-xs text-zinc-400 space-y-0.5">
                    <p>파일: {item.file_name}</p>
                    <p>구간: {item.start_ms}ms ~ {(item.start_ms || 0) + item.duration_ms}ms</p>
                    <p>속도: {item.speed}x | 볼륨: {item.volume_gain_db}dB</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
