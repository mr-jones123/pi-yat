export type TaskType = "summarization" | "question_answering";
export type AttributionMethod = "clime" | "lshap" | "loo";
export type JobStatus =
	| "pending"
	| "generating"
	| "explaining_coarse"
	| "explaining_fine"
	| "complete"
	| "failed";

export interface UnitAttribution {
	text: string;
	unit_type: string; // "s" | "ph" | "w" | "n"
	score: number; // [-1, 1]
	index: number;
	children?: UnitAttribution[] | null;
}

export interface ExplainRequest {
	document: string;
	task: TaskType;
	question?: string | null;
	method: AttributionMethod;
	scalarizer: string;
}

export interface ExplainResponse {
	job_id: string;
	status: JobStatus;
	task: TaskType;
	document: string;
	question?: string | null;
	generated_output?: string | null;
	attributions: UnitAttribution[];
	progress: number;
	error?: string | null;
}

export interface HealthResponse {
	status: string;
	models_loaded: boolean;
	device: string;
}
