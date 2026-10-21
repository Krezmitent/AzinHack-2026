import type { Grant } from "./types";

export function formQuestions(grant: Grant) {
  return (grant.inspection?.questions ?? []).filter((question) => !["file", "checkbox", "other"].includes(question.field_type));
}

export function submissionAnswers(answers: Record<string, string>) {
  return Object.fromEntries(Object.entries(answers).filter(([, answer]) => answer.trim() && !answer.startsWith("Information not provided;")));
}

export function draftIssues(grant: Grant, answers: Record<string, string>): string[] {
  if (!grant.inspection?.complete) return ["Inspect the complete application form before starting a run."];
  const issues: string[] = [];
  for (const question of grant.inspection.questions) {
    const answer = answers[question.label]?.trim() ?? "";
    if (question.required && ["file", "checkbox", "other"].includes(question.field_type)) {
      issues.push(`Complete in the provider portal: ${question.label}`);
    } else if (question.required && (!answer || answer.startsWith("Information not provided;"))) {
      issues.push(`Complete the required answer: ${question.label}`);
    } else if (answer && !answer.startsWith("Information not provided;")) {
      if (question.max_words && answer.split(/\s+/).length > question.max_words) issues.push(`Word limit exceeded: ${question.label}`);
      if ((question.max_characters && answer.length > question.max_characters) || answer.length > 10000) issues.push(`Character limit exceeded: ${question.label}`);
      if (question.field_type === "select" && question.options.length && !question.options.includes(answer)) issues.push(`Choose a listed option: ${question.label}`);
    }
  }
  return issues;
}
