import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type MyPageProps = {
    onBack: () => void;
};

export default function MyPage({ onBack }: MyPageProps) {
    const [userEmail, setUserEmail] = useState<string | null>(null);

    useEffect(() => {
        supabase.auth.getUser().then(({ data }) => {
            setUserEmail(data.user?.email ?? "사용자");
        });
    }, []);

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
            </div>
        </div>
    );
}
