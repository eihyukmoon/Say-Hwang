import express from "express"
import cors from "cors"

console.log("✅ index.js 시작")

const app = express()
app.use(cors())
app.use(express.json())

app.get("/api/hello", (req, res) => {
  res.json({ message: "백엔드 연결 성공!" })
})

app.get('/api/output-sequence', (req, res) => {
  const sequence = require('./output_sequence.json');
  res.json(sequence);
});

app.listen(4000, () => {
  console.log("서버 실행: http://localhost:4000")
})
