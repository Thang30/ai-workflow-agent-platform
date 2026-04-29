from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import choice
from typing import Any

from app.agents.prompts import PLANNER_PROMPT_KEY
from app.core.config import settings
from app.models.trace import ExperimentAssignment

EXPERIMENT_TYPE_MODEL = "model"
EXPERIMENT_TYPE_PROMPT = "prompt"
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


def _normalize_prompt_text(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None

    return normalized.replace("\\n", "\n")


def _resolve_prompt_file_path(value: str) -> Path:
    raw_path = Path(value).expanduser()
    if raw_path.is_absolute():
        return raw_path

    return BACKEND_ROOT / raw_path


def _load_prompt_text(
    *,
    prompt_text: str | None,
    prompt_file: str | None,
    variant_name: str,
) -> str | None:
    normalized_prompt_file = _normalize_optional_text(prompt_file)
    if normalized_prompt_file is not None:
        prompt_path = _resolve_prompt_file_path(normalized_prompt_file)
        if not prompt_path.is_file():
            raise ValueError(
                f"Planner prompt file for variant {variant_name} was not found: {prompt_path}"
            )

        file_prompt = _normalize_optional_text(prompt_path.read_text(encoding="utf-8"))
        if file_prompt is None:
            raise ValueError(
                f"Planner prompt file for variant {variant_name} is empty: {prompt_path}"
            )

        return file_prompt

    return _normalize_prompt_text(prompt_text)


@dataclass(frozen=True, slots=True)
class ActiveExperimentVariant:
    name: str
    config: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ActiveExperiment:
    name: str
    type: str
    variants: tuple[ActiveExperimentVariant, ActiveExperimentVariant]

    def assign_variant(self) -> ExperimentAssignment:
        selected_variant = choice(self.variants)
        return ExperimentAssignment(
            experiment_id=None,
            experiment_name=self.name,
            experiment_type=self.type,
            variant_id=None,
            variant_name=selected_variant.name,
            variant_config=dict(selected_variant.config),
        )


def _build_active_experiment() -> ActiveExperiment | None:
    if not settings.experiment_enabled:
        return None

    name = _normalize_optional_text(settings.experiment_name)
    if name is None:
        raise ValueError(
            "EXPERIMENT_NAME is required when experiment routing is enabled."
        )

    experiment_type = _normalize_optional_text(settings.experiment_type)
    if experiment_type not in {EXPERIMENT_TYPE_MODEL, EXPERIMENT_TYPE_PROMPT}:
        raise ValueError(
            "EXPERIMENT_TYPE must be 'model' or 'prompt' when experiment routing is enabled."
        )

    variant_a_name = _normalize_optional_text(settings.experiment_variant_a_name) or "A"
    variant_b_name = _normalize_optional_text(settings.experiment_variant_b_name) or "B"
    if variant_a_name == variant_b_name:
        raise ValueError("Experiment variant names must be different.")

    if experiment_type == EXPERIMENT_TYPE_MODEL:
        variant_a_model = _normalize_optional_text(settings.experiment_variant_a_model)
        variant_b_model = _normalize_optional_text(settings.experiment_variant_b_model)
        if variant_a_model is None or variant_b_model is None:
            raise ValueError(
                "Model experiments require EXPERIMENT_VARIANT_A_MODEL and EXPERIMENT_VARIANT_B_MODEL."
            )
        if variant_a_model == variant_b_model:
            raise ValueError(
                "Model experiment variants must use different model values."
            )

        return ActiveExperiment(
            name=name,
            type=experiment_type,
            variants=(
                ActiveExperimentVariant(
                    name=variant_a_name,
                    config={"model": variant_a_model},
                ),
                ActiveExperimentVariant(
                    name=variant_b_name,
                    config={"model": variant_b_model},
                ),
            ),
        )

    variant_a_prompt = _load_prompt_text(
        prompt_text=settings.experiment_variant_a_planner_prompt,
        prompt_file=settings.experiment_variant_a_planner_prompt_file,
        variant_name=variant_a_name,
    )
    variant_b_prompt = _load_prompt_text(
        prompt_text=settings.experiment_variant_b_planner_prompt,
        prompt_file=settings.experiment_variant_b_planner_prompt_file,
        variant_name=variant_b_name,
    )
    if variant_a_prompt is None or variant_b_prompt is None:
        raise ValueError(
            "Prompt experiments require planner prompt text or planner prompt files for both variants."
        )
    if variant_a_prompt == variant_b_prompt:
        raise ValueError(
            "Prompt experiment variants must use different planner prompts."
        )

    return ActiveExperiment(
        name=name,
        type=experiment_type,
        variants=(
            ActiveExperimentVariant(
                name=variant_a_name,
                config={
                    "prompt_key": PLANNER_PROMPT_KEY,
                    "prompt_text": variant_a_prompt,
                },
            ),
            ActiveExperimentVariant(
                name=variant_b_name,
                config={
                    "prompt_key": PLANNER_PROMPT_KEY,
                    "prompt_text": variant_b_prompt,
                },
            ),
        ),
    )


ACTIVE_EXPERIMENT = _build_active_experiment()


def get_active_experiment() -> ActiveExperiment | None:
    return ACTIVE_EXPERIMENT


def assign_active_variant() -> ExperimentAssignment | None:
    if ACTIVE_EXPERIMENT is None:
        return None

    return ACTIVE_EXPERIMENT.assign_variant()
