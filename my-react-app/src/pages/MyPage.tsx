import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type MyPageProps = {
    onBack: () => void;
};

interface GenerationHistory {
    id: number;
    created_at: string;
    text: string;
    audio_url: string | null;
}

export default function MyPage({ onBack }: MyPageProps) {
    const [userEmail, setUserEmail] = useState<string | null>(null);
    const [history, setHistory] = useState<GenerationHistory[]>([]);

    useEffect(() => {
        async function loadData() {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                setUserEmail(user.email ?? "사용자");

                // 히스토리 불러오기
                const { data } = await supabase
                    .from('generations')
                    .select('*')
                    .eq('user_id', user.id)
                    .order('created_at', { ascending: false });
                
                if (data) {
                    setHistory(data);
                }
            }
        }
        loadData();
    }, []);

    const handleDelete = async (id: number, audioUrl: string | null) => {
        if (!confirm("정말 삭제하시겠습니까?")) return;

        try {
            // 1. Storage에서 파일 삭제 (audio_url이 있는 경우)
            if (audioUrl) {
                // publicUrl에서 path 추출. 예: .../audios/userId/timestamp.mp3 -> userId/timestamp.mp3
                // URL 구조에 따라 다를 수 있으나 보통 audios/ 이후가 경로임
                const parts = audioUrl.split('/audios/');
                if (parts.length > 1) {
                    // URL decoding이 필요할 수도 있음 (파일 이름에 공백 등이 있는 경우)
                    const filePath = decodeURIComponent(parts[1]); 
                    
                    const { error: storageError } = await supabase.storage
                        .from('audios')
                        .remove([filePath]);
                    
                    if (storageError) {
                         console.warn("Storage 삭제 실패 (무시됨):", storageError);
                    }
                }
            }

            // 2. DB에서 레코드 삭제
            const { error: dbError } = await supabase
                .from('generations')
                .delete()
                .eq('id', id);

            if (dbError) {
                throw dbError;
            }

            // 3. UI 업데이트
            setHistory(prev => prev.filter(item => item.id !== id));

        } catch (err) {
            console.error("삭제 중 오류:", err);
            alert("삭제에 실패했습니다.");
        }
    };

    return (
        <div className="min-h-screen w-full bg-zinc-950 text-zinc-100 p-8 flex flex-col items-center">
            <div className="w-full max-w-2xl space-y-8 animate-fade-in-up">

                {/* Header with Back Button */}
                <div className="flex items-center justify-between">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        돌아가기
                    </button>
                    <h1 className="text-2xl font-bold">마이페이지</h1>
                    <div className="w-20" /> {/* Spacer for centering */}
                </div>

                {/* Profile Card */}
                <div className="p-8 rounded-3xl bg-white/5 border border-white/10 space-y-6">
                    <div className="flex items-center gap-6">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center text-3xl font-bold text-white shadow-lg">
                            {userEmail ? userEmail[0].toUpperCase() : "U"}
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-white">
                                {userEmail}
                            </h2>
                            <p className="text-sm text-zinc-500">
                                개인 회원
                            </p>
                        </div>
                    </div>

                    <div className="pt-6 border-t border-white/10">
                        <h3 className="text-sm font-medium text-zinc-400 mb-4">계정 설정</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 rounded-2xl bg-black/20 hover:bg-black/30 transition-colors cursor-pointer">
                                <span>프로필 수정</span>
                                <svg className="w-5 h-5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                            <div className="flex items-center justify-between p-4 rounded-2xl bg-black/20 hover:bg-black/30 transition-colors cursor-pointer">
                                <span>알림 설정</span>
                                <svg className="w-5 h-5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                {/* History Section */}
                <div className="p-8 rounded-3xl bg-white/5 border border-white/10 space-y-6">
                    <h3 className="text-lg font-bold text-white">내가 말했던 문장들</h3>
                    <div className="space-y-4">
                        {history.length === 0 ? (
                             <div className="p-8 text-center text-zinc-500">
                                 아직 저장된 이야기가 없습니다.
                             </div>
                        ) : (
                            history.map((item) => (
                                <div key={item.id} className="p-4 rounded-2xl bg-black/20 border border-white/5 hover:bg-black/30 transition-colors">
                                    <p className="text-zinc-300 mb-3">"{item.text}"</p>
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-zinc-500">
                                            {new Date(item.created_at).toLocaleDateString()}
                                        </span>
                                        <div className="flex items-center gap-4">
                                            {item.audio_url && (
                                                <audio
                                                    controls
                                                    src={item.audio_url}
                                                    className="h-8 max-w-[200px]"
                                                />
                                            )}
                                            <button 
                                                onClick={() => handleDelete(item.id, item.audio_url)}
                                                className="p-2 text-zinc-500 hover:text-red-400 transition-colors"
                                                title="삭제"
                                            >
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
