import pytest
import asyncio
from core.streaming_composer import StreamingFunctionComposer

@pytest.mark.asyncio
async def test_streaming_composer_eager_execution():
    composer = StreamingFunctionComposer()
    
    # Mock generator representing incoming token stream from LLM
    async def mock_llm_stream():
        tokens = [
            "Planning started.\n",
            "STEP: {\"name\": \"Setup Worktree\", \"command\": \"git checkout -b temp\"}",
            "\nNext step is coming up.\n",
            "STEP: {\"name\": \"Apply Patch\", \"command\": \"patch file.py patch.diff\"}",
            "\nFinished planning."
        ]
        for token in tokens:
            yield token
            await asyncio.sleep(0.01)

    executed_steps = []
    
    async def mock_executor_handler(step_data):
        executed_steps.append(step_data["name"])
        return f"Success: {step_data['command']}"

    results = await composer.pipe_steps(mock_llm_stream(), mock_executor_handler)
    
    assert len(executed_steps) == 2
    assert executed_steps[0] == "Setup Worktree"
    assert executed_steps[1] == "Apply Patch"
    
    assert len(results) == 2
    assert results[0]["step"] == "Setup Worktree"
    assert "Success: git checkout -b temp" in results[0]["result"]
