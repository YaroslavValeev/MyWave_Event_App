"""Kazan 2026 paper/IWWF sheets transcribed from owner scans (no phones).

Homologation on every sheet: Not homologated → results stay draft.
Junior → U18, Grom → U14, Ope → Open (ADR-0007).
"""

from __future__ import annotations

# engine: boat = execution/intensity/composition; surf = execution/intensity/difficulty/variety
# Times are local Kazan (MSK, UTC+3). Homologation: Not homologated → draft only.


def _h(
    code: str,
    *,
    disc: str,
    klass: str,
    sex: str,
    rnd: str,
    idx: int,
    when: str,
    engine: str,
    entries: list[dict],
    chief: str | None = None,
    scorer: str | None = None,
    source: str = "owner_scan",
    time_inferred: bool = False,
) -> dict:
    return {
        "code": code,
        "discipline": disc,
        "iwwf_class": klass,
        "sex": sex,
        "round": rnd,
        "heat_index": idx,
        "scheduled_at": when,
        "engine": engine,
        "chief_judge": chief,
        "scorer": scorer,
        "source": source,
        "time_inferred": time_inferred,
        "entries": entries,
    }


def _e(
    order: int,
    latin: str,
    *,
    place: int | None = None,
    score: float | None = None,
    q: str | None = None,
    dns: bool = False,
    seeded: bool = False,
    ru: str | None = None,
    **criteria: float,
) -> dict:
    row: dict = {"order": order, "latin": latin, "seeded": seeded, "dns": dns}
    if place is not None:
        row["place"] = place
    if score is not None:
        row["score"] = score
    if q:
        row["q"] = q
    if ru:
        row["ru"] = ru
    if criteria:
        row["criteria"] = criteria
    return row


WB = "Wakeboard (boat)"
WS = "Wakesurf"
WK = "Wakeskim"
BOAT = "IWWF_BOAT_EIC"
SURF = "WSWS_DRIVE"
CJ_WB = "Balakin Alexandr"
SC_WB = "Filippov Alexey"
CJ_SU = "Filippov Alexey"
SC_SU = "Zhivaev Sergey"

HEATS = [
    # --- Wakeboard boat qualifications Thursday 13.08 ---
    _h(
        "d1-wb-u14-f-qual1",
        disc=WB, klass="U14", sex="f", rnd="qual", idx=1,
        when="2026-08-13T10:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Kagirova Renata", place=4, score=20.00, q="Q", execution=6.66, intensity=6.68, composition=6.66),
            _e(2, "Garan Vera", place=3, score=30.00, q="Q", execution=9.99, intensity=10.02, composition=9.99),
            _e(3, "Seliverstova Nina", place=5, score=13.33, q="Q", execution=4.66, intensity=4.34, composition=4.33),
            _e(4, "Seliverstova Maria", place=2, score=38.78, q="Q", execution=13.10, intensity=13.14, composition=12.54),
            _e(5, "Filippova Maria", place=1, score=50.00, q="Q", execution=16.10, intensity=16.70, composition=17.21),
        ],
    ),
    _h(
        "d1-wb-u14-m-qual1",
        disc=WB, klass="U14", sex="m", rnd="qual", idx=1,
        when="2026-08-13T10:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Gultyaev Grigorii", place=5, score=10.00, q="Q", execution=3.33, intensity=3.34, composition=3.33),
            _e(2, "Borovikov Lion", place=4, score=19.33, q="Q", execution=6.44, intensity=6.46, composition=6.44),
            _e(3, "Seliverstov Yuri", place=6, score=7.33, q="Q", execution=2.44, intensity=2.45, composition=2.44),
            _e(4, "Sabarov Matvey", place=3, score=30.00, q="Q", execution=9.99, intensity=10.02, composition=9.99),
            _e(5, "Zaitcev Alexander", place=2, score=50.00, q="Q", execution=16.65, intensity=16.70, composition=16.65),
            _e(6, "Ersh Vadim", place=1, score=60.00, q="Q", execution=19.98, intensity=20.04, composition=19.98),
        ],
    ),
    _h(
        "d1-wb-u18-f-qual1",
        disc=WB, klass="U18", sex="f", rnd="qual", idx=1,
        when="2026-08-13T11:15:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Idiatulina Danna", place=2, score=25.00, q="Q", execution=8.33, intensity=8.35, composition=8.33),
            _e(2, "Zhivaeva Maya", place=3, score=10.00, q="Q", execution=3.33, intensity=3.34, composition=3.33),
            _e(3, "Chudina Ulyana", place=1, score=45.00, q="Q", execution=14.99, intensity=15.03, composition=14.99),
        ],
    ),
    _h(
        "d1-wb-u18-m-qual1",
        disc=WB, klass="U18", sex="m", rnd="qual", idx=1,
        when="2026-08-13T11:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Zubkov Yaroslav"),
            _e(2, "Alliulov Artur"),
            _e(3, "Seliverstov Vladimir"),
            _e(4, "Sunin Daren"),
        ],
    ),
    _h(
        "d1-wb-open-f-qual1",
        disc=WB, klass="Open", sex="f", rnd="qual", idx=1,
        when="2026-08-13T13:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Petrova Valentina", place=3, score=20.67, q="L", seeded=True, execution=6.44, intensity=6.46, composition=7.77),
            _e(2, "Amelchenko Evgeniya", place=4, score=19.22, q="L", seeded=True, execution=5.00, intensity=6.68, composition=7.55),
            _e(3, "Zvezdova Aleksandra", place=2, score=26.78, q="Q", execution=9.55, intensity=9.46, composition=7.77),
            _e(4, "Shupliakova Anastasia", place=1, score=37.78, q="Q", seeded=True, execution=12.21, intensity=12.80, composition=12.77),
        ],
    ),
    _h(
        "d1-wb-open-f-qual2",
        disc=WB, klass="Open", sex="f", rnd="qual", idx=2,
        when="2026-08-13T13:20:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Shvedova Daria", place=2, score=21.23, q="Q", execution=6.44, intensity=8.13, composition=6.66),
            _e(2, "Mukhtasarova Yuliya", place=3, score=10.00, q="L", execution=3.33, intensity=3.34, composition=3.33),
            _e(3, "Vorobeva Valentina", place=1, score=48.67, q="Q", execution=14.76, intensity=16.14, composition=17.76),
        ],
    ),
    _h(
        "d1-wb-open-m-qual1",
        disc=WB, klass="Open", sex="m", rnd="qual", idx=1,
        when="2026-08-13T14:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Zhatko Aleksandr", seeded=True),
            _e(2, "Valeev Yaroslav"),
            _e(3, "Mukhtasarov Denis"),
            _e(4, "Khudnitskiy Georgiy"),
        ],
    ),
    _h(
        "d1-wb-open-m-qual2",
        disc=WB, klass="Open", sex="m", rnd="qual", idx=2,
        when="2026-08-13T14:20:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Karpukhov Konstantin", seeded=True),
            _e(2, "Matveev Konstantin", seeded=True),
            _e(3, "Chernov Dmitry", seeded=True),
            _e(4, "Lazin Vladimir"),
        ],
    ),
    _h(
        "d1-wb-open-m-qual3",
        disc=WB, klass="Open", sex="m", rnd="qual", idx=3,
        when="2026-08-13T14:40:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Borovikov Nikolay", seeded=True),
            _e(2, "Khairullin Almaz", seeded=True),
            _e(3, "Nikitin Sergey", seeded=True),
            _e(4, "Maslov Dmitriy"),
        ],
    ),
    _h(
        "d1-wb-open-m-qual4",
        disc=WB, klass="Open", sex="m", rnd="qual", idx=4,
        when="2026-08-13T15:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Simonov Evgeniy", seeded=True),
            _e(2, "Dementev Alexey", seeded=True),
            _e(3, "Kozlov Denis", seeded=True),
            _e(4, "Kuzmin Ivan", seeded=True),
            _e(5, "Likhtarev Georgiy"),
        ],
    ),
    _h(
        "d1-wb-open-m-qual5",
        disc=WB, klass="Open", sex="m", rnd="qual", idx=5,
        when="2026-08-13T15:20:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Kafichev Zahar"),
            _e(2, "Lozitskiy Slava", seeded=True),
            _e(3, "Kudryashov Georgy"),
            _e(4, "Abzalov Kamil"),
            _e(5, "Zhivaev Viacheslav"),
        ],
    ),
    # --- Wakeboard open men SF Friday 14.08 (results sheet) ---
    _h(
        "d2-wb-open-m-sf1",
        disc=WB, klass="Open", sex="m", rnd="sf", idx=1,
        when="2026-08-14T16:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Valeev Yaroslav", place=1, score=53.33, q="Q", execution=16.65, intensity=18.37, composition=18.32),
            _e(2, "Maslov Dmitriy", place=2, score=43.11, q="Q", execution=14.43, intensity=14.25, composition=14.43),
            _e(3, "Kuzmin Ivan", place=3, score=40.89, q="Q", seeded=True, execution=13.43, intensity=13.92, composition=13.54),
            _e(4, "Simonov Evgeniy", place=4, score=35.00, seeded=True, execution=11.10, intensity=11.91, composition=11.99),
            _e(5, "Karpukhov Konstantin", place=5, score=29.33, seeded=True, execution=9.77, intensity=9.80, composition=9.77),
            _e(6, "Kudryashov Georgy", place=6, score=24.22, execution=8.10, intensity=8.24, composition=7.88),
        ],
    ),
    _h(
        "d2-wb-open-m-sf2",
        disc=WB, klass="Open", sex="m", rnd="sf", idx=2,
        when="2026-08-14T16:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        entries=[
            _e(1, "Khudnitskiy Georgiy", place=1, score=80.56, q="Q", execution=26.64, intensity=26.94, composition=26.97),
            _e(2, "Likhtarev Georgii", place=2, score=64.11, q="Q", execution=21.42, intensity=21.49, composition=21.20),
            _e(3, "Zhivaev Viacheslav", place=3, score=61.78, q="Q", execution=20.76, intensity=20.49, composition=20.54),
            _e(4, "Lazin Vladimir", place=4, score=40.56, execution=13.32, intensity=13.58, composition=13.65),
            _e(5, "Kozlov Denis", place=5, score=34.56, seeded=True, execution=11.43, intensity=11.58, composition=11.54),
            _e(6, "Borovikov Nikolay", place=6, score=19.33, seeded=True, execution=6.44, intensity=6.46, composition=6.44),
        ],
    ),
    # --- Wakeboard finals Saturday (start order from scans; places from FVLS press 15.08) ---
    _h(
        "d3-wb-u14-f-final1",
        disc=WB, klass="U14", sex="f", rnd="final", idx=1,
        when="2026-08-15T09:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Seliverstova Nina"),
            _e(2, "Kagirova Renata"),
            _e(3, "Garan Vera", place=3, ru="Вера Гаран"),
            _e(4, "Seliverstova Maria", place=2, ru="Мария Селиверстова"),
            _e(5, "Filippova Maria", place=1, ru="Мария Филиппова"),
        ],
    ),
    _h(
        "d3-wb-u14-m-final1",
        disc=WB, klass="U14", sex="m", rnd="final", idx=1,
        when="2026-08-15T09:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Seliverstov Yuri"),
            _e(2, "Gultyaev Grigorii"),
            _e(3, "Borovikov Lion"),
            _e(4, "Sabarov Matvey", place=3, ru="Матвей Сабаров"),
            _e(5, "Zaitcev Alexander", place=2, ru="Александр Зайцев"),
            _e(6, "Ersh Vadim", place=1, ru="Вадим Ерш"),
        ],
    ),
    _h(
        "d3-wb-u18-f-final1",
        disc=WB, klass="U18", sex="f", rnd="final", idx=1,
        when="2026-08-15T10:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Zhivaeva Maya", place=3, ru="Майя Живаева"),
            _e(2, "Idiatulina Danna", place=2, ru="Дания Идиятуллина"),
            _e(3, "Chudina Ulyana", place=1, ru="Ульяна Чудина"),
        ],
    ),
    _h(
        "d3-wb-u18-m-final1",
        disc=WB, klass="U18", sex="m", rnd="final", idx=1,
        when="2026-08-15T10:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Zubkov Yaroslav"),
            _e(2, "Alliulov Artur", place=3, ru="Артур Аллиулов"),
            _e(3, "Seliverstov Vladimir", place=2, ru="Владимир Селиверстов"),
            _e(4, "Sunin Daren", place=1, ru="Дарэн Сунин"),
        ],
    ),
    # --- Wakesurf Friday quals + Saturday finals ---
    _h(
        "d2-ws-open-f-qual1",
        disc=WS, klass="Open", sex="f", rnd="qual", idx=1,
        when="2026-08-14T08:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Khomiuk Ekaterina", place=4, score=17.50, q="L", seeded=True, execution=2.00, intensity=1.50, difficulty=2.00, variety=1.50),
            _e(2, "Vorozhenina Milana", place=5, score=8.25, q="L", execution=0.40, intensity=1.97, difficulty=0.50, variety=0.43),
            _e(3, "Apanyakina Ksenia", place=3, score=24.42, q="L", execution=2.50, intensity=2.27, difficulty=2.63, variety=2.37),
            _e(4, "Terekhova Anastasia", place=1, score=34.67, q="Q", seeded=True, execution=3.67, intensity=3.40, difficulty=3.40, variety=3.40),
            _e(5, "Sadovnikova Lidia", place=2, score=29.33, q="Q", seeded=True, execution=2.90, intensity=2.93, difficulty=3.00, variety=2.90),
        ],
    ),
    _h(
        "d2-ws-open-f-qual2",
        disc=WS, klass="Open", sex="f", rnd="qual", idx=2,
        when="2026-08-14T08:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Isaeva Valeria", place=4, score=8.00, q="L", execution=0.80, intensity=0.80, difficulty=0.80, variety=0.80),
            _e(2, "Fursova Tatiana", q="L", dns=True, seeded=True),
            _e(3, "Krokhina Mariia", place=2, score=43.83, q="Q", execution=4.33, intensity=4.27, difficulty=4.43, variety=4.50),
            _e(4, "Blanket Maria", place=1, score=54.50, q="Q", execution=5.43, intensity=5.23, difficulty=5.57, variety=5.57),
            _e(5, "Shelkova Aleksandra", place=3, score=17.83, q="L", seeded=True, execution=1.50, intensity=1.93, difficulty=2.20, variety=1.50),
        ],
    ),
    _h(
        "d2-ws-open-m-qual1",
        disc=WS, klass="Open", sex="m", rnd="qual", idx=1,
        when="2026-08-14T09:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Korolkov Stanislav"),
            _e(2, "Ofitserov Andrey", seeded=True),
            _e(3, "Solovev Andrei Jr", seeded=True),
            _e(4, "Sivoglazov Viktor"),
            _e(5, "Solovev Andrei Alex", seeded=True),
        ],
    ),
    _h(
        "d2-ws-open-m-qual2",
        disc=WS, klass="Open", sex="m", rnd="qual", idx=2,
        when="2026-08-14T10:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Mokrousov Aleksandr"),
            _e(2, "Savichev Matvey", seeded=True),
            _e(3, "Kantemir Aleksey", seeded=True),
            _e(4, "Krasnikov Dmitrii", seeded=True),
            _e(5, "Zhdanov Ivan", seeded=True),
        ],
    ),
    _h(
        "d3-ws-open-f-final1",
        disc=WS, klass="Open", sex="f", rnd="final", idx=1,
        when="2026-08-15T11:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Shelkova Aleksandra", seeded=True),
            _e(2, "Apanyakina Ksenia"),
            _e(3, "Krokhina Mariia"),
            _e(4, "Sadovnikova Lidia", place=3, seeded=True, ru="Лидия Садовникова"),
            _e(5, "Terekhova Anastasia", place=2, seeded=True, ru="Анастасия Терехова"),
            _e(6, "Blanket Maria", place=1, ru="Мария Бланкет"),
        ],
    ),
    _h(
        "d3-ws-open-m-final1",
        disc=WS, klass="Open", sex="m", rnd="final", idx=1,
        when="2026-08-15T12:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Krasnikov Dmitrii", seeded=True),
            _e(2, "Solovev Andrei Alex", seeded=True),
            _e(3, "Zhdanov Ivan", seeded=True),
            _e(4, "Solovev Andrei Jr", place=3, seeded=True, ru="Андрей Соловьев мл."),
            _e(5, "Korolkov Stanislav", place=1, ru="Станислав Корольков"),
            _e(6, "Savichev Matvey", place=2, seeded=True, ru="Матвей Савичев"),
        ],
    ),
    # --- Wakeskim Thursday quals (start list + results where present) ---
    _h(
        "d1-wk-u14-m-qual1",
        disc=WK, klass="U14", sex="m", rnd="qual", idx=1,
        when="2026-08-13T12:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Vikhrov Timofei"),
            _e(2, "Solovev Andrei Jr"),
            _e(3, "Savichev Matvey"),
        ],
    ),
    _h(
        "d1-wk-u18-f-qual1",
        disc=WK, klass="U18", sex="f", rnd="qual", idx=1,
        when="2026-08-13T12:20:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Efimova Evgenia"),
            _e(2, "Medvedeva Anastasia"),
            _e(3, "Maksakova Taisia"),
            _e(4, "Medvedeva Ekaterina"),
        ],
    ),
    _h(
        "d1-wk-open-f-qual1",
        disc=WK, klass="Open", sex="f", rnd="qual", idx=1,
        when="2026-08-13T16:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Kopalkina Tatiana", place=1, score=60.00, q="Q", seeded=True, execution=6.00, intensity=6.00, difficulty=6.00, variety=6.00),
            _e(2, "Kargina Iana", place=3, score=45.00, q="L", execution=4.83, intensity=4.00, difficulty=4.83, variety=4.33),
            _e(3, "Malysheva Daria", place=2, score=51.00, q="Q", seeded=True, execution=5.00, intensity=5.17, difficulty=5.07, variety=5.17),
            _e(4, "Kuznetsova Nadezhda", place=4, score=31.25, q="L", seeded=True, execution=3.17, intensity=3.17, difficulty=3.17, variety=3.00),
        ],
    ),
    _h(
        "d1-wk-open-f-qual2",
        disc=WK, klass="Open", sex="f", rnd="qual", idx=2,
        when="2026-08-13T16:50:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Kechaeva Kristina", place=3, score=15.00, q="L", execution=1.50, intensity=1.50, difficulty=1.50, variety=1.50),
            _e(2, "Ruban Iuliia", place=1, score=19.42, q="Q", execution=1.97, intensity=1.90, difficulty=1.93, variety=1.97),
            _e(3, "Kuznetsova Olga", place=2, score=18.83, q="Q", execution=1.87, intensity=1.80, difficulty=2.00, variety=1.87),
        ],
    ),
    # Open men skim: scored heats (results sheet) — SoT over start-list grouping
    _h(
        "d1-wk-open-m-qual1",
        disc=WK, klass="Open", sex="m", rnd="qual", idx=1,
        when="2026-08-13T17:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Semenov Filipp", place=1, score=75.58, q="Q", execution=6.87, intensity=7.83, difficulty=8.00, variety=7.53),
            _e(2, "Andronov Evgenii", place=2, score=36.00, q="Q", seeded=True, execution=3.17, intensity=3.83, difficulty=3.90, variety=3.50),
            _e(3, "Bochkarev Alexander", place=3, score=29.17, q="L", seeded=True, execution=2.17, intensity=3.00, difficulty=3.50, variety=3.00),
            _e(4, "Makhrin Aleksandr", place=4, score=18.00, q="L", execution=1.77, intensity=1.67, difficulty=2.00, variety=1.77),
            _e(5, "Zhdanov Ivan", place=5, score=17.58, q="L", seeded=True, execution=1.60, intensity=1.67, difficulty=2.00, variety=1.77),
        ],
    ),
    _h(
        "d1-wk-open-m-qual2",
        disc=WK, klass="Open", sex="m", rnd="qual", idx=2,
        when="2026-08-13T17:55:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        entries=[
            _e(1, "Savichev Matvey", place=1, score=78.08, q="Q", seeded=True, execution=7.17, intensity=8.00, difficulty=8.17, variety=7.90),
            _e(2, "Ivanov Vitaly", place=2, score=51.00, q="Q", execution=4.83, intensity=5.67, difficulty=5.00, variety=4.90),
            _e(3, "Solovev Andrei Alex", place=3, score=24.67, q="L", seeded=True, execution=2.60, intensity=2.70, difficulty=2.50, variety=2.07),
            _e(4, "Shamarin Mikhail", place=4, score=10.17, q="L", execution=1.00, intensity=1.00, difficulty=1.07, variety=1.00),
            _e(5, "Kostenko Victor", q="L", dns=True, seeded=True),
            _e(6, "Mokrousov Aleksandr"),
        ],
    ),
    _h(
        "d3-wk-u18-f-final1",
        disc=WK, klass="U18", sex="f", rnd="final", idx=1,
        when="2026-08-15T08:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Efimova Evgenia"),
            _e(2, "Medvedeva Anastasia", place=2, ru="Анастасия Медведева"),
            _e(3, "Medvedeva Ekaterina", place=3, ru="Екатерина Медведева"),
            _e(4, "Maksakova Taisia", place=1, ru="Таисия Максакова"),
        ],
    ),
    _h(
        "d3-wk-u14-m-final1",
        disc=WK, klass="U14", sex="m", rnd="final", idx=1,
        when="2026-08-15T08:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Vikhrov Timofei", place=2, ru="Тимофей Вихров"),
            _e(2, "Solovev Andrei Jr", place=1, ru="Андрей Соловьев"),
        ],
    ),
    _h(
        "d3-wk-open-f-final1",
        disc=WK, klass="Open", sex="f", rnd="final", idx=1,
        when="2026-08-15T13:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Kuznetsova Nadezhda", place=3, seeded=True, ru="Надежда Кузнецова"),
            _e(2, "Kargina Iana", place=2, ru="Яна Каргина"),
            _e(3, "Kuznetsova Olga"),
            _e(4, "Malysheva Daria", seeded=True),
            _e(5, "Kopalkina Tatiana", place=1, seeded=True, ru="Татьяна Копалкина"),
            _e(6, "Ruban Iuliia"),
        ],
    ),
    _h(
        "d3-wk-open-m-final1",
        disc=WK, klass="Open", sex="m", rnd="final", idx=1,
        when="2026-08-15T14:00:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="owner_scan+fvls_press_post",
        entries=[
            _e(1, "Zhdanov Ivan", seeded=True),
            _e(2, "Bochkarev Alexander", seeded=True),
            _e(3, "Ivanov Vitaly"),
            _e(4, "Andronov Evgenii", place=3, seeded=True, ru="Евгений Андронов"),
            _e(5, "Semenov Filipp", place=1, ru="Филипп Семенов"),
            _e(6, "Savichev Matvey", place=2, seeded=True, ru="Матвей Савичев"),
        ],
    ),
    # --- Open / Masters medals from FVLS press (no IWWF final sheet for these heats) ---
    _h(
        "d3-wb-open-f-final1",
        disc=WB, klass="Open", sex="f", rnd="final", idx=1,
        when="2026-08-15T15:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Vorobeva Valentina", place=1, ru="Валентина Воробьева"),
            _e(2, "Zvezdova Aleksandra", place=2, ru="Александра Звездова"),
            _e(3, "Shvedova Daria", place=3, ru="Дарья Шведова"),
        ],
    ),
    _h(
        "d3-wb-open-m-final1",
        disc=WB, klass="Open", sex="m", rnd="final", idx=1,
        when="2026-08-15T15:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Khudnitskiy Georgiy", place=1, ru="Георгий Худницкий"),
            _e(2, "Likhtarev Georgii", place=2, ru="Георгий Лихтарёв"),
            _e(3, "Zhivaev Viacheslav", place=3, ru="Вячеслав Живаев"),
        ],
    ),
    _h(
        "d3-wb-o30-f-final1",
        disc=WB, klass="O30", sex="f", rnd="final", idx=1,
        when="2026-08-15T16:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Shupliakova Anastasia", place=1, seeded=True, ru="Анастасия Шуплякова"),
            _e(2, "Petrova Valentina", place=2, seeded=True, ru="Валентина Петрова"),
            _e(3, "Amelchenko Evgeniya", place=3, seeded=True, ru="Евгения Амельченко"),
        ],
    ),
    _h(
        "d3-wb-o30-m-final1",
        disc=WB, klass="O30", sex="m", rnd="final", idx=1,
        when="2026-08-15T16:30:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Kuzmin Ivan", place=1, seeded=True, ru="Иван Кузьмин"),
            _e(2, "Simonov Evgeniy", place=2, seeded=True, ru="Евгений Симонов"),
            _e(3, "Kozlov Denis", place=3, seeded=True, ru="Денис Козлов"),
        ],
    ),
    _h(
        "d3-ws-o30-f-final1",
        disc=WS, klass="O30", sex="f", rnd="final", idx=1,
        when="2026-08-15T11:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Terekhova Anastasia", place=1, seeded=True, ru="Анастасия Терехова"),
            _e(2, "Sadovnikova Lidia", place=2, seeded=True, ru="Лидия Садовникова"),
            _e(3, "Shelkova Aleksandra", place=3, seeded=True, ru="Александра Шелкова"),
        ],
    ),
    _h(
        "d3-ws-o30-m-final1",
        disc=WS, klass="O30", sex="m", rnd="final", idx=1,
        when="2026-08-15T12:30:00+03:00", engine=SURF, chief=CJ_SU, scorer=SC_SU,
        source="fvls_press_post", time_inferred=True,
        entries=[
            _e(1, "Zhdanov Ivan", place=1, seeded=True, ru="Иван Жданов"),
            _e(2, "Solovev Andrei Alex", place=2, seeded=True, ru="Андрей Соловьев"),
            _e(3, "Krasnikov Dmitrii", place=3, seeded=True, ru="Дмитрий Красников"),
        ],
    ),
    _h(
        "d3-wb-o40-m-final1",
        disc=WB, klass="O40", sex="m", rnd="final", idx=1,
        when="2026-08-15T17:00:00+03:00", engine=BOAT, chief=CJ_WB, scorer=SC_WB,
        source="owner_podium", time_inferred=True,
        entries=[
            _e(1, "Chernov Dmitry", place=1, seeded=True, ru="Дмитрий Чернов"),
            _e(2, "Matveev Konstantin", place=2, seeded=True, ru="Константин Матвеев"),
            _e(3, "Dementev Alexey", place=3, seeded=True, ru="Алексей Дементьев"),
        ],
    ),
]

ROUND_TITLE = {"qual": "квалификация", "sf": "полуфинал", "final": "финал"}

# FVLS press 15.08.2026: «Мастерс» without O30/O40 split → O30 (ADR-0007).
# Dual ranking: same athlete can medal in Open and Masters (Terekhova / Sadovnikova wakesurf).
# O40 veterans WB boat podium given by owner (Chernov / Matveev / Dementev); they also appear on Open qual start lists.
GAPS = [
    "Junior Men Wakeboard qualifications — старт-лист, без баллов",
    "Open Men Wakeboard qualifications — старт-листы 5 заездов, без баллов",
    "Open Men Wakesurf qualifications — старт-листы, без баллов",
    "U14 / U18 Wakeskim qualifications — старт-листы, без баллов",
    "Финалы: места из поста ФВЛС и пьедестала O40, баллов финала на сканах не было",
    "O40 ветераны: только вейкборд-катер муж., без баллов и без старт-листа отдельного заезда",
    "Старт-лист финала Open WB в сканах не было — только пьедестал ФВЛС",
]

FVLS_EVENT_BLURB = (
    "Чемпионат и Первенство России 2026 по воднолыжному спорту "
    "(вейкборд-катер, wakesurf / катер-доска-длинная, wakeskim / катер-доска-короткая). "
    "Оз. Нижний Кабан, Казань. Более 96 спортсменов из 17 регионов. "
    "Категории: U14 (до 15), U18 (до 19), Open, Мастерс (O30), Ветераны (O40, вейкборд-катер). "
    "Итоговые места — по официальному посту ФВЛС от 15.08.2026 и пьедесталу O40. "
    "Бумажные протоколы заездов: Not homologated."
)
