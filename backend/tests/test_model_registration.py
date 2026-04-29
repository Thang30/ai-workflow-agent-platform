import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.core.db import Base
from app.repositories.workflow_runs import WorkflowRunRepository


class ModelRegistrationTests(unittest.TestCase):
    def test_workflow_repository_registers_experiment_tables(self):
        self.assertIsNotNone(WorkflowRunRepository)
        self.assertIn("experiments", Base.metadata.tables)
        self.assertIn("experiment_variants", Base.metadata.tables)
        self.assertIn("workflow_runs", Base.metadata.tables)
