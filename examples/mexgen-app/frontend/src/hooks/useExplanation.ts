import { useCallback, useRef, useState } from "react";
import { submitExplanation, subscribeToJob } from "@/api/client";
import type { ExplainRequest, ExplainResponse, JobStatus } from "@/types";

interface UseExplanationReturn {
	result: ExplainResponse | null;
	status: JobStatus | null;
	progress: number;
	error: string | null;
	loading: boolean;
	run: (req: ExplainRequest) => Promise<void>;
	reset: () => void;
}

export function useExplanation(): UseExplanationReturn {
	const [result, setResult] = useState<ExplainResponse | null>(null);
	const [status, setStatus] = useState<JobStatus | null>(null);
	const [progress, setProgress] = useState(0);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);
	const cleanupRef = useRef<(() => void) | null>(null);

	const reset = useCallback(() => {
		cleanupRef.current?.();
		cleanupRef.current = null;
		setResult(null);
		setStatus(null);
		setProgress(0);
		setError(null);
		setLoading(false);
	}, []);

	const run = useCallback(
		async (req: ExplainRequest) => {
			reset();
			setLoading(true);

			try {
				const initial = await submitExplanation(req);
				setResult(initial);
				setStatus(initial.status);

				// Subscribe to progress via WebSocket
				const cleanup = subscribeToJob(
					initial.job_id,
					(data) => {
						setResult(data);
						setStatus(data.status);
						setProgress(data.progress);
						if (data.status === "complete" || data.status === "failed") {
							setLoading(false);
							if (data.error) setError(data.error);
						}
					},
					() => {
						// On WS error, fall back to polling
						setError("WebSocket connection lost. Refresh to retry.");
						setLoading(false);
					},
				);
				cleanupRef.current = cleanup;
			} catch (err: any) {
				setError(err.message ?? "Unknown error");
				setLoading(false);
			}
		},
		[reset],
	);

	return { result, status, progress, error, loading, run, reset };
}
