from afridock_api.inference.profiles import ModelProfileRegistry, get_profile_registry


def test_default_registry_loads_expected_profiles() -> None:
    registry = get_profile_registry()

    assert "llama-3.1-8b-instruct" in registry
    assert "claude-fallback" in registry
    assert registry.default_chain == [
        "llama-3.1-8b-nim",
        "llama-3.2-1b-instruct",
        "llama-3.3-70b-nvidia",
        "llama-3.1-8b-instruct",
        "mixtral-8x7b-instruct",
        "claude-fallback",
    ]
    # CLAUDE.md's #1 constraint: self-hosted (your-own-hardware NIM box, then
    # in-container Ollama) first, commercial last and marked is_commercial
    # (gated by Organization.allow_commercial_fallback).
    assert registry.get("llama-3.1-8b-nim").provider == "nvidia_nim"
    assert registry.get("llama-3.1-8b-nim").is_commercial is False
    assert registry.get("llama-3.2-1b-instruct").provider == "ollama"
    assert registry.get("llama-3.2-1b-instruct").is_commercial is False
    # NVIDIA's *hosted* cloud API catalog — not self-hosted, but still an
    # open-weight model, so treated like the Hugging-Face-hosted entries
    # (not is_commercial) rather than gated behind allow_commercial_fallback.
    assert registry.get("llama-3.3-70b-nvidia").provider == "nvidia_cloud"
    assert registry.get("llama-3.3-70b-nvidia").is_commercial is False
    assert registry.get("claude-fallback").is_commercial is True


def test_get_unknown_profile_raises_key_error() -> None:
    registry = get_profile_registry()

    try:
        registry.get("does-not-exist")
    except KeyError as exc:
        assert "does-not-exist" in str(exc)
    else:
        raise AssertionError("expected KeyError")


def test_profile_fields_populated() -> None:
    registry = get_profile_registry()

    profile = registry.get("llama-3.1-8b-instruct")

    assert profile.provider == "huggingface"
    assert profile.litellm_model.startswith("huggingface/")
    assert profile.default_params["temperature"] == 0.7


def test_registry_is_reusable_from_scratch(tmp_path) -> None:
    custom_yaml = tmp_path / "profiles.yaml"
    custom_yaml.write_text(
        """
        profiles:
          test-model:
            provider: test
            litellm_model: test/test-model
            input_cost_per_1k_tokens: 0.0
            output_cost_per_1k_tokens: 0.0
        default_chain:
          - test-model
        """
    )

    registry = ModelProfileRegistry.from_yaml(custom_yaml)

    assert registry.default_chain == ["test-model"]
    assert registry.get("test-model").litellm_model == "test/test-model"
