"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AnalysisTask, createAnalysis, getReport, listTasks, uploadVideo } from "@/lib/api";

function ReportSection({ title, data }: { title: string; data: Record<string, unknown> }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
      <h3 className="mb-3 text-lg font-semibold text-signal">{title}</h3>
      <dl className="space-y-2 text-sm text-stone-200">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex gap-3 border-b border-white/5 pb-2 last:border-0">
            <dt className="w-32 shrink-0 text-stone-400">{key}</dt>
            <dd>{Array.isArray(value) ? value.join(" / ") : String(value)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function TimelineCard({
  start,
  end,
  sceneLabel,
  transcript,
  recommendation,
}: {
  start: number;
  end: number;
  sceneLabel: string;
  transcript: string;
  recommendation: string;
}) {
  return (
    <article className="rounded-3xl border border-white/10 bg-black/20 p-5">
      <div className="flex items-center justify-between gap-4">
        <h4 className="text-base font-semibold text-signal">{sceneLabel}</h4>
        <span className="text-xs text-stone-500">
          {start.toFixed(1)}s - {end.toFixed(1)}s
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-stone-200">{transcript}</p>
      <p className="mt-3 rounded-2xl border border-signal/20 bg-signal/10 p-3 text-sm text-stone-100">
        {recommendation}
      </p>
    </article>
  );
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [platform, setPlatform] = useState("抖音 / TikTok");
  const [file, setFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [task, setTask] = useState<AnalysisTask | null>(null);
  const [tasks, setTasks] = useState<AnalysisTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadTasks = async () => {
      try {
        const nextTasks = await listTasks();
        if (active) setTasks(nextTasks);
      } catch {
        if (active) setTasks([]);
      }
    };

    loadTasks();
    const timer = window.setInterval(loadTasks, 3000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!taskId) return;

    let active = true;
    const load = async () => {
      try {
        const nextTask = await getReport(taskId);
        if (active) setTask(nextTask);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "获取报告失败");
      }
    };

    load();
    const timer = window.setInterval(load, 1500);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [taskId]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setTask(null);

    try {
      let videoId: string | undefined;
      if (file) {
        const uploaded = await uploadVideo(file);
        videoId = uploaded.video_id;
      }

      const created = await createAnalysis({
        video_id: videoId,
        url: videoId ? undefined : url,
        platform,
        title: url || file?.name,
      });
      setTaskId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务创建失败");
    } finally {
      setLoading(false);
    }
  }

  const report = task?.report;
  const timeline = report?.timeline ?? [];
  const ocr = report?.ocr ?? [];
  const visualEmbeddings = report?.visual_embeddings ?? [];
  const recommendations = report?.recommendations ?? [];

  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,#2d260d,transparent_35%),#08080b] px-5 py-8 md:px-10">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-[2rem] border border-white/10 bg-black/30 p-6 shadow-2xl shadow-black/30 md:p-8">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.35em] text-signal">AIVIS</p>
          <h1 className="text-4xl font-black tracking-tight md:text-6xl">AI 视频理解操作系统</h1>
          <p className="mt-5 max-w-xl text-base leading-8 text-stone-300">
            上传视频或输入 URL，系统会创建多 Agent 分析任务，输出内容、导演、剪辑、情绪与运营维度的导演级报告。
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-5">
            <label className="block">
              <span className="mb-2 block text-sm text-stone-300">视频 URL</span>
              <input
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/video.mp4"
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-signal"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm text-stone-300">上传本地视频</span>
              <input
                type="file"
                accept="video/*"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="w-full rounded-2xl border border-dashed border-white/20 bg-white/5 px-4 py-4 text-sm text-stone-300"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm text-stone-300">目标平台</span>
              <input
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none focus:border-signal"
              />
            </label>

            <button
              disabled={loading || (!file && !url)}
              className="w-full rounded-2xl bg-signal px-5 py-4 font-bold text-ink transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "创建分析中..." : "开始分析"}
            </button>
          </form>

          {error && <p className="mt-4 rounded-2xl bg-red-500/15 p-4 text-sm text-red-200">{error}</p>}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-stone-950/80 p-6 md:p-8">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-stone-500">Report</p>
              <h2 className="mt-1 text-2xl font-bold">导演级分析报告</h2>
            </div>
            <span className="rounded-full border border-white/10 px-4 py-2 text-sm text-stone-300">
              {task?.status ?? "idle"}
            </span>
          </div>

          {!report && (
            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 text-stone-400">
              报告将在任务完成后显示。当前 MVP 使用可替换的占位 AI 分析链路，后续可接入 FFmpeg、Whisper、Qwen-VL、CLIP 与 RAG。
            </div>
          )}

          {report && (
            <div className="space-y-5">
              <ReportSection title="一、视频概览" data={report.overview} />
              <ReportSection title="二、选题分析" data={report.topic} />
              <ReportSection title="三、剧本分析" data={report.script} />
              <ReportSection title="四、镜头分析" data={report.director} />
              <ReportSection title="五、剪辑分析" data={report.editing} />
              <ReportSection title="六、运营分析" data={report.marketing} />
              <ReportSection title="六.1、OCR 识别" data={{ count: ocr.length }} />
              <ReportSection title="六.2、视觉向量" data={{ count: visualEmbeddings.length }} />
              <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
                <h3 className="mb-4 text-lg font-semibold text-signal">七、时间轴报告</h3>
                <div className="space-y-4">
                  {timeline.map((item) => (
                    <TimelineCard
                      key={`${item.start}-${item.end}-${item.scene_label}`}
                      start={item.start}
                      end={item.end}
                      sceneLabel={item.scene_label}
                      transcript={item.transcript}
                      recommendation={item.recommendation}
                    />
                  ))}
                </div>
              </section>
              <section className="rounded-3xl border border-signal/30 bg-signal/10 p-5">
                <h3 className="mb-3 text-lg font-semibold text-signal">八、AI 建议</h3>
                <ul className="space-y-2 text-sm text-stone-100">
                  {recommendations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            </div>
          )}

          <div className="mt-8 rounded-3xl border border-white/10 bg-white/[0.03] p-5">
            <h3 className="mb-4 text-lg font-semibold text-stone-100">最近任务</h3>
            {tasks.length === 0 ? (
              <p className="text-sm text-stone-500">暂无历史任务。</p>
            ) : (
              <div className="space-y-3">
                {tasks.slice(0, 5).map((item) => (
                  <Link
                    key={item.id}
                    href={`/report/${item.id}`}
                    className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-left transition hover:border-signal/40 hover:bg-white/[0.04]"
                  >
                    <div>
                      <p className="text-sm font-medium text-stone-100">{item.video.title}</p>
                      <p className="mt-1 text-xs text-stone-500">
                        {item.video.source_type} · {item.video.platform ?? "未指定平台"}
                      </p>
                    </div>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-stone-300">
                      {item.status}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
