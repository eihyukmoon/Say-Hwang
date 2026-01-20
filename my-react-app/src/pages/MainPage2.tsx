

type MainPage2Props = {
    audioSrc: string | null;
    text: string | null;
    onBack: () => void;
};

export default function MainPage2({ audioSrc, text, onBack }: MainPage2Props) {
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
                        {text && (
                            <p className="text-xl text-black font-medium leading-relaxed px-4 break-keep">
                                "{text}"
                            </p>
                        )}
                    </div>

                </div>
            </div>

            {audioSrc ? (
                <div className="absolute top-[80%] left-1/2 -translate-x-1/2 w-full max-w-lg flex flex-col items-center gap-6 animate-fade-in-up pointer-events-auto filter drop-shadow-lg">
                    <audio controls src={audioSrc || undefined} className="w-full" />
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
            )}
        </div>
    );
}
