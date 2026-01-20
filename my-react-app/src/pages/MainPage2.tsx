

type MainPage2Props = {
    audioSrc: string | null;
    onBack: () => void;
};

export default function MainPage2({ audioSrc, onBack }: MainPage2Props) {
    return (
        <div className="w-full relative overflow-hidden">
            {/* Background Spline Viewer */}
            <div className="fixed inset-0 z-0 w-full h-full">
                {/* @ts-ignore */}
                <spline-viewer url="https://prod.spline.design/KCyEtKileUygFmF4/scene.splinecode"></spline-viewer>
            </div>

            <div className="min-h-screen w-full p-8 flex flex-col items-center justify-center relative z-10 pointer-events-none">
                <div className="max-w-3xl w-full space-y-8 text-center pointer-events-auto">
                    <div className="space-y-4">
                        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">

                        </h2>
                        <p className="text-zinc-400 text-sm"></p>
                    </div>

                    {audioSrc ? (
                        <div className="flex flex-col items-center justify-center gap-6 animate-fade-in-up">
                            <audio controls src={audioSrc} className="w-full max-w-lg" />
                            <div className="flex gap-4">
                                <a
                                    href={audioSrc}
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
                        <div className="text-zinc-500">
                            오디오 데이터가 없습니다.
                            <br />
                            <button onClick={onBack} className="text-white underline mt-2">돌아가기</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
