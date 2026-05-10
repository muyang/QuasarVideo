"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AnalysisTask, getReport } from "@/lib/api";

const sections = [
  { id: "overview", label: "视频概览" },
  { id: "preprocess", label: "预处理摘要" },
  { id: "agent", label: "Agent 摘要" },
  { id: "flow", label: "Agent 流程" },
  { id: "dna", label: "视频 DNA" },
  { id: "cases", label: "相似案例" },
  { id: "timeline", label: "时间轴报告" },
  { id: "ocr", label: "OCR 识别" },
  { id: "embedding", label: "视觉向量" },
  { id: "recommendations", label: "AI 建议" },
];

function Section({
  id,
  title,
  collapsed,
  onToggle,
  children,
}: {
  id: string;
  title: string;
  collapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
      <button
        type="button"
        onClick={onToggle}
        className="mb-4 flex w-full items-center justify-between gap-4 text-left"
      >
        <h3 className="text-lg font-semibold text-signal">{title}</h3>
        <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-stone-400">
          {collapsed ? "展开" : "收起"}
        </span>
      </button>
      {!collapsed && children}
    </section>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-4 border-b border-white/5 py-2 last:border-0">
      <dt className="w-36 shrink-0 text-sm text-stone-400">{label}</dt>
      <dd className="text-sm text-stone-100">{value}</dd>
    </div>
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

function MetricPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.25em] text-stone-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-stone-100">{value}</p>
    </div>
  );
}

function TimelineChart({
  items,
}: {
  items: Array<{
    start: number;
    end: number;
    scene_label: string;
  }>;
}) {
  const total = items.length
    ? Math.max(...items.map((item) => item.end))
    : 1;

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const width = Math.max(((item.end - item.start) / total) * 100, 5);
        return (
          <div key={`${item.start}-${item.end}-${item.scene_label}`} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-stone-400">
              <span>{item.scene_label}</span>
              <span>
                {item.start.toFixed(1)}s - {item.end.toFixed(1)}s
              </span>
            </div>
            <div className="h-3 rounded-full bg-white/5">
              <div
                className="h-3 rounded-full bg-gradient-to-r from-signal to-orange-400"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AgentFlow() {
  const nodes = [
    "Upload",
    "Preprocess",
    "ASR",
    "Scene",
    "Embedding",
    "Agents",
    "RAG",
    "Report",
  ];

  return (
    <div className="grid gap-3 md:grid-cols-4">
      {nodes.map((node, index) => (
        <div key={node} className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-stone-500">Step {index + 1}</p>
          <p className="mt-2 text-sm font-semibold text-stone-100">{node}</p>
        </div>
      ))}
    </div>
  );
}

export default function VideoDetailPage() {
  const params = useParams<{ taskId: string }>();
  const taskId = params.taskId;
  const [task, setTask] = useState<AnalysisTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({
    overview: false,
    preprocess: false,
    agent: false,
    flow: false,
    dna: false,
    cases: false,
    timeline: false,
    ocr: false,
    embedding: false,
    recommendations: false,
  });

  useEffect(() => {
    if (!taskId) return;

    let active = true;
    const load = async () => {
      try {
        const nextTask = await getReport(taskId);
        if (active) setTask(nextTask);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "获取任务失败");
      }
    };

    load();
    const timer = window.setInterval(load, 1500);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [taskId]);

  const report = task?.report;
  const timeline = report?.timeline ?? [];
  const ocr = report?.ocr ?? [];
  const visualEmbeddings = report?.visual_embeddings ?? [];
  const recommendations = report?.recommendations ?? [];
  const similarCases = report?.similar_cases ?? [];
  const summaryItems = [
    { label: "状态", value: task?.status ?? "loading" },
    { label: "时长", value: String(report?.overview.duration ?? "-") },
    { label: "OCR", value: String(ocr.length) },
    { label: "向量", value: String(visualEmbeddings.length) },
  ];
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const exportUrl = taskId ? `${apiBaseUrl}/api/v1/report/${taskId}/export` : "";
  const markdownExportUrl = taskId ? `${apiBaseUrl}/api/v1/report/${taskId}/export.md` : "";
  const htmlExportUrl = taskId ? `${apiBaseUrl}/api/v1/report/${taskId}/export.html` : "";

  function toggleSection(id: string) {
    setCollapsedSections((current) => ({
      ...current,
      [id]: !current[id],
    }));
  }

  function openAllSections() {
    setCollapsedSections({
      overview: false,
      preprocess: false,
      agent: false,
      flow: false,
      dna: false,
      cases: false,
      timeline: false,
      ocr: false,
      embedding: false,
      recommendations: false,
    });
  }

  function collapseAllSections() {
    setCollapsedSections({
      overview: true,
      preprocess: true,
      agent: true,
      flow: true,
      dna: true,
      cases: true,
      timeline: true,
      ocr: true,
      embedding: true,
      recommendations: true,
    });
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#2d260d,transparent_35%),#08080b] px-5 py-8 md:px-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between gap-4 rounded-[2rem] border border-white/10 bg-black/30 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-signal">AIVIS</p>
            <h1 className="mt-2 text-3xl font-black md:text-5xl">视频详情页</h1>
            <p className="mt-3 text-sm text-stone-400">任务 ID: {taskId}</p>
          </div>
          <Link
            href="/"
            className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-stone-100 transition hover:border-signal/50"
          >
            返回首页
          </Link>
        </div>

        {error && <p className="rounded-2xl bg-red-500/15 p-4 text-sm text-red-200">{error}</p>}

        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="h-fit rounded-[2rem] border border-white/10 bg-stone-950/80 p-5 lg:sticky lg:top-6">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">Quick Nav</p>
            <h2 className="mt-2 text-lg font-semibold text-stone-100">页面导航</h2>
            <div className="mt-4 space-y-2">
              {sections.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className="block rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-stone-300 transition hover:border-signal/40 hover:text-white"
                >
                  {item.label}
                </a>
              ))}
            </div>

            <div className="mt-5 grid gap-3">
              {summaryItems.map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-stone-500">{item.label}</p>
                  <p className="mt-2 text-lg font-semibold text-stone-100">{item.value}</p>
                </div>
              ))}
            </div>

            {report && (
              <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-stone-500">时间轴定位</p>
                <div className="mt-3 space-y-2">
                  {timeline.map((item) => (
                    <a
                      key={`${item.start}-${item.end}-${item.scene_label}`}
                      href={`#timeline-${item.start}`}
                      className="block rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-stone-300 transition hover:border-signal/40 hover:text-white"
                    >
                      {item.scene_label} · {item.start.toFixed(1)}s
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-5 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={openAllSections}
                className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-stone-200 transition hover:border-signal/40"
              >
                全部展开
              </button>
              <button
                type="button"
                onClick={collapseAllSections}
                className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-stone-200 transition hover:border-signal/40"
              >
                全部收起
              </button>
            </div>
          </aside>

          <section className="rounded-[2rem] border border-white/10 bg-stone-950/80 p-6 md:p-8">
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-stone-500">Status</p>
                <h2 className="mt-1 text-2xl font-bold">{task?.video.title ?? "加载中"}</h2>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full border border-white/10 px-4 py-2 text-sm text-stone-300">
                  {task?.status ?? "loading"}
                </span>
                <div className="flex flex-wrap gap-2">
                  {exportUrl && (
                    <a
                      href={exportUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-stone-100 transition hover:border-signal/50"
                    >
                      JSON
                    </a>
                  )}
                  {markdownExportUrl && (
                    <a
                      href={markdownExportUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-stone-100 transition hover:border-signal/50"
                    >
                      Markdown
                    </a>
                  )}
                  {htmlExportUrl && (
                    <a
                      href={htmlExportUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-2xl border border-signal/30 bg-signal/10 px-4 py-2 text-sm text-stone-100 transition hover:border-signal"
                    >
                      打印/PDF
                    </a>
                  )}
                </div>
              </div>
            </div>

            {!report && <p className="text-stone-400">报告生成后会在此显示。</p>}

            {report && (
              <div className="space-y-5">
                <div className="grid gap-3 md:grid-cols-4">
                  <MetricPill label="场景数" value={String(timeline.length)} />
                  <MetricPill label="OCR 条数" value={String(ocr.length)} />
                  <MetricPill label="视觉向量" value={String(visualEmbeddings.length)} />
                  <MetricPill label="建议数" value={String(recommendations.length)} />
                </div>

                <Section
                  id="overview"
                  title="一、视频概览"
                  collapsed={collapsedSections.overview}
                  onToggle={() => toggleSection("overview")}
                >
                  <dl className="space-y-1">
                    {Object.entries(report.overview).map(([key, value]) => (
                      <DetailRow
                        key={key}
                        label={key}
                        value={Array.isArray(value) ? value.join(" / ") : String(value)}
                      />
                    ))}
                  </dl>
                </Section>

                <div className="grid gap-5 lg:grid-cols-2">
                  <Section
                    id="preprocess"
                    title="预处理摘要"
                    collapsed={collapsedSections.preprocess}
                    onToggle={() => toggleSection("preprocess")}
                  >
                    <dl className="space-y-1">
                      <DetailRow label="帧目录" value={String(report.overview.frame_directory ?? "-")} />
                      <DetailRow label="音频路径" value={String(report.overview.audio_path ?? "-")} />
                      <DetailRow label="OCR 数量" value={String(ocr.length)} />
                      <DetailRow label="视觉向量" value={String(visualEmbeddings.length)} />
                    </dl>
                  </Section>

                  <Section
                    id="agent"
                    title="Agent 摘要"
                    collapsed={collapsedSections.agent}
                    onToggle={() => toggleSection("agent")}
                  >
                    <dl className="space-y-1">
                      <DetailRow label="编剧" value={String(report.script.hook_type ?? "-")} />
                      <DetailRow label="导演" value={String(report.director.camera_style ?? "-")} />
                      <DetailRow label="剪辑" value={String(report.editing.asl ?? "-")} />
                      <DetailRow label="运营" value={String(report.marketing.viral_score ?? "-")} />
                    </dl>
                  </Section>
                </div>

                <Section
                  id="flow"
                  title="Agent 流程"
                  collapsed={collapsedSections.flow}
                  onToggle={() => toggleSection("flow")}
                >
                  <AgentFlow />
                </Section>

                <div className="grid gap-5 lg:grid-cols-2">
                  <Section
                    id="dna"
                    title="视频 DNA"
                    collapsed={collapsedSections.dna}
                    onToggle={() => toggleSection("dna")}
                  >
                    <dl className="space-y-1">
                      <DetailRow label="Hook 强度" value={report.dna.hook_strength} />
                      <DetailRow label="节奏" value={report.dna.pacing} />
                      <DetailRow label="情绪模式" value={report.dna.emotion_pattern} />
                      <DetailRow label="视觉模式" value={report.dna.visual_pattern} />
                    </dl>
                  </Section>

                  <Section
                    id="cases"
                    title="相似案例"
                    collapsed={collapsedSections.cases}
                    onToggle={() => toggleSection("cases")}
                  >
                    <div className="space-y-3">
                      {similarCases.map((item) => (
                        <div
                          key={`${item.title}-${item.platform}`}
                          className="rounded-2xl border border-white/10 bg-black/20 p-4"
                        >
                          <p className="text-sm font-semibold text-stone-100">{item.title}</p>
                          <p className="mt-1 text-xs text-stone-500">
                            {item.platform} · 相似度 {item.similarity}
                          </p>
                          <p className="mt-2 text-sm text-stone-300">{item.reason}</p>
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>

                <Section
                  id="timeline"
                  title="时间轴报告"
                  collapsed={collapsedSections.timeline}
                  onToggle={() => toggleSection("timeline")}
                >
                  <div className="space-y-5">
                    <TimelineChart
                        items={timeline.map((item) => ({
                        start: item.start,
                        end: item.end,
                        scene_label: item.scene_label,
                      }))}
                    />
                    <div className="space-y-4">
                        {timeline.map((item) => (
                        <div
                          id={`timeline-${item.start}`}
                          key={`${item.start}-${item.end}-${item.scene_label}`}
                        >
                          <TimelineCard
                            start={item.start}
                            end={item.end}
                            sceneLabel={item.scene_label}
                            transcript={item.transcript}
                            recommendation={item.recommendation}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </Section>

                <div className="grid gap-5 lg:grid-cols-2">
                  <Section
                    id="ocr"
                    title="OCR 识别"
                    collapsed={collapsedSections.ocr}
                    onToggle={() => toggleSection("ocr")}
                  >
                    <div className="space-y-3">
                      {ocr.length === 0 ? (
                        <p className="text-sm text-stone-500">暂无 OCR 结果。</p>
                      ) : (
                        ocr.map((item) => (
                          <div
                            key={`${item.frame}-${item.text}`}
                            className="rounded-2xl border border-white/10 bg-black/20 p-4"
                          >
                            <p className="text-xs text-stone-500">{item.frame}</p>
                            <p className="mt-2 text-sm text-stone-100">{item.text}</p>
                            <p className="mt-2 text-xs text-stone-400">confidence {item.confidence}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </Section>

                  <Section
                    id="embedding"
                    title="视觉向量"
                    collapsed={collapsedSections.embedding}
                    onToggle={() => toggleSection("embedding")}
                  >
                    <div className="space-y-3">
                      {visualEmbeddings.length === 0 ? (
                        <p className="text-sm text-stone-500">暂无视觉向量。</p>
                      ) : (
                        visualEmbeddings.map((item) => (
                          <div
                            key={`${item.frame}-${item.vector.length}`}
                            className="rounded-2xl border border-white/10 bg-black/20 p-4"
                          >
                            <p className="text-xs text-stone-500">{item.frame}</p>
                            <p className="mt-2 break-all text-xs text-stone-300">
                              {item.vector.join(", ")}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </Section>
                </div>

                <Section
                  id="recommendations"
                  title="AI 建议"
                  collapsed={collapsedSections.recommendations}
                  onToggle={() => toggleSection("recommendations")}
                >
                  <ul className="space-y-2 text-sm text-stone-100">
                    {recommendations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Section>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
