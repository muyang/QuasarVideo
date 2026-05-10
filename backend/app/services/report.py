from __future__ import annotations

from app.domain import AgentResult, AnalysisReport, DNASignature, PreprocessResult, TimelineEntry, VideoRecord
from app.services.knowledge import knowledge_service


def _agent_output(results: list[AgentResult], name: str) -> dict:
    for result in results:
        if result.name == name:
            return result.output
    return {}


class ReportGenerator:
    def build(
        self,
        video: VideoRecord,
        preprocess: PreprocessResult,
        agent_results: list[AgentResult],
    ) -> AnalysisReport:
        script = _agent_output(agent_results, "script")
        director = _agent_output(agent_results, "director")
        editing = _agent_output(agent_results, "editing")
        emotion = _agent_output(agent_results, "emotion")
        marketing = _agent_output(agent_results, "marketing")

        timeline = self._build_timeline(preprocess)

        report = AnalysisReport(
            overview={
                "title": video.title,
                "source_type": video.source_type,
                "platform": video.platform or marketing.get("platform", "unknown"),
                "theme": self._theme(preprocess),
                "duration": video.duration or preprocess.duration or preprocess.scenes[-1].end,
                "frame_directory": preprocess.frame_directory,
                "audio_path": preprocess.audio_path,
                "frames_sampled": preprocess.frames_sampled,
                "scene_count": len(preprocess.scenes),
                "ocr_lines": len(preprocess.ocr),
                "visual_embeddings": len(preprocess.visual_embeddings),
                "capabilities": preprocess.capabilities,
                "warnings": preprocess.warnings,
            },
            topic={
                "direction": self._topic_direction(preprocess),
                "hook_strength": self._hook_strength(preprocess),
                "audience_fit": marketing.get("target_audience"),
            },
            script=script,
            director=director,
            editing=editing,
            emotion=emotion,
            marketing=marketing,
            timeline=timeline,
            dna=DNASignature(
                hook_strength="unknown",
                pacing="unknown",
                emotion_pattern="unknown",
                visual_pattern="unknown",
            ),
            similar_cases=[],
            recommendations=[
                *self._recommendations(preprocess),
            ],
            agent_results=agent_results,
        )
        report.dna = knowledge_service.build_dna(preprocess, report)
        report.similar_cases = knowledge_service.find_similar_cases(report, video.platform)
        return report

    @staticmethod
    def _theme(preprocess: PreprocessResult) -> str:
        if preprocess.capabilities.get("whisper") and preprocess.transcript:
            return "基于真实语音转写的内容分析"
        if preprocess.frames_sampled:
            return "基于真实抽帧和时长的结构分析"
        return "工具缺失，仅完成上传与任务链路，内容语义未真实分析"

    @staticmethod
    def _topic_direction(preprocess: PreprocessResult) -> str:
        if preprocess.transcript and preprocess.capabilities.get("whisper"):
            return "由 ASR 文本进一步归纳"
        if preprocess.ocr and preprocess.capabilities.get("tesseract"):
            return "由画面 OCR 文本进一步归纳"
        return "缺少 ASR/OCR/视觉模型，暂不能真实判断选题"

    @staticmethod
    def _hook_strength(preprocess: PreprocessResult) -> str:
        first_scene = preprocess.scenes[0]
        duration = max(preprocess.duration or preprocess.scenes[-1].end, 1)
        ratio = (first_scene.end - first_scene.start) / duration
        if ratio <= 0.08:
            return "fast_opening"
        if ratio <= 0.18:
            return "normal_opening"
        return "slow_opening"

    @staticmethod
    def _recommendations(preprocess: PreprocessResult) -> list[str]:
        recommendations = []
        if not preprocess.capabilities.get("ffmpeg"):
            recommendations.append("安装 ffmpeg 后可启用真实抽帧、抽音频和更可靠的节奏分析。")
        if not preprocess.capabilities.get("whisper"):
            recommendations.append("安装 Whisper 或 faster-whisper 后可启用真实语音转写和剧本分析。")
        if not preprocess.capabilities.get("tesseract"):
            recommendations.append("安装 Tesseract 或 PaddleOCR 后可启用真实画面文字识别。")
        if preprocess.frames_sampled:
            recommendations.append(f"已抽取 {preprocess.frames_sampled} 帧，可继续接入视觉模型生成画面语义。")
        return recommendations or ["当前视频预处理完成，可进入人工复核或模型增强阶段。"]

    def to_markdown(self, task) -> str:
        report = task.report
        if report is None:
            return ""

        lines = [
            f"# AIVIS 报告 - {task.video.title}",
            "",
            "## 视频概览",
        ]
        for key, value in report.overview.items():
            lines.append(f"- {key}: {value}")

        lines.extend([
            "",
            "## 选题分析",
            f"- direction: {report.topic.get('direction')}",
            f"- hook_strength: {report.topic.get('hook_strength')}",
            f"- audience_fit: {report.topic.get('audience_fit')}",
            "",
            "## 剧本分析",
        ])
        for key, value in report.script.items():
            lines.append(f"- {key}: {value}")

        lines.extend([
            "",
            "## 导演分析",
        ])
        for key, value in report.director.items():
            lines.append(f"- {key}: {value}")

        lines.extend([
            "",
            "## 剪辑分析",
        ])
        for key, value in report.editing.items():
            lines.append(f"- {key}: {value}")

        lines.extend([
            "",
            "## 运营分析",
        ])
        for key, value in report.marketing.items():
            lines.append(f"- {key}: {value}")

        lines.extend([
            "",
            "## 时间轴报告",
        ])
        for item in report.timeline:
            lines.append(f"- {item.start:.1f}s-{item.end:.1f}s [{item.scene_label}] {item.transcript}")

        lines.extend([
            "",
            "## AI 建议",
        ])
        for item in report.recommendations:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "## 视频 DNA",
            f"- hook_strength: {report.dna.hook_strength}",
            f"- pacing: {report.dna.pacing}",
            f"- emotion_pattern: {report.dna.emotion_pattern}",
            f"- visual_pattern: {report.dna.visual_pattern}",
            "",
            "## 相似案例",
        ])
        for item in report.similar_cases:
            lines.append(f"- {item.title} | {item.platform} | {item.similarity} | {item.reason}")

        return "\n".join(lines).strip() + "\n"

    def to_html(self, task) -> str:
        markdown = self.to_markdown(task)
        body = "\n".join(
            self._markdown_line_to_html(line)
            for line in markdown.splitlines()
        )
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>AIVIS Report - {task.video.title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.7; color: #111827; margin: 48px; }}
    h1 {{ font-size: 32px; margin-bottom: 24px; }}
    h2 {{ border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; margin-top: 32px; }}
    li {{ margin: 6px 0; }}
    @media print {{ body {{ margin: 24px; }} }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

    @staticmethod
    def _markdown_line_to_html(line: str) -> str:
        escaped = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        if escaped.startswith("# "):
            return f"<h1>{escaped[2:]}</h1>"
        if escaped.startswith("## "):
            return f"<h2>{escaped[3:]}</h2>"
        if escaped.startswith("- "):
            return f"<li>{escaped[2:]}</li>"
        if not escaped:
            return "<br />"
        return f"<p>{escaped}</p>"

    def _build_timeline(self, preprocess: PreprocessResult) -> list[TimelineEntry]:
        transcript_index = 0
        timeline: list[TimelineEntry] = []

        for scene in preprocess.scenes:
            transcript_text = self._pick_transcript(preprocess.transcript, transcript_index, scene.start, scene.end)
            recommendation = self._recommendation_for_scene(scene.label)
            timeline.append(
                TimelineEntry(
                    start=scene.start,
                    end=scene.end,
                    scene_label=scene.label,
                    transcript=transcript_text,
                    recommendation=recommendation,
                )
            )
            transcript_index += 1

        return timeline

    @staticmethod
    def _pick_transcript(
        transcript: list,
        index: int,
        start: float,
        end: float,
    ) -> str:
        if index < len(transcript):
            return transcript[index].text
        return f"{start:.1f}s - {end:.1f}s 段落内容"

    @staticmethod
    def _recommendation_for_scene(label: str) -> str:
        if label == "hook":
            return "用冲突字幕和强视觉点立即抓住注意力"
        if label == "climax":
            return "在此段强化反转、情绪爆发和 CTA"
        return "保持信息推进和节奏稳定，避免过长停顿"
