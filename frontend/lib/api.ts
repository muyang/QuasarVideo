export type TaskStatus = "queued" | "processing" | "completed" | "failed";

export type AnalysisTask = {
  id: string;
  status: TaskStatus;
  error?: string | null;
  video: {
    id: string;
    title: string;
    source_type: "upload" | "url";
    source: string;
    platform?: string | null;
  };
  report?: {
    overview: Record<string, unknown>;
    topic: Record<string, unknown>;
    script: Record<string, unknown>;
    director: Record<string, unknown>;
    editing: Record<string, unknown>;
    emotion: Record<string, unknown>;
    marketing: Record<string, unknown>;
    dna: {
      hook_strength: string;
      pacing: string;
      emotion_pattern: string;
      visual_pattern: string;
    };
    similar_cases: Array<{
      title: string;
      platform: string;
      similarity: number;
      reason: string;
    }>;
    timeline: Array<{
      start: number;
      end: number;
      scene_label: string;
      transcript: string;
      recommendation: string;
    }>;
    ocr: Array<{
      frame: string;
      text: string;
      confidence: number;
    }>;
    visual_embeddings: Array<{
      frame: string;
      vector: number[];
    }>;
    recommendations: string[];
  } | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readError(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return data?.detail ? `${fallback}: ${data.detail}` : fallback;
  } catch {
    return fallback;
  }
}

export async function uploadVideo(file: File): Promise<{ video_id: string; title: string }> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/video/upload`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    throw new Error(await readError(response, "视频上传失败"));
  }
  return response.json();
}

export async function createAnalysis(payload: {
  video_id?: string;
  url?: string;
  platform?: string;
  title?: string;
}): Promise<{ id: string; status: TaskStatus }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await readError(response, "创建分析任务失败"));
  }
  return response.json();
}

export async function getReport(id: string): Promise<AnalysisTask> {
  const response = await fetch(`${API_BASE_URL}/api/v1/report/${id}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await readError(response, "获取报告失败"));
  }
  return response.json();
}

export async function listTasks(): Promise<AnalysisTask[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await readError(response, "获取任务列表失败"));
  }
  return response.json();
}
