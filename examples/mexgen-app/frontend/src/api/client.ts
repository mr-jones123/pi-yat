import type { ExplainRequest, ExplainResponse, HealthResponse } from "@/types";

const BASE = "";

export async function submitExplanation(
	req: ExplainRequest,
): Promise<ExplainResponse> {
	const res = await fetch(`${BASE}/api/explain`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw new Error(body.detail ?? `HTTP ${res.status}`);
	}
	return res.json();
}

export async function fetchJob(jobId: string): Promise<ExplainResponse> {
	const res = await fetch(`${BASE}/api/jobs/${jobId}`);
	if (!res.ok) throw new Error(`HTTP ${res.status}`);
	return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
	const res = await fetch(`${BASE}/api/health`);
	if (!res.ok) throw new Error(`HTTP ${res.status}`);
	return res.json();
}

/**
 * Open a WebSocket to stream job progress.
 * Returns a cleanup function.
 */
export function subscribeToJob(
	jobId: string,
	onMessage: (data: ExplainResponse) => void,
	onError?: (err: Event) => void,
): () => void {
	const proto = location.protocol === "https:" ? "wss:" : "ws:";
	const ws = new WebSocket(`${proto}//${location.host}/ws/jobs/${jobId}`);

	ws.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data) as ExplainResponse;
			onMessage(data);
		} catch {
			// ignore malformed frames
		}
	};

	ws.onerror = (event) => onError?.(event);

	return () => {
		if (ws.readyState <= WebSocket.OPEN) ws.close();
	};
}
