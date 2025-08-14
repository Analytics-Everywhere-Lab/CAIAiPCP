"""
Argumentative Elderly Care Plan Generator with Gradio Interface

This system generates personalized care plans for elderly individuals using
AI-driven argumentation with human-in-the-loop review via Gradio.

The system will launch a web interface where you can:
1. Enter patient information
2. Review and modify generated arguments
3. Get a comprehensive care plan with explanations
"""

from uuid import uuid4
import torch
import gradio as gr
from env_config import HUGGINGFACE_MODEL_NAME
from graph import create_care_plan_graph
from state import Argument

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class CarePlanGradioInterface:
    def __init__(self):
        self.graph = None
        self.current_state = None
        self.current_thread_id = None
        self.app = None
        self.review_complete = False
        self.interface = None

    def format_arguments_display(self, state):
        """Format arguments for display in chat"""
        display_text = "## Generated Arguments for Review\n\n"

        for i, option in enumerate(state["handling_options"]):
            display_text += f"### Option {i+1}: {option}\n\n"
            option_args = [
                arg for arg in state["arguments"] if arg.parent_option == option
            ]

            # Group by type
            support_args = [
                arg for arg in option_args if arg.argument_type == "support"
            ]
            attack_args = [arg for arg in option_args if arg.argument_type == "attack"]

            if support_args:
                display_text += "**Supporting Arguments:**\n"
                for _, arg in enumerate(support_args):
                    arg_idx = state["arguments"].index(arg)
                    display_text += f"- [{arg_idx}] {arg.content}\n"
                display_text += "\n"

            if attack_args:
                display_text += "**Attacking Arguments (Concerns/Challenges):**\n"
                for _, arg in enumerate(attack_args):
                    arg_idx = state["arguments"].index(arg)
                    display_text += f"- [{arg_idx}] {arg.content}\n"
                display_text += "\n"

        display_text += "\n---\n"
        display_text += "**Available Actions:**\n"
        display_text += "- Type 'accept' to accept all arguments and continue\n"
        display_text += (
            "- Type 'remove [index]' to remove an argument (e.g., 'remove 3')\n"
        )
        display_text += "- Type 'add support [option_number] [argument]' to add a supporting argument\n"
        display_text += "- Type 'add attack [option_number] [argument]' to add an attacking argument\n"

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

        elif message.startswith("add support ") or message.startswith("add attack "):
            try:
                parts = message.split(maxsplit=3)
                arg_type = parts[1]  # 'support' or 'attack'
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
                return "Invalid add command. Use format: 'add [support/attack] [option_number] [argument text]'"

        else:
            return "Invalid command. Please use 'accept', 'remove [index]', or 'add [support/attack] [option] [text]'"

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
                    elem_classes=["care-plan-chat"]
                )
                
                msg = gr.Textbox(
                    label="Your Input",
                    placeholder="Type 'accept' to approve all, 'remove [index]' to remove, or 'add [support/attack] [option_num] [text]' to add",
                    submit_btn=True,
                    stop_btn=True,
                )

                # Hidden state for storing references
                references_state = gr.State({})

                def format_care_plan_for_chat(final_state):
                    """Format the final care plan as chat messages with collapsible citations"""
                    if not final_state or 'revised_care_plan' not in final_state:
                        return []
                    
                    care_plan = final_state['revised_care_plan']
                    messages = []
                    
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
                    
                    messages.append({
                        "role": "assistant",
                        "content": metrics_content
                    })
                    
                    # Message 2: Main recommendations
                    recommendations = care_plan['recommendations']
                    
                    # Extract citations from recommendations
                    import re
                    ref_pattern = r'\[REF-(\d+)\]'
                    cited_refs = re.findall(ref_pattern, recommendations)
                    cited_ref_ids = list(set(int(ref) for ref in cited_refs))
                    
                    # Clean recommendations (remove [REF-X] tags for cleaner display)
                    clean_recommendations = re.sub(ref_pattern, '', recommendations)
                    
                    recommendations_content = f"""## 📝 Care Plan Recommendations

    {clean_recommendations}"""
                    
                    messages.append({
                        "role": "assistant",
                        "content": recommendations_content
                    })
                    
                    # Message 3: Collapsible citations for each cited document
                    ref_data = {}
                    if 'document_references' in final_state and cited_ref_ids:
                        # Store reference data
                        for ref in final_state['document_references']:
                            ref_data[ref['id']] = ref
                        
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
                                
                                if ref['similarity_score'] > 0.7:
                                    primary_citations.append(citation_text)
                                else:
                                    supporting_citations.append(citation_text)
                        
                        # Add primary citations if any
                        if primary_citations:
                            messages.append({
                                "role": "assistant",
                                "content": "\n\n".join(primary_citations),
                                "metadata": {"title": f"📚 Primary Evidence ({len(primary_citations)} documents)"}
                            })
                        
                        # Add supporting citations if any
                        if supporting_citations:
                            messages.append({
                                "role": "assistant",
                                "content": "\n\n".join(supporting_citations),
                                "metadata": {"title": f"📄 Supporting Evidence ({len(supporting_citations)} documents)"}
                            })
                    
                    # Message 4: Search queries used (collapsible)
                    if 'search_queries' in final_state and final_state['search_queries']:
                        queries_content = "**Queries used to retrieve medical knowledge:**\n\n"
                        for i, query in enumerate(final_state['search_queries'][:10], 1):
                            queries_content += f"{i}. {query}\n"
                        
                        messages.append({
                            "role": "assistant",
                            "content": queries_content,
                            "metadata": {"title": f"🔍 Search Queries ({len(final_state['search_queries'])} queries)"}
                        })
                    
                    # Message 5: Adaptive retrieval details (if available, collapsible)
                    if 'adaptive_retrieval_summary' in final_state:
                        summary = final_state['adaptive_retrieval_summary']
                        adaptive_content = f"""**Adaptive Evidence Enhancement Results:**

    - Arguments Enhanced: {summary['arguments_enhanced']}
    - Average Score Improvement: {summary['average_score_improvement']:.3f}

    **Enhanced Arguments:**"""
                        
                        for detail in summary.get('details', []):
                            adaptive_content += f"\n\n**Argument:** {detail['argument'][:100]}..."
                            adaptive_content += f"\n• Initial Score: {detail['initial_score']:.2f}"
                            adaptive_content += f"\n• Updated Score: {detail['updated_score']:.2f}"
                            adaptive_content += f"\n• Evidence Documents Used: {detail['evidence_used']}"
                        
                        messages.append({
                            "role": "assistant",
                            "content": adaptive_content,
                            "metadata": {"title": "🔄 Adaptive Evidence Retrieval"}
                        })
                    
                    # Message 6: Completion notification
                    messages.append({
                        "role": "assistant",
                        "content": "✅ **Care plan generation complete!**\n\n💡 *Click on the collapsible sections above to view citations and evidence details.*"
                    })
                    
                    return messages, ref_data

                def format_arguments_display_as_message(state):
                    """Format arguments for display as a message"""
                    display_text = "## Generated Arguments for Review\n\n"

                    for i, option in enumerate(state["handling_options"]):
                        display_text += f"### Option {i+1}: {option}\n\n"
                        option_args = [
                            arg for arg in state["arguments"] if arg.parent_option == option
                        ]

                        # Group by type
                        support_args = [
                            arg for arg in option_args if arg.argument_type == "support"
                        ]
                        attack_args = [arg for arg in option_args if arg.argument_type == "attack"]

                        if support_args:
                            display_text += "**Supporting Arguments:**\n"
                            for _, arg in enumerate(support_args):
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- [{arg_idx}] {arg.content}\n"
                            display_text += "\n"

                        if attack_args:
                            display_text += "**Attacking Arguments (Concerns/Challenges):**\n"
                            for _, arg in enumerate(attack_args):
                                arg_idx = state["arguments"].index(arg)
                                display_text += f"- [{arg_idx}] {arg.content}\n"
                            display_text += "\n"

                    display_text += "\n---\n"
                    display_text += "**Available Actions:**\n"
                    display_text += "- Type 'accept' to accept all arguments and continue\n"
                    display_text += "- Type 'remove [index]' to remove an argument (e.g., 'remove 3')\n"
                    display_text += "- Type 'add support [option_number] [argument]' to add a supporting argument\n"
                    display_text += "- Type 'add attack [option_number] [argument]' to add an attacking argument\n"

                    return {"role": "assistant", "content": display_text}

                def continue_after_review(history):
                    """Continue processing after human review is complete"""
                    if not self.review_complete or not self.current_state:
                        return history, {}
                    
                    try:
                        # Create a new thread ID for the continuation
                        continuation_thread_id = f"continue_{uuid4().hex}"
                        cfg = {"configurable": {"thread_id": continuation_thread_id}}
                        
                        # Add processing message
                        history.append({
                            "role": "assistant",
                            "content": "⏳ Validating arguments and generating final care plan..."
                        })
                        
                        # Make sure the state has human_review_complete = True
                        self.current_state["human_review_complete"] = True
                        self.current_state["current_step"] = "argument_validation"
                        
                        # Create a new graph instance
                        continuation_graph = create_care_plan_graph()
                        
                        # Run the remaining nodes
                        final_state = None
                        events_seen = []
                        
                        for event in continuation_graph.stream(self.current_state, cfg):
                            print(f"Processing event after review: {list(event.keys())}")
                            events_seen.extend(list(event.keys()))
                            for node_name, node_state in event.items():
                                if node_name == "plan_revision":
                                    final_state = node_state
                        
                        print(f"Events processed: {events_seen}")
                        
                        if (
                            final_state
                            and "revised_care_plan" in final_state
                            and final_state["revised_care_plan"]
                        ):
                            # Remove processing message
                            history = history[:-1]
                            
                            # Format care plan as messages with collapsible citations
                            care_plan_messages, ref_data = format_care_plan_for_chat(final_state)
                            
                            # Add all care plan messages to history
                            for msg in care_plan_messages:
                                history.append(msg)
                            
                            return history, ref_data
                        else:
                            history.append({
                                "role": "assistant",
                                "content": "❌ Error: Unable to generate final care plan."
                            })
                            return history, {}
                    
                    except Exception as e:
                        import traceback
                        print(f"Error in continue_after_review: {traceback.format_exc()}")
                        history.append({
                            "role": "assistant",
                            "content": f"❌ Error during processing: {str(e)}"
                        })
                        return history, {}

                def process_user_input_message(message, history):
                    """Process user commands during review - returns message format"""
                    if not self.current_state:
                        return {
                            "role": "assistant",
                            "content": "No active review session. Please start a care plan generation first."
                        }

                    message_lower = message.strip().lower()

                    if message_lower == "accept":
                        self.current_state["human_review_complete"] = True
                        self.current_state["current_step"] = "argument_validation"
                        self.review_complete = True
                        return {
                            "role": "assistant",
                            "content": "✅ Arguments accepted. Proceeding to validation..."
                        }

                    elif message_lower.startswith("remove "):
                        try:
                            idx = int(message_lower.split()[1])
                            if 0 <= idx < len(self.current_state["arguments"]):
                                removed_arg = self.current_state["arguments"].pop(idx)
                                response = f"❌ Removed argument: {removed_arg.content}\n\n"
                                response += self.format_arguments_display_as_message(self.current_state)["content"]
                                return {"role": "assistant", "content": response}
                            else:
                                return {
                                    "role": "assistant",
                                    "content": "Invalid argument index. Please check the numbers in square brackets."
                                }
                        except:
                            return {
                                "role": "assistant",
                                "content": "Invalid remove command. Use format: 'remove [index]'"
                            }

                    elif message_lower.startswith("add support ") or message_lower.startswith("add attack "):
                        try:
                            parts = message.split(maxsplit=3)
                            arg_type = parts[1]
                            option_idx = int(parts[2]) - 1
                            arg_content = parts[3]

                            if 0 <= option_idx < len(self.current_state["handling_options"]):
                                new_arg = Argument(
                                    content=arg_content,
                                    argument_type=arg_type,
                                    parent_option=self.current_state["handling_options"][option_idx],
                                )
                                self.current_state["arguments"].append(new_arg)
                                response = f"✅ Added {arg_type} argument: {arg_content}\n\n"
                                response += self.format_arguments_display_as_message(self.current_state)["content"]
                                return {"role": "assistant", "content": response}
                            else:
                                return {
                                    "role": "assistant",
                                    "content": f"Invalid option number. Please use 1-{len(self.current_state['handling_options'])}"
                                }
                        except:
                            return {
                                "role": "assistant",
                                "content": "Invalid add command. Use format: 'add [support/attack] [option_number] [argument text]'"
                            }

                    else:
                        return {
                            "role": "assistant",
                            "content": "Invalid command. Please use 'accept', 'remove [index]', or 'add [support/attack] [option] [text]'"
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
                            chat_history, new_ref_data = continue_after_review(chat_history)
                            return "", chat_history, new_ref_data
                    else:
                        # After care plan is complete, handle follow-up questions
                        response_content = "The care plan is complete. You can review the collapsible sections above for detailed evidence and citations."
                        chat_history.append({
                            "role": "assistant",
                            "content": response_content
                        })
                    
                    return "", chat_history, ref_data

                def generate_care_plan_gradio(patient_info):
                    """Wrapper to run care plan generation with Gradio"""
                    if not patient_info.strip():
                        return (
                            gr.update(visible=True, value="❌ Please enter patient information"),
                            [{"role": "assistant", "content": "❌ Please enter patient information"}],
                            gr.update(visible=False),
                            {},
                        )
                    
                    # Reset interface state
                    self.review_complete = False
                    self.current_state = None
                    self.current_thread_id = None
                    chat_history = []
                    
                    try:
                        # Initialize the graph
                        self.graph = create_care_plan_graph()
                        
                        # Create a new thread ID
                        self.current_thread_id = f"session_{uuid4().hex}"
                        
                        # Initial state with RAG fields
                        initial_state = {
                            "patient_info": patient_info,
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
                        }
                        
                        cfg = {"configurable": {"thread_id": self.current_thread_id}}
                        
                        # Add initial message
                        chat_history.append({
                            "role": "assistant",
                            "content": "🤖 Starting care plan generation...\n\n📚 Retrieving relevant medical knowledge from database..."
                        })
                        
                        # Run until human review
                        reached_human_review = False
                        for event in self.graph.stream(initial_state, cfg):
                            print(f"Event during generation: {list(event.keys())}")
                            for node_name, node_state in event.items():
                                if node_name == "rag_retrieval":
                                    # Add collapsible section for retrieved documents
                                    if node_state.get('retrieved_documents'):
                                        doc_summary = f"Successfully retrieved {len(node_state['retrieved_documents'])} relevant documents.\n\n"
                                        doc_summary += "**Search queries used:**\n"
                                        for i, query in enumerate(node_state.get('search_queries', [])[:5], 1):
                                            doc_summary += f"{i}. {query}\n"
                                        
                                        chat_history.append({
                                            "role": "assistant",
                                            "content": doc_summary,
                                            "metadata": {"title": f"📚 Retrieved {len(node_state['retrieved_documents'])} Documents"}
                                        })
                                        
                                    chat_history.append({
                                        "role": "assistant",
                                        "content": "🔄 Generating care plan options and arguments based on retrieved knowledge..."
                                    })
                                elif node_name == "human_review":
                                    self.current_state = node_state.copy()
                                    reached_human_review = True
                                    break
                            if reached_human_review:
                                break
                        
                        if not reached_human_review or not self.current_state:
                            raise Exception("Failed to reach human review stage")
                        
                        # Display arguments for review
                        review_message = format_arguments_display_as_message(self.current_state)
                        chat_history.append(review_message)
                        
                        return (
                            gr.update(visible=True, value="## Review Generated Arguments"),
                            chat_history,
                            gr.update(visible=True),
                            {},
                        )
                    except Exception as e:
                        error_msg = f"❌ Error generating care plan: {str(e)}"
                        import traceback
                        print(f"Error details: {traceback.format_exc()}")
                        return (
                            gr.update(visible=True, value=error_msg),
                            [{"role": "assistant", "content": error_msg}],
                            gr.update(visible=False),
                            {},
                        )

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
                - `add attack [option_number] [argument_text]` - Add a challenging argument
                
                **Examples:**
                - `remove 3` - Removes argument #3
                - `add support 1 The patient has good insurance coverage for home modifications`
                - `add attack 2 The patient's neighborhood lacks accessible public transportation`
                
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
        self.interface.launch(share=share)


# Example usage
if __name__ == "__main__":
    # Ensure model is loaded
    print(f"Loading HuggingFace model: {HUGGINGFACE_MODEL_NAME} on {DEVICE}")
    print("This may take a moment on first run...")

    # Launch Gradio interface
    print("\n" + "=" * 50)
    print("Launching Elderly Care Plan Generator Interface")
    print("=" * 50)
    print("\nThe interface will open in your default browser.")
    print("If it doesn't open automatically, click the URL shown below.")
    print("\nIn the interface, you can:")
    print("1. Enter patient information")
    print("2. Review and modify generated arguments interactively")
    print("3. Get a comprehensive care plan with explanations")
    print("\nPress Ctrl+C to stop the server.\n")

    interface = CarePlanGradioInterface()
    interface.launch(share=False)  # Set share=True to create a public link
