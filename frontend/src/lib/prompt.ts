import type { Branding } from "./brandingTypes";

function formatClause(fmt: string | undefined) {
  switch (fmt) {
    case 'bulletPoints':
      return `Write in concise bullet points. Use short, scannable bullets. Avoid paragraphs unless explicitly requested.`;
    case 'letSystemChoose':
      return `Choose the clearest format for the user's intent. Prefer paragraphs for explanations; use bullets for short lists.`;
    case 'paragraphs':
    default:
      return `Write in descriptive, cohesive paragraphs. Do not use bullet points unless explicitly requested.`;
  }
}

export function buildSystemPrompt(branding: Branding): string {
  const base = (branding.aiSystemPrompt ?? '').trim();

  const format = formatClause(branding.responseFormat);
  const followUps = `
- Do not greet mid-conversation. Only greet on the very first assistant turn.
- If you ask a follow-up, put it at the end wrapped as:
  <ask>Your concise follow-up question?</ask>
- When the next user message is brief (e.g., "yes", "no", "2", "maybe"), treat it as an answer to your most recent <ask> and continue. Do not re-greet.
  `.trim();

  return [base, format, followUps].filter(Boolean).join('\n\n');
}