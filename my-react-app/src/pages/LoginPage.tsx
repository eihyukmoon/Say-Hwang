import React, { useMemo, useState } from "react";

type LoginForm = {
  email: string;
  password: string;
  remember: boolean;
};

export default function LoginPage() {
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
    remember: true,
  });
  const [showPw, setShowPw] = useState(false);

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

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("login submit", form);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-zinc-950 to-zinc-900 text-zinc-100">
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md rounded-3xl bg-white/5 p-6 ring-1 ring-white/10 backdrop-blur">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold">로그인</h2>
              <p className="mt-1 text-sm text-zinc-300">
                이메일과 비밀번호로 로그인하세요
              </p>
            </div>
            <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200 ring-1 ring-emerald-400/20">
              Beta
            </span>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs text-zinc-300">
                이메일
              </label>
              <input
                value={form.email}
                onChange={onChange("email")}
                type="email"
                placeholder="you@example.com"
                className="w-full rounded-2xl bg-zinc-950/40 px-4 py-3 text-sm outline-none ring-1 ring-white/10 placeholder:text-zinc-500 focus:ring-2 focus:ring-white/20"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs text-zinc-300">
                비밀번호
              </label>
              <div className="relative">
                <input
                  value={form.password}
                  onChange={onChange("password")}
                  type={showPw ? "text" : "password"}
                  placeholder="최소 6자"
                  className="w-full rounded-2xl bg-zinc-950/40 px-4 py-3 pr-12 text-sm outline-none ring-1 ring-white/10 placeholder:text-zinc-500 focus:ring-2 focus:ring-white/20"
                />
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl px-3 py-2 text-xs text-zinc-300 hover:bg-white/5"
                  onClick={() => setShowPw((v) => !v)}
                >
                  {showPw ? "숨김" : "보기"}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-zinc-300">
              <label className="flex items-center gap-2">
                <input
                  checked={form.remember}
                  onChange={onChange("remember")}
                  type="checkbox"
                  className="h-4 w-4 rounded border-white/20 bg-white/5"
                />
                로그인 상태 유지
              </label>
              <button type="button" className="hover:underline">
                비밀번호 찾기
              </button>
            </div>

            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full rounded-2xl bg-white py-3 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              로그인
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-zinc-400">
            계정이 없으신가요?{" "}
            <button className="text-zinc-200 hover:underline">
              회원가입
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
