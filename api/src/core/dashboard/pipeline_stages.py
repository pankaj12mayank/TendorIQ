"""Derive display pipeline stages from real document / analysis state (no synthetic progress)."""

from __future__ import annotations

from typing import Any, Literal, Optional

PipelineStepStatus = Literal['pending', 'active', 'completed', 'failed']

STAGE_LABELS: dict[str, str] = {
    'upload': 'Upload',
    'extracting': 'Text extraction',
    'processing': 'AI processing',
    'risk_detection': 'Risk detection',
    'proposal_generation': 'Proposal generation',
}

STAGE_ORDER = (
    'upload',
    'extracting',
    'processing',
    'risk_detection',
    'proposal_generation',
)


def _step(
    stage_id: str,
    status: PipelineStepStatus,
    *,
    description: Optional[str] = None,
) -> dict[str, Any]:
    return {
        'id': stage_id,
        'label': STAGE_LABELS[stage_id],
        'status': status,
        'description': description,
    }


def derive_pipeline_stages(
    processing_status: str,
    *,
    analysis_meta: Optional[dict[str, Any]] = None,
    has_analysis_result: bool = False,
    has_proposal: bool = False,
    retry_count: int = 0,
    processing_error: Optional[str] = None,
) -> dict[str, Any]:
    """
    Map backend fields to operational stages.

    DB statuses are coarse (uploaded/processing/retrying/completed/failed/needs_review).
    Sub-stages are inferred only from persisted metadata and related rows.
    """
    status = (processing_status or 'uploaded').lower()
    meta = analysis_meta if isinstance(analysis_meta, dict) else {}
    analysis_state = str(meta.get('status') or '').lower()
    retry_note = f'Retry attempt {retry_count}' if retry_count > 0 else None

    steps: dict[str, PipelineStepStatus] = {k: 'pending' for k in STAGE_ORDER}
    failed_at: Optional[str] = None

    if status == 'uploaded':
        steps['upload'] = 'completed'
        steps['extracting'] = 'active'

    elif status in ('processing', 'retrying'):
        steps['upload'] = 'completed'
        if analysis_state == 'running':
            steps['extracting'] = 'completed'
            steps['processing'] = 'active'
        else:
            steps['extracting'] = 'active'
        if status == 'retrying':
            failed_at = None

    elif status == 'completed':
        steps['upload'] = 'completed'
        steps['extracting'] = 'completed'
        steps['processing'] = 'completed'
        steps['risk_detection'] = 'completed' if has_analysis_result else 'pending'
        steps['proposal_generation'] = 'completed' if has_proposal else 'pending'

    elif status == 'needs_review':
        steps['upload'] = 'completed'
        steps['extracting'] = 'completed'
        steps['processing'] = 'completed'
        steps['risk_detection'] = 'completed' if has_analysis_result else 'active'

    elif status == 'failed':
        steps['upload'] = 'completed'
        if analysis_state == 'failed' or has_analysis_result:
            steps['extracting'] = 'completed'
            steps['processing'] = 'failed'
            failed_at = 'processing'
        elif analysis_state == 'running':
            steps['extracting'] = 'completed'
            steps['processing'] = 'failed'
            failed_at = 'processing'
        else:
            steps['extracting'] = 'failed'
            failed_at = 'extracting'
        for sid in STAGE_ORDER:
            idx = STAGE_ORDER.index(failed_at)
            if STAGE_ORDER.index(sid) > idx:
                steps[sid] = 'pending'

    current = next(
        (sid for sid in STAGE_ORDER if steps[sid] in ('active', 'failed')),
        None,
    )
    if not current:
        if status == 'completed' and not has_proposal:
            current = 'proposal_generation'
        elif status in ('completed', 'needs_review'):
            current = 'proposal_generation' if not has_proposal else None
        elif steps.get('proposal_generation') == 'pending' and steps.get('risk_detection') == 'completed':
            current = 'proposal_generation'

    out_steps = []
    for sid in STAGE_ORDER:
        desc = None
        if sid == 'processing' and retry_note and steps[sid] == 'active':
            desc = retry_note
        if sid == failed_at and processing_error:
            desc = processing_error[:240]
        out_steps.append(_step(sid, steps[sid], description=desc))

    return {
        'stages': out_steps,
        'current_stage': current,
        'processing_status': status,
        'is_terminal': status in ('completed', 'failed', 'needs_review'),
        'is_failed': status == 'failed',
        'is_retrying': status == 'retrying',
        'retry_count': retry_count,
    }
