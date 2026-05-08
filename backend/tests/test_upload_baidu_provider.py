from db.models import ProviderConfig, SystemProviderConfig, User
from routes.upload import _resolve_baidu_paper_cut_provider


def test_resolve_baidu_provider_falls_back_to_system_provider(db):
    user = User(id=1, username="test", email="test@example.com", password_hash="x")
    db.add(user)
    db.add(SystemProviderConfig(
        id="system-baidu",
        category="baidu_paper_cut",
        name="System Baidu Paper Cut",
        is_active=True,
        api_key="system-key",
        base_url="https://baidu.example.com/paper_cut_edu",
    ))
    db.commit()

    provider, source = _resolve_baidu_paper_cut_provider(db, user.id)

    assert source == "system"
    assert provider.api_key == "system-key"


def test_resolve_baidu_provider_prefers_personal_provider(db):
    user = User(id=1, username="test", email="test@example.com", password_hash="x")
    db.add(user)
    db.add(SystemProviderConfig(
        id="system-baidu",
        category="baidu_paper_cut",
        name="System Baidu Paper Cut",
        is_active=True,
        api_key="system-key",
    ))
    db.add(ProviderConfig(
        id="personal-baidu",
        user_id=user.id,
        category="baidu_paper_cut",
        name="Personal Baidu Paper Cut",
        is_active=True,
        api_key="personal-key",
    ))
    db.commit()

    provider, source = _resolve_baidu_paper_cut_provider(db, user.id)

    assert source == "personal"
    assert provider.api_key == "personal-key"
