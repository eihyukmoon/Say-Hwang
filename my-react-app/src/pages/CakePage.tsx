import { useRef, useState } from "react";

type CakePageProps = {
    onBack: () => void;
};

export default function CakePage({ onBack }: CakePageProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [name, setName] = useState("");
    const [audioSrc, setAudioSrc] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        // 한글 3글자만 허용
        if (value.length <= 3) {
            setName(value);
        }
    };

    const handleSubmit = async () => {
        if (name.trim().length !== 3) {
            alert("이름은 정확히 3글자여야 합니다.");
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch('/api/birthday', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "생일 축하 실패");
            }

            const data = await response.json();
            const binaryString = window.atob(data.audio_base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);

            setAudioSrc(url);

        } catch (err) {
            alert('오류가 발생했습니다: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full bg-zinc-950 text-zinc-100 p-8 flex flex-col items-center justify-center relative overflow-hidden">
            {/* Background Spline Viewer */}
            <div className="fixed inset-0 z-0 w-full h-full">
                {/* @ts-ignore */}
                <spline-viewer url="https://prod.spline.design/v3k8kXwZIveZv1Te/scene.splinecode"></spline-viewer>
            </div>

            {/* Content */}
            <div className="relative z-10 flex flex-col items-center justify-center space-y-8 max-w-md w-full">
                {/* Back Button */}
                <button
                    onClick={onBack}
                    className="absolute top-8 left-8 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    돌아가기
                </button>

                {/* Title */}
                <div className="text-center space-y-4 pt-12">
                    <h1 className="text-4xl font-bold text-white">
                        이름을 입력해주세요
                    </h1>
                    <p className="text-zinc-400">
                        정확히 3글자만 입력 가능합니다
                    </p>
                </div>

                {/* Input Field and Audio Player */}
                {audioSrc ? (
                    <div className="w-full space-y-4">
                        <div className="text-center text-lg font-semibold text-white mb-4">
                            {name}님을 위한 생일 축하 메시지
                        </div>
                        <audio
                            ref={audioRef}
                            controls
                            src={audioSrc}
                            className="w-full"
                        />
                        <div className="flex gap-4 justify-center pt-4">
                            <a
                                href={audioSrc}
                                download="birthday.mp3"
                                className="px-5 py-2.5 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-colors"
                            >
                                다운로드
                            </a>
                            <button
                                onClick={() => {
                                    setAudioSrc(null);
                                    setName("");
                                }}
                                className="px-5 py-2.5 bg-white/10 backdrop-blur-sm border border-white/20 text-white font-semibold rounded-full hover:bg-white/20 transition-colors"
                            >
                                다시 입력
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="w-full space-y-4">
                        <input
                            ref={inputRef}
                            type="text"
                            value={name}
                            onChange={handleInputChange}
                            placeholder="예: 황정민"
                            maxLength={3}
                            className="w-full px-6 py-4 bg-white/20 border border-white/10 rounded-2xl text-white text-center text-2xl placeholder:text-zinc-600 focus:outline-none focus:bg-white/30 focus:border-white/20 transition-all"
                            autoFocus
                        />
                        <p className="text-center text-zinc-500 text-sm">
                            {name.length}/3
                        </p>
                    </div>
                )}

                {/* Submit Button */}
                {!audioSrc && (
                    <button
                        onClick={handleSubmit}
                        disabled={name.length !== 3 || isLoading}
                        className="w-full px-6 py-3 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? "준비 중..." : "확인"}
                    </button>
                )}
            </div>
        </div>
    );
}
