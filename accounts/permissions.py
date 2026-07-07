"""Central ratify authorization (P05.4). One place, so interval-scoping (P05 §확장) grafts here later."""
from chrono.models import Authority

GOVERNANCE_KINDS = {Authority.Kind.ICS, Authority.Kind.SUBCOMMISSION}


def can_ratify(user, proposal=None):
    """
    A user may ratify if they hold a Membership in a governance Authority (ICS / subcommission).
    MVP = global (single ICS Authority). LATER: also require the authority's scope_unit to cover
    `proposal.affected` — hence proposal is already threaded through this signature.
    """
    if not (user and user.is_authenticated):
        return False
    return user.memberships.filter(authority__kind__in=GOVERNANCE_KINDS).exists()
