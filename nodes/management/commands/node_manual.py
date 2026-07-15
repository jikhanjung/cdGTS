"""
노드 매뉴얼 생성 — 카테고리별 NodeType 레퍼런스를 마크다운으로 방출.

손으로 쓴 매뉴얼은 금세 낡는다. 단일 진리원은 **시드(→DB)** 와 **커널 코드**이므로 거기서 조립한다:
  - NodeType.description · params_schema(+`help`) · Port          ← DB (seed/02_nodes.json 이 원본)
  - 어떤 커널이 이 slug 를 처리하나 + 그 커널 docstring            ← engine.kernels.kernel_for()
  - 실제로 어느 그래프가 몇 개 쓰나                                 ← graph.NodeInstance

산문을 채우는 곳은 이 파일이 아니라 **시드의 `description`/`help` 필드와 커널 docstring** 이다.
(JSON 에 주석 *문법* 은 없지만 `params_schema` 는 JSONField 라 `help` 같은 키를 자유롭게 넣을 수 있다.
 단 fixture `fields` **최상위**에 모델에 없는 키를 넣으면 loaddata 가 DeserializationError 를 낸다.)

⚠️ **갓 시드한 DB 에 대고 돌릴 것** — 운영 DB 로 생성하면 "사용처"에 사용자 fork(P05)가 섞여 문서가 DB 마다
달라진다. 시스템 시드만 담긴 DB 라야 재현 가능하다:

    DATABASE_PATH=/tmp/fresh.sqlite3 python manage.py migrate --noinput
    DATABASE_PATH=/tmp/fresh.sqlite3 python manage.py seed --mode=replace
    DATABASE_PATH=/tmp/fresh.sqlite3 python manage.py seed_demo
    DATABASE_PATH=/tmp/fresh.sqlite3 python manage.py node_manual

(운영 DB 를 `cp` 로 복사해 쓰지 말 것 — WAL 모드라 `-wal`/`-shm` 없이 복사하면 torn copy 가 된다.)

Usage: manage.py node_manual [--out docs/node-manual.md] [--print]
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils import timezone

from engine.kernels import kernel_for
from graph.models import NodeInstance
from nodes.models import NodeType

HEADER = """# 노드 매뉴얼 — cdGTS

<!-- 생성된 문서입니다. 손으로 고치지 마세요 — `manage.py node_manual` 이 덮어씁니다.
     산문을 고치려면 seed/02_nodes.json 의 description/params_schema.help 또는 engine/kernels.py 의
     커널 docstring 을 고치고 재생성하세요. -->

> **자동 생성** (`manage.py node_manual`) — 시드(NodeType·Port·params_schema) × 커널 코드 × 실제 사용처를 조립.
> 목적: 어떤 노드가 무슨 기능을 갖는지 한눈에 보고 **무엇이 정말 필요한지·무엇이 더 필요한지** 판단하기 위한 것.
> 개념 지도는 [concept-map](concept-map.md) · 카테고리 모델은 [tier-category-model](tier-category-model.md).
"""

CATEGORY_BLURB = {
    "data": "관측·저작된 값이 들어오는 leaf. 커널 없이 `params.distribution` 을 방출하는 것이 기본 "
            "(`calibration-constant`·`radiometric-uPb` 만 예외 — 공유 계통원 태그를 실어 방출).",
    "process": "상류 분포를 받아 계산하는 노드. 커널이 없으면 pass-through(= 의미론적/구조적 노드).",
    "reference": "인용 provenance. `cite` 엣지로 데이터/모델 노드를 가리킨다(값을 나르지 않는다).",
}


def _props(nt):
    ps = nt.params_schema or {}
    return ps.get("properties", ps) if isinstance(ps, dict) else {}


class Command(BaseCommand):
    help = "카테고리별 노드 매뉴얼을 마크다운으로 생성한다 (시드 + 커널 + 사용처)."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="docs/node-manual.md")
        # NOTE: 플래그 이름을 `--stdout` 으로 두면 안 된다 — BaseCommand.execute() 가 options["stdout"] 을
        # OutputWrapper 로 씌우려다 bool 을 받고 터진다.
        parser.add_argument("--print", action="store_true", dest="to_stdout", help="파일 대신 표준출력으로")

    def handle(self, *args, **opts):
        usage = defaultdict(list)
        for ni in NodeInstance.objects.select_related("node_type", "graph"):
            usage[ni.node_type.slug].append(ni.graph.slug)

        types = list(NodeType.objects.prefetch_related("ports").order_by("category", "slug"))
        by_cat = defaultdict(list)
        for nt in types:
            by_cat[nt.category].append(nt)

        out = [HEADER]
        out.append(f"> 생성: {timezone.now():%Y-%m-%d} · NodeType **{len(types)}** 개 "
                   f"· 사용 중 **{sum(1 for t in types if usage[t.slug])}** 개 "
                   f"· **미사용 {sum(1 for t in types if not usage[t.slug])}** 개\n")

        # --- 요약 표 (전체 조망 — "무엇이 필요한가" 판단용) ---
        out.append("## 요약\n")
        out.append("| 노드 | 카테고리 | 커널 | 포트 (in → out) | 인스턴스 |")
        out.append("|---|---|---|---|---|")
        for nt in types:
            label, _ = kernel_for(nt.category, nt.slug)
            ins = [p.name for p in nt.ports.all() if p.direction == "in"]
            outs = [p.name for p in nt.ports.all() if p.direction == "out"]
            n = len(usage[nt.slug])
            cnt = f"**{n}**" if n else "— **미사용**"
            out.append(f"| `{nt.slug}` | {nt.category} | `{label}` | "
                       f"{', '.join(ins) or '—'} → {', '.join(outs) or '—'} | {cnt} |")
        out.append("")

        dead = [t.slug for t in types if not usage[t.slug]]
        if dead:
            out.append(f"> ⚠️ **어떤 그래프도 쓰지 않는 타입**: {', '.join(f'`{s}`' for s in dead)}. "
                       f"의도된 여지인지, 정리 대상인지 검토 필요.\n")

        # --- 카테고리별 상세 ---
        for cat in ("data", "process", "reference"):
            if cat not in by_cat:
                continue
            out.append(f"## {cat}\n")
            if CATEGORY_BLURB.get(cat):
                out.append(f"> {CATEGORY_BLURB[cat]}\n")
            for nt in by_cat[cat]:
                label, note = kernel_for(nt.category, nt.slug)
                graphs = usage[nt.slug]
                out.append(f"### `{nt.slug}`\n")
                if (nt.description or "").strip():
                    out.append(f"{nt.description.strip()}\n")
                else:
                    out.append("*(description 없음 — 시드에 채워 넣을 것)*\n")

                out.append(f"- **커널**: `{label}`")
                if note:
                    first = note.splitlines()[0].strip()
                    out.append(f"  - {first}")
                if graphs:
                    tally = ", ".join(f"{g} ×{graphs.count(g)}" for g in sorted(set(graphs)))
                    out.append(f"- **사용**: {len(graphs)}개 인스턴스 — {tally}")
                else:
                    out.append("- **사용**: ⚠️ **없음** (어떤 그래프도 이 타입을 쓰지 않는다)")

                ports = list(nt.ports.all())
                if ports:
                    out.append("- **포트**:")
                    for p in sorted(ports, key=lambda p: (p.direction, p.order)):
                        multi = " · multiple" if p.multiple else ""
                        out.append(f"  - `{p.name}` ({p.direction}, {p.datatype}{multi})")

                props = _props(nt)
                if props:
                    out.append("- **파라미터**:")
                    for k, v in props.items():
                        v = v if isinstance(v, dict) else {}
                        t = v.get("type", "?")
                        choices = v.get("enum") or v.get("choices")
                        ch = f" ∈ {{{', '.join(map(str, choices))}}}" if choices else ""
                        h = (v.get("help") or "").strip()
                        out.append(f"  - `{k}` ({t}{ch})" + (f" — {h}" if h else " — *(help 없음)*"))
                out.append("")

        text = "\n".join(out).rstrip() + "\n"
        if opts["to_stdout"]:
            self.stdout.write(text)
            return
        with open(opts["out"], "w") as f:
            f.write(text)
        self.stderr.write(f"wrote {opts['out']} — NodeType {len(types)}, 미사용 {len(dead)}")
