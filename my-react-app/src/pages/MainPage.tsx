import { useRef } from "react";
import { supabase } from "../lib/supabaseClient";

type MainPageProps = {
    onLogout: () => void;
    onMyPage: () => void;
};

export default function MainPage({ onLogout, onMyPage }: MainPageProps) {
    const nextSectionRef = useRef<HTMLDivElement>(null);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        onLogout();
    };

    const handleSave = () => {
        // Scroll to the next section
        nextSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    return (
        <div className="w-full bg-zinc-950 text-zinc-100">
            {/* First Screen: Input */}
            <div className="min-h-screen w-full p-8 flex flex-col">
                {/* Header */}
                <header className="flex items-center justify-between mb-12">
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
                        Say Hwang
                    </h1>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onMyPage}
                            className="px-4 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
                        >
                            마이페이지
                        </button>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
                        >
                            로그아웃
                        </button>
                    </div>
                </header>

                {/* Main Content - Centered Input */}
                <div className="flex-1 flex flex-col items-center justify-center animate-fade-in-up space-y-8">
                    <div className="w-full max-w-3xl space-y-4">
                        <h2 className="text-3xl md:text-4xl font-semibold text-center text-white/80">
                            무슨 생각을 하고 계신가요?
                        </h2>
                        <div className="relative group">
                            <textarea
                                className="w-full h-48 bg-white/5 border border-white/10 rounded-3xl p-6 text-lg text-white placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all duration-300 resize-none"
                                placeholder="이곳에 당신의 이야기를 적어주세요..."
                            />
                            <div className="absolute bottom-4 right-4">
                                <button
                                    onClick={handleSave}
                                    className="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-zinc-200 transition-colors"
                                >
                                    저장
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Second Screen: Content (Initially hidden via scroll) */}
            <div
                ref={nextSectionRef}
                className="min-h-screen w-full bg-zinc-900 p-8 flex items-center justify-center"
            >
                <div className="max-w-3xl w-full text-center space-y-8">
                    <h2 className="text-3xl font-bold">저장된 이야기</h2>
                    <p className="text-zinc-400">
                        여기에 저장된 내용이 표시되거나, 새로운 단계가 진행될 예정입니다.
                    </p>
                    {/* Placeholder content */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                        <div className="p-6 rounded-3xl bg-black/20 border border-white/5">
                            <div className="w-10 h-10 rounded-full bg-indigo-500/20 mb-4" />
                            <h3 className="text-lg font-medium mb-2">분석 중...</h3>
                            <p className="text-sm text-zinc-500">당신의 이야기를 분석하고 있습니다.</p>
                        </div>
                        <div className="p-6 rounded-3xl bg-black/20 border border-white/5">
                            <div className="w-10 h-10 rounded-full bg-rose-500/20 mb-4" />
                            <h3 className="text-lg font-medium mb-2">인사이트</h3>
                            <p className="text-sm text-zinc-500">곧 새로운 통찰을 제공해 드릴게요.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
