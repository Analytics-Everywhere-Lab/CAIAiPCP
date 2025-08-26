from uuid import uuid4
import gradio as gr
from graph import create_care_plan_graph
from state import Argument


class CarePlanGradioInterface:
    """
    Argumentative Elderly Care Plan Generator with Gradio Interface

    This system generates personalized care plans for elderly individuals using
    AI-driven argumentation with human-in-the-loop review via Gradio.

    The system will launch a web interface where you can:
    1. Enter patient information
    2. Review and modify generated arguments
    3. Get a comprehensive care plan with explanations
    """
    def __init__(self):
        self.graph = None
        self.current_state = None
        self.current_thread_id = None
        self.app = None
        self.review_complete = False
        self.interface = None

    def format_arguments_display(self, state):
        """
        Enhanced display showing LLM's team selection reasoning
        """
        display_text = "## 🏥 AI-Selected Healthcare Team Review\n\n"

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
                    agent_key = f"{arg.agent_name} ({arg.agent_role})"
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

    def process_user_input(self, message, history):
        """Process user commands during review"""
        if not self.current_state:
            return (
                "No active review session. Please start a care plan generation first."
            )

        message = message.strip().lower()

        if message == "accept":
            # Mark review as complete in the current state
            self.current_state["human_review_complete"] = True
            self.current_state["current_step"] = "argument_validation"
            self.review_complete = True
            return "✅ Arguments accepted. Proceeding to validation..."

        elif message.startswith("remove "):
            try:
                idx = int(message.split()[1])
                if 0 <= idx < len(self.current_state["arguments"]):
                    removed_arg = self.current_state["arguments"].pop(idx)
                    response = f"❌ Removed argument: {removed_arg.content}\n\n"
                    response += self.format_arguments_display(self.current_state)
                    return response
                else:
                    return "Invalid argument index. Please check the numbers in square brackets."
            except:
                return "Invalid remove command. Use format: 'remove [index]'"

        elif message.startswith("add support ") or message.startswith("add challenge "):
            try:
                parts = message.split(maxsplit=3)
                arg_type = parts[1]  # 'support' or 'challenge'
                option_idx = int(parts[2]) - 1
                arg_content = parts[3]

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
                    return response
                else:
                    return f"Invalid option number. Please use 1-{len(self.current_state['handling_options'])}"
            except:
                return "Invalid add command. Use format: 'add [support/challenge] [option_number] [argument text]'"

        else:
            return "Invalid command. Please use 'accept', 'remove [index]', or 'add [support/challenge] [option] [text]'"

    def create_interface(self):
        """Create the Gradio interface"""
        custom_css = """
        .gradio-container {
            font-family: 'Arial', sans-serif;
        }
        .markdown-text {
            line-height: 1.6;
        }
        """

        with gr.Blocks(
            title="Elderly Care Plan Generator", css=custom_css
        ) as self.interface:
            gr.Markdown("# 🏥 Argumentative Elderly Care Plan Generator")
            gr.Markdown(
                """
                This AI-powered system generates personalized care plans for elderly individuals using argumentation-based reasoning.
                The system will:
                1. Generate handling options based on patient information
                2. Create supporting and challenging arguments for each option
                3. Allow you to review and modify arguments
                4. Produce a comprehensive care plan with explanations
                """
            )

            with gr.Tab("🏠 Generate Care Plan"):
                patient_input = gr.Textbox(
                    label="Patient Information",
                    placeholder="Enter patient details including age, living situation, medical conditions, mobility issues, etc.",
                    lines=5,
                )

                generate_btn = gr.Button("Generate Care Plan", variant="primary")

                # Progress display
                progress_display = gr.Markdown("", visible=False)

                # Chat interface for human review - increased height
                chatbot = gr.Chatbot(
                    label="Care Plan Review",
                    height=600,
                    type="messages",  # Use messages format for metadata support
                    elem_classes=["care-plan-chat"],
                )

                msg = gr.Textbox(
                    label="Your Input",
                    placeholder="Type 'accept' to approve all, 'remove [index]' to remove, or 'add [support/challenge] [option_num] [text]' to add",
                    submit_btn=True,
                    stop_btn=True,
                )

                # Hidden state for storing references
                references_state = gr.State({})

                def format_care_plan_for_chat(final_state):
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
                    care_plan.setdefault(
                        "recommendations", "No recommendations generated."
                    )
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
                    import re

                    ref_pattern = r"\[REF-(\d+)\]"
                    cited_refs = re.findall(ref_pattern, recommendations)
                    cited_ref_ids = list(set(int(ref) for ref in cited_refs))

                    # Clean recommendations (remove [REF-X] tags for cleaner display)
                    clean_recommendations = re.sub(ref_pattern, "", recommendations)

                    recommendations_content = (
                        f"""## 📝 Care Plan Recommendations {clean_recommendations}"""
                    )

                    messages.append(
                        {"role": "assistant", "content": recommendations_content}
                    )

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
                    if (
                        "search_queries" in final_state
                        and final_state["search_queries"]
                    ):
                        queries_content = (
                            "**Queries used to retrieve medical knowledge:**\n\n"
                        )
                        for i, query in enumerate(
                            final_state["search_queries"][:10], 1
                        ):
                            queries_content += f"{i}. {query}\n"

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
                    if "adaptive_retrieval_summary" in final_state:
                        summary = final_state["adaptive_retrieval_summary"]
                        adaptive_content = f"""**Adaptive Evidence Enhancement Results:**
                        - Arguments Enhanced: {summary['arguments_enhanced']}
                        - Average Score Improvement: {summary['average_score_improvement']:.3f}
                        **Enhanced Arguments:**"""

                        for detail in summary.get("details", []):
                            adaptive_content += (
                                f"\n\n**Argument:** {detail['argument'][:100]}..."
                            )
                            adaptive_content += (
                                f"\n• Initial Score: {detail['initial_score']:.2f}"
                            )
                            adaptive_content += (
                                f"\n• Updated Score: {detail['updated_score']:.2f}"
                            )
                            adaptive_content += f"\n• Evidence Documents Used: {detail['evidence_used']}"

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

                    return messages, ref_data

                def format_arguments_display_as_message(state):
                    """Format arguments for display as a message"""
                    display_text = "## Generated Arguments for Review\n\n"

                    for i, option in enumerate(state["handling_options"]):
                        display_text += f"### Option {i+1}: {option}\n\n"
                        option_args = [
                            arg
                            for arg in state["arguments"]
                            if arg.parent_option == option
                        ]

                        # Group by type
                        support_args = [
                            arg for arg in option_args if arg.argument_type == "support"
                        ]
                        attack_args = [
                            arg for arg in option_args if arg.argument_type == "challenge"
                        ]

                        if support_args:
                            display_text += "**Support Arguments:**\n"
                            for arg in support_args:
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- [{arg_idx}] {arg.content}\n"
                            display_text += "\n"

                        if attack_args:
                            display_text += (
                                "**Challenge Arguments:**\n"
                            )
                            for arg in attack_args:
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- [{arg_idx}] {arg.content}\n"
                            display_text += "\n"

                    display_text += "\n---\n"
                    display_text += "**Available Actions:**\n"
                    display_text += (
                        "- Type 'accept' to accept all arguments and continue\n"
                    )
                    display_text += "- Type 'remove [index]' to remove an argument (e.g., 'remove 3')\n"
                    display_text += "- Type 'add support [option_number] [argument]' to add a support argument\n"
                    display_text += "- Type 'add challenge [option_number] [argument]' to add a challenge argument\n"

                    return {"role": "assistant", "content": display_text}

                def continue_after_review(history):
                    """Continue processing after human review is complete with streaming"""
                    if not self.review_complete or not self.current_state:
                        return history, {}

                    try:
                        # Create a new thread ID for the continuation
                        # This avoids any checkpointing issues
                        continuation_thread_id = f"continue_{uuid4().hex}"
                        cfg = {"configurable": {"thread_id": continuation_thread_id}}

                        # Make sure the state has human_review_complete = True
                        self.current_state["human_review_complete"] = True
                        self.current_state["current_step"] = "argument_validation"

                        # Enable streaming for final generation
                        self.current_state["enable_streaming"] = True

                        # Add initial processing message
                        processing_msg_idx = len(history)
                        history.append(
                            {
                                "role": "assistant",
                                "content": "⏳ Validating arguments and generating final care plan...",
                            }
                        )

                        # Create a new graph instance to avoid state contamination
                        continuation_graph = create_care_plan_graph()

                        # Create generator for streaming updates
                        def stream_updates():
                            nonlocal history
                            final_state = None
                            events_seen = []
                            current_node = None

                            # Track progress through nodes
                            node_messages = {
                                "argument_validation": "🔍 Validating arguments with medical evidence...",
                                "plan_revision": "📝 Generating personalized care plan recommendations...",
                            }

                            for event in continuation_graph.stream(
                                self.current_state, cfg
                            ):
                                print(
                                    f"Processing event after review: {list(event.keys())}"
                                )
                                events_seen.extend(list(event.keys()))

                                for node_name, node_state in event.items():
                                    # Update progress message for each node
                                    if node_name != current_node:
                                        current_node = node_name
                                        if node_name in node_messages:
                                            history[processing_msg_idx] = {
                                                "role": "assistant",
                                                "content": node_messages[node_name],
                                            }
                                            yield history, {}

                                    # Handle argument validation progress
                                    if node_name == "argument_validation":
                                        # Check if adaptive retrieval is happening
                                        if "adaptive_retrieval_summary" in node_state:
                                            summary = node_state[
                                                "adaptive_retrieval_summary"
                                            ]
                                            progress_msg = f"🔍 Validating arguments with medical evidence...\n\n"
                                            progress_msg += f"Enhanced {summary.get('arguments_enhanced', 0)} arguments with additional evidence"
                                            history[processing_msg_idx] = {
                                                "role": "assistant",
                                                "content": progress_msg,
                                            }
                                            yield history, {}

                                    # Stream partial responses during plan revision
                                    elif node_name == "plan_revision":
                                        # Check for streaming chunks
                                        if "streaming_chunk" in node_state:
                                            # Update the processing message with partial content
                                            if "partial_response" in node_state:
                                                partial = node_state["partial_response"]
                                                # Format partial response nicely
                                                streaming_msg = (
                                                    f"## 📝 Generating Care Plan...\n\n"
                                                )

                                                # Show a preview of what's being generated
                                                if len(partial) > 100:
                                                    # Extract sections if they exist
                                                    if "1." in partial:
                                                        streaming_msg += "**Generating recommendations:**\n"
                                                    elif "Risk" in partial:
                                                        streaming_msg += "**Adding risk mitigation strategies:**\n"
                                                    elif "Implementation" in partial:
                                                        streaming_msg += "**Detailing implementation steps:**\n"
                                                    else:
                                                        streaming_msg += "**Processing care plan details:**\n"

                                                # Add partial content (limit display length for better UX)
                                                display_partial = (
                                                    partial[-500:]
                                                    if len(partial) > 500
                                                    else partial
                                                )
                                                streaming_msg += f"\n{display_partial}"

                                                # Add a subtle indicator that generation is ongoing
                                                streaming_msg += (
                                                    "\n\n*...generating...*"
                                                )

                                                history[processing_msg_idx] = {
                                                    "role": "assistant",
                                                    "content": streaming_msg,
                                                }
                                                yield history, {}

                                        # Store final state
                                        final_state = node_state

                            print(f"Events processed: {events_seen}")

                            # Final formatting after streaming completes
                            if (
                                final_state
                                and "revised_care_plan" in final_state
                                and final_state["revised_care_plan"]
                            ):
                                # Remove the streaming/processing message
                                history = history[:processing_msg_idx]

                                # Add a brief transition message
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": "📕 Finalizing care plan with evidence citations...",
                                    }
                                )
                                yield history, {}

                                # Small delay for better UX
                                import time

                                time.sleep(0.5)

                                # Remove transition message
                                history = history[:-1]

                                # Format final care plan with collapsible citations
                                care_plan_messages, ref_data = (
                                    format_care_plan_for_chat(final_state)
                                )

                                # Add messages one by one with small delays for better streaming effect
                                for i, msg in enumerate(care_plan_messages):
                                    history.append(msg)
                                    # Yield after each message for progressive display
                                    yield history, ref_data

                                    # Small delay between messages for visual effect (optional)
                                    if i < len(care_plan_messages) - 1:
                                        time.sleep(0.1)

                            else:
                                # Error case - no valid final state
                                history[processing_msg_idx] = {
                                    "role": "assistant",
                                    "content": "❌ Error: Unable to generate final care plan. The planning process did not complete successfully.",
                                }
                                print(
                                    f"Final state issue - state exists: {final_state is not None}, "
                                    f"has care plan: {'revised_care_plan' in final_state if final_state else False}"
                                )
                                yield history, {}

                        # Return the generator for streaming
                        return stream_updates()

                    except Exception as e:
                        import traceback

                        error_details = traceback.format_exc()
                        print(f"Error in continue_after_review: {error_details}")

                        # Update the last message with error
                        if len(history) > 0 and history[-1]["role"] == "assistant":
                            history[-1] = {
                                "role": "assistant",
                                "content": f"❌ Error during care plan generation:\n\n{str(e)}\n\nPlease try again or contact support if the issue persists.",
                            }
                        else:
                            history.append(
                                {
                                    "role": "assistant",
                                    "content": f"❌ Error during processing: {str(e)}",
                                }
                            )

                        return history, {}

                def process_user_input_message(message, history):
                    """Process user commands during review - returns message format"""
                    if not self.current_state:
                        return {
                            "role": "assistant",
                            "content": "No active review session. Please start a care plan generation first.",
                        }

                    message_lower = message.strip().lower()

                    if message_lower == "accept":
                        self.current_state["human_review_complete"] = True
                        self.current_state["current_step"] = "argument_validation"
                        self.review_complete = True
                        return {
                            "role": "assistant",
                            "content": "✅ Arguments accepted. Proceeding to validation...",
                        }

                    elif message_lower.startswith("remove "):
                        try:
                            idx = int(message_lower.split()[1])
                            if 0 <= idx < len(self.current_state["arguments"]):
                                removed_arg = self.current_state["arguments"].pop(idx)
                                response = (
                                    f"❌ Removed argument: {removed_arg.content}\n\n"
                                )
                                response += self.format_arguments_display_as_message(
                                    self.current_state
                                )["content"]
                                return {"role": "assistant", "content": response}
                            else:
                                return {
                                    "role": "assistant",
                                    "content": "Invalid argument index. Please check the numbers in square brackets.",
                                }
                        except:
                            return {
                                "role": "assistant",
                                "content": "Invalid remove command. Use format: 'remove [index]'",
                            }

                    elif message_lower.startswith(
                        "add support "
                    ) or message_lower.startswith("add challenge "):
                        try:
                            parts = message.split(maxsplit=3)
                            arg_type = parts[1]
                            option_idx = int(parts[2]) - 1
                            arg_content = parts[3]

                            if (
                                0
                                <= option_idx
                                < len(self.current_state["handling_options"])
                            ):
                                new_arg = Argument(
                                    content=arg_content,
                                    argument_type=arg_type,
                                    parent_option=self.current_state[
                                        "handling_options"
                                    ][option_idx],
                                )
                                self.current_state["arguments"].append(new_arg)
                                response = (
                                    f"✅ Added {arg_type} argument: {arg_content}\n\n"
                                )
                                response += self.format_arguments_display_as_message(
                                    self.current_state
                                )["content"]
                                return {"role": "assistant", "content": response}
                            else:
                                return {
                                    "role": "assistant",
                                    "content": f"Invalid option number. Please use 1-{len(self.current_state['handling_options'])}",
                                }
                        except:
                            return {
                                "role": "assistant",
                                "content": "Invalid add command. Use format: 'add [support/challenge] [option_number] [argument text]'",
                            }

                    else:
                        return {
                            "role": "assistant",
                            "content": "Invalid command. Please use 'accept', 'remove [index]', or 'add [support/challenge] [option] [text]'",
                        }

                def respond(message, chat_history, ref_data):
                    """Handle chat responses in message format"""
                    # Add user message
                    chat_history.append({"role": "user", "content": message})

                    if not self.review_complete:
                        # Process user input during review
                        response = process_user_input_message(message, chat_history)
                        chat_history.append(response)

                        # Check if review is complete and continue processing
                        if self.review_complete:
                            for updated_history, updated_refs in continue_after_review(
                                chat_history
                            ):
                                yield "", updated_history, updated_refs
                            return
                    else:
                        # After care plan is complete, handle follow-up questions
                        response_content = "The care plan is complete. You can review the collapsible sections above for detailed evidence and citations."
                        chat_history.append(
                            {"role": "assistant", "content": response_content}
                        )

                    yield "", chat_history, ref_data

                def generate_care_plan_gradio(patient_info):
                    """Wrapper to run care plan generation with Gradio streaming"""
                    # Validate input
                    if not patient_info.strip():
                        return (
                            gr.update(
                                visible=True,
                                value="❌ Please enter patient information",
                            ),
                            [
                                {
                                    "role": "assistant",
                                    "content": "❌ Please enter patient information",
                                }
                            ],
                            gr.update(visible=False),
                            {},
                        )

                    # Reset interface state
                    self.review_complete = False
                    self.current_state = None
                    self.current_thread_id = None

                    # Create generator for streaming updates during initial generation
                    def stream_initial_generation():
                        chat_history = []

                        try:
                            # Initialize the graph (create fresh instance to avoid state contamination)
                            self.graph = create_care_plan_graph()

                            # Create a new thread ID for this session
                            self.current_thread_id = f"session_{uuid4().hex}"

                            # Initial state with RAG fields and streaming enabled
                            initial_state = {
                                "patient_info": patient_info,
                                "custom_team_requirements": None,
                                "handling_options": [],
                                "arguments": [],
                                "validated_arguments": [],
                                "revised_care_plan": {},
                                "human_feedback": None,
                                "current_step": "rag_retrieval",
                                "human_review_complete": False,
                                "user_action": None,
                                "retrieved_documents": [],
                                "search_queries": [],
                                "rag_context": "",
                                "document_references": [],
                                "cited_documents": set(),
                                "enable_streaming": True,
                            }

                            cfg = {
                                "configurable": {"thread_id": self.current_thread_id}
                            }

                            # Add initial message
                            chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": "🤖 Starting care plan generation...\n\n📚 Retrieving relevant medical knowledge from database...",
                                }
                            )

                            # Yield initial state
                            yield (
                                gr.update(
                                    visible=True, value="## Generating Care Plan"
                                ),
                                chat_history,
                                gr.update(visible=True),
                                {},
                            )

                            # Track progress through nodes
                            reached_human_review = False
                            current_message_idx = len(chat_history) - 1
                            documents_retrieved = False
                            options_generated = False
                            current_node = None

                            # Run the graph stream
                            for event in self.graph.stream(initial_state, cfg):
                                print(f"Event during generation: {list(event.keys())}")

                                for node_name, node_state in event.items():
                                    # Always update status when entering a new node
                                    if node_name != current_node:
                                        current_node = node_name
                                        node_status_messages = {
                                            "rag_retrieval": "📚 Searching medical knowledge database...",
                                            "care_plan_generation": "🏥 Analyzing patient information and generating care options...",
                                            "argument_generation": "💭 Creating evidence-based arguments...",
                                            "human_review": "📋 Preparing arguments for your review...",
                                        }

                                        if node_name in node_status_messages:
                                            # Update or add status message
                                            if current_message_idx < len(chat_history):
                                                chat_history[current_message_idx] = {
                                                    "role": "assistant",
                                                    "content": node_status_messages[
                                                        node_name
                                                    ],
                                                }
                                            else:
                                                chat_history.append(
                                                    {
                                                        "role": "assistant",
                                                        "content": node_status_messages[
                                                            node_name
                                                        ],
                                                    }
                                                )
                                                current_message_idx = (
                                                    len(chat_history) - 1
                                                )

                                            # Immediate yield for status update
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value=f"## Processing: {node_name.replace('_', ' ').title()}",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                    # Handle RAG retrieval node
                                    if node_name == "rag_retrieval":
                                        # Add periodic status updates even without specific progress
                                        if (
                                            "search_queries" in node_state
                                            and not documents_retrieved
                                        ):
                                            query_count = len(
                                                node_state.get("search_queries", [])
                                            )
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"📚 Searching medical knowledge...\n\n🔍 Generated {query_count} search queries...",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Retrieving Medical Knowledge",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # Update with search query progress if available
                                        if "rag_progress" in node_state:
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"📚 Retrieving medical knowledge...\n\n{node_state['rag_progress']}",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Care Plan",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # When retrieval is complete
                                        if (
                                            "retrieved_documents" in node_state
                                            and not documents_retrieved
                                        ):
                                            documents_retrieved = True
                                            doc_count = len(
                                                node_state.get(
                                                    "retrieved_documents", []
                                                )
                                            )

                                            # Show processing status
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"📚 Processing {doc_count} medical documents...",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Processing Documents",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                            # Small delay for UX
                                            import time

                                            time.sleep(0.2)

                                            # Add collapsible section for retrieved documents
                                            if doc_count > 0:
                                                doc_summary = f"Successfully retrieved {doc_count} relevant documents.\n\n"
                                                doc_summary += (
                                                    "**Search queries used:**\n"
                                                )
                                                for i, query in enumerate(
                                                    node_state.get(
                                                        "search_queries", []
                                                    )[:5],
                                                    1,
                                                ):
                                                    doc_summary += f"{i}. {query}\n"

                                                chat_history.append(
                                                    {
                                                        "role": "assistant",
                                                        "content": doc_summary,
                                                        "metadata": {
                                                            "title": f"📚 Retrieved {doc_count} Documents"
                                                        },
                                                    }
                                                )

                                                # Add new progress message
                                                chat_history.append(
                                                    {
                                                        "role": "assistant",
                                                        "content": "🔄 Generating care plan options based on retrieved knowledge...",
                                                    }
                                                )
                                                current_message_idx = (
                                                    len(chat_history) - 1
                                                )

                                                yield (
                                                    gr.update(
                                                        visible=True,
                                                        value="## Generating Care Plan",
                                                    ),
                                                    chat_history,
                                                    gr.update(visible=True),
                                                    {},
                                                )

                                    # Handle care plan generation node
                                    elif node_name == "care_plan_generation":
                                        # Show initial status if no progress yet
                                        if (
                                            "handling_options" not in node_state
                                            and "options_generation_progress"
                                            not in node_state
                                        ):
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": "🔄 Analyzing patient needs and generating personalized care options...",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Options",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # Stream options generation progress
                                        if "options_generation_progress" in node_state:
                                            progress = node_state[
                                                "options_generation_progress"
                                            ]
                                            # Count options being generated
                                            option_count = progress.count("Option")
                                            status_msg = f"🔄 Generating care plan options... ({option_count} options so far)\n\n"

                                            # Show a preview of options being generated
                                            if len(progress) > 100:
                                                status_msg += "**Preview:**\n"
                                                status_msg += f"{progress[:500]}..."
                                            else:
                                                status_msg += progress

                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": status_msg,
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Care Plan",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # When options are complete
                                        if (
                                            "handling_options" in node_state
                                            and node_state["handling_options"]
                                            and not options_generated
                                        ):
                                            options_generated = True
                                            options_count = len(
                                                node_state["handling_options"]
                                            )
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"✅ Generated {options_count} care plan options\n\n💭 Now generating supporting and challenging arguments for each option...",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Arguments",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                    # Handle argument generation node
                                    elif node_name == "argument_generation":
                                        # Calculate progress
                                        total_expected_args = (
                                            len(node_state.get("handling_options", []))
                                            * 4
                                        )  # 2 support + 2 attack per option
                                        current_args = len(
                                            node_state.get("arguments", [])
                                        )

                                        # Show initial status
                                        if (
                                            current_args == 0
                                            and "argument_generation_progress"
                                            not in node_state
                                        ):
                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"💭 Starting argument generation (0/{total_expected_args} arguments)...",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Arguments",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # Show progress through argument generation
                                        if "argument_generation_progress" in node_state:
                                            progress_msg = node_state[
                                                "argument_generation_progress"
                                            ]

                                            # Add progress counter
                                            progress_msg = f"[{current_args}/{total_expected_args}] {progress_msg}"

                                            # Add preview of current argument being generated if available
                                            if "current_argument_stream" in node_state:
                                                preview = node_state[
                                                    "current_argument_stream"
                                                ]
                                                # Extract just the argument part for preview
                                                if "Support:" in preview:
                                                    preview_text = preview.split(
                                                        "Support:"
                                                    )[-1][:150]
                                                    progress_msg += f"\n\n**Generating support argument:**\n_{preview_text}..._"
                                                elif "Challenge:" in preview:
                                                    preview_text = preview.split(
                                                        "Challenge:"
                                                    )[-1][:150]
                                                    progress_msg += f"\n\n**Generating challenge argument:**\n_{preview_text}..._"

                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"💭 {progress_msg}",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Arguments",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # Periodic updates based on argument count
                                        elif (
                                            "arguments" in node_state
                                            and current_args > 0
                                        ):
                                            support_count = sum(
                                                1
                                                for arg in node_state["arguments"]
                                                if arg.argument_type == "support"
                                            )
                                            attack_count = sum(
                                                1
                                                for arg in node_state["arguments"]
                                                if arg.argument_type == "attack"
                                            )

                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"💭 Generating arguments... [{current_args}/{total_expected_args}]\n\n"
                                                f"🟢 Support: {support_count} | ⚠️ Challenge: {attack_count}",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Generating Arguments",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                        # When arguments are complete
                                        if (
                                            "arguments" in node_state
                                            and node_state["arguments"]
                                            and current_args >= total_expected_args - 1
                                        ):
                                            total_args = len(node_state["arguments"])
                                            support_count = sum(
                                                1
                                                for arg in node_state["arguments"]
                                                if arg.argument_type == "support"
                                            )
                                            attack_count = sum(
                                                1
                                                for arg in node_state["arguments"]
                                                if arg.argument_type == "attack"
                                            )

                                            chat_history[current_message_idx] = {
                                                "role": "assistant",
                                                "content": f"✅ Generated {total_args} arguments: ({support_count} support, {attack_count} challenge)\n\n📋 Please review the arguments below:",
                                            }
                                            yield (
                                                gr.update(
                                                    visible=True,
                                                    value="## Review Arguments",
                                                ),
                                                chat_history,
                                                gr.update(visible=True),
                                                {},
                                            )

                                    # Handle human review node
                                    elif node_name == "human_review":
                                        # Show transition message
                                        chat_history[current_message_idx] = {
                                            "role": "assistant",
                                            "content": "✨ Preparing arguments for your review...",
                                        }
                                        yield (
                                            gr.update(
                                                visible=True,
                                                value="## Preparing Review",
                                            ),
                                            chat_history,
                                            gr.update(visible=True),
                                            {},
                                        )

                                        self.current_state = (
                                            node_state.copy()
                                        )  # Make a copy to avoid reference issues
                                        reached_human_review = True
                                        break

                                if reached_human_review:
                                    break

                            # Check if we successfully reached human review
                            if not reached_human_review or not self.current_state:
                                error_msg = "Failed to reach human review stage. The generation process may have been interrupted."
                                chat_history.append(
                                    {"role": "assistant", "content": f"❌ {error_msg}"}
                                )
                                yield (
                                    gr.update(visible=True, value="## Error"),
                                    chat_history,
                                    gr.update(visible=False),
                                    {},
                                )
                                return

                            # Display arguments for review
                            review_message = format_arguments_display_as_message(
                                self.current_state
                            )
                            chat_history.append(review_message)

                            # Final yield with review interface enabled
                            yield (
                                gr.update(
                                    visible=True, value="## Review Generated Arguments"
                                ),
                                chat_history,
                                gr.update(visible=True),
                                {},
                            )

                        except Exception as e:
                            import traceback

                            error_details = traceback.format_exc()
                            print(
                                f"Error in generate_care_plan_gradio: {error_details}"
                            )

                            error_msg = f"❌ Error generating care plan: {str(e)}"

                            # Add error message to chat
                            chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": f"{error_msg}\n\nPlease try again with different patient information or contact support if the issue persists.",
                                }
                            )

                            yield (
                                gr.update(visible=True, value="## Error Occurred"),
                                chat_history,
                                gr.update(visible=False),
                                {},
                            )

                    # Return the generator
                    yield from stream_initial_generation()

                def format_arguments_display_as_message(state):
                    """Helper function to format arguments for display as a message"""
                    display_text = "## 📋 Generated Arguments for Review\n\n"

                    for i, option in enumerate(state["handling_options"]):
                        display_text += f"### Option {i+1}: {option}\n\n"
                        option_args = [
                            arg
                            for arg in state["arguments"]
                            if arg.parent_option == option
                        ]

                        # Group by type
                        support_args = [
                            arg for arg in option_args if arg.argument_type == "support"
                        ]
                        attack_args = [
                            arg
                            for arg in option_args
                            if arg.argument_type == "attack"
                        ]

                        if support_args:
                            display_text += "**🟢 Support Arguments:**\n"
                            for arg in support_args:
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- `[{arg_idx}]` {arg.content}\n"
                            display_text += "\n"

                        if attack_args:
                            display_text += "**⚠️ Challenge Arguments:**\n"
                            for arg in attack_args:
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- `[{arg_idx}]` {arg.content}\n"
                            display_text += "\n"

                    display_text += "---\n\n"
                    display_text += "### 🎯 **Available Actions:**\n\n"
                    display_text += (
                        "- ✅ Type **`accept`** to accept all arguments and continue\n"
                    )
                    display_text += "- ❌ Type **`remove [index]`** to remove an argument (e.g., `remove 3`)\n"
                    display_text += "- ➕ Type **`add support [option_number] [argument]`** to add a support argument\n"
                    display_text += "- ⚠️ Type **`add challenge [option_number] [argument]`** to add a challenge argument\n\n"
                    display_text += "*Example: `add support 1 The patient has good family support nearby`*"

                    return {"role": "assistant", "content": display_text}

                # Event handlers
                generate_btn.click(
                    generate_care_plan_gradio,
                    inputs=[patient_input],
                    outputs=[progress_display, chatbot, msg, references_state],
                )

                msg.submit(
                    respond,
                    inputs=[msg, chatbot, references_state],
                    outputs=[msg, chatbot, references_state],
                    queue=True,
                )

            with gr.Tab("📋 Example Patients"):
                gr.Markdown(
                    """
                ### Example Patient Cases
                
                **Case 1: Mrs. Johnson**
                ```
                Mrs. Johnson, 82 years old, lives alone in a two-story house. She has mild cognitive 
                impairment, arthritis in her knees, and recently had a minor fall. She is determined 
                to remain in her home but her family is concerned about her safety. She has limited 
                mobility on stairs and sometimes forgets to take her medications.
                ```
                
                **Case 2: Mr. Chen**
                ```
                Mr. Chen, 78 years old, recently widowed, lives in a single-story apartment. He has 
                diabetes, moderate hearing loss, and early-stage Parkinson's disease. He is socially 
                isolated and has been showing signs of depression. His children live in another city 
                and visit monthly.
                ```
                
                **Case 3: Ms. Rodriguez**
                ```
                Ms. Rodriguez, 85 years old, lives with her daughter who works full-time. She uses 
                a walker, has heart disease, and requires assistance with daily activities like 
                bathing and meal preparation. She is mentally sharp but physically frail.
                ```
                """
                )

            with gr.Tab("ℹ️ How to Use"):
                gr.Markdown(
                    """
                ## How to Use This System
                
                ### Step 1: Enter Patient Information
                Provide comprehensive details about the elderly patient including:
                - Age and living situation
                - Medical conditions and medications
                - Mobility and cognitive status
                - Social support and family involvement
                - Any recent incidents or concerns
                
                ### Step 2: Review Generated Arguments
                The system will generate handling options with supporting and challenging arguments.
                You can interact with these arguments using simple commands:
                
                **Available Commands:**
                - `accept` - Accept all arguments and proceed to final care plan
                - `remove [index]` - Remove a specific argument by its index number
                - `add support [option_number] [argument_text]` - Add a supporting argument
                - `add challenge [option_number] [argument_text]` - Add a challenging argument
                
                **Examples:**
                - `remove 3` - Removes argument #3
                - `add support 1 The patient has good insurance coverage for home modifications`
                - `add challenge 2 The patient's neighborhood lacks accessible public transportation`
                
                ### Step 3: Get Your Care Plan
                After accepting the arguments, the system will:
                - Validate each argument's relevance and accuracy
                - Generate a comprehensive care plan
                - Provide decision confidence scores
                - Explain the reasoning behind recommendations
                
                ### Tips for Best Results
                - Be specific about medical conditions and functional limitations
                - Include information about the patient's preferences and goals
                - Consider both physical and psychosocial needs
                - Review arguments carefully - they directly influence the final plan
                """
                )

            with gr.Row():
                toggle_dark = gr.Button(value="Toggle Dark")
                toggle_dark.click(
                    None,
                    js="""
                    () => {
                        document.body.classList.toggle('dark');
                    }
                    """,
                )

        return self.interface

    def launch(self, share=False):
        """Launch the Gradio interface"""
        if not self.interface:
            self.create_interface()
        self.interface.queue()
        self.interface.launch(share=share)
