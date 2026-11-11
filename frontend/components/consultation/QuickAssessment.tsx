"use client";

import { memo, useId, useState } from "react";
import type { AssessmentForm } from "@/lib/api";

type QuickAssessmentProps = {
  assessment: AssessmentForm;
  onSubmit: (formattedText: string) => Promise<boolean>;
  disabled: boolean;
  onFocusChat?: () => void;
};

function getSeverityDescriptor(val: number): string {
  if (val <= 3) return "Mild";
  if (val <= 6) return "Moderate";
  if (val <= 8) return "Severe";
  return "Very severe";
}

const QuickAssessment = memo(function QuickAssessment({
  assessment,
  onSubmit,
  disabled,
  onFocusChat,
}: QuickAssessmentProps) {
  const formId = useId();
  const [answers, setAnswers] = useState<Record<string, string | string[] | number>>(() => {
    const initial: Record<string, string | string[] | number> = {};
    for (const q of assessment.questions) {
      if (q.type === "slider") {
        initial[q.id] = q.default ?? 5;
      }
    }
    return initial;
  });

  const [notes, setNotes] = useState("");
  const [showNotes, setShowNotes] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submittedSummary, setSubmittedSummary] = useState("");

  const handleSingleSelect = (questionId: string, option: string) => {
    if (disabled || submitting || submitted) return;
    if (option === "Other") {
      setShowNotes(true);
    }
    setAnswers((prev) => ({
      ...prev,
      [questionId]: prev[questionId] === option ? "" : option,
    }));
  };

  const handleMultiSelect = (questionId: string, option: string) => {
    if (disabled || submitting || submitted) return;
    if (option === "Other") {
      setShowNotes(true);
    }
    setAnswers((prev) => {
      const current = Array.isArray(prev[questionId]) ? (prev[questionId] as string[]) : [];
      if (option.toLowerCase().includes("none")) {
        return { ...prev, [questionId]: current.includes(option) ? [] : [option] };
      }
      const filtered = current.filter((item) => !item.toLowerCase().includes("none"));
      if (filtered.includes(option)) {
        return { ...prev, [questionId]: filtered.filter((item) => item !== option) };
      }
      return { ...prev, [questionId]: [...filtered, option] };
    });
  };

  const handleSliderChange = (questionId: string, value: number) => {
    if (disabled || submitting || submitted) return;
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const hasAnyAnswer = (): boolean => {
    if (notes.trim()) return true;
    for (const [qid, val] of Object.entries(answers)) {
      if (typeof val === "string" && val.trim()) return true;
      if (Array.isArray(val) && val.length > 0) return true;
      const qDef = assessment.questions.find((q) => q.id === qid);
      if (qDef?.type === "slider") return true;
    }
    return false;
  };

  const handleSubmit = async () => {
    if (disabled || submitting || submitted || !hasAnyAnswer()) return;
    setSubmitting(true);

    const lines: string[] = [];
    for (const q of assessment.questions) {
      const val = answers[q.id];
      if (q.type === "single_choice" && typeof val === "string" && val) {
        const displayLabel = q.id === "location" ? "Location" : q.id === "onset" ? "Onset" : q.label.replace(/\?$/, "");
        lines.push(`${displayLabel}: ${val}`);
      } else if (q.type === "multi_choice" && Array.isArray(val) && val.length > 0) {
        const displayLabel = q.id === "associated" ? "Associated symptoms" : q.label.replace(/\?$/, "");
        lines.push(`${displayLabel}: ${val.join(", ")}`);
      } else if (q.type === "slider" && typeof val === "number") {
        lines.push(`Severity: ${val}/10 (${getSeverityDescriptor(val)})`);
      }
    }

    if (notes.trim()) {
      lines.push(`Additional details: ${notes.trim()}`);
    }

    const formatted = lines.join("\n");
    const success = await onSubmit(formatted);
    if (success) {
      setSubmitted(true);
      setSubmittedSummary(formatted);
    }
    setSubmitting(false);
  };

  if (submitted) {
    return (
      <div className="qa-submitted" role="status" aria-live="polite">
        <div className="qa-submitted-badge">
          <span className="qa-check-icon" aria-hidden="true">✓</span>
          <strong>Assessment details submitted</strong>
        </div>
        <p className="qa-submitted-summary">{submittedSummary}</p>
      </div>
    );
  }

  return (
    <section
      className="quick-assessment"
      aria-label={assessment.title}
      id={`qa-${formId}`}
    >
      <header className="qa-header">
        <span className="qa-badge" aria-hidden="true">✦ Quick Select</span>
        <h3 className="qa-title">{assessment.title}</h3>
        <p className="qa-help">Select your symptoms or tap options to respond quickly.</p>
      </header>

      <div className="qa-questions">
        {assessment.questions.map((q) => {
          const qInputId = `${formId}-${q.id}`;
          return (
            <fieldset key={q.id} className="qa-fieldset">
              <legend className="qa-label" id={`${qInputId}-label`}>
                {q.label}
              </legend>

              {q.type === "single_choice" && q.options && (
                <div
                  className="qa-chip-group"
                  role="radiogroup"
                  aria-labelledby={`${qInputId}-label`}
                >
                  {q.options.map((opt) => {
                    const isSelected = answers[q.id] === opt;
                    return (
                      <button
                        key={opt}
                        type="button"
                        role="radio"
                        aria-checked={isSelected}
                        className={`qa-chip ${isSelected ? "is-selected" : ""}`}
                        onClick={() => handleSingleSelect(q.id, opt)}
                        disabled={disabled || submitting}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              )}

              {q.type === "multi_choice" && q.options && (
                <div
                  className="qa-chip-group"
                  role="group"
                  aria-labelledby={`${qInputId}-label`}
                >
                  {q.options.map((opt) => {
                    const selectedList = Array.isArray(answers[q.id])
                      ? (answers[q.id] as string[])
                      : [];
                    const isSelected = selectedList.includes(opt);
                    return (
                      <button
                        key={opt}
                        type="button"
                        aria-pressed={isSelected}
                        className={`qa-chip ${isSelected ? "is-selected" : ""}`}
                        onClick={() => handleMultiSelect(q.id, opt)}
                        disabled={disabled || submitting}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              )}

              {q.type === "slider" && (
                <div className="qa-slider-box">
                  <div className="qa-slider-header">
                    <span className="qa-slider-val">
                      {typeof answers[q.id] === "number" ? answers[q.id] : 5} / {q.max ?? 10}
                    </span>
                    <span className="qa-slider-descriptor">
                      {getSeverityDescriptor(
                        typeof answers[q.id] === "number" ? (answers[q.id] as number) : 5
                      )}
                    </span>
                  </div>
                  <input
                    type="range"
                    id={qInputId}
                    min={q.min ?? 1}
                    max={q.max ?? 10}
                    step={1}
                    value={typeof answers[q.id] === "number" ? (answers[q.id] as number) : 5}
                    onChange={(e) => handleSliderChange(q.id, Number(e.target.value))}
                    disabled={disabled || submitting}
                    className="qa-slider"
                    aria-label={q.label}
                    aria-valuemin={q.min ?? 1}
                    aria-valuemax={q.max ?? 10}
                    aria-valuenow={typeof answers[q.id] === "number" ? (answers[q.id] as number) : 5}
                  />
                  <div className="qa-slider-scale" aria-hidden="true">
                    <span>1 (Mild)</span>
                    <span>5 (Moderate)</span>
                    <span>10 (Severe)</span>
                  </div>
                </div>
              )}
            </fieldset>
          );
        })}
      </div>

      <div className="qa-notes-section">
        {!showNotes ? (
          <button
            type="button"
            className="qa-toggle-notes"
            onClick={() => setShowNotes(true)}
            disabled={disabled || submitting}
          >
            ✎ Describe in my own words (optional)
          </button>
        ) : (
          <div className="qa-notes-field">
            <label htmlFor={`${formId}-notes`} className="qa-notes-label">
              Describe in your own words (optional)
            </label>
            <textarea
              id={`${formId}-notes`}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Sharp pain when moving, started right after lunch..."
              rows={2}
              maxLength={400}
              disabled={disabled || submitting}
              className="qa-notes-textarea"
            />
          </div>
        )}
      </div>

      <div className="qa-actions">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || submitting || !hasAnyAnswer()}
          className="qa-btn-submit"
        >
          {submitting ? "Sending..." : "Continue assessment →"}
        </button>

        {onFocusChat && (
          <button
            type="button"
            onClick={onFocusChat}
            disabled={disabled || submitting}
            className="qa-btn-skip"
          >
            Skip & type in chat
          </button>
        )}
      </div>
    </section>
  );
});

export default QuickAssessment;
