import assert from "node:assert/strict";
import test from "node:test";
import { draftIssues, formQuestions, submissionAnswers } from "../lib/application.ts";

const question = { label: "Impact", field_type: "textarea", required: true, max_words: 3, max_characters: 30, options: [], help_text: "" };
const grant = { inspection: { complete: true, questions: [question] } };

test("submission requires a complete inspection and real answers", () => {
  assert.ok(draftIssues({}, {}).length);
  assert.ok(draftIssues(grant, { Impact: "Information not provided; add evidence." }).length);
  assert.deepEqual(draftIssues(grant, { Impact: "Affordable clean energy" }), []);
});

test("provider word limits and exact choice options are enforced", () => {
  assert.ok(draftIssues(grant, { Impact: "One two three four" }).some((issue) => issue.includes("Word limit")));
  const choice = { inspection: { complete: true, questions: [{ ...question, field_type: "select", options: ["Yes", "No"] }] } };
  assert.ok(draftIssues(choice, { Impact: "Maybe" }).length);
  assert.deepEqual(draftIssues(choice, { Impact: "Yes" }), []);
});

test("required uploads remain manual while optional missing answers are omitted", () => {
  const upload = { inspection: { complete: true, questions: [{ ...question, field_type: "file" }] } };
  assert.deepEqual(formQuestions(upload), []);
  assert.ok(draftIssues(upload, {}).some((issue) => issue.includes("provider portal")));
  assert.deepEqual(submissionAnswers({ Impact: "Ready", optional: "", missing: "Information not provided; optional" }), { Impact: "Ready" });
});
