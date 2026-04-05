interface Props {
	generatedOutput: string;
	task: string;
}

export default function OutputPanel({ generatedOutput, task }: Props) {
	const label =
		task === "summarization" ? "Generated Summary" : "Generated Answer";

	return (
		<div className="rounded-lg border border-zinc-700/60 bg-surface-2 p-4">
			<h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
				{label}
			</h3>
			<p className="text-[15px] leading-relaxed text-zinc-100">
				{generatedOutput}
			</p>
		</div>
	);
}
