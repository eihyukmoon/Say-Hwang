import { useState, useEffect } from "react";

type MainPage2Props = {
    audioSrc: string | null;
    onBack: () => void;
};

export default function MainPage2({ audioSrc, onBack }: MainPage2Props) {
    return (
        <div className="min-h-screen w-full bg-zinc-900 p-8 flex flex-col items-center justify-center">
            <div className="max-w-3xl w-full space-y-8 text-center">
                <div className="space-y-4">
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
                        저장된 이야기
                    </h2>
                    <p className="text-zinc-400 text-sm">생성된 오디오를 들어보세요</p>
                </div>

                {audioSrc ? (
                    <div className="flex flex-col items-center justify-center gap-6 p-12 bg-white/5 rounded-3xl border border-white/10 animate-fade-in-up">
                        <audio controls autoPlay src={audioSrc} className="w-full max-w-lg" />
                        <div className="flex gap-4">
                            <a
                                href={audioSrc}
                                download="story.mp3"
                                className="px-6 py-3 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-colors"
                            >
                                다운로드
                            </a>
                            <button
                                onClick={onBack}
                                className="px-6 py-3 bg-transparent border border-white/20 text-white font-semibold rounded-full hover:bg-white/10 transition-colors"
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
    );
}
