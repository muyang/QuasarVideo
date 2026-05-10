from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import AgentResult, PreprocessResult, VideoRecord


class AnalysisAgent(ABC):
    name: str

    @abstractmethod
    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        raise NotImplementedError


class ScriptAgent(AnalysisAgent):
    name = "script"

    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        first_text = data.transcript[0].text if data.transcript else "无可用转写文本"
        has_real_transcript = data.capabilities.get("whisper", False) and bool(data.transcript)
        return AgentResult(
            name=self.name,
            output={
                "hook_type": self._hook_type(first_text, has_real_transcript),
                "story_structure": f"基于 {len(data.scenes)} 个场景的分段结构",
                "climax_time": data.scenes[-1].start,
                "opening_text": first_text,
                "transcript_source": "whisper" if has_real_transcript else "fallback/no-asr",
                "cta": "需结合真实字幕或人工复核判断" if not has_real_transcript else "根据尾段语义判断 CTA",
            },
        )

    @staticmethod
    def _hook_type(text: str, has_real_transcript: bool) -> str:
        if not has_real_transcript:
            return "unknown_without_asr"
        if any(keyword in text for keyword in ["为什么", "没想到", "结果", "竟然", "注意"]):
            return "疑问/反转式开场"
        return "叙述式开场"


class DirectorAgent(AnalysisAgent):
    name = "director"

    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        scene_lengths = [scene.end - scene.start for scene in data.scenes]
        avg_shot_duration = round(sum(scene_lengths) / len(scene_lengths), 2)
        return AgentResult(
            name=self.name,
            output={
                "camera_style": "需接入视觉模型识别" if not data.visual_embeddings else "基于抽帧的视觉特征摘要",
                "avg_shot_duration": avg_shot_duration,
                "frames_sampled": data.frames_sampled,
                "visual_feature_count": len(data.visual_embeddings),
                "dominant_colors": [],
                "visual_language": "抽帧可用，语义视觉模型未接入" if data.frames_sampled else "ffmpeg 不可用，无法抽帧",
            },
        )


class EditingAgent(AnalysisAgent):
    name = "editing"

    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        duration = data.duration or data.scenes[-1].end
        scene_count = max(len(data.scenes), 1)
        avg_scene_duration = round(duration / scene_count, 2)
        jump_density = "high" if avg_scene_duration < 3 else "medium" if avg_scene_duration < 8 else "low"
        return AgentResult(
            name=self.name,
            output={
                "asl": avg_scene_duration,
                "beat_match": "requires_audio_beat_detection",
                "climax_range": [data.scenes[-1].start, data.scenes[-1].end],
                "scene_count": scene_count,
                "jump_density": jump_density,
            },
        )


class EmotionAgent(AnalysisAgent):
    name = "emotion"

    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        duration = data.duration or data.scenes[-1].end
        return AgentResult(
            name=self.name,
            output={
                "curve": [
                    {"time": round(scene.start, 2), "emotion": self._emotion_for_scene(scene.label)}
                    for scene in data.scenes
                ],
                "basis": "scene_position_heuristic",
                "duration": duration,
            },
        )

    @staticmethod
    def _emotion_for_scene(label: str) -> str:
        if label == "hook":
            return "注意/好奇"
        if label == "climax":
            return "峰值/转折"
        return "推进/理解"


class MarketingAgent(AnalysisAgent):
    name = "marketing"

    async def analyze(self, video: VideoRecord, data: PreprocessResult) -> AgentResult:
        platform = video.platform or "抖音 / TikTok"
        duration = data.duration or data.scenes[-1].end
        has_text = bool(data.transcript or data.ocr)
        viral_score = min(90, max(35, 70 - int(duration / 10) + len(data.scenes) * 3 + (10 if has_text else 0)))
        return AgentResult(
            name=self.name,
            output={
                "platform": platform,
                "viral_score": viral_score,
                "target_audience": "需结合真实内容语义确认",
                "tags": self._tags(data),
                "basis": "duration + scene_count + text_availability heuristic",
            },
        )

    @staticmethod
    def _tags(data: PreprocessResult) -> list[str]:
        tags = ["视频分析"]
        if (data.duration or 0) <= 60:
            tags.append("短视频")
        if data.ocr:
            tags.append("含画面文字")
        if data.transcript:
            tags.append("含语音/字幕线索")
        return tags


class OrchestratorAgent:
    def __init__(self) -> None:
        self.agents: list[AnalysisAgent] = [
            ScriptAgent(),
            DirectorAgent(),
            EditingAgent(),
            EmotionAgent(),
            MarketingAgent(),
        ]

    async def run(self, video: VideoRecord, data: PreprocessResult) -> list[AgentResult]:
        results: list[AgentResult] = []
        for agent in self.agents:
            results.append(await agent.analyze(video, data))
        return results
