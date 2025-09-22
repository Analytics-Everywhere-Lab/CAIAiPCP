import json
from uuid import uuid4
import gradio as gr
from graph import create_care_plan_graph
from state import Argument
import time
from markdown import heading, examples, usage
import re


class CarePlanGradioInterface:
    """
    Argumentative Elderly Care Plan Generator with Gradio Interface
    Refactored to reduce nesting and extract long logic into composable helpers.
    """

    NODE_STATUS = {
        "rag_retrieval": "🔍 Retrieving information...",
        "care_plan_generation": "🤖 Generating care plan...",
        "argument_generation": "🗣️ Preparing plan rationale...",
        "human_review": "👨‍⚕️ Waiting for human review...",
        "argument_validation": "✅ Validating arguments...",
        "plan_revision": "📝 Revising care plan...",
        "scheduling": "📋 Checking provider availability..."
    }


    def __init__(self):
        self.graph = None
        self.current_state = None
        self.current_thread_id = None
        self.app = None
        self.review_complete = False
        self.interface = None

    def _initial_state(self, patient_info):
        return {
            # Core patient and care planning data
            "patient_info": patient_info,
            "handling_options": [],
            "arguments": [],
            "validated_arguments": [],
            "revised_care_plan": {},
            # Human interaction and feedback
            "human_feedback": None,
            "current_step": "rag_retrieval",
            "human_review_complete": False,
            "user_action": None,
            # RAG and document retrieval
            "retrieved_documents": [],
            "search_queries": [],
            "rag_context": "",
            "adaptive_retrieval_summary": None,
            "document_references": [],
            "cited_documents": set(),
            # Multi-agent healthcare team management
            "custom_team_requirements": None,
            "team_selection_rationale": None,
            "patient_analysis": None,
            "healthcare_team": [],
            "agent_arguments_tracking": {},
            "team_selection_logs": None,
            # Streaming and progress tracking
            "enable_streaming": True,
            "options_generation_progress": None,
            "argument_generation_progress": None,
            "current_argument_stream": None,
            "validation_progress": None,
            "current_validation_stream": None,
            "streaming_chunk": None,
            "partial_response": None,
            "rag_progress": None,
        }

    def format_arguments_display(self, state):
        """
        Enhanced display showing LLM's team selection reasoning
        """
        if not self._debug_state(state, "format_arguments_display"):
            return "Error: Invalid state"

        display_text = "## 🏥 Multi-Agents Collaboration\n\n"

        # Show the AI's reasoning for team selection
        if "team_selection_rationale" in state:
            display_text += "### 🤖 AI Team Selection Rationale:\n"
            display_text += f"_{state['team_selection_rationale']}_\n\n"

        # Show patient analysis if available
        if "patient_analysis" in state:
            analysis = state["patient_analysis"]
            display_text += "### 📊 Patient Complexity Assessment:\n"
            display_text += f"- **Complexity Level:** {analysis.get('complexity_level', 'Unknown')}\n"
            display_text += f"- **Coordination Needs:** {analysis.get('coordination_intensity', 'Unknown')}\n"

            if analysis.get("safety_risks"):
                display_text += f"- **Key Safety Risks:** {', '.join(analysis['safety_risks'][:3])}\n"

            if analysis.get("medical_conditions"):
                display_text += f"- **Primary Conditions:** {', '.join(analysis['medical_conditions'][:3])}\n"

            display_text += "\n---\n\n"

        # Display team composition
        if "healthcare_team" in state and state["healthcare_team"]:
            display_text += "### 👥 Healthcare Team Assembled:\n"
            for member in state["healthcare_team"]:
                # Show expertise areas for each member
                expertise_preview = ", ".join(member["expertise"][:3])
                display_text += f"- **{member['name']}** - {member['role']}\n"
                display_text += f"  _Expertise: {expertise_preview}_\n"
            display_text += "\n---\n\n"

        # Rest of the display (arguments by option)
        display_text += "## 📋 Professional Perspectives on Care Options\n\n"

        for i, option in enumerate(state["handling_options"]):
            display_text += f"### Option {i+1}: {option}\n\n"

            option_args = [
                arg for arg in state["arguments"] if arg.parent_option == option
            ]

            # Group by agent
            agent_grouped = {}
            for arg in option_args:
                if hasattr(arg, "agent_name"):
                    agent_key = f"{arg.agent_role}"
                    if agent_key not in agent_grouped:
                        agent_grouped[agent_key] = {"support": [], "attack": []}
                    agent_grouped[agent_key][arg.argument_type].append(arg)

            # Display grouped arguments
            for agent_key, args_dict in agent_grouped.items():
                if args_dict["support"] or args_dict["attack"]:
                    display_text += f"**💬 {agent_key}:**\n"

                    if args_dict["support"]:
                        display_text += "  ✅ *Supports:*\n"
                        for arg in args_dict["support"]:
                            arg_idx = state["arguments"].index(arg)
                            clean_content = arg.content
                            if (
                                hasattr(arg, "agent_role")
                                and f"[{arg.agent_role}]" in clean_content
                            ):
                                clean_content = clean_content.replace(
                                    f"[{arg.agent_role}]", ""
                                ).strip()
                            display_text += f"  - `[{arg_idx}]` {clean_content}\n"

                    if args_dict["attack"]:
                        display_text += "  ⚠️ *Challenges:*\n"
                        for arg in args_dict["attack"]:
                            arg_idx = state["arguments"].index(arg)
                            clean_content = arg.content
                            if (
                                hasattr(arg, "agent_role")
                                and f"[{arg.agent_role}]" in clean_content
                            ):
                                clean_content = clean_content.replace(
                                    f"[{arg.agent_role}]", ""
                                ).strip()
                            display_text += f"  - `[{arg_idx}]` {clean_content}\n"

                    display_text += "\n"

            display_text += "---\n\n"

        # Team participation summary
        if "agent_arguments_tracking" in state:
            display_text += "### 📊 Team Participation Summary:\n"
            for agent_name, agent_args in state["agent_arguments_tracking"].items():
                support_count = sum(1 for arg in agent_args if arg["type"] == "support")
                attack_count = sum(
                    1 for arg in agent_args if arg["type"] == "challenge"
                )
                display_text += f"- **{agent_name}**: {support_count} support, {attack_count} challenge\n"
            display_text += "\n"

        display_text += "---\n\n"
        display_text += "### 🎯 **Available Actions:**\n\n"
        display_text += "- ✅ Type **`accept`** to accept all arguments and continue\n"
        display_text += "- ❌ Type **`remove [index]`** to remove an argument\n"
        display_text += (
            "- ➕ Type **`add support [option_number] [argument]`** to add support\n"
        )
        display_text += "- ⚠️ Type **`add challenge [option_number] [argument]`** to add challenge\n\n"
        display_text += "💡 **Note:** The AI selected this specific team based on the patient's unique needs and complexity.\n"

        return display_text

    def format_care_plan_for_chat(self, final_state):
        """Format the final care plan as chat messages with collapsible citations"""
        if not final_state or "revised_care_plan" not in final_state:
            return []

        care_plan = final_state["revised_care_plan"]
        messages = []

        # Ensure all required fields exist with defaults
        care_plan.setdefault("decision_confidence", 0.5)
        care_plan.setdefault(
            "argument_summary",
            {
                "total_arguments": 0,
                "support_arguments": 0,
                "attack_arguments": 0,
                "avg_validity": 0,
            },
        )
        care_plan.setdefault("total_documents_retrieved", 0)
        care_plan.setdefault("documents_cited", 0)
        care_plan.setdefault("recommendations", "No recommendations generated.")
        care_plan.setdefault("cited_document_ids", [])

        # Message 1: Header and metrics
        metrics_content = f"""## 📋 Final Care Plan Generated
        **Decision Confidence:** {care_plan['decision_confidence']:.1%}

        **Argument Analysis:**
        - Total Arguments Evaluated: {care_plan['argument_summary']['total_arguments']}
        - Supporting Arguments: {care_plan['argument_summary']['support_arguments']}
        - Challenging Arguments: {care_plan['argument_summary']['attack_arguments']}
        - Average Validity Score: {care_plan['argument_summary']['avg_validity']:.2f}

        **Evidence Base:**
        - Documents Retrieved: {care_plan.get('total_documents_retrieved', 0)}
        - Documents Cited: {care_plan.get('documents_cited', 0)}"""

        messages.append({"role": "assistant", "content": metrics_content})

        # Message 2: Main recommendations
        recommendations = care_plan["recommendations"]

        # Extract citations from recommendations
        ref_pattern = r"\[REF-(\d+)\]"
        cited_refs = re.findall(ref_pattern, recommendations)
        cited_ref_ids = list(set(int(ref) for ref in cited_refs))

        # Clean recommendations (remove [REF-X] tags for cleaner display)
        clean_recommendations = re.sub(ref_pattern, "", recommendations)

        recommendations_content = (
            f"""## 📝 Care Plan Recommendations {clean_recommendations}"""
        )

        messages.append({"role": "assistant", "content": recommendations_content})

        # Message 3: Collapsible citations for each cited document
        ref_data = {}
        if "document_references" in final_state and cited_ref_ids:
            # Store reference data
            for ref in final_state["document_references"]:
                ref_data[ref["id"]] = ref

            # Group citations by category for better organization
            primary_citations = []
            supporting_citations = []

            for ref_id in sorted(cited_ref_ids):
                if ref_id in ref_data:
                    ref = ref_data[ref_id]
                    citation_text = f"""**[REF-{ref_id}]**
                    📍 Search Query: {ref['search_query']}
                    📊 Relevance Score: {ref['similarity_score']:.1%}
                    {'-' * 40}
                    {ref['full_content']}"""

                    if ref["similarity_score"] > 0.7:
                        primary_citations.append(citation_text)
                    else:
                        supporting_citations.append(citation_text)

            # Add primary citations if any
            if primary_citations:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "\n\n".join(primary_citations),
                        "metadata": {
                            "title": f"📚 Primary Evidence ({len(primary_citations)} documents)"
                        },
                    }
                )

            # Add supporting citations if any
            if supporting_citations:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "\n\n".join(supporting_citations),
                        "metadata": {
                            "title": f"🟢 Support Evidence ({len(supporting_citations)} documents)"
                        },
                    }
                )

        # Message 4: Search queries used (collapsible)
        if "search_queries" in final_state and final_state["search_queries"]:
            queries_content = "**Queries used to retrieve medical knowledge:**\n\n"
            for i, query in enumerate(final_state["search_queries"][:10], 1):
                queries_content += f"{query}\n"

            messages.append(
                {
                    "role": "assistant",
                    "content": queries_content,
                    "metadata": {
                        "title": f"🔍 Search Queries ({len(final_state['search_queries'])} queries)"
                    },
                }
            )

        # Message 5: Adaptive retrieval details (if available, collapsible)
        if final_state["adaptive_retrieval_summary"] is not None:
            summary = final_state["adaptive_retrieval_summary"]
            adaptive_content = f"""**Adaptive Evidence Enhancement Results:**
                - Arguments Enhanced: {summary['arguments_enhanced']}
                - Average Score Improvement: {summary['average_score_improvement']:.3f}
                **Enhanced Arguments:**"""

            for detail in summary.get("details", []):
                adaptive_content += f"\n\n**Argument:** {detail['argument'][:100]}..."
                adaptive_content += f"\n• Initial Score: {detail['initial_score']:.2f}"
                adaptive_content += f"\n• Updated Score: {detail['updated_score']:.2f}"
                adaptive_content += (
                    f"\n• Evidence Documents Used: {detail['evidence_used']}"
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": adaptive_content,
                    "metadata": {"title": "🔄 Adaptive Evidence Retrieval"},
                }
            )

        # Message 6: Completion notification
        messages.append(
            {
                "role": "assistant",
                "content": "✅ **Care plan generation complete!**\n\n💡 *Click on the collapsible sections above to view citations and evidence details.*",
            }
        )

        # Message 7: Scheduling
        sched_summary = final_state.get("scheduling_summary")
        sched_slots   = final_state.get("scheduling_slots") or {}
        if sched_summary or sched_slots:
            # build markdown
            lines = []
            lines.append("## 📅 Scheduling — Provider Availability\n")
            if sched_summary:
                lines.append(sched_summary.strip())
                lines.append("")
            if not sched_slots:
                lines.append("> No availability returned.")
            else:
                lines.append("| Provider | Next slots |")
                lines.append("|---|---|")
                for provider, items in sched_slots.items():
                    if not items:
                        lines.append(f"| {provider} | *(no slots)* |")
                        continue
                    previews = []
                    for itm in items[:3]:
                        if isinstance(itm, str):
                            try:
                                itm = json.loads(itm)
                            except json.JSONDecodeError:
                                itm = {}
                        ts = itm.get("time_slot") or ""
                        sn = itm.get("slot_number")
                        previews.append(f"`#{sn} — {ts}`" if sn is not None else f"`{ts}`")
                    lines.append(f"| {provider} | " + " ".join(previews) + " |")

            messages.append({
                "role": "assistant",
                "content": "\n".join(lines),
                "metadata": {
                    "title": f"📅 Provider Availability ({len(sched_slots)} providers)"
                }
            })

        return messages, ref_data

    def process_user_input_msg(self, message):
        """Message-format handler used by the Chatbot events"""
        if not self._debug_state(self.current_state, "process_user_input_msg"):
            return {"role": "assistant", "content": "Error: Invalid state"}

        if not self.current_state:
            return {
                "role": "assistant",
                "content": "No active review session. Please start a care plan generation first.",
            }

        msg = message.strip().lower()
        if msg == "accept":
            self.current_state["human_review_complete"] = True
            self.current_state["current_step"] = "argument_validation"
            self.review_complete = True
            return {
                "role": "assistant",
                "content": "✅ Arguments accepted. Proceeding to validation...",
            }

        if msg.startswith("remove "):
            try:
                idx = int(msg.split()[1])
                if 0 <= idx < len(self.current_state["arguments"]):
                    removed_arg = self.current_state["arguments"].pop(idx)
                    response = f"❌ Removed argument: {removed_arg.content}\n\n"
                    response += self.format_arguments_display(self.current_state)
                    return {"role": "assistant", "content": response}
                return {
                    "role": "assistant",
                    "content": "Invalid argument index. Please check the numbers in square brackets.",
                }
            except Exception:
                return {
                    "role": "assistant",
                    "content": "Invalid remove command. Use format: 'remove [index]'",
                }

        if msg.startswith("add support ") or msg.startswith("add challenge "):
            try:
                parts = message.split(maxsplit=3)
                arg_type = parts[1]
                option_idx = int(parts) - 1
                arg_content = parts
                if 0 <= option_idx < len(self.current_state["handling_options"]):
                    new_arg = Argument(
                        content=arg_content,
                        argument_type=arg_type,
                        parent_option=self.current_state["handling_options"][
                            option_idx
                        ],
                    )
                    self.current_state["arguments"].append(new_arg)
                    response = f"✅ Added {arg_type} argument: {arg_content}\n\n"
                    response += self.format_arguments_display(self.current_state)
                    return {"role": "assistant", "content": response}
                return {
                    "role": "assistant",
                    "content": f"Invalid option number. Please use 1-{len(self.current_state['handling_options'])}",
                }
            except Exception:
                return {
                    "role": "assistant",
                    "content": "Invalid add command. Use format: 'add [support/challenge] [option_number] [argument text]'",
                }

        return {
            "role": "assistant",
            "content": "Invalid command. Please use 'accept', 'remove [index]', or 'add [support/challenge] [option] [text]'",
        }


    def _reset_session(self):
        self.review_complete = False
        self.current_state = None
        self.current_thread_id = None
        self.graph = None

    def _yield_ui(self, title, chat_history, msg_visible=True, refs=None):
        return (
            gr.update(visible=True, value=title),
            chat_history,
            gr.update(visible=msg_visible),
            {} if refs is None else refs,
        )

    def _on_enter_node(self, node_name, chat_history):
        if node_name in self.NODE_STATUS:
            chat_history.append(
                {"role": "assistant", "content": self.NODE_STATUS[node_name]}
            )
        return chat_history

    def _handle_rag_retrieval(self, node_state, chat_history, msg_idx):
        updates = []
        if (
            "search_queries" in node_state
            and node_state.get("search_queries")
            and node_state.get("_rag_announced") is None
        ):
            query_count = len(node_state.get("search_queries", []))
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"📚 Searching medical knowledge...\n\n🔍 Generated {query_count} search queries...",
            }
            updates.append(
                self._yield_ui("## Retrieving Medical Knowledge", chat_history)
            )
            node_state["_rag_announced"] = True

        if "rag_progress" in node_state:
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"📚 Retrieving medical knowledge...\n\n{node_state['rag_progress']}",
            }
            updates.append(self._yield_ui("## Generating Care Plan", chat_history))

        if "retrieved_documents" in node_state and not node_state.get("_docs_done"):
            doc_count = len(node_state.get("retrieved_documents", []))
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"📚 Processing {doc_count} medical documents...",
            }
            updates.append(self._yield_ui("## Processing Documents", chat_history))

            if doc_count > 0:
                doc_summary = f"Successfully retrieved {doc_count} relevant documents.\n\n**Search queries used:**\n"
                for q in node_state.get("search_queries", [])[:5]:
                    doc_summary += f"{q}\n"

                chat_history.append(
                    {
                        "role": "assistant",
                        "content": doc_summary,
                        "metadata": {"title": f"📚 Retrieved {doc_count} Documents"},
                    }
                )
                chat_history.append(
                    {
                        "role": "assistant",
                        "content": "🔄 Generating care plan options based on retrieved knowledge...",
                    }
                )
                updates.append(self._yield_ui("## Generating Care Plan", chat_history))
            node_state["_docs_done"] = True
        return updates, chat_history

    def _handle_care_plan_generation(self, node_state, chat_history, msg_idx):
        updates = []
        if (
            "handling_options" not in node_state
            and "options_generation_progress" not in node_state
        ):
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": "🔄 Analyzing patient needs and generating personalized care options...",
            }
            updates.append(self._yield_ui("## Generating Options", chat_history))

        if "options_generation_progress" in node_state:
            progress = node_state["options_generation_progress"]
            option_count = progress.count("Option")
            status_msg = f"🔄 Generating care plan options... ({option_count} options so far)\n\n"
            if len(progress) > 100:
                status_msg += "**Preview:**\n" + f"{progress[:500]}..."
            else:
                status_msg += progress
            chat_history[msg_idx] = {"role": "assistant", "content": status_msg}
            updates.append(self._yield_ui("## Generating Care Plan", chat_history))

        if node_state.get("handling_options") and not node_state.get("_options_done"):
            options_count = len(node_state["handling_options"])
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"✅ Generated {options_count} care plan options\n 💭 Generating arguments...",
            }
            updates.append(self._yield_ui("## Generating Arguments...", chat_history))
            node_state["_options_done"] = True
        return updates, chat_history

    def _handle_argument_generation(self, node_state, chat_history, msg_idx):
        updates = []
        total_expected_args = len(node_state.get("handling_options", [])) * 2
        current_args = len(node_state.get("arguments", []))

        if (
            current_args == 0
            and "argument_generation_progress" not in node_state
            and not node_state.get("_args_started")
        ):
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"💭 Starting argument generation (0/{total_expected_args} arguments)...",
            }
            updates.append(self._yield_ui("## Generating Arguments...", chat_history))
            node_state["_args_started"] = True

        if "argument_generation_progress" in node_state:
            progress_msg = node_state["argument_generation_progress"]
            progress_msg = f"[{current_args}/{total_expected_args}] {progress_msg}"
            if "current_argument_stream" in node_state:
                preview = node_state["current_argument_stream"]
                if "Support:" in preview:
                    preview_text = preview.split("Support:")[-1][:150]
                    progress_msg += (
                        f"\n\n**Generating support argument:**\n_{preview_text}..._"
                    )
                elif "Challenge:" in preview:
                    preview_text = preview.split("Challenge:")[-1][:150]
                    progress_msg += (
                        f"\n\n**Generating challenge argument:**\n_{preview_text}..._"
                    )
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"💭 {progress_msg}",
            }
            updates.append(self._yield_ui("## Generating Arguments...", chat_history))
        elif "arguments" in node_state and current_args > 0:
            support_count = sum(
                1 for a in node_state["arguments"] if a.argument_type == "support"
            )
            attack_count = sum(
                1 for a in node_state["arguments"] if a.argument_type == "attack"
            )
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"💭 Generating arguments... [{current_args}/{total_expected_args}]\n\n🟢 Support: {support_count} | ⚠️ Challenge: {attack_count}",
            }
            updates.append(self._yield_ui("## Generating Arguments...", chat_history))

        if (
            node_state.get("arguments")
            and current_args >= total_expected_args - 1
            and not node_state.get("_args_done")
        ):
            total_args = len(node_state["arguments"])
            support_count = sum(
                1 for a in node_state["arguments"] if a.argument_type == "support"
            )
            attack_count = sum(
                1 for a in node_state["arguments"] if a.argument_type == "attack"
            )
            chat_history[msg_idx] = {
                "role": "assistant",
                "content": f"✅ Generated {total_args} arguments: ({support_count} support, {attack_count} challenge)\n📋 Please review the arguments below:",
            }
            updates.append(self._yield_ui("## Review Arguments...", chat_history))

            # Team selection logs (collapsible)
            if node_state.get("team_selection_logs"):
                team_logs_content = "**🤖 AI Team Selection Process:**\n\n"
                for log_line in node_state["team_selection_logs"]:
                    team_logs_content += f"{log_line}\n"
                if "team_selection_rationale" in node_state:
                    team_logs_content += f"\n**Selection Rationale:**\n_{node_state['team_selection_rationale']}_\n"
                if "patient_analysis" in node_state:
                    analysis = node_state["patient_analysis"]
                    team_logs_content += "\n**Patient Complexity Assessment:**\n"
                    team_logs_content += f"- Complexity Level: {analysis.get('complexity_level', 'Unknown')}\n"
                    team_logs_content += f"- Coordination Needs: {analysis.get('coordination_intensity', 'Unknown')}\n"
                    if analysis.get("safety_risks"):
                        team_logs_content += f"- Key Safety Risks: {', '.join(analysis['safety_risks'][:3])}\n"
                    if analysis.get("medical_conditions"):
                        team_logs_content += f"- Primary Conditions: {', '.join(analysis['medical_conditions'][:3])}\n"
                if node_state.get("healthcare_team"):
                    team_logs_content += "\n**Final Healthcare Team:**\n"
                    for member in node_state["healthcare_team"]:
                        team_logs_content += (
                            f"\n**{member['name']}** - {member['role']}\n"
                        )
                        expertise_preview = ", ".join(member["expertise"][:3])
                        team_logs_content += f"  _Expertise: {expertise_preview}_\n"
                if node_state.get("agent_arguments_tracking"):
                    team_logs_content += "\n**Team Participation Summary:**\n"
                    for agent_name, agent_args in node_state[
                        "agent_arguments_tracking"
                    ].items():
                        support_count = sum(
                            1 for arg in agent_args if arg["type"] == "support"
                        )
                        attack_count = sum(
                            1
                            for arg in agent_args
                            if arg["type"] in ("attack", "challenge")
                        )
                        team_logs_content += f"- {agent_name}: {support_count} support, {attack_count} challenge arguments\n"

                chat_history.append(
                    {
                        "role": "assistant",
                        "content": team_logs_content,
                        "metadata": {
                            "title": f"🤖 AI Team Selection ({len(node_state.get('healthcare_team', []))} healthcare professionals)"
                        },
                    }
                )
                updates.append(self._yield_ui("## Review Arguments...", chat_history))

            node_state["_args_done"] = True

        return updates, chat_history

    def _enter_human_review(self, node_state, chat_history, msg_idx):
        chat_history[msg_idx] = {
            "role": "assistant",
            "content": "✨ Preparing arguments for your review...",
        }
        self.current_state = node_state.copy()
        review_message = self.format_arguments_display(self.current_state)
        chat_history.append({"role": "assistant", "content": review_message})
        return [
            self._yield_ui("## Preparing Review...", chat_history),
            self._yield_ui("## Review Arguments...", chat_history),
        ], chat_history

    def _debug_state(self, state, method_name):
        """Debug helper to validate state structure"""
        if state is None:
            print(f"ERROR in {method_name}: state is None!")
            return False
        if not isinstance(state, dict):
            print(f"ERROR in {method_name}: state is not a dict, it's {type(state)}")
            return False
        return True

    def stream_initial_generation(self, patient_info):
        chat_history = []
        try:
            # Initialize
            self.graph = create_care_plan_graph()
            self.current_thread_id = f"session_{uuid4().hex}"
            initial_state = self._initial_state(patient_info)
            cfg = {"configurable": {"thread_id": self.current_thread_id}}

            # Opening message
            chat_history.append(
                {
                    "role": "assistant",
                    "content": "🤖 Starting care plan generation...\n📚 Retrieving relevant medical knowledge from database...",
                }
            )
            yield self._yield_ui("## Generating Care Plan...", chat_history)

            reached_human_review = False
            current_message_idx = len(chat_history) - 1
            current_node = None

            for event in self.graph.stream(initial_state, cfg):
                for node_name, node_state in event.items():
                    if node_name != current_node:
                        current_node = node_name
                        chat_history = self._on_enter_node(node_name, chat_history)
                        current_message_idx = len(chat_history) - 1
                        yield self._yield_ui(
                            f"## Processing: {node_name.replace('_', ' ').title()}",
                            chat_history,
                        )

                    if node_name == "rag_retrieval":
                        updates, chat_history = self._handle_rag_retrieval(
                            node_state, chat_history, current_message_idx
                        )
                        for upd in updates:
                            yield upd

                    elif node_name == "care_plan_generation":
                        updates, chat_history = self._handle_care_plan_generation(
                            node_state, chat_history, current_message_idx
                        )
                        for upd in updates:
                            yield upd

                    elif node_name == "argument_generation":
                        updates, chat_history = self._handle_argument_generation(
                            node_state, chat_history, current_message_idx
                        )
                        for upd in updates:
                            yield upd

                    elif node_name == "human_review":
                        updates, chat_history = self._enter_human_review(
                            node_state, chat_history, current_message_idx
                        )
                        for upd in updates:
                            yield upd
                        reached_human_review = True
                        break

                if reached_human_review:
                    break

            if not reached_human_review or not self.current_state:
                chat_history.append(
                    {
                        "role": "assistant",
                        "content": "❌ Failed to reach human review stage.",
                    }
                )
                yield self._yield_ui("## Error", chat_history, msg_visible=False)
                return

        except Exception as e:
            chat_history.append(
                {
                    "role": "assistant",
                    "content": f"❌ Error generating care plan: {str(e)}\n\nPlease try again with different patient information or contact support if the issue persists.",
                }
            )
            yield self._yield_ui("## Error Occurred", chat_history, msg_visible=False)

    def generate_care_plan(self, patient_info):
        """Wrapper to run care plan generation with Gradio streaming"""
        # Validate input
        if not patient_info or not patient_info.strip():
            return (
                gr.update(visible=True, value="❌ Please enter patient information"),
                [
                    {
                        "role": "assistant",
                        "content": "❌ Please enter patient information",
                    }
                ],
                gr.update(visible=False),
                {},
            )

        # Reset and start a new session
        self._reset_session()
        yield from self.stream_initial_generation(patient_info)

    def respond(self, message, chat_history, ref_data):
        """Handle chat responses in message format"""
        chat_history.append({"role": "user", "content": message})

        if not self.review_complete:
            response = self.process_user_input_msg(message)
            chat_history.append(response)

            if self.review_complete:
                for updated_history, updated_refs in self.continue_after_review(
                    chat_history
                ):
                    # During processing after acceptance: hide the input
                    yield self._yield_ui(
                        "## Validating Arguments and Finalizing Care Plan...",
                        updated_history,
                        msg_visible=False,
                        refs=updated_refs,
                    )
                return
        else:
            response_content = "The care plan is complete. You can review the collapsible sections above for detailed evidence and citations."
            chat_history.append({"role": "assistant", "content": response_content})

        yield self._yield_ui(
            "## Finalized Care Plan",
            chat_history,
            msg_visible=True,
            refs=ref_data,
        )

    def _handle_argument_validation_node(self, node_state, history, processing_msg_idx):
        """Handle argument validation node updates"""
        updates = []

        # Initial validation message
        validation_msg = "🔍 Validating arguments with medical evidence..."

        # Check for validation progress
        if "validation_progress" in node_state:
            validation_msg += f"\n\n{node_state['validation_progress']}"
            history[processing_msg_idx] = {
                "role": "assistant",
                "content": validation_msg,
            }
            updates.append((history.copy(), {}))

        # Check for adaptive retrieval summary
        summary = node_state.get("adaptive_retrieval_summary")
        if summary is not None:
            progress_msg = "🔍 Validating arguments with medical evidence...\n\n"
            progress_msg += f"✅ Enhanced {summary.get('arguments_enhanced', 0)} arguments with additional evidence\n"
            progress_msg += f"📈 Average score improvement: {summary.get('average_score_improvement', 0):.3f}"

            history[processing_msg_idx] = {"role": "assistant", "content": progress_msg}
            updates.append((history.copy(), {}))

            # Add detailed summary as collapsible message
            if summary.get("details"):
                details_msg = "**Arguments Enhanced with Additional Evidence:**\n\n"
                for detail in summary["details"][:3]:  # Show first 3 for brevity
                    details_msg += f"• Initial Score: {detail['initial_score']:.2f} → {detail['updated_score']:.2f}\n"
                    details_msg += (
                        f"  Evidence documents used: {detail['evidence_used']}\n\n"
                    )

                history.append(
                    {
                        "role": "assistant",
                        "content": details_msg,
                        "metadata": {
                            "title": f"🔄 Adaptive Evidence Retrieval ({summary['arguments_enhanced']} arguments enhanced)"
                        },
                    }
                )
                updates.append((history.copy(), {}))

        # Check if validation is complete
        if "validated_arguments" in node_state:
            validated_count = len(node_state.get("validated_arguments", []))
            avg_validity = (
                sum(arg.validity_score for arg in node_state["validated_arguments"])
                / validated_count
                if validated_count
                else 0
            )

            completion_msg = f"✅ Validation complete!\n\n"
            completion_msg += f"• Arguments validated: {validated_count}\n"
            completion_msg += f"• Average validity score: {avg_validity:.2f}\n"
            completion_msg += f"• High validity (>0.8): {sum(1 for arg in node_state['validated_arguments'] if arg.validity_score > 0.8)}\n"
            completion_msg += f"• Moderate (0.5-0.8): {sum(1 for arg in node_state['validated_arguments'] if 0.5 <= arg.validity_score <= 0.8)}\n"
            completion_msg += f"• Low (<0.5): {sum(1 for arg in node_state['validated_arguments'] if arg.validity_score < 0.5)}"

            history[processing_msg_idx] = {
                "role": "assistant",
                "content": completion_msg,
            }
            updates.append((history.copy(), {}))

        return updates

    def _handle_plan_revision_node(self, node_state, history, processing_msg_idx):
        """Handle plan revision node updates with streaming"""
        updates = []

        # Initial message
        revision_msg = "📝 Generating personalized care plan recommendations..."
        history[processing_msg_idx] = {"role": "assistant", "content": revision_msg}
        updates.append((history.copy(), {}))

        # Handle streaming partial responses
        partial = node_state.get("partial_response")
        if partial:
            streaming_msg = "## 📝 Generating Care Plan...\n\n"

            # Determine what section is being generated based on content
            if len(partial) > 100:
                if "prioritized list" in partial.lower() or "1." in partial:
                    streaming_msg += "**Creating prioritized recommendations:**\n"
                elif "risk" in partial.lower():
                    streaming_msg += "**Adding risk mitigation strategies:**\n"
                elif "implementation" in partial.lower() or "steps" in partial.lower():
                    streaming_msg += "**Detailing implementation steps:**\n"
                elif (
                    "evidence" in partial.lower() or "justification" in partial.lower()
                ):
                    streaming_msg += "**Adding evidence-based justifications:**\n"
                else:
                    streaming_msg += "**Processing care plan details:**\n"

            # Show last 500 chars for context
            display_partial = partial[-500:] if len(partial) > 500 else partial
            streaming_msg += f"\n```\n{display_partial}\n```\n\n*...generating...*"

            history[processing_msg_idx] = {
                "role": "assistant",
                "content": streaming_msg,
            }
            updates.append((history.copy(), {}))

        # Check if revision is complete
        if "revised_care_plan" in node_state:
            care_plan = node_state["revised_care_plan"]

            completion_msg = "✅ Care plan generation complete!\n\n"
            completion_msg += f"• Decision confidence: {care_plan.get('decision_confidence', 0):.1%}\n"
            completion_msg += f"• Documents cited: {care_plan.get('documents_cited', 0)}/{care_plan.get('total_documents_retrieved', 0)}\n"
            completion_msg += "• Finalizing with citations..."

            history[processing_msg_idx] = {
                "role": "assistant",
                "content": completion_msg,
            }
            updates.append((history.copy(), {}))

        return updates

    def _format_final_care_plan(self, final_state, history):
        """Format and return the final care plan with all citations"""
        updates = []

        # Remove any temporary processing messages
        # Find the last processing message index
        processing_msg_idx = None
        for i in range(len(history) - 1, -1, -1):
            if history[i].get("role") == "assistant" and any(
                keyword in history[i].get("content", "")
                for keyword in ["Finalizing", "complete!", "Validation complete!"]
            ):
                processing_msg_idx = i
                break

        if processing_msg_idx is not None:
            # Remove processing message
            history = history[:processing_msg_idx]

        # Format the care plan messages
        care_plan_messages, ref_data = self.format_care_plan_for_chat(final_state)

        # Add each message individually with updates
        for msg in care_plan_messages:
            history.append(msg)
            updates.append((history.copy(), ref_data))

        return updates

    def _handle_scheduling_node(self, node_state, history, processing_msg_idx):
        """Handle scheduling node updates: show provider availability in a compact table"""
        updates = []

        # Initial message while fetching/formatting
        history[processing_msg_idx] = {
            "role": "assistant",
            "content": "📅 Checking provider availability..."
        }
        updates.append((history.copy(), {}))

        slots = node_state.get("scheduling_slots") or {}
        summary = (node_state.get("scheduling_summary") or "Availability retrieved.").strip()

        # Build a compact markdown table
        md = []
        md.append("## 📅 Scheduling — Provider Availability\n")
        md.append(summary)
        md.append("")

        if not slots:
            md.append("> No availability returned.")
        else:
            md.append("| Provider | Next slots |")
            md.append("|---|---|")
            for provider, items in slots.items():
                if not items:
                    md.append(f"| {provider} | *(no slots)* |")
                    continue

                # Show first 3 slots to keep it tidy
                previews = []
                for itm in items[:3]:
                    # If the returned slot is a JSON string, parse it into a dict
                    if isinstance(itm, str):
                        try:
                            itm = json.loads(itm)
                        except json.JSONDecodeError:
                            itm = {}  # fallback to empty dict if parsing fails

                    ts = itm.get("time_slot") or ""
                    sn = itm.get("slot_number")
                    previews.append(f"`#{sn} — {ts}`" if sn is not None else f"`{ts}`")

                md.append(f"| {provider} | " + "<br>".join(previews) + " |")

        history[processing_msg_idx] = {
            "role": "assistant",
            "content": "\n".join(md),
        }
        updates.append((history.copy(), {}))

        return updates


    def continue_after_review(self, history):
        """Refactored version that yields updates for each node individually"""
        if not self.review_complete or not self.current_state:
            yield history, {}
            return

        try:
            cfg = {"configurable": {"thread_id": self.current_thread_id}}

            # Update state for continuation
            self.current_state["human_review_complete"] = True
            self.current_state["current_step"] = "argument_validation"
            self.current_state["enable_streaming"] = True

            # Add initial processing message
            processing_msg_idx = len(history)
            history.append(
                {
                    "role": "assistant",
                    "content": "⏳ Processing your accepted arguments...",
                }
            )
            yield history, {}

            # Update graph state
            self.graph.update_state(
                cfg,
                {
                    "human_review_complete": True,
                    "current_step": "argument_validation",
                    "enable_streaming": True,
                },
            )

            # Track current node and final state
            current_node = None
            final_state = None
            nodes_completed = set()

            # Stream through the graph
            for event in self.graph.stream(None, cfg):
                for node_name, node_state in event.items():
                    # Track node changes
                    if node_name != current_node:
                        current_node = node_name

                        # Update message for new node
                        node_messages = {
                            "argument_validation": "🔍 Validating arguments with medical evidence...",
                            "plan_revision": "📝 Generating personalized care plan recommendations...",
                        }

                        if node_name in node_messages:
                            history[processing_msg_idx] = {
                                "role": "assistant",
                                "content": node_messages[node_name],
                            }
                            yield history, {}

                    # Handle argument validation node
                    if node_name == "argument_validation":
                        validation_updates = self._handle_argument_validation_node(
                            node_state, history, processing_msg_idx
                        )
                        for updated_history, refs in validation_updates:
                            yield updated_history, refs

                        # Mark as completed when done
                        if "validated_arguments" in node_state:
                            nodes_completed.add("argument_validation")

                    # Handle plan revision node
                    elif node_name == "plan_revision":
                        revision_updates = self._handle_plan_revision_node(
                            node_state, history, processing_msg_idx
                        )
                        for updated_history, refs in revision_updates:
                            yield updated_history, refs

                        if "revised_care_plan" in node_state:
                            nodes_completed.add("plan_revision")

                    # Handle scheduling node
                    elif node_name == "scheduling":
                        scheduling_updates = self._handle_scheduling_node(
                            node_state, history, processing_msg_idx
                        )
                        for updated_history, refs in scheduling_updates:
                            yield updated_history, refs

                        if "scheduling_slots" in node_state:
                            # mark scheduling as complete and set the final state here
                            nodes_completed.add("scheduling")
                            final_state = node_state


            # Format and yield final care plan if we have it
            if final_state and final_state.get("revised_care_plan"):
                # Brief finalization message
                history[processing_msg_idx] = {
                    "role": "assistant",
                    "content": "📋 Finalizing care plan with evidence citations...",
                }
                yield history, {}

                # Format and yield the final care plan
                final_updates = self._format_final_care_plan(final_state, history)
                for updated_history, refs in final_updates:
                    yield updated_history, refs

            else:
                # Error if we didn't get a final care plan
                history[processing_msg_idx] = {
                    "role": "assistant",
                    "content": "❌ Error: Unable to generate final care plan. The planning process did not complete successfully.",
                }
                yield history, {}

        except Exception as e:
            # Handle errors
            error_msg = f"❌ Error during care plan generation:\n\n{str(e)}\n\nPlease try again or contact support if the issue persists."

            if len(history) > 0 and history[-1]["role"] == "assistant":
                history[-1] = {"role": "assistant", "content": error_msg}
            else:
                history.append({"role": "assistant", "content": error_msg})

            yield history, {}
            return

    def create_interface(self):
        """Create the Gradio interface"""
        custom_css = """
        .gradio-container { font-family: 'Arial', sans-serif; }
        .markdown-text { line-height: 1.6; }
        """

        with gr.Blocks(
            title="Elderly Care Plan Generator",
            theme="shivi/calm_seafoam",
            css=custom_css,
        ) as self.interface:
            gr.Markdown("# 🏥 Argumentative Elderly Care Plan Generator")
            gr.Markdown(heading)

            with gr.Tab("🏠 Generate Care Plan"):
                patient_input = gr.Textbox(
                    label="Patient Information",
                    placeholder="Enter patient details including age, living situation, medical conditions, mobility issues, etc.",
                    lines=5,
                )
                generate_btn = gr.Button("Generate Care Plan", variant="primary")

                progress_display = gr.Markdown("", visible=False)

                chatbot = gr.Chatbot(
                    label="Care Plan Review",
                    height=1000,
                    type="messages",
                    elem_classes=["care-plan-chat"],
                    resizable=True,
                    show_copy_button=True,
                    show_label=False,
                    group_consecutive_messages=False,
                )

                msg = gr.Textbox(
                    label="Your Input",
                    placeholder="Type 'accept' to approve all, 'remove [index]' to remove, or 'add [support/challenge] [option_num] [text]' to add",
                    submit_btn=True,
                    stop_btn=True,
                )

                references_state = gr.State({})

                generate_btn.click(
                    self.generate_care_plan,
                    inputs=[patient_input],
                    outputs=[progress_display, chatbot, msg, references_state],
                )

                msg.submit(
                    self.respond,
                    inputs=[msg, chatbot, references_state],
                    outputs=[progress_display, chatbot, msg, references_state],
                )

            with gr.Tab("📋 Example Patients"):
                gr.Markdown(examples)

            with gr.Tab("ℹ️ How to Use"):
                gr.Markdown(usage)

            with gr.Row():
                toggle_dark = gr.Button(value="Toggle Dark")
                toggle_dark.click(
                    None,
                    js="""
                    () => { document.body.classList.toggle('dark'); }
                    """,
                )

        return self.interface

    def launch(self, share=False):
        """Launch the Gradio interface"""
        if not self.interface:
            self.create_interface()
        self.interface.queue()
        self.interface.launch(share=share)
