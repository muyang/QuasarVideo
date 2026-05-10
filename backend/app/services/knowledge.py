from __future__ import annotations

from app.domain import DNASignature, SimilarCase, AnalysisReport, AnalysisTask, PreprocessResult


class KnowledgeService:
    """Minimal RAG/video-DNA layer with deterministic fallback results."""

    def build_dna(self, preprocess: PreprocessResult, report: AnalysisReport) -> DNASignature:
        if not preprocess.visual_embeddings and not preprocess.capabilities.get("whisper", False):
            return DNASignature(
                hook_strength="unknown_without_asr_or_visual_model",
                pacing="estimated_from_fallback_scenes",
                emotion_pattern="heuristic_only",
                visual_pattern="unknown_without_visual_model",
            )

        hook_strength = "strong" if preprocess.scenes and preprocess.scenes[0].label == "hook" else "medium"
        pacing = "fast" if len(preprocess.scenes) >= 4 else "medium"
        emotion_pattern = self._emotion_pattern(report)
        visual_pattern = self._visual_pattern(preprocess)
        return DNASignature(
            hook_strength=hook_strength,
            pacing=pacing,
            emotion_pattern=emotion_pattern,
            visual_pattern=visual_pattern,
        )

    def find_similar_cases(self, report: AnalysisReport, platform: str | None) -> list[SimilarCase]:
        capabilities = report.overview.get("capabilities", {})
        if not report.timeline or not capabilities.get("ffmpeg"):
            return []

        base_platform = platform or report.marketing.get("platform", "抖音")
        return [
            SimilarCase(
                title="高冲突情绪短剧模板",
                platform=str(base_platform),
                similarity=0.91,
                reason="开场冲突强，三段式推进，结尾 CTA 明确",
            ),
            SimilarCase(
                title="反转剧情短视频",
                platform=str(base_platform),
                similarity=0.84,
                reason="节奏紧凑，反转点集中在中后段",
            ),
        ]

    def enrich_task(self, task: AnalysisTask) -> tuple[DNASignature, list[SimilarCase]]:
        if task.report is None:
            return DNASignature(
                hook_strength="unknown",
                pacing="unknown",
                emotion_pattern="unknown",
                visual_pattern="unknown",
            ), []

        dna = self.build_dna(self._empty_preprocess(task), task.report)
        similar_cases = self.find_similar_cases(task.report, task.video.platform)
        return dna, similar_cases

    @staticmethod
    def _emotion_pattern(report: AnalysisReport) -> str:
        if report.emotion.get("curve"):
            return "递进式情绪曲线"
        return "平滑情绪曲线"

    @staticmethod
    def _visual_pattern(preprocess: PreprocessResult) -> str:
        if len(preprocess.visual_embeddings) >= 3:
            return "多镜头视觉语义聚合"
        return "单点视觉强调"

    @staticmethod
    def _empty_preprocess(task: AnalysisTask) -> PreprocessResult:
        return PreprocessResult(
            video_id=task.video.id,
            source_path=task.video.source,
            duration=task.video.duration,
            frame_directory=None,
            audio_path=None,
            frames_sampled=0,
            scenes=[],
            transcript=[],
            ocr=[],
            visual_embeddings=[],
            audio_profile={},
            capabilities={},
            warnings=[],
        )


knowledge_service = KnowledgeService()
