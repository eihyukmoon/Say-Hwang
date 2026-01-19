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

  const handleGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
        },
      });
      if (error) throw error;
    } catch (error: any) {
      alert("Google 로그인 실패: " + error.message);
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

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-zinc-950 px-2 text-zinc-500">Or continue with</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="w-full bg-white/10 text-white font-medium rounded-2xl py-3.5 text-sm hover:bg-white/20 active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Google로 계속하기
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
