# LLM Integration · Events & Actions

Fetched 2026-09-29 · condensed extracts

## LLM Integration
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/llm-hub

- **LLM Hub:** configurations (Name, Type `OpenAI`|`Ollama`, Model, credentials), each scoped to None / All Teams / Specific Teams. Global configurations are made by platform admins (credentials hidden); team-level ones are editable by the team.
- **Slots LLM1–LLM5** in a coaching's Basic Settings. Swapping the model only means reassigning the slot. After a platform update, coachings default to LLM1.
- **Global LLM Settings** (Basic Settings: coaching, form of speech, coach, participant) are required for Sessions and OneShots.
- **LLM Session:** a message type. Control is handed to a multi-turn, single-topic LLM conversation and later returned. Configured with a prompt (write prompts in English), meta information, an optional stop criterion and an optional **Session Identifier** (reuse it to continue the same context). **Result variables** can be typed: freetext raw/cleaned, number (parsed from words), decimal, boolean, other. The session can stop automatically once they're collected. Users can close it with the ✕ or by saying they're done. Replies are labelled "AI Chat". Tip: the handback to the rule flow "is often perceived as a usability break", so follow it with a OneShot that has no open answer.
- **LLM OneShot:** a message type that generates a single personalised message (prompt plus optional local meta), with a **Test Run** in the editor. It can have no reply, a free-text reply or options.
- **LLM calls in JS:** `//+llm`, `llm(slot, prompt)` or `llm(slot, systemPrompt, prompt)` returns `{success, message}`. Always provide a fallback. For non-English coachings, add "Answer in $participantLanguage".
- Costs are the customer's. OpenAI needs an org id, an API key and a project id.

## Events & Actions
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/events-and-actions

Content that is edited often, kept outside the intervention so it can be updated without revising the intervention, and reused across interventions:
1. **Service Channel News** (see [communication-channel](../communication-channel.md))
2. **Sending emails to users**
3. **Prompting questionnaires** (JSON questionnaires)
