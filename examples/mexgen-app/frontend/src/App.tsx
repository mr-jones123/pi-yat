import { Brain, Github } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchHealth } from "@/api/client";
import DocumentInput from "@/components/DocumentInput";
import ExplanationView from "@/components/ExplanationView";
import { useExplanation } from "@/hooks/useExplanation";
import type { HealthResponse } from "@/types";

export default function App() {
	const [health, setHealth] = useState<HealthResponse | null>(null);
	const { result, status, progress, error, loading, run, reset } =
		useExplanation();

	useEffect(() => {
		fetchHealth()
			.then(setHealth)
			.catch(() => {});
	}, []);

	return (
		<div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6 py-8">
			{/* Header */}
			<header className="mb-8 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/15">
						<Brain size={20} className="text-accent" />
					</div>
					<div>
						<h1 className="text-lg font-semibold tracking-tight text-zinc-100">
							MExGen
						</h1>
						<p className="text-xs text-zinc-500">
							Multi-Level Explanations for Generative Language Models
						</p>
					</div>
				</div>

				<div className="flex items-center gap-4">
					{health && (
						<div className="flex items-center gap-2 text-xs text-zinc-500">
							<span
								className={`h-2 w-2 rounded-full ${health.models_loaded ? "bg-emerald-500" : "bg-amber-500 animate-pulse"}`}
							/>
							{health.models_loaded
								? `Ready (${health.device})`
								: "Loading models …"}
						</div>
					)}
					<a
						href="https://arxiv.org/abs/2403.14459"
						target="_blank"
						rel="noopener noreferrer"
						className="text-xs text-zinc-500 transition hover:text-zinc-300"
					>
						Paper
					</a>
					<a
						href="https://github.com/IBM/ICX360"
						target="_blank"
						rel="noopener noreferrer"
						className="text-zinc-500 transition hover:text-zinc-300"
					>
						<Github size={16} />
					</a>
				</div>
			</header>

			{/* Main content */}
			<main className="flex-1 space-y-8">
				<section>
					<DocumentInput onSubmit={run} loading={loading} />
				</section>

				{result && (
					<section>
						<ExplanationView result={result} loading={loading} />
					</section>
				)}

				{error && !result && (
					<div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
						{error}
					</div>
				)}
			</main>

			{/* Footer */}
			<footer className="mt-12 border-t border-zinc-800 pt-4 text-center text-xs text-zinc-600">
				Based on{" "}
				<a
					href="https://arxiv.org/abs/2403.14459"
					className="underline hover:text-zinc-400"
					target="_blank"
					rel="noopener noreferrer"
				>
					Paes, Wei et al. (ACL 2025)
				</a>{" "}
				and the{" "}
				<a
					href="https://github.com/IBM/ICX360"
					className="underline hover:text-zinc-400"
					target="_blank"
					rel="noopener noreferrer"
				>
					ICX360 toolkit
				</a>
			</footer>
		</div>
	);
}
