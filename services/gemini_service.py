from groq import Groq
import json
from config import config
from utils.logger import get_logger

logger = get_logger("groq_service")

class GroqService:
    """
    Central Groq API service.
    All agents route through here — never call Groq directly.
    Supports single prompts and the broker batch pattern.
    """

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        logger.info(f"GroqService initialized with model: {self.model}")

    def call(self, prompt: str, system_instruction: str = "") -> str:
        """Single prompt call. Returns raw text response."""
        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Groq call | prompt length: {len(prompt)} chars")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1024
            )
            result = response.choices[0].message.content.strip()
            logger.debug(f"Groq response length: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Groq call failed: {e}")
            raise

    def broker_call(self, agent_prompts: dict[str, str], system_instruction: str = "") -> dict[str, str]:
        """
        Broker batch pattern — bundles multiple agent prompts into ONE Groq call.
        agent_prompts: { "kova": "...", "finix": "..." }
        Returns: { "kova": "...", "finix": "..." }
        Core cost-saving mechanism of FINIX.
        """
        bundled = json.dumps(agent_prompts, indent=2)

        prompt = f"""You are the FINIX AI engine. Answer ALL of the following agent questions.
Each key is an agent name. Respond ONLY with a valid JSON object using the same keys.
No preamble. No markdown. No explanation. Raw JSON only.

Agent questions:
{bundled}

Respond in this exact format:
{{
  "agent_name": "your answer here"
}}"""

        try:
            logger.debug(f"Broker call | agents: {list(agent_prompts.keys())}")
            raw = self.call(prompt, system_instruction=system_instruction)

            # Strip markdown fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1]
                clean = clean.rsplit("```", 1)[0]

            result = json.loads(clean)
            logger.debug(f"Broker call success | keys: {list(result.keys())}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Broker JSON parse failed: {e} | raw: {raw[:300]}")
            return {k: "" for k in agent_prompts}
        except Exception as e:
            logger.error(f"Broker call failed: {e}")
            raise

# Singleton — imported by all agents
gemini_service = GroqService()  # kept as gemini_service so all imports stay unchanged
