from __future__ import annotations

from datetime import datetime, timezone

from app.domain import AnalysisTask, TaskStatus
from app.services.agents import OrchestratorAgent
from app.services.preprocess import VideoPreprocessor
from app.services.report import ReportGenerator
from app.store import store


class AnalysisPipeline:
    def __init__(self) -> None:
        self.preprocessor = VideoPreprocessor()
        self.orchestrator = OrchestratorAgent()
        self.report_generator = ReportGenerator()

    async def run(self, task: AnalysisTask) -> None:
        try:
            task.status = TaskStatus.processing
            task.updated_at = datetime.now(timezone.utc)
            store.save_task(task)

            preprocess = await self.preprocessor.run(task.video)
            agent_results = await self.orchestrator.run(task.video, preprocess)
            task.report = self.report_generator.build(task.video, preprocess, agent_results)
            task.status = TaskStatus.completed
            task.updated_at = datetime.now(timezone.utc)
            store.save_task(task)
        except Exception as exc:  # pragma: no cover - defensive task boundary
            task.status = TaskStatus.failed
            task.error = str(exc)
            task.updated_at = datetime.now(timezone.utc)
            store.save_task(task)


pipeline = AnalysisPipeline()
