import json
import logging
import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import SYSTEM_PROMPT
from app.schemas import APIResponse, TicketInput, TriageResult
from app.tools import AVAILABLE_TOOLS, TOOLS_SCHEMA

logger = logging.getLogger("support-triage-agent.agent")


load_dotenv()


class SupportTriageAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables or .env file.")

        # Supports both the official OpenAI API and OpenRouter (uses OPENAI_BASE_URL from .env when set).
        base_url = os.getenv("OPENAI_BASE_URL")

        # gpt-4o-mini is a good default for OpenRouter: it supports tool calling and structured outputs, and it is inexpensive.
        self.model = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
        self.client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    def check_openai_health(self) -> dict:
        """Confirm the API key works and the configured model is available.

        Uses GET /models. Compatible hosts such as OpenRouter return 404 for
        GET /models/{id}, while the list endpoint works for both.
        """
        client = self.client.with_options(timeout=15.0, max_retries=0)
        try:
            for model in client.models.list():
                if model.id == self.model:
                    return {"status": "healthy", "model": self.model, "detail": None}
        except openai.APIStatusError as exc:
            logger.warning("OpenAI health check failed with HTTP %s", exc.status_code)
            return {
                "status": "unhealthy",
                "model": self.model,
                "detail": f"OpenAI API returned HTTP {exc.status_code}",
            }
        except openai.APIConnectionError:
            logger.warning("OpenAI health check could not connect")
            return {
                "status": "unhealthy",
                "model": self.model,
                "detail": "Could not connect to the OpenAI API",
            }
        except openai.APIError:
            logger.warning("OpenAI health check failed")
            return {
                "status": "unhealthy",
                "model": self.model,
                "detail": "OpenAI API request failed",
            }

        return {
            "status": "unhealthy",
            "model": self.model,
            "detail": f"Configured model '{self.model}' was not found",
        }

    def _format_ticket_for_llm(self, ticket: TicketInput) -> str:
        """Turn ticket input into text the model can read easily."""
        messages_text = "\n".join(
            [f"- [{msg.timestamp}]: {msg.content}" for msg in ticket.messages]
        )
        customer_id = ticket.customer_id or "Not provided"
        return (
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Customer ID: {customer_id}\n"
            f"Customer Info: {ticket.customer_info}\n\n"
            f"Conversation History:\n{messages_text}"
        )

    def process_ticket(self, ticket: TicketInput) -> APIResponse:
        """
        Run the agent loop:
        1. Send the ticket so the model can choose which tools to call.
        2. Run the requested Python functions and send the results back.
        3. Ask the model for a final answer that matches the Pydantic schema (TriageResult).
        """
        logger.info(f"Processing ticket: {ticket.ticket_id}")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._format_ticket_for_llm(ticket)},
        ]
        tools_called: list[str] = []

        # Allow up to 5 tool-calling rounds (guards against an infinite loop).
        for _ in range(5):

            logger.info(f"[{ticket.ticket_id}] Step {_ + 1}: Consulting model...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1,  # Low temperature keeps decisions stable and consistent.
            )

            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            # If the model stops calling tools, it has enough context. Exit the loop and summarize.
            if not assistant_message.tool_calls:
                break

            # If the model requested tools, run each one.
            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                tools_called.append(f"{func_name}({json.dumps(func_args, ensure_ascii=False)})")

                # Call the real function from AVAILABLE_TOOLS in tools.py.
                tool_func = AVAILABLE_TOOLS.get(func_name)
                if tool_func:
                    tool_output = tool_func(**func_args)
                else:
                    tool_output = json.dumps({"error": f"Tool {func_name} not found"})

                # Append the tool result to the conversation history (messages).
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_output,
                    }
                )

        # Final step: force the model to reply as structured output (TriageResult).
        final_completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=TriageResult,
            temperature=0.1,
        )

        triage_result = final_completion.choices[0].message.parsed

        logger.info(f"[{ticket.ticket_id}] Completed | Urgency: {triage_result.urgency.value} | Action: {triage_result.next_action.value}")


        return APIResponse(
            ticket_id=ticket.ticket_id,
            tools_called=tools_called,
            triage_result=triage_result,
        )
