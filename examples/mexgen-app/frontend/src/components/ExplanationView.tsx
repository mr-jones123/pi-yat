import type { ExplainResponse } from "@/types";
import ColorLegend from "./ColorLegend";
import HighlightedText from "./HighlightedText";
import OutputPanel from "./OutputPanel";
import ProgressBar from "./ProgressBar";

interface Props {
	result: ExplainResponse;
	loading: boolean;
}

export default function ExplanationView({ result, loading }: Props) {
	const {
		status,
		progress,
		generated_output,
		attributions,
		error,
		task,
		question,
	} = result;
	const isTerminal = status === "complete" || status === "failed";

	return (
		<div className="space-y-6">
			{/* Progress */}
			{!isTerminal && <ProgressBar status={status} progress={progress} />}

			{/* Error */}
			{error && (
				<div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
					<p className="font-medium">Error</p>
					<pre className="mt-1 whitespace-pre-wrap text-xs opacity-80">
						{error}
					</pre>
				</div>
			)}

			{/* Generated output */}
			{generated_output && (
				<OutputPanel generatedOutput={generated_output} task={task} />
			)}

			{/* Question echo (QA) */}
			{question && (
				<div className="text-sm text-zinc-400">
					<span className="font-medium text-zinc-500">Question:</span>{" "}
					{question}
				</div>
			)}

			{/* Attributions */}
			{attributions.length > 0 && (
				<div className="space-y-3">
					<div className="flex items-center justify-between">
						<h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
							Input Attribution
						</h3>
						{isTerminal && (
							<span className="rounded-full bg-emerald-900/40 px-2.5 py-0.5 text-xs text-emerald-400">
								{attributions.length} units
							</span>
						)}
					</div>

					<ColorLegend />

					<div className="rounded-lg border border-zinc-700/60 bg-surface-2 p-5">
						<HighlightedText attributions={attributions} />
					</div>
				</div>
			)}
		</div>
	);
}
