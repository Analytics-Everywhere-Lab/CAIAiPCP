"""A scripted stand-in for the Ollama /api/generate endpoint.

It is installed in place of ``requests.post`` inside llm_caller, so tests run
the real call_llm / call_llm_stream / call_llm_json code paths. Responses are
chosen from distinctive phrases of each prompt.
"""
import json
import re
from typing import Callable, Dict, List, Optional

PLAN_MARKDOWN = """## Care Plan Summary
The patient lives alone after a recent fall and wishes to remain at home. The plan prioritises home safety [REF-1].

## Goals of Care
- Prevent falls over the next six months
- Maintain independence in daily activities

## Recommended Interventions
### Option 1: Home safety assessment and modification
Recommended: grab bars and rails reduce fall risk [REF-1].

### Option 2: Transition to assisted living
Clinical judgment required: keep as a fallback if falls continue.

## Implementation Plan
| Action | Responsible | Timeline | Notes |
|---|---|---|---|
| Home safety assessment | Occupational Therapist | Week 1 | Stairs and bathroom |

## Risk Management
| Risk | Mitigation | Owner |
|---|---|---|
| Falls on stairs | Install rails | Occupational Therapist |

## Monitoring and Follow-up
- Weekly nurse check for the first month

## Care Team Coordination
The Registered Nurse coordinates care with the family.
"""


class FakeResponse:
    def __init__(self, text: str, stream: bool):
        self._text = text
        self._stream = stream

    def raise_for_status(self):
        return None

    def json(self):
        return {"response": self._text, "done": True, "done_reason": "stop"}

    def iter_lines(self):
        words = re.findall(r"\S+\s*|\s+", self._text) or [""]
        for word in words:
            yield json.dumps({"response": word, "done": False}).encode()
        yield json.dumps({"response": "", "done": True, "done_reason": "stop"}).encode()


class FakeOllama:
    def __init__(self):
        self.calls: List[Dict] = []
        self.strategy_response: Optional[Dict] = None  # override the revision-strategy answer
        self.feedback_ops: Optional[Callable[[str], Dict]] = None  # override feedback interpretation
        self.fail_json = False

    def count(self, phrase: str) -> int:
        return sum(1 for call in self.calls if phrase in call["prompt"])

    def post(self, url, json=None, stream=False, **kwargs):  # noqa: A002 - mirrors requests.post
        payload = json or {}
        prompt = payload.get("prompt", "")
        self.calls.append({"prompt": prompt, "format": payload.get("format"), "stream": payload.get("stream")})
        text = self.respond(prompt)
        if self.fail_json and text.lstrip().startswith(("{", "[")):
            text = "Sorry, I cannot produce that."  # every structured answer fails, in JSON mode or not
        return FakeResponse(text, bool(payload.get("stream")))

    @staticmethod
    def verify_group(prompt: str) -> Dict:
        """Judge an option's arguments the way a careful panel would for the test patient:
        home-based supports are central, the generic cost concern is minor at home and
        is answered by the first support, and a repeated point is marked as such."""
        option = re.search(r"^Care option (O\d+): (.+)$", prompt, re.MULTILINE)
        at_home = bool(option) and "Home safety" in option.group(2)
        rows = re.findall(r"^(A\d+) \| (support|challenge) \| ([^|]+?) \| (.+)$", prompt, re.MULTILINE)
        results, seen, rebuttals = [], {}, []
        first_support = next((arg_id for arg_id, stance, _, _ in rows if stance == "support"), None)
        for arg_id, stance, author, text in rows:
            lowered = text.lower()
            if author.strip() == "clinician" or any(k in lowered for k in ("stay home", "age in place", "prefers")):
                validity, relevance = 0.85, "high"
            elif stance == "support":
                validity, relevance = (0.86, "high") if at_home else (0.6, "moderate")
            elif "costly" in lowered:
                validity, relevance = (0.55, "low") if at_home else (0.75, "high")
            else:
                validity, relevance = 0.7, "moderate"
            key = (stance, lowered)
            results.append({"id": arg_id, "validity": validity, "relevance": relevance, "same_as": seen.get(key),
                            "refs": [1], "note": f"{'Central' if relevance == 'high' else 'Secondary'} point for this patient."})
            seen.setdefault(key, arg_id)
            if at_home and first_support and stance == "challenge" and "costly" in lowered and not rebuttals:
                rebuttals.append({"from": first_support, "to": arg_id, "strength": "full",
                                  "reason": "Grab bars and rails are low-cost changes."})
        summary = ("Strong fit: it targets her falls risk at home, as she wishes; cost is minor." if at_home
                   else "Weak fit: relocation conflicts with her wish to stay at home.")
        return {"arguments": results, "rebuttals": rebuttals, "summary": summary}

    # ------------------------------------------------------------------ script

    def respond(self, prompt: str) -> str:
        dump = __import__("json").dumps
        if "assess the severity" in prompt:
            return "Moderate"
        if "generate 3-5 specific search queries" in prompt:
            return "elderly fall prevention home\ngeriatric mild cognitive impairment living alone"
        if "Then screen each candidate as a careful clinician would" in prompt:
            return dump({"options": [
                {"option": "Home safety assessment and modification", "fit": "strong",
                 "why": "Targets her falls risk and keeps her at home, as she wishes."},
                {"option": "Transition to assisted living", "fit": "possible",
                 "why": "A fallback if falls continue despite home changes."},
                {"option": "Immediate nursing home admission", "fit": "poor",
                 "why": "Conflicts with her wish to stay at home; her needs do not require it."},
            ]})
        if "generate 1-2 specific handling options" in prompt:
            return "Option 1: Home safety assessment and modification\nOption 2: Transition to assisted living"
        if "structured analysis in JSON format" in prompt:
            return dump({"medical_conditions": ["mild cognitive impairment"], "safety_risks": ["falls"],
                         "psychosocial_needs": ["social isolation"], "functional_status": {"mobility": "assisted"},
                         "complexity_level": "moderate", "coordination_intensity": "moderate"})
        if "assembling an optimal interdisciplinary healthcare team" in prompt:
            return dump({"selected_team": [{"role": "Registered Nurse", "reasoning": "medication"},
                                           {"role": "Occupational Therapist", "reasoning": "home safety"}],
                         "team_size": 2, "overall_strategy": "home-focused"})
        if "explain why this specific healthcare team" in prompt:
            return "A nurse and an occupational therapist cover medication and home safety."
        if "Lessons learned from earlier clinician reviews of other patients" in prompt:
            ids = re.findall(r"\[(mem_[0-9a-f]+)\]", prompt)
            if not ids:
                return dump({"arguments": []})
            return dump({"arguments": [{"memory_id": ids[0], "option_id": "O2", "stance": "attack",
                                        "content": "The patient prefers to age in place, so relocation should come last."}]})
        if "Assess this care option for this patient from your perspective" in prompt:
            role = re.search(r"As a ([A-Za-z ]+?) named", prompt) or re.search(r"You are a ([A-Za-z ]+?) named", prompt)
            option = "home" if "Home safety" in prompt.split("Care Option Being Evaluated:")[-1] else "facility"
            return (f"Support: The {option} option addresses the falls risk from a "
                    f"{role.group(1) if role else 'clinical'} perspective.\n"
                    f"Challenge: The {option} option may be costly and disruptive for the patient.")
        if "verification panel for an interdisciplinary aging-in-place care plan" in prompt:
            return dump(self.verify_group(prompt))
        if "contestation interpreter" in prompt:
            if self.feedback_ops is not None:
                return dump(self.feedback_ops(prompt))
            return dump({"operations": []})
        if "You are deciding how to update a care plan" in prompt:
            if self.strategy_response is not None:
                return dump(self.strategy_response)
            suggested = re.search(r"A rule-based check suggests (\w+) on ([\w, ]+)\.", prompt)
            strategy = suggested.group(1) if suggested else "full_regeneration"
            sections = [part.strip() for part in suggested.group(2).split(",")] if suggested else []
            return dump({"strategy": strategy, "sections": sections,
                         "rationale": "The change is local, so only the affected sections are rewritten."})
        if "You are revising one section" in prompt:
            title = re.search(r'Rewrite ONLY the section "([^"]+)"', prompt).group(1)
            return f"## {title}\n\nRevised {title.lower()} reflecting the clinician's feedback [REF-1]."
        if "Rewrite the presentation of this aging-in-place care plan" in prompt:
            return PLAN_MARKDOWN.replace("The patient lives alone", "In plain language: the patient lives alone")
        if "write a professional, evidence-based care plan" in prompt:
            return PLAN_MARKDOWN
        if "A reviewing clinician proposed a new care option" in prompt:
            return ("Support: [Registered Nurse] Day programs provide supervision and social contact.\n"
                    "Challenge: [Occupational Therapist] Transport to the program may be tiring.")
        if "reflection module of an aging-in-place care-planning assistant" in prompt:
            op_ids = re.findall(r"^(H\w+) \|", prompt, re.MULTILINE) or ["H1"]
            return dump({
                "episodic": {"observation": "For an older adult living alone with falls, the clinician removed "
                                            "the relocation argument because the patient prefers to age in place.",
                             "profile_pattern": "lives alone, falls", "confidence": 0.85, "op_ids": op_ids[:2]},
                "failures": [{"failure_type": "irrelevant_argument", "stage": "argument_generation",
                              "trigger_pattern": "patient prefers to remain at home",
                              "lesson": "Avoid arguing for relocation when the patient prefers to age in place "
                                        "and home risks can be mitigated.",
                              "recommended_action": "Prioritise home supports before relocation.",
                              "polarity": "avoid", "confidence": 0.8, "op_ids": op_ids[:1]}],
                "semantic": None,
            })
        if "You verify lessons before they are stored" in prompt:
            ids = re.findall(r'"candidate_id": "([^"]+)"', prompt)
            return dump({"results": [{"candidate_id": cid, "verified": True, "reason": "grounded"} for cid in ids]})
        if "Synthesize ONE general rule" in prompt:
            return dump({"trigger_pattern": "older adults who prefer to age in place",
                         "lesson": "Weigh home-based supports before relocation when the patient prefers to age in place.",
                         "recommended_action": "Offer relocation only when home risks cannot be mitigated.",
                         "polarity": "do", "confidence": 0.82})
        if "consistent with EVERY source observation" in prompt:
            return dump({"consistent_with_all": True, "reason": "consistent"})
        if "Classify the semantic relation" in prompt:
            pairs = re.findall(r'"pair_id": "(\d+)"', prompt)
            return dump({"results": [{"pair_id": pid, "relation": "unrelated"} for pid in pairs]})
        if "Update the running summary" in prompt:
            return "The clinician asked about fall prevention and medication timing."
        if "assisting a clinician with one patient's aging-in-place care plan" in prompt:
            return "Argument A1 supports home safety; the plan recommends grab bars first."
        return "OK"
