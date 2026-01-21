import React, { useMemo, useState } from "react";
import { supabase } from "../lib/supabaseClient";

type RegisterForm = {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
};

type RegisterPageProps = {
    onLoginClick: () => void;
};

export default function RegisterPage({ onLoginClick }: RegisterPageProps) {
    const [form, setForm] = useState<RegisterForm>({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
    });
    const [showPw, setShowPw] = useState(false);
    const [loading, setLoading] = useState(false);

    const canSubmit = useMemo(() => {
        const nameOk = form.name.trim().length >= 2;
        const emailOk = form.email.trim().length > 3 && form.email.includes("@");
        const pwOk = form.password.length >= 6;
        const matchOk = form.password === form.confirmPassword;
        return nameOk && emailOk && pwOk && matchOk;
    }, [form]);

    const onChange =
        (key: keyof RegisterForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
            setForm((prev) => ({ ...prev, [key]: e.target.value }));
        };

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!canSubmit) return;

        setLoading(true);
        try {
            const { error } = await supabase.auth.signUp({
                email: form.email,
                password: form.password,
                options: {
                    data: {
                        full_name: form.name,
                    },
                },
            });

            if (error) throw error;

            alert("회원가입 성공! 로그인을 진행해주세요.");
            onLoginClick();
        } catch (error: any) {
            alert("회원가입 실패: " + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-zinc-950 text-zinc-100 p-4">
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="relative w-full max-w-sm flex flex-col items-center">
                <div className="mb-8 text-center space-y-2">
                    <h1 className="text-2xl font-bold tracking-tight text-white">
                        회원가입
                    </h1>
                    <p className="text-sm text-zinc-400">새로운 계정을 생성하세요</p>
                </div>

                <form onSubmit={onSubmit} className="w-full space-y-4">
                    <div className="space-y-4">
                        <input
                            value={form.name}
                            onChange={onChange("name")}
                            type="text"
                            placeholder="이름"
                            className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3.5 text-sm text-center placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all duration-200"
                        />
                        <input
                            value={form.email}
                            onChange={onChange("email")}
                            type="email"
                            placeholder="이메일"
                            className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3.5 text-sm text-center placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all duration-200"
                        />
                        <div className="relative">
                            <input
                                value={form.password}
                                onChange={onChange("password")}
                                type={showPw ? "text" : "password"}
                                placeholder="비밀번호 (6자 이상)"
                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3.5 text-sm text-center placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all duration-200"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPw(!showPw)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                            >
                                {showPw ? "숨김" : "보기"}
                            </button>
                        </div>
                        <input
                            value={form.confirmPassword}
                            onChange={onChange("confirmPassword")}
                            type="password"
                            placeholder="비밀번호 확인"
                            className={`w-full bg-white/5 border rounded-2xl px-4 py-3.5 text-sm text-center placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 transition-all duration-200 ${form.confirmPassword && form.password !== form.confirmPassword
                                ? "border-red-500/50 focus:border-red-500"
                                : "border-white/10 focus:border-white/20"
                                }`}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={!canSubmit || loading}
                        className="w-full bg-white text-black font-semibold rounded-2xl py-3.5 text-sm hover:bg-zinc-200 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-200"
                    >
                        {loading ? "가입 중..." : "가입하기"}
                    </button>
                </form>

                <p className="mt-8 text-xs text-zinc-500">
                    이미 계정이 있으신가요?{" "}
                    <button
                        onClick={onLoginClick}
                        className="text-white font-medium hover:underline ml-1"
                    >
                        로그인
                    </button>
                </p>
            </div>
        </div>
    );
}
