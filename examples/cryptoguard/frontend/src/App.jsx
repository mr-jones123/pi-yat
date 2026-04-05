import { useState } from "react";

const VERDICT_STYLES = {
	scam: {
		bg: "#fee2e2",
		border: "#ef4444",
		emoji: "🚨",
		label: "SCAM DETECTED",
	},
	legitimate: {
		bg: "#dcfce7",
		border: "#22c55e",
		emoji: "✅",
		label: "LEGITIMATE",
	},
	uncertain: {
		bg: "#fef9c3",
		border: "#eab308",
		emoji: "❓",
		label: "UNCERTAIN",
	},
};

function ScoreBar({ score, label }) {
	return (
		<div className="score-row">
			<div className="score-bar-track">
				<div
					className="score-bar-fill"
					style={{ width: `${Math.min(score * 100, 100)}%` }}
				/>
			</div>
			<span className="score-value">{score.toFixed(3)}</span>
			<span className="score-label">{label}</span>
		</div>
	);
}

export default function App() {
	const [url, setUrl] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);
	const [result, setResult] = useState(null);

	async function handleSubmit(e) {
		e.preventDefault();
		if (!url.trim()) return;

		setLoading(true);
		setError(null);
		setResult(null);

		try {
			const resp = await fetch("/api/analyze", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ url }),
			});

			if (!resp.ok) {
				const data = await resp.json().catch(() => ({}));
				throw new Error(data.detail || `HTTP ${resp.status}`);
			}

			setResult(await resp.json());
		} catch (err) {
			setError(err.message);
		} finally {
			setLoading(false);
		}
	}

	const r = result?.result;
	const v = r ? VERDICT_STYLES[r.verdict] || VERDICT_STYLES.uncertain : null;

	return (
		<div className="app">
			<header>
				<h1>🛡️ CryptoGuard</h1>
				<p className="subtitle">
					Detect cryptocurrency scams in short-form videos using vision-language
					AI
				</p>
			</header>

			<form onSubmit={handleSubmit} className="input-form">
				<input
					type="url"
					value={url}
					onChange={(e) => setUrl(e.target.value)}
					placeholder="Paste a video URL (YouTube Shorts, TikTok, etc.)"
					required
					disabled={loading}
				/>
				<button type="submit" disabled={loading || !url.trim()}>
					{loading ? "Analysing…" : "Analyse"}
				</button>
			</form>

			{loading && (
				<div className="loading">
					<div className="spinner" />
					<p>
						Downloading video, extracting frames, running CLIP + Whisper +
						Qwen3-VL…
					</p>
				</div>
			)}

			{error && <div className="error">Error: {error}</div>}

			{r && (
				<div className="results">
					{/* Verdict card */}
					<div
						className="verdict-card"
						style={{ background: v.bg, borderColor: v.border }}
					>
						<span className="verdict-emoji">{v.emoji}</span>
						<span className="verdict-label">{v.label}</span>
						<span className="verdict-confidence">
							{(r.confidence * 100).toFixed(0)}% confidence
						</span>
					</div>

					{/* Reasoning */}
					<section>
						<h2>Reasoning</h2>
						<p className="reasoning">{r.reasoning}</p>
					</section>

					{/* Image grid */}
					{result.image_grid_b64 && (
						<section>
							<h2>Video Frames (Image Grid)</h2>
							<img
								className="grid-preview"
								src={`data:image/png;base64,${result.image_grid_b64}`}
								alt="Image grid of video frames"
							/>
						</section>
					)}

					{/* CLIP scores */}
					{r.clip_scores && Object.keys(r.clip_scores).length > 0 && (
						<section>
							<h2>CLIP Scam Indicator Scores</h2>
							{Object.entries(r.clip_scores)
								.sort(([, a], [, b]) => b - a)
								.map(([label, score]) => (
									<ScoreBar key={label} label={label} score={score} />
								))}
						</section>
					)}

					{/* VLM indicators */}
					{r.indicators && r.indicators.length > 0 && (
						<section>
							<h2>VLM-Detected Indicators</h2>
							<ul className="indicators">
								{r.indicators.map((ind, i) => (
									<li key={i}>
										<strong>{ind.name}</strong> — {ind.score.toFixed(2)}{" "}
										<span className="tag">{ind.source}</span>
									</li>
								))}
							</ul>
						</section>
					)}

					{/* Transcript */}
					{r.transcript && (
						<section>
							<h2>Audio Transcript</h2>
							<blockquote>{r.transcript}</blockquote>
						</section>
					)}

					<p className="meta">
						Processed in {result.duration_seconds.toFixed(1)}s
					</p>
				</div>
			)}
		</div>
	);
}
