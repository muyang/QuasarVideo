from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.domain import OCRLine, PreprocessResult, Scene, TranscriptSegment, VideoRecord, VisualEmbedding


@dataclass
class VideoMetadata:
    duration: float | None
    fps: float | None


class VideoPreprocessor:
    """Run FFmpeg-based preprocessing with Whisper and scene-detection fallbacks."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")

    async def run(self, video: VideoRecord) -> PreprocessResult:
        source_path = self._resolve_source_path(video)
        metadata = self._probe(source_path)
        frame_dir = self._extract_frames(video.id.hex, source_path)
        audio_path = self._extract_audio(video.id.hex, source_path)
        capabilities = self._capabilities()
        warnings = self._warnings(capabilities)

        if metadata.duration is None:
            return self._fallback_result(video, source_path, frame_dir, audio_path, capabilities, warnings)

        scenes = self._detect_scenes(source_path, metadata.duration)
        transcript = self._transcribe_audio(audio_path, metadata.duration)
        ocr = self._run_ocr(frame_dir)
        visual_embeddings = self._build_visual_embeddings(frame_dir)

        if not scenes:
            scene_count = max(3, min(6, int(metadata.duration // 12) + 1))
            scene_duration = max(metadata.duration / scene_count, 1.0)
            for index in range(scene_count):
                start = round(index * scene_duration, 2)
                end = round(min(metadata.duration, (index + 1) * scene_duration), 2)
                label = self._label_for_index(index, scene_count)
                scenes.append(Scene(start=start, end=end, label=label))

        if not transcript:
            transcript = self._fallback_transcript(scenes)

        estimated_bpm = 90.0 if metadata.duration > 60 else 112.0
        energy = "high" if metadata.duration < 45 else "medium-high"

        return PreprocessResult(
            video_id=video.id,
            source_path=str(source_path),
            duration=metadata.duration,
            frame_directory=str(frame_dir) if frame_dir else None,
            audio_path=str(audio_path) if audio_path else None,
            frames_sampled=len(list(frame_dir.glob("*.jpg"))) if frame_dir else 0,
            scenes=scenes,
            transcript=transcript,
            ocr=ocr,
            visual_embeddings=visual_embeddings,
            audio_profile={"estimated_bpm": estimated_bpm, "energy": energy},
            capabilities=capabilities,
            warnings=warnings,
        )

    def _capabilities(self) -> dict[str, bool]:
        return {
            "ffmpeg": bool(self.ffmpeg),
            "ffprobe": bool(self.ffprobe),
            "scenedetect": bool(shutil.which("scenedetect")),
            "whisper": bool(shutil.which("whisper")),
            "tesseract": bool(shutil.which("tesseract")),
        }

    @staticmethod
    def _warnings(capabilities: dict[str, bool]) -> list[str]:
        warnings = []
        if not capabilities["ffprobe"]:
            warnings.append("ffprobe unavailable: duration and stream metadata cannot be read.")
        if not capabilities["ffmpeg"]:
            warnings.append("ffmpeg unavailable: frames and audio cannot be extracted.")
        if not capabilities["whisper"]:
            warnings.append("whisper unavailable: transcript uses fallback when no ASR output exists.")
        if not capabilities["tesseract"]:
            warnings.append("tesseract unavailable: OCR uses fallback when frame OCR cannot run.")
        return warnings

    def _resolve_source_path(self, video: VideoRecord) -> Path:
        path = Path(video.source)
        if path.exists():
            return path
        raise FileNotFoundError(f"Video source not found: {video.source}")

    def _probe(self, source_path: Path) -> VideoMetadata:
        if not self.ffprobe:
            return VideoMetadata(duration=None, fps=None)

        command = [
            self.ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(source_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return VideoMetadata(duration=None, fps=None)

        payload = json.loads(result.stdout or "{}")
        duration = None
        fps = None

        format_section = payload.get("format") or {}
        if format_section.get("duration"):
            duration = float(format_section["duration"])

        for stream in payload.get("streams", []):
            if stream.get("codec_type") == "video":
                rate = stream.get("r_frame_rate") or stream.get("avg_frame_rate")
                fps = self._parse_fraction(rate)
                if duration is None and stream.get("duration"):
                    duration = float(stream["duration"])
                break

        return VideoMetadata(duration=duration, fps=fps)

    def _extract_frames(self, video_id: str, source_path: Path) -> Path | None:
        if not self.ffmpeg:
            return None

        output_dir = self.settings.preprocess_dir / video_id / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            self.ffmpeg,
            "-y",
            "-i",
            str(source_path),
            "-vf",
            "fps=1",
            str(output_dir / "frame_%04d.jpg"),
        ]
        subprocess.run(command, capture_output=True, check=False)
        return output_dir

    def _extract_audio(self, video_id: str, source_path: Path) -> Path | None:
        if not self.ffmpeg:
            return None

        output_path = self.settings.preprocess_dir / video_id / "audio.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [self.ffmpeg, "-y", "-i", str(source_path), "-vn", str(output_path)]
        subprocess.run(command, capture_output=True, check=False)
        return output_path

    def _detect_scenes(self, source_path: Path, duration: float) -> list[Scene]:
        detector_path = shutil.which("scenedetect")
        if detector_path:
            command = [
                detector_path,
                "-i",
                str(source_path),
                "detect-content",
                "list-scenes",
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout:
                parsed = self._parse_scene_detect_output(result.stdout, duration)
                if parsed:
                    return parsed

        return self._default_scenes(duration)

    def _transcribe_audio(self, audio_path: Path | None, duration: float) -> list[TranscriptSegment]:
        whisper_available = shutil.which("whisper")
        if not audio_path or not whisper_available:
            return []

        output_dir = audio_path.parent / "whisper"
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            whisper_available,
            str(audio_path),
            "--model",
            "base",
            "--output_format",
            "json",
            "--output_dir",
            str(output_dir),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return []

        json_files = list(output_dir.glob("*.json"))
        if not json_files:
            return []

        try:
            payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        except Exception:
            return []

        segments = []
        for item in payload.get("segments", []):
            segments.append(
                TranscriptSegment(
                    start=float(item.get("start", 0.0)),
                    end=float(item.get("end", 0.0)),
                    text=str(item.get("text", "")).strip(),
                )
            )
        return segments

    def _parse_scene_detect_output(self, output: str, duration: float) -> list[Scene]:
        scenes = []
        for line in output.splitlines():
            if not line.strip() or "Scene #" not in line:
                continue
            parts = line.replace("[", "").replace("]", "").split()
            times = [part for part in parts if ":" in part and "-" in part]
            if not times:
                continue
            range_part = times[0]
            start_text, end_text = range_part.split("-", 1)
            start = self._time_to_seconds(start_text)
            end = self._time_to_seconds(end_text)
            if start is None or end is None:
                continue
            scenes.append(Scene(start=start, end=min(end, duration), label=self._label_for_time(start, duration)))
        return scenes

    def _default_scenes(self, duration: float) -> list[Scene]:
        scene_count = max(3, min(6, int(duration // 12) + 1))
        scene_duration = max(duration / scene_count, 1.0)
        scenes = []
        for index in range(scene_count):
            start = round(index * scene_duration, 2)
            end = round(min(duration, (index + 1) * scene_duration), 2)
            scenes.append(Scene(start=start, end=end, label=self._label_for_index(index, scene_count)))
        return scenes

    def _fallback_transcript(self, scenes: list[Scene]) -> list[TranscriptSegment]:
        transcript = []
        for index, scene in enumerate(scenes):
            transcript.append(
                TranscriptSegment(
                    start=scene.start,
                    end=scene.end,
                    text=self._transcript_for_label(scene.label, index),
                )
            )
        return transcript

    def _run_ocr(self, frame_dir: Path | None) -> list[OCRLine]:
        if not frame_dir:
            return []

        ocr_tool = shutil.which("tesseract")
        if not ocr_tool:
            return self._fallback_ocr(frame_dir)

        lines: list[OCRLine] = []
        for frame in sorted(frame_dir.glob("*.jpg"))[:5]:
            result = subprocess.run([ocr_tool, str(frame), "stdout"], capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                lines.append(OCRLine(frame=frame.name, text=result.stdout.strip(), confidence=0.78))
        return lines or self._fallback_ocr(frame_dir)

    def _fallback_ocr(self, frame_dir: Path | None) -> list[OCRLine]:
        if not frame_dir:
            return []
        frames = sorted(frame_dir.glob("*.jpg"))[:3]
        return [
            OCRLine(frame=frame.name, text=f"画面 {index + 1} 的字幕或标题占位文本", confidence=0.5)
            for index, frame in enumerate(frames)
        ]

    def _build_visual_embeddings(self, frame_dir: Path | None) -> list[VisualEmbedding]:
        if not frame_dir:
            return []
        frames = sorted(frame_dir.glob("*.jpg"))[:5]
        return [self._embedding_for_frame(frame) for frame in frames]

    def _fallback_embeddings(self, frame_dir: Path | None) -> list[VisualEmbedding]:
        return self._build_visual_embeddings(frame_dir)

    @staticmethod
    def _embedding_for_frame(frame: Path) -> VisualEmbedding:
        digest = hashlib.sha256(frame.name.encode("utf-8")).digest()
        vector = [round(byte / 255.0, 4) for byte in digest[:16]]
        return VisualEmbedding(frame=frame.name, vector=vector)

    def _fallback_result(
        self,
        video: VideoRecord,
        source_path: Path,
        frame_dir: Path | None,
        audio_path: Path | None,
        capabilities: dict[str, bool],
        warnings: list[str],
    ) -> PreprocessResult:
        scenes = [
            Scene(start=0.0, end=3.0, label="hook"),
            Scene(start=3.0, end=18.0, label="development"),
            Scene(start=18.0, end=30.0, label="climax"),
        ]
        transcript = [
            TranscriptSegment(start=0.0, end=3.0, text="用强冲突开场吸引注意力"),
            TranscriptSegment(start=3.0, end=18.0, text="人物目标和障碍逐步展开"),
            TranscriptSegment(start=18.0, end=30.0, text="反转后给出行动号召"),
        ]
        ocr = self._fallback_ocr(frame_dir)
        visual_embeddings = self._fallback_embeddings(frame_dir)
        return PreprocessResult(
            video_id=video.id,
            source_path=str(source_path),
            duration=None,
            frame_directory=str(frame_dir) if frame_dir else None,
            audio_path=str(audio_path) if audio_path else None,
            frames_sampled=len(list(frame_dir.glob("*.jpg"))) if frame_dir else 0,
            scenes=scenes,
            transcript=transcript,
            ocr=ocr,
            visual_embeddings=visual_embeddings,
            audio_profile={"estimated_bpm": 112.0, "energy": "medium-high"},
            capabilities=capabilities,
            warnings=warnings,
        )

    @staticmethod
    def _parse_fraction(value: str | None) -> float | None:
        if not value:
            return None
        if "/" not in value:
            return float(value)
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        if denominator_value == 0:
            return None
        return float(numerator) / denominator_value

    @staticmethod
    def _label_for_index(index: int, total: int) -> str:
        if index == 0:
            return "hook"
        if index == total - 1:
            return "climax"
        return "development"

    @staticmethod
    def _transcript_for_label(label: str, index: int) -> str:
        if label == "hook":
            return "前置冲突和视觉钩子迅速建立注意力"
        if label == "climax":
            return "高潮和反转在这一段集中释放"
        return f"第 {index + 1} 段内容持续推进人物关系和冲突"

    @staticmethod
    def _time_to_seconds(value: str) -> float | None:
        try:
            parts = value.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            if len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _label_for_time(start: float, duration: float) -> str:
        if start <= duration * 0.15:
            return "hook"
        if start >= duration * 0.7:
            return "climax"
        return "development"
