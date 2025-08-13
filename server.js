import express from "express";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();
const app = express();
app.use(express.json());

app.post("/generate", async (req, res) => {
    const userPrompt = req.body.prompt;

    try {
        const aiResponse = await fetch("https://api.openai.com/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
            },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{ role: "user", content: userPrompt }]
            })
        });

        const data = await aiResponse.json();
        res.json({ output: data.choices[0].message.content });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "AI request failed" });
    }
});

app.listen(5000, () => console.log("Server running on port 5000"));
