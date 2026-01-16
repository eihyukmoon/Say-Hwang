import express from "express"
import cors from "cors"

console.log("✅ index.js 시작")

const app = express()
app.use(cors())
app.use(express.json())

app.get("/api/hello", (req, res) => {
  res.json({ message: "백엔드 연결 성공!" })
})

app.listen(4000, () => {
  console.log("서버 실행: http://localhost:4000")
})
