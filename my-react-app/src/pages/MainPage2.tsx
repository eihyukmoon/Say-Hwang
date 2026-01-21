import { useRef, useState, useEffect } from "react";

type TimingItem = {
    char: string;
    start: number;
    end: number;
    type: string;
};

type MainPage2Props = {
    audioSrc: string | null;
    text: string | null;
    timingData: TimingItem[];
    isLoading: boolean;
    onBack: () => void;
};

export default function MainPage2({ audioSrc, text, timingData, isLoading, onBack }: MainPage2Props) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTime, setCurrentTime] = useState(0);

    const handleTimeUpdate = () => {
        if (audioRef.current) {
            // currentTime is in seconds, convert to ms
            setCurrentTime(audioRef.current.currentTime * 1000);
        }
    };

    return (
        <div className="w-full relative overflow-hidden">
            {/* Background Spline Viewer */}
            <div className="fixed inset-0 z-0 w-full h-full">
                {/* @ts-ignore */}
                <spline-viewer url="https://prod.spline.design/KCyEtKileUygFmF4/scene.splinecode"></spline-viewer>
            </div>

            <div className="min-h-screen w-full p-8 flex flex-col items-center justify-start pt-[20vh] relative z-10 pointer-events-none">
                <div className="max-w-3xl w-full space-y-12 text-center pointer-events-auto">
                    <div className="space-y-4">
                        {isLoading ? (
                            <div className="animate-pulse flex flex-col items-center justify-center gap-4">
                                <div className="text-xl md:text-3xl text-zinc-500 font-medium">
                                    황정민이 대본을 읽는 중입니다...
                                </div>
                                {/* Optional: Add a spinner or progress bar */}
                                <div className="w-16 h-1 bg-zinc-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 animate-progress"></div>
                                </div>
                            </div>
                        ) : timingData && timingData.length > 0 ? (
                            <p className="text-2xl md:text-5xl text-black font-medium leading-relaxed px-4 break-keep flex flex-wrap justify-center gap-1">
                                {timingData.map((item, index) => {
                                    // Skip spaces for styling if needed, or handle them
                                    if (item.char === " ") return <span key={index} className="w-3 md:w-4 inline-block"></span>;
                                    
                                    // 자막 싱크 보정: 음성보다 200ms 먼저 하이라이트 시작
                                    const syncOffset = 300; 
                                    const displayTime = currentTime + syncOffset;

                                    const isActive = displayTime >= item.start && displayTime < item.end;
                                    const isPast = displayTime >= item.end;
                                    
                                    return (
                                        <span 
                                            key={index}
                                            className={`transition-all duration-100 ${
                                                isActive 
                                                    ? "text-blue-600 font-bold scale-110 drop-shadow-md" 
                                                    : isPast 
                                                        ? "text-zinc-800 opacity-80" 
                                                        : "text-zinc-400 opacity-50"
                                            }`}
                                        >
                                            {item.char}
                                        </span>
                                    );
                                })}
                            </p>
                        ) : (
                            text && (
                                <p className="text-2xl md:text-5xl text-black font-medium leading-relaxed px-4 break-keep">
                                    "{text}"
                                </p>
                            )
                        )}
                    </div>

                </div>
            </div>

            {!isLoading && (
                audioSrc ? (
                    <div className="absolute top-[80%] left-1/2 -translate-x-1/2 w-full max-w-lg flex flex-col items-center gap-6 animate-fade-in-up pointer-events-auto filter drop-shadow-lg">
                        <audio 
                            ref={audioRef}
                            controls 
                            autoPlay
                            src={audioSrc || undefined} 
                            className="w-full"
                            onTimeUpdate={handleTimeUpdate}
                        />
                        <div className="flex gap-4">
                            <a
                                href={audioSrc || undefined}
                                download="story.mp3"
                                className="px-5 py-2.5 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-colors"
                            >
                                다운로드
                            </a>
                            <button
                                onClick={onBack}
                                className="px-5 py-2.5 bg-white/10 backdrop-blur-sm border border-white/20 text-white font-semibold rounded-full hover:bg-white/20 transition-colors"
                            >
                                처음으로
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="absolute top-[80%] left-1/2 -translate-x-1/2 pointer-events-auto">
                        <div className="text-zinc-500 text-center">
                            오디오 데이터가 없습니다.
                            <br />
                            <button onClick={onBack} className="text-white underline mt-2">돌아가기</button>
                        </div>
                    </div>
                )
            )}
        </div>
    );
}
