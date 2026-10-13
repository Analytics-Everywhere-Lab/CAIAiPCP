"""Quantitative Bipolar Argumentation Framework (QBAF) over care options.

Each handling option is a claim node ("this option belongs in the care plan")
with a neutral base score. Every active argument is a node; it supports or
attacks its option, or another argument when ``target_arg_id`` is set (e.g.
clinician feedback rebutting one specific argument). Final strengths use
quadratic energy semantics (Potyka, 2018), the update SEMV's A-QBAF propagator
applies, generalised here to multi-level graphs by iterating to a fixed point.

An argument's base score is its verified validity weighted by how much it
matters for this patient, both judged when the option's arguments are verified
together as a group:
- relevance: points about the patient's main risks and stated goals count in
  full; secondary points count less, generic or speculative ones least. Without
  this, every option collects a similar number of pros and cons of similar
  validity, they cancel out, and every option lands near 0.5.
- repetition: a point already made by an earlier argument adds corroboration,
  not a second full vote.
- rebuttal: when an argument answers an opposing one (a support showing that a
  concern is manageable), it also attacks that argument, so answered concerns
  weigh less.

Human contestation enters the framework directly: rejected arguments leave the
graph, edited ones are re-verified, and clinician-authored arguments blend the
verifier's validity with a prior of clinician authority.
"""
import hashlib
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from arguments import active_arguments, is_human_authored, option_id, option_index
from env_config import HUMAN_TRUST_PRIOR, HUMAN_TRUST_WEIGHT
from state import Argument
from utils import clip_text

OPTION_BASE_SCORE = 0.5
RELEVANCE_WEIGHTS = {"high": 1.0, "moderate": 0.65, "low": 0.3}
DUPLICATE_WEIGHT = 0.35

# (lower bound, tier key, label shown in the care plan)
TIERS = [
    (0.70, "recommended", "Recommended"),
    (0.55, "conditional", "Recommended with conditions"),
    (0.45, "uncertain", "Clinical judgment required"),
    (0.30, "deferred", "Not recommended at this time"),
    (0.00, "not_recommended", "Not recommended"),
]


TIER_LABELS = {key: label for _, key, label in TIERS}


def tier_for(strength: float) -> Dict[str, str]:
    for bound, key, label in TIERS:
        if strength >= bound:
            return {"tier": key, "tier_label": label}
    return {"tier": TIERS[-1][1], "tier_label": TIERS[-1][2]}


def argument_weighting(arg: Argument, duplicate: bool = False) -> Tuple[float, float]:
    """(validity, weight) of an argument; its base score is their product.

    An argument not yet verified for relevance keeps its full weight."""
    validity = arg.validity_score if arg.validity_score is not None else 0.5
    weight = RELEVANCE_WEIGHTS.get(arg.relevance or "", 1.0)
    if is_human_authored(arg):
        validity = HUMAN_TRUST_WEIGHT * HUMAN_TRUST_PRIOR + (1.0 - HUMAN_TRUST_WEIGHT) * validity
        weight = max(weight, RELEVANCE_WEIGHTS["moderate"])  # the clinician chose to raise it
    if duplicate:
        weight *= DUPLICATE_WEIGHT
    return validity, weight


def argument_base_score(arg: Argument, duplicate: bool = False) -> float:
    validity, weight = argument_weighting(arg, duplicate)
    return validity * weight


def is_duplicate(arg: Argument, active_ids) -> bool:
    return bool(arg.same_as) and arg.same_as != arg.arg_id and arg.same_as in active_ids


def _h(value: float) -> float:
    positive = max(value, 0.0)
    return positive ** 2 / (1.0 + positive ** 2)


def _quadratic_energy(base: float, energy: float) -> float:
    score = base + (1.0 - base) * _h(energy) - base * _h(-energy)
    return max(0.0, min(1.0, score))


def propagate(nodes: Dict[str, Dict[str, Any]], edges: List[Dict[str, str]],
              max_iter: int = 200, tol: float = 1e-9) -> Dict[str, float]:
    """Iterate the quadratic energy update to a fixed point.

    Acyclic graphs (the normal case) converge exactly after depth + 1 rounds;
    the iteration cap only matters for cyclic argument chains."""
    incoming: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for edge in edges:
        incoming[edge["to"]].append(edge)
    strength = {node_id: node["base"] for node_id, node in nodes.items()}
    for _ in range(max_iter):
        updated = {}
        for node_id, node in nodes.items():
            energy = sum(
                strength[edge["from"]] * (1.0 if edge["relation"] == "support" else -1.0)
                for edge in incoming[node_id]
            )
            updated[node_id] = _quadratic_energy(node["base"], energy)
        delta = max((abs(updated[key] - strength[key]) for key in updated), default=0.0)
        strength = updated
        if delta < tol:
            break
    return strength


def build_graph(options: List[str], arguments: List[Argument]):
    """Return (nodes, edges, option_of) for the active arguments."""
    nodes: Dict[str, Dict[str, Any]] = {}
    for index, option in enumerate(options):
        nodes[option_id(index)] = {"kind": "option", "base": OPTION_BASE_SCORE, "label": option}
    active = [arg for arg in active_arguments(arguments) if arg.arg_id]
    active_ids = {arg.arg_id for arg in active}
    edges: List[Dict[str, str]] = []
    targets: Dict[str, str] = {}
    for arg in active:
        idx = option_index(options, arg.parent_option)
        if arg.target_arg_id in active_ids and arg.target_arg_id != arg.arg_id:
            target = arg.target_arg_id
        elif idx is not None:
            target = option_id(idx)
        else:
            continue  # its option no longer exists
        nodes[arg.arg_id] = {"kind": "argument", "base": argument_base_score(arg, is_duplicate(arg, active_ids))}
        targets[arg.arg_id] = target
        edges.append({
            "from": arg.arg_id,
            "to": target,
            "relation": "support" if arg.argument_type == "support" else "attack",
        })
    # Rebuttals found by the group verification: answering an argument weakens it.
    for arg in active:
        for answered in arg.rebuts or []:
            if arg.arg_id in nodes and answered in nodes and answered != arg.arg_id:
                edges.append({"from": arg.arg_id, "to": answered, "relation": "attack", "kind": "rebuttal"})

    def option_of(arg_id: str) -> Optional[str]:
        seen = set()
        node = arg_id
        while node in targets and node not in seen:
            seen.add(node)
            node = targets[node]
        return node if node in nodes and nodes[node]["kind"] == "option" else None

    return nodes, edges, option_of


def evaluate_qbaf(options: List[str], arguments: List[Argument]) -> Dict[str, Any]:
    """Evaluate the QBAF, write final strengths onto the arguments, and summarise.

    Each argument's contribution is the change in its option's strength when
    the argument is removed (removal-based attribution), which is what the plan
    writer and the UI use to explain why an option ranks where it does."""
    nodes, edges, option_of = build_graph(options, arguments)
    strength = propagate(nodes, edges)

    by_id = {arg.arg_id: arg for arg in arguments if arg.arg_id}
    active_ids = {node_id for node_id, node in nodes.items() if node["kind"] == "argument"}
    for arg in arguments:
        arg.strength = strength.get(arg.arg_id) if arg.arg_id in nodes else None

    argument_rows: Dict[str, Dict[str, Any]] = {}
    for node_id, node in nodes.items():
        if node["kind"] != "argument":
            continue
        target_option = option_of(node_id)
        contribution = 0.0
        if target_option is not None:
            reduced_nodes = {key: value for key, value in nodes.items() if key != node_id}
            reduced_edges = [edge for edge in edges if node_id not in (edge["from"], edge["to"])]
            without = propagate(reduced_nodes, reduced_edges)
            contribution = strength[target_option] - without[target_option]
        argument_rows[node_id] = {
            "base": round(node["base"], 4),
            "strength": round(strength[node_id], 4),
            "contribution": round(contribution, 4),
            "option_id": target_option,
            "target": next(edge["to"] for edge in edges if edge["from"] == node_id),
        }

    option_rows = []
    for index, option in enumerate(options):
        oid = option_id(index)
        attached = [
            (by_id[arg_id], row) for arg_id, row in argument_rows.items()
            if row["option_id"] == oid and arg_id in by_id
        ]
        supports = sorted(
            [pair for pair in attached if pair[1]["contribution"] >= 0],
            key=lambda pair: pair[1]["contribution"], reverse=True,
        )
        attacks = sorted(
            [pair for pair in attached if pair[1]["contribution"] < 0],
            key=lambda pair: pair[1]["contribution"],
        )
        option_strength = strength[oid]
        decisiveness = abs(option_strength - 0.5) * 2.0
        grounding = _grounding([arg for arg, _ in attached], active_ids)
        option_rows.append({
            "option_id": oid,
            "option": option,
            "strength": round(option_strength, 4),
            # How decisively the arguments settle this option, scaled by how well
            # grounded they are: a clear verdict from weak arguments is not confident,
            # and a balanced verdict from sound arguments is moderately confident.
            "confidence": round(grounding * (0.5 + 0.5 * decisiveness), 4),
            "decisiveness": round(decisiveness, 4),
            "grounding": round(grounding, 4),
            **tier_for(option_strength),
            "support_count": sum(1 for arg, _ in attached if arg.argument_type == "support"),
            "attack_count": sum(1 for arg, _ in attached if arg.argument_type == "attack"),
            "top_supports": [_driver(arg, row) for arg, row in supports[:3]],
            "top_attacks": [_driver(arg, row) for arg, row in attacks[:3]],
        })
    ranked = sorted(option_rows, key=lambda row: row["strength"], reverse=True)
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank

    confidence = (
        sum(row["confidence"] for row in option_rows) / len(option_rows) if option_rows else 0.0
    )
    summary = {
        "semantics": "quadratic_energy",
        "options": option_rows,
        "arguments": argument_rows,
        "edges": edges,
        "decision_confidence": round(confidence, 2),
    }
    summary["signature"] = hashlib.sha1(
        json.dumps({"options": [(row["option_id"], row["strength"]) for row in option_rows],
                    "arguments": argument_rows}, sort_keys=True).encode()
    ).hexdigest()[:16]
    return summary


def _grounding(arguments: List[Argument], active_ids) -> float:
    """Relevance-weighted mean validity of an option's arguments (0 without any)."""
    pairs = [argument_weighting(arg, is_duplicate(arg, active_ids)) for arg in arguments]
    total = sum(weight for _, weight in pairs)
    return sum(validity * weight for validity, weight in pairs) / total if total else 0.0


def _driver(arg: Argument, row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "arg_id": arg.arg_id,
        "content": arg.content,
        "stance": arg.argument_type,
        "role": arg.agent_role or "General",
        "source": arg.source,
        "strength": row["strength"],
        "contribution": row["contribution"],
    }


def qbaf_delta(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two QBAF evaluations at the option level."""
    if not previous:
        return {"has_previous": False, "options": [], "ranking_changed": False,
                "tier_changed": False, "options_added": [], "options_removed": [],
                "max_strength_shift": 0.0}
    before = {row["option"]: row for row in previous.get("options", [])}
    after = {row["option"]: row for row in current.get("options", [])}
    rows = []
    for option, row in after.items():
        old = before.get(option)
        rows.append({
            "option_id": row["option_id"],
            "option": option,
            "strength_before": old["strength"] if old else None,
            "strength_after": row["strength"],
            "tier_before": old["tier"] if old else None,
            "tier_after": row["tier"],
            "rank_before": old.get("rank") if old else None,
            "rank_after": row.get("rank"),
        })
    common = [option for option in after if option in before]
    order_before = sorted(common, key=lambda option: before[option]["strength"], reverse=True)
    order_after = sorted(common, key=lambda option: after[option]["strength"], reverse=True)
    shifts = [
        abs(row["strength_after"] - row["strength_before"])
        for row in rows if row["strength_before"] is not None
    ]
    return {
        "has_previous": True,
        "options": rows,
        "ranking_changed": order_before != order_after,
        "tier_changed": any(
            row["tier_before"] is not None and row["tier_before"] != row["tier_after"] for row in rows
        ),
        "options_added": [option for option in after if option not in before],
        "options_removed": [option for option in before if option not in after],
        "max_strength_shift": round(max(shifts, default=0.0), 4),
    }


def qbaf_prompt_summary(qbaf: Optional[Dict[str, Any]], max_drivers: int = 3, max_chars: int = 220) -> str:
    """Render the evaluated QBAF as compact text for LLM prompts."""
    if not qbaf:
        return "No argument evaluation available."
    lines = []
    for row in sorted(qbaf.get("options", []), key=lambda r: r.get("rank", 0)):
        lines.append(
            f"{row['option_id']} [{row['tier_label']}, strength {row['strength']:.2f}] {row['option']}"
        )
        if row.get("review"):
            lines.append(f"   Verification panel: {clip_text(row['review'], 2 * max_chars)}")
        for driver in row["top_supports"][:max_drivers]:
            lines.append(f"   + {driver['arg_id']} ({driver['contribution']:+.2f}) {clip_text(driver['content'], max_chars)}")
        for driver in row["top_attacks"][:max_drivers]:
            lines.append(f"   - {driver['arg_id']} ({driver['contribution']:+.2f}) {clip_text(driver['content'], max_chars)}")
    return "\n".join(lines)
