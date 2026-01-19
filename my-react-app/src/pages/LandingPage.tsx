
type LandingPageProps = {
    onStart: () => void;
};

export default function LandingPage({ onStart }: LandingPageProps) {
    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-zinc-950 text-zinc-100 p-4 relative overflow-hidden">
            {/* Background gradients */}
            {/* Background Spline Viewer */}
            <div className="fixed inset-0">
                {/* @ts-ignore */}
                <spline-viewer url="https://prod.spline.design/7RzisIUMo9vQux6i/scene.splinecode"></spline-viewer>
            </div>

            <div className="relative z-10 flex flex-col items-center text-center space-y-8 animate-fade-in-up">
                <div className="space-y-4">
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white to-zinc-500">
                        Say Hwang
                    </h1>
                    <p className="text-lg md:text-xl text-zinc-400 max-w-lg mx-auto leading-relaxed">

                    </p>
                </div>

                <button
                    onClick={onStart}
                    className="group relative px-8 py-4 bg-white text-black font-semibold rounded-full text-lg hover:scale-105 active:scale-95 transition-all duration-300 shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] hover:shadow-[0_0_60px_-15px_rgba(255,255,255,0.5)]"
                >
                    <span className="relative z-10">시작하기</span>
                    <div className="absolute inset-0 rounded-full bg-white blur opacity-0 group-hover:opacity-40 transition-opacity duration-300" />
                </button>
            </div>
        </div>
    );
}
