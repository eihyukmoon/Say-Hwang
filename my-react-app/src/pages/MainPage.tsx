import { useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type MainPageProps = {
    onLogout: () => void;
    onMyPage: () => void;
    onGenerateStart: (text: string) => void;
};

export default function MainPage({ onLogout, onMyPage, onGenerateStart }: MainPageProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        onLogout();
    };

    const handleSave = () => {
        const text = textareaRef.current?.value;
        if (!text || text.trim().length === 0) {
            alert('이야기를 입력해주세요');
            return;
        }
        
        // 실제 API 호출 로직은 상위(App.tsx)로 이동됨
        // 여기서는 "생성 시작" 신호만 보냄
        onGenerateStart(text);
    };

    return (
        <div className="w-full bg-zinc-950 text-zinc-100 relative">
            {/* Background Spline Viewer */}
            <div className="fixed inset-0 z-0">
                {/* @ts-ignore */}
                <spline-viewer url="https://prod.spline.design/5xsYQk4pcCREoNoe/scene.splinecode"></spline-viewer>
            </div>

            {/* First Screen: Input */}
            <div className="min-h-screen w-full p-8 flex flex-col relative z-10 pointer-events-none">
                {/* Header */}
                <header className="flex items-center justify-between mb-12 pointer-events-auto">
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
                        Say Hwang
                    </h1>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onMyPage}
                            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
                        >
                            마이페이지
                        </button>
                        <button
                            onClick={handleLogout}
                            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
                        >
                            로그아웃
                        </button>
                    </div>
                </header>

                {/* Main Content - Centered Input */}
                <div className="flex-1 flex flex-col items-center justify-end animate-fade-in-up space-y-8 pb-12">
                    <div className="w-full max-w-lg space-y-4 pointer-events-auto">
                        <h2 className="text-3xl md:text-4xl font-semibold text-center text-white/80">
                            황정민이 대신 전해드립니다.
                        </h2>
                        <div className="relative group">
                            <textarea
                                ref={textareaRef}
                                className="w-full h-32 bg-white/20 border border-white/10 rounded-3xl p-6 text-lg text-white placeholder:text-zinc-600 focus:outline-none focus:bg-white/30 focus:border-white/20 transition-all duration-300 resize-none text-center"
                                placeholder="이곳에 당신의 이야기를 적어주세요..."
                            />
                            <div className="absolute bottom-4 right-4">
                                <button
                                    onClick={handleSave}
                                    className="bg-white text-black px-5 py-2 rounded-full font-medium hover:bg-zinc-200 transition-colors"
                                >
                                    {loading ? "생성 중..." : "고"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
