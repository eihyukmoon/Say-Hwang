import express from "express"
import cors from "cors"
import { fileURLToPath } from "url"
import path from "path"
import fs from "fs"
import { exec } from "child_process"

console.log("✅ index.js 시작")

const app = express()
app.use(cors())
app.use(express.json())

// const PYTHON_SERVER_URL = "http://localhost:5000" // Not used in this version

app.post("/api/save-story", async (req, res) => {
  try {
    const { story } = req.body;
    console.log("요청 받은 텍스트:", story);

    if (!story) {
      return res.status(400).json({ error: "텍스트가 없습니다." });
    }

    // Resolve paths
    const __filename = fileURLToPath(import.meta.url)
    const __dirname = path.dirname(__filename)
    const generatorScript = path.resolve(__dirname, "../generator/assemble_v3.py")
    const generatorCwd = path.resolve(__dirname, "../generator")
    const outputPath = path.resolve(__dirname, "../generator/final_output_hybrid.mp3")

    // Python 스크립트 실행
    // 주의: 실제 배포 환경에서는 보안을 위해 입력값(story)을 철저히 검증/이스케이프해야 합니다.
    const escapedStory = story.replace(/"/g, '\\"');
    const command = `python3 "${generatorScript}" "${escapedStory}"`;

    console.log("실행 명령:", command);

    exec(command, { cwd: generatorCwd }, (error, stdout, stderr) => {
      if (error) {
        console.error(`실행 오류: ${error.message}`);
        console.error(`stderr: ${stderr}`);
        return res.status(500).json({ error: "오디오 생성 실패", details: stderr });
      }

      console.log(`stdout: ${stdout}`);

      if (!fs.existsSync(outputPath)) {
        console.error("파일이 생성되지 않음:", outputPath);
        return res.status(404).json({ error: "생성된 오디오 파일을 찾을 수 없습니다." });
      }

      res.sendFile(outputPath);
    });

  } catch (err) {
    console.error("/api/save-story 처리 실패:", err)
    res.status(500).json({ error: "처리 실패", details: String(err && err.message || err) })
  }
})

app.listen(4000, () => {
  console.log("서버 실행: http://localhost:4000")
})
