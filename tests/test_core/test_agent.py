from clawarena.core.agent import AgentInfo, AgentResponse, TokenUsage


def test_token_usage():
    usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150, cached_tokens=20)
    assert usage.total_tokens == 150
    assert usage.cached_tokens == 20


def test_agent_info():
    info = AgentInfo(name="TestAgent", version="1.0", model="test-model")
    assert info.name == "TestAgent"
    assert info.description == ""


def test_agent_response():
    resp = AgentResponse(
        output="hello",
        token_usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        duration_seconds=0.5,
        api_calls=1,
    )
    assert resp.output == "hello"
    assert resp.error is None
    assert resp.api_calls == 1
