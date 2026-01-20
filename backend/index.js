import express from "express"
import cors from "cors"

console.log("✅ index.js 시작")

const app = express()
app.use(cors())
app.use(express.json())

const PYTHON_SERVER_URL = "http://localhost:5000"

app.post("/api/save-story", async (req, res) => {
  try {
    const { story } = req.body;
    console.log("요청 받은 텍스트:", story);

    if (!story) {
        return res.status(400).json({ error: "텍스트가 없습니다." });
    }

    // Python Flask 서버로 요청 전달
    const response = await fetch(`${PYTHON_SERVER_URL}/api/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: story })
    });

    if (!response.ok) {
        const errorData = await response.json();
        return res.status(response.status).json(errorData);
    }

    // Python 서버에서 받은 오디오 파일을 그대로 클라이언트로 전달
    const audioBuffer = await response.arrayBuffer();
    res.set('Content-Type', 'audio/mpeg');
    res.send(Buffer.from(audioBuffer));

  } catch (err) {
    console.error("/api/save-story 처리 실패:", err)
    res.status(500).json({ error: "처리 실패", details: String(err && err.message || err) })
  }
})

app.listen(4000, () => {
  console.log("서버 실행: http://localhost:4000")
})
