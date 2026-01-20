import { useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type MainPageProps = {
    onLogout: () => void;
    onMyPage: () => void;
    onGenerateSuccess: (audioUrl: string) => void;
};

export default function MainPage({ onLogout, onMyPage, onGenerateSuccess }: MainPageProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        onLogout();
    };

    const handleSave = async () => {
        const text = textareaRef.current?.value;
        if (!text || text.trim().length === 0) {
            alert('이야기를 입력해주세요');
            return;
        }

        try {
            setLoading(true);

            // 1. Python 서버로 오디오 생성 요청 (Port 4000)
            const response = await fetch('http://localhost:4000/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || '저장 실패');
            }

            const data = await response.json();

            // Base64 -> Blob 변환
            const binaryString = window.atob(data.audio_base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: 'audio/mpeg' });

            const url = URL.createObjectURL(blob);

            // 2. Supabase 저장 (비동기 처리)
            try {
                const { data: { user } } = await supabase.auth.getUser();
                if (user) {
                    const timestamp = new Date().getTime();
                    const filePath = `${user.id}/${timestamp}.mp3`;

                    // Storage 업로드
                    const audioFile = new File([blob], "audio.mp3", { type: "audio/mpeg" });
                    const { error: uploadError } = await supabase.storage
                        .from('audios')
                        .upload(filePath, audioFile);

                    if (!uploadError) {
                        // Public URL 가져오기
                        const { data: { publicUrl } } = supabase.storage
                            .from('audios')
                            .getPublicUrl(filePath);

                        // DB Insert
                        const { error: dbError } = await supabase.from('generations').insert({
                            user_id: user.id,
                            text: text,
                            audio_url: publicUrl
                        });

                        if (dbError) {
                            console.error("DB Error:", dbError);
                        }
                    } else {
                        console.error("Upload Error:", uploadError);
                    }
                }
            } catch (saveWarn) {
                console.warn("저장 실패 (재생은 가능):", saveWarn);
            }

            setLoading(false);
            // 페이지 전환
            onGenerateSuccess(url);

        } catch (err) {
            alert('오류가 발생했습니다: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
            setLoading(false);
        }
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
                                    className="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-zinc-200 transition-colors"
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
