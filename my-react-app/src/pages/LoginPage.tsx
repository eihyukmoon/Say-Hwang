import React, { useMemo, useState } from "react";

type LoginForm = {
  email: string;
  password: string;
  remember: boolean;
};

type LoginPageProps = {
  onSignUpClick: () => void;
  onLoginSuccess: () => void;
};

import { supabase } from "../lib/supabaseClient";

export default function LoginPage({ onSignUpClick, onLoginSuccess }: LoginPageProps) {
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
    remember: true,
  });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => {
    const emailOk = form.email.trim().length > 3 && form.email.includes("@");
    const pwOk = form.password.length >= 6;
    return emailOk && pwOk;
  }, [form.email, form.password]);

  const onChange =
    (key: keyof LoginForm) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const value =
          key === "remember" ? e.target.checked : e.target.value;
        setForm((prev) => ({ ...prev, [key]: value }));
      };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: form.email,
        password: form.password,
      });

      if (error) throw error;

      // alert("로그인 성공!"); 
      onLoginSuccess();
    } catch (error: any) {
      alert("로그인 실패: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-zinc-950 text-zinc-100 p-4">
      {/* Background gradients for subtle effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="relative w-full max-w-sm flex flex-col items-center">
        <div className="mb-8 text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-white/10 mb-4 ring-1 ring-white/20 backdrop-blur-sm">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">환영합니다</h1>
          <p className="text-sm text-zinc-400">
            서비스 이용을 위해 로그인해주세요
          </p>
        </div>

        <form onSubmit={onSubmit} className="w-full space-y-4">
          <div className="space-y-4">
            <div className="group relative">
              <input
                value={form.email}
                onChange={onChange("email")}
                type="email"
                placeholder="이메일"
                className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3.5 text-sm text-center placeholder:text-zinc-600 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all duration-200"
              />
            </div>

            <div className="relative">
              <input
                value={form.password}
                onChange={onChange("password")}
                type={showPw ? "text" : "password"}
                placeholder="비밀번호"
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
          </div>

          <div className="flex items-center justify-center gap-2 py-2">
            <button
              type="button"
              onClick={() => setForm(prev => ({ ...prev, remember: !prev.remember }))}
              className={`flex items-center gap-2 text-xs transition-colors ${form.remember ? "text-white" : "text-zinc-500 hover:text-zinc-400"
                }`}
            >
              <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${form.remember ? "bg-white border-white" : "border-zinc-700 bg-transparent"
                }`}>
                {form.remember && (
                  <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              로그인 유지
            </button>
            <span className="text-zinc-700">|</span>
            <button type="button" className="text-xs text-zinc-500 hover:text-white transition-colors">
              비밀번호 찾기
            </button>
          </div>

          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="w-full bg-white text-black font-semibold rounded-2xl py-3.5 text-sm hover:bg-zinc-200 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-200"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <p className="mt-8 text-xs text-zinc-500">
          계정이 없으신가요?{" "}
          <button
            type="button"
            onClick={onSignUpClick}
            className="text-white font-medium hover:underline ml-1"
          >
            회원가입
          </button>
        </p>
      </div>
    </div>
  );
}
