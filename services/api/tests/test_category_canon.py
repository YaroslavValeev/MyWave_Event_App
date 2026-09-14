"""IWWF category canon (ADR-0007)."""

from app.services.category_canon import canonical_category, iwwf_class_from_source, sex_from_label


def test_youth_labels():
    assert iwwf_class_from_source("Девочки U14", birth_year=2014) == "U14"
    assert iwwf_class_from_source("Grom Boys", birth_year=2014) == "U14"
    assert iwwf_class_from_source("Junior Women", birth_year=2010) == "U18"
    assert iwwf_class_from_source("Девушки U18", birth_year=2009) == "U18"
    assert iwwf_class_from_source("до 15", birth_year=2013) == "U14"
    assert iwwf_class_from_source("до 19", birth_year=2009) == "U18"


def test_open_split_by_age():
    assert iwwf_class_from_source("Женщины", birth_year=2001) == "Open"
    assert iwwf_class_from_source("Мужчины", birth_year=1990) == "O30"
    assert iwwf_class_from_source("Женщины", birth_year=1973) == "O40"
    assert iwwf_class_from_source("Open Men", birth_year=2001) == "Open"


def test_canonical_code_and_title():
    cat = canonical_category("Девочки U14", discipline="Wakeboard (boat)", birth_year=2014)
    assert cat.code == "wb-u14-f"
    assert cat.iwwf_class == "U14"
    assert "первенство" in cat.title
    open_m = canonical_category("Мужчины", discipline="Wakesurf", birth_year=2000)
    assert open_m.code == "ws-open-m"
    assert "чемпионат" in open_m.title


def test_sex_from_open_men():
    assert sex_from_label("Open Men") == "m"
    assert sex_from_label("U14 F") == "f"


def test_masters_from_fvls_label():
    assert iwwf_class_from_source("Мастерс - мужчины", birth_year=None) == "O30"
    cat = canonical_category("Мастерс", discipline="Wakeboard (boat)", sex_hint="f")
    assert cat.code == "wb-o30-f"
    assert "мастерс" in cat.title


def test_veterans_o40_from_label():
    assert iwwf_class_from_source("O40+ Ветераны", birth_year=None) == "O40"
    cat = canonical_category("Ветераны", discipline="Wakeboard (boat)", sex_hint="m")
    assert cat.code == "wb-o40-m"
    assert "ветераны" in cat.title
