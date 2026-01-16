import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type MainPageProps = {
    onLogout: () => void;
};

export default function MainPage({ onLogout }: MainPageProps) {
    const [userEmail, setUserEmail] = useState<string | null>(null);

    useEffect(() => {
        supabase.auth.getUser().then(({ data }) => {
            setUserEmail(data.user?.email ?? "사용자");
        });
    }, []);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        onLogout();
    };

    return (
        <div className="min-h-screen w-full bg-zinc-950 text-zinc-100 p-8">
            {/* Header */}
            <header className="flex items-center justify-between mb-12">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
                    Say Hwang
                </h1>
                <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-full transition-colors"
                >
                    로그아웃
                </button>
            </header>

            {/* Welcome Section */}
            <div className="max-w-4xl mx-auto space-y-8 animate-fade-in-up">
                <div className="space-y-2">
                    <h2 className="text-3xl md:text-4xl font-semibold">
                        반갑습니다, <span className="text-emerald-400">{userEmail}</span>님
                    </h2>
                    <p className="text-zinc-400">오늘의 활동을 시작해보세요.</p>
                </div>

                {/* Dashboard Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="p-6 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group"
                        >
                            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                <div className="w-6 h-6 bg-emerald-400/50 rounded-full" />
                            </div>
                            <h3 className="text-lg font-medium mb-2">메뉴 아이템 {i}</h3>
                            <p className="text-sm text-zinc-500">
                                새로운 기능을 여기에서 확인해보세요. 준비 중인 서비스입니다.
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
