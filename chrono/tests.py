import pytest
from django.core.management import call_command

from chrono.models import Boundary, Rank, Unit


@pytest.fixture
def seeded(db):
    call_command("loaddata", "01_chrono", verbosity=0)


def test_fixture_loads_icc_boundaries(seeded):
    # ICS chart.ttl 확장: 예제 3 + period+/finer 경계. 예제 슬러그는 보존.
    assert Boundary.objects.count() == 175
    assert {"base-triassic", "base-proterozoic", "base-cambrian"} <= set(
        Boundary.objects.values_list("slug", flat=True)
    )


def test_dual_naming(db):
    u = Unit.objects.create(slug="induan", name="Induan", rank=Rank.AGE)
    assert u.chronostratigraphic_name == "Induan Stage"
    assert u.geochronologic_name == "Induan Age"


def test_separates_and_hierarchy(seeded):
    bt = Boundary.objects.get(slug="base-triassic")
    assert bt.definition_type == Boundary.DefinitionType.GSSP
    assert bt.below.name == "Changhsingian"
    assert bt.above.name == "Induan"
    # 위계: Induan(Age) < Lower Triassic(Epoch) < Triassic(Period)
    # (early-triassic 중복 제거 → induan 은 chart.ttl 정본 lowertriassic 아래)
    assert bt.above.parent.name == "Lower Triassic"
    assert bt.above.parent.parent.name == "Triassic"


def test_gssa_has_no_stratotype(seeded):
    bp = Boundary.objects.get(slug="base-proterozoic")
    assert bp.definition_type == Boundary.DefinitionType.GSSA
    assert not hasattr(bp, "stratotype")


def test_gssp_stratotype(seeded):
    bt = Boundary.objects.get(slug="base-triassic")
    assert bt.stratotype.name.startswith("Meishan D")
    assert bt.ratifications.first().year == 2001
