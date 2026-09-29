# Defining the Conversational Coaching Flow

Source: https://my.pathmate.app/pmcp-documentation/doc-6-0/best-practices/defining-the-conversational-coaching-flow · fetched 2026-09-29 · near-verbatim extract

> **The only page in the PMCP docs about interruptions and unanswered questions.** See [../README.md#interruptions-and-pile-up](../README.md#interruptions-and-pile-up) for what it does *not* say.

**Important:** before developing a conversational coaching flow concept, create a comprehensive overview of all micro dialogues, their triggers and timing. (Related: [timing-messages](timing-messages.md), [designing-a-coaching-intervention](designing-a-coaching-intervention.md).)

## Summary: four questions per question/micro dialogue

1. **Is the question mandatory/blocking?** Must it be answered before proceeding, or will it time out after a set period?
2. **Can the active micro dialogue be interrupted by a new micro dialogue?**
3. **By which micro dialogues can it be interrupted?** Typically based on priority or hierarchy.
4. **What happens after it is interrupted?** Does it resume or terminate after the new dialogue completes?

## Blocking questions vs. time-out questions

1. **Blocking questions (typically used).** Stay active until the user responds. They won't disappear from the chat until answered. "While persistent, blocking questions can still be interrupted or bypassed."
2. **Time-out questions.** Remain active for a predefined period and disappear if not answered within that time.

Best practice: "Blocking questions is the default and most common for coaching interactions." Users feel confused and frustrated when questions disappear before they can answer. "Time-out questions should be reserved for exceptional cases", e.g. "How do you feel at this very moment?"

## Handling open questions during pending dialogues

When a new dialogue is due but an open question from the current dialogue is unanswered:

1. The new dialogue **interrupts** the current one. The open question is **deactivated**.
2. The new dialogue is **not allowed** to interrupt. It waits until the current dialogue completes, creating a "queue".

### Best practice: hierarchy system

"A higher-priority dialogue cannot be interrupted by a lower-priority dialogue, but the reverse is allowed."

- High-priority dialogues can interrupt low-priority ones.
- Low-priority dialogues cannot interrupt high-priority ones.
- Define whether dialogues of the same priority can interrupt each other.

**Note (ours):** this is a *design principle* the author implements. The docs describe no priority field or setting.

## Handling deactivated open questions

### Option 1: reactivating deactivated open questions (typically used)

Deactivated open questions are resumed after the user completes the interrupting dialogue. Transitional phrases like "Let's get back to our earlier discussion..." smoothly reintroduce them.

Best practice: "Reactivating deactivated questions aligns well with user needs because it allows users to respond to all open questions at their own pace and reduces frustration from missing previous questions." However, "it requires more sophisticated dialogue state management and careful planning to avoid overwhelming the user with too many interruptions, which can lead to confusion."

### Option 2: deleting unanswered questions

Any unanswered question is deleted when a new, more relevant dialogue is introduced, so only the most timely content remains in focus.

Best practice: use only "in specific cases where unanswered questions lose relevance after the new dialogue starts". It may also suit dialogues that follow a predictable, chronological sequence. It keeps the conversation focused, but risks frustrating users who miss the chance to answer earlier questions.

**Note (ours):** the page does not name the editor settings that implement deactivate/reactivate/delete. See the README.
