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
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [timingData, setTimingData] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

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
    } = supabase.auth.onAuthStateChange((event, session) => {
      // SIGNED_IN 이벤트는 초기 로드/로그인 시에만 필요하지만,
      // 이미 view가 설정된 상태(예: main2)에서 중복 발생하여 화면을 리셋시키는 것을 방지하기 위해
      // 여기서는 SIGNED_OUT만 처리하고, 로그인은 각 페이지 콜백이나 초기 getSession에서 처리하도록 함
      if (event === 'SIGNED_OUT') {
        setView("landing");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleGenerate = async (text: string) => {
      // 1. 상태 초기화 및 화면 전환 (즉시)
      setIsGenerating(true);
      setGeneratedText(text);
      setAudioSrc(null);
      setTimingData([]);
      setView("main2");

      try {
          // 2. Python 서버로 오디오 생성 요청
          const response = await fetch('/api/generate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: text }),
          });

          if (!response.ok) {
              const errData = await response.json();
              throw new Error(errData.error || '저장 실패');
          }

          // 3. 응답 처리 및 디코딩
          const data = await response.json();
          const binaryString = window.atob(data.audio_base64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: 'audio/mpeg' });
          const url = URL.createObjectURL(blob);

          setAudioSrc(url);
          setTimingData(data.timing_data || []);

          // 4. Supabase 백그라운드 저장 (비동기)
          saveToSupabase(text, blob).catch(err => console.warn("Supabase 저장 실패:", err));

      } catch (err) {
          alert('오류가 발생했습니다: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
          setView("main"); // 실패 시 메인으로 복귀
      } finally {
          setIsGenerating(false);
      }
  };

  const saveToSupabase = async (text: string, blob: Blob) => {
      try {
          const { data: { user } } = await supabase.auth.getUser();
          if (user) {
              const timestamp = new Date().getTime();
              const filePath = `${user.id}/${timestamp}.mp3`;
              
              const audioFile = new File([blob], "audio.mp3", { type: "audio/mpeg" });
              const { error: uploadError } = await supabase.storage
                  .from('audios')
                  .upload(filePath, audioFile);

              if (!uploadError) {
                  const { data: { publicUrl } } = supabase.storage
                      .from('audios')
                      .getPublicUrl(filePath);

                  await supabase.from('generations').insert({
                      user_id: user.id,
                      text: text,
                      audio_url: publicUrl
                  });
              }
          }
      } catch (saveWarn) {
          console.warn("저장 실패 (재생은 가능):", saveWarn);
      }
  };

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
          onGenerateStart={handleGenerate}
        />
      )}
      {view === "main2" && (
        <MainPage2
          audioSrc={audioSrc}
          text={generatedText}
          timingData={timingData}
          isLoading={isGenerating}
          onBack={() => setView("main")}
        />
      )}
      {view === "mypage" && (
        <MyPage onBack={() => setView("main")} />
      )}
    </>
  );
}

