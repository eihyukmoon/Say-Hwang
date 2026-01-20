import { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage";
import LandingPage from "./pages/LandingPage";
import RegisterPage from "./pages/RegisterPage";
import MainPage from "./pages/MainPage";
import MainPage2 from "./pages/MainPage2";
import MyPage from "./pages/MyPage";
import { supabase } from "./lib/supabaseClient";

type ViewState = "landing" | "login" | "register" | "main" | "main2" | "mypage";

export default function App() {
  const [view, setView] = useState<ViewState>("landing");
  const [loading, setLoading] = useState(true);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setView("main");
      }
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setView("main");
      } else {
        // Only redirect to landing if we were in a protected route? 
        // For simplicity, staying on landing/login is fine, but if logout happens, go to landing.
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">Loading...</div>;
  }

  return (
    <>
      {view === "landing" && (
        <LandingPage onStart={() => setView("login")} />
      )}
      {view === "login" && (
        <LoginPage
          onSignUpClick={() => setView("register")}
          onLoginSuccess={() => setView("main")}
        />
      )}
      {view === "register" && (
        <RegisterPage onLoginClick={() => setView("login")} />
      )}
      {view === "main" && (
        <MainPage
          onLogout={() => setView("landing")}
          onMyPage={() => setView("mypage")}
          onGenerateSuccess={(url) => {
            setAudioSrc(url);
            setView("main2");
          }}
        />
      )}
      {view === "main2" && (
        <MainPage2
          audioSrc={audioSrc}
          onBack={() => setView("main")}
        />
      )}
      {view === "mypage" && (
        <MyPage onBack={() => setView("main")} />
      )}
    </>
  );
}

