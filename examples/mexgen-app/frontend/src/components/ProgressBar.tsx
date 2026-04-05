import type { JobStatus } from "@/types";
import { STATUS_LABELS } from "@/utils/colors";

interface Props {
	status: JobStatus;
	progress: number;
}

export default function ProgressBar({ status, progress }: Props) {
	const pct = Math.round(progress * 100);
	const label = STATUS_LABELS[status] ?? status;

	return (
		<div className="w-full space-y-1.5">
			<div className="flex items-center justify-between text-xs text-zinc-400">
				<span>{label}</span>
				<span className="font-mono">{pct}%</span>
			</div>
			<div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
				<div
					className="h-full rounded-full bg-accent transition-all duration-500 ease-out"
					style={{ width: `${pct}%` }}
				/>
			</div>
		</div>
	);
}
