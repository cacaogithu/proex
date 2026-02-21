# Implementation Plan - Remove ML Component for Stability

# Goal Description
Remove the `PromptEnhancer` and related unsupervised learning components from the letter generation pipeline. This will eliminate the "drift" and unpredictability caused by the ML feedback loop, ensuring consistent, high-quality output as requested by the client. We will retain the `HeterogeneityArchitect` as it provides necessary variety without the instability of unsupervised learning.

## User Review Required
> [!IMPORTANT]
> This change will disable the "self-improving" aspect of the system. The system will no longer automatically adjust prompts based on feedback or clustering. This is intentional to guarantee consistency.

## Proposed Changes

### Backend Core

#### [MODIFY] [processor.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/core/processor.py)
- Remove `PromptEnhancer` initialization and training.
- Remove `PromptEnhancer` dependency injection into `BlockGenerator`.
- Remove embedding generation and saving (unsupervised learning data).

#### [MODIFY] [block_generator.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/core/block_generator.py)
- Remove `prompt_enhancer` parameter from `__init__`.
- Remove `prompt_enhancer.enhance_block_prompt` calls in `generate_block3` (and others if present).
- Clean up the class to rely solely on the deterministic `base_prompt`.

### ML Components

#### [DELETE] [prompt_enhancer.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/ml/prompt_enhancer.py)
- Delete the file entirely as it is no longer needed.

#### [DELETE] [cluster_analyzer.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/ml/cluster_analyzer.py)
- Delete the file as it supports `PromptEnhancer`.

#### [DELETE] [embedding_engine.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/ml/embedding_engine.py)
- Delete the file as it supports `PromptEnhancer`.

#### [DELETE] [feedback_analyzer.py](file:///Users/rafaelalmeida/Proex-Replit/proex/backend/app/ml/feedback_analyzer.py)
- Delete the file as it supports `PromptEnhancer`.

## Verification Plan

### Automated Tests
- Run a test submission to ensure the pipeline still completes without the ML components.
- Verify that `BlockGenerator` produces output without errors.

### Manual Verification
- Inspect the logs to ensure no "ML training" or "embedding generation" messages appear.
- Verify that the output letters are generated successfully.
