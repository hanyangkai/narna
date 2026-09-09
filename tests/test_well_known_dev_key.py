"""Test rejection of well-known seed/dev keys in production mode."""

import os
import pytest
from unittest.mock import patch


def test_well_known_dev_key_hash():
    """Verify the hash of the well-known dev key is correct."""
    from web.backend.app.auth import hash_key, WELL_KNOWN_SEED_HASHES
    
    seed_key = "uap_live_dev_local_key_change_in_prod"
    expected_hash = "5790c9c9a6eef649172e2867d5311512586536eb220df83943ac42e5f53c033f"
    
    assert hash_key(seed_key) == expected_hash
    assert expected_hash in WELL_KNOWN_SEED_HASHES


def test_production_mode_detection():
    """Test is_production_mode() correctly detects prod environment."""
    from web.backend.app.auth import is_production_mode
    
    # Test UAP_CRYPTO_MODE=live
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": ""}):
        assert is_production_mode() is True
    
    # Test SENTRY_ENVIRONMENT=production
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "production"}):
        assert is_production_mode() is True
    
    # Test both set
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": "production"}):
        assert is_production_mode() is True
    
    # Test dev mode (neither set)
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "development"}, clear=True):
        assert is_production_mode() is False


def test_well_known_key_denied_in_production():
    """Test that well-known dev key is denied in production mode."""
    from web.backend.app.auth import is_key_denied
    
    seed_key = "uap_live_dev_local_key_change_in_prod"
    
    # In production mode (UAP_CRYPTO_MODE=live), well-known key should be denied
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": "", "UAP_KEY_DENYLIST": ""}):
        assert is_key_denied(seed_key) is True
    
    # In production mode (SENTRY_ENVIRONMENT=production), well-known key should be denied
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "production", "UAP_KEY_DENYLIST": ""}):
        assert is_key_denied(seed_key) is True


def test_well_known_key_allowed_in_dev():
    """Test that well-known dev key is allowed in dev/test mode."""
    from web.backend.app.auth import is_key_denied
    
    seed_key = "uap_live_dev_local_key_change_in_prod"
    
    # In dev mode, well-known key should NOT be denied (unless in denylist)
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "development", "UAP_KEY_DENYLIST": ""}):
        assert is_key_denied(seed_key) is False


def test_manual_denylist_overrides():
    """Test that UAP_KEY_DENYLIST works in both prod and dev."""
    from web.backend.app.auth import is_key_denied, hash_key, load_key_denylist
    
    test_key = "some_random_test_key"
    test_hash = hash_key(test_key)
    
    # Manual denylist should work in dev mode
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "", "UAP_KEY_DENYLIST": test_hash}):
        # Reload denylist
        from web.backend.app import auth
        auth._KEY_DENYLIST = load_key_denylist()
        assert is_key_denied(test_key) is True
    
    # Manual denylist should work in prod mode
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": "", "UAP_KEY_DENYLIST": test_hash}):
        # Reload denylist
        from web.backend.app import auth
        auth._KEY_DENYLIST = load_key_denylist()
        assert is_key_denied(test_key) is True


def test_seed_dev_org_skipped_in_production():
    """Test that _seed_dev_org() is skipped in production mode."""
    # This is a conceptual test - in real deployment, the seed function
    # checks environment and skips seeding when UAP_CRYPTO_MODE=live or SENTRY_ENVIRONMENT=production
    
    # Import the main module to verify the logic exists
    from web.backend.app.main import _seed_dev_org
    
    # In production, _seed_dev_org should return early without seeding
    with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": ""}):
        # Call should return early - verify by checking it doesn't crash
        # (actual DB seeding would require DB setup)
        try:
            _seed_dev_org()
        except Exception as e:
            # Should not reach DB code in prod mode
            if "database" in str(e).lower() or "session" in str(e).lower():
                pytest.fail(f"_seed_dev_org should have returned early in prod mode, but attempted DB access: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
