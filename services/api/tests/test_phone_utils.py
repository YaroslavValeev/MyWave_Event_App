"""Phone helpers unit tests."""

from app.services.phone_utils import mask_phone, normalize_phone


def test_normalize_phone_ru():
    assert normalize_phone("8 (904) 765-43-21") == "+79047654321"
    assert normalize_phone("+7 904 765 43 21") == "+79047654321"
    assert normalize_phone("9047654321") == "+79047654321"
    assert normalize_phone(None) is None
    assert normalize_phone("") is None


def test_mask_phone():
    assert mask_phone("+79047654321") == "+7***4321"
