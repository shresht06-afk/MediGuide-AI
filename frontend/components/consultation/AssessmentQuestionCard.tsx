"use client";

import { memo, useId, useState } from "react";
import type { AssessmentForm, AssessmentQuestion } from "@/lib/api";

type AssessmentQuestionCardProps = {
  assessment: AssessmentForm;
  onSubmit: (formattedText: string) => Promise<boolean>;
  disabled: boolean;
  onFocusChat?: () => void;
};

function getSeverityDescriptor(val: number): string {
  if (val <= 3) return "Mild";
  if (val <= 6) return "Moderate";
  if (val <= 8) return "Severe";
  return "Very Severe";
}

const AssessmentQuestionCard = memo(function AssessmentQuestionCard({
  assessment,
  onSubmit,
  disabled,
  onFocusChat,
}: AssessmentQuestionCardProps) {
  const formId = useId();
  const questions: AssessmentQuestion[] = assessment.questions || [];
  const totalSteps = questions.length || 1;

  // Active question index (0 to totalSteps - 1)
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Store answers across all steps
  const [answers, setAnswers] = useState<Record<string, string | string[] | number>>(() => {
    const initial: Record<string, string | string[] | number> = {};
    for (const q of questions) {
      if (q.type === "slider") {
        initial[q.id] = q.default ?? 5;
      }
    }
    return initial;
  });

  // Inline custom text for when "Other" is selected on a specific question
  const [otherText, setOtherText] = useState<Record<string, string>>({});

  // Optional general notes
  const [notes, setNotes] = useState("");
  const [showNotes, setShowNotes] = useState(false);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedSummary, setSubmittedSummary] = useState("");

  const currentQ: AssessmentQuestion | undefined = questions[currentStepIndex];
  const isLastStep = currentStepIndex === totalSteps - 1;
  const progressPercent = Math.round(((currentStepIndex + 1) / totalSteps) * 100);

  // Handlers for answer selection
  const handleSingleSelect = (questionId: string, option: string) => {
    if (disabled || submitting || submitted) return;
    setAnswers((prev) => ({
      ...prev,
      [questionId]: prev[questionId] === option ? "" : option,
    }));
  };

  const handleMultiSelect = (questionId: string, option: string) => {
    if (disabled || submitting || submitted) return;
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

  // Check if current question has an answer
  const isCurrentQuestionAnswered = (): boolean => {
    if (!currentQ) return false;
    const val = answers[currentQ.id];
    if (currentQ.type === "slider") return typeof val === "number";
    if (currentQ.type === "single_choice") {
      return typeof val === "string" && val.trim().length > 0;
    }
    if (currentQ.type === "multi_choice") {
      return Array.isArray(val) && val.length > 0;
    }
    return true;
  };

  // Format all answers into clinical summary string
  const compileFormattedSubmission = (): string => {
    const lines: string[] = [];
    for (const q of questions) {
      const val = answers[q.id];
      const customOther = otherText[q.id];

      if (q.type === "single_choice" && typeof val === "string" && val) {
        const displayLabel =
          q.id === "location"
            ? "Location"
            : q.id === "sensation"
            ? "Sensation"
            : q.id === "onset"
            ? "Onset"
            : q.label.replace(/\?$/, "");
        const formattedVal = val === "Other" && customOther?.trim() ? `Other (${customOther.trim()})` : val;
        lines.push(`${displayLabel}: ${formattedVal}`);
      } else if (q.type === "multi_choice" && Array.isArray(val) && val.length > 0) {
        const displayLabel = q.id === "associated" ? "Associated symptoms" : q.label.replace(/\?$/, "");
        const items = val.map((item) =>
          item === "Other" && customOther?.trim() ? `Other (${customOther.trim()})` : item
        );
        lines.push(`${displayLabel}: ${items.join(", ")}`);
      } else if (q.type === "slider" && typeof val === "number") {
        lines.push(`Severity: ${val}/10 (${getSeverityDescriptor(val)})`);
      }
    }

    if (notes.trim()) {
      lines.push(`Additional details: ${notes.trim()}`);
    }

    return lines.join("\n");
  };

  const handleNext = async () => {
    if (disabled || submitting || submitted) return;

    if (!isLastStep) {
      setCurrentStepIndex((prev) => prev + 1);
      return;
    }

    // Final step submission
    setSubmitting(true);
    const formatted = compileFormattedSubmission();
    const success = await onSubmit(formatted);
    if (success) {
      setSubmitted(true);
      setSubmittedSummary(formatted);
    }
    setSubmitting(false);
  };

  const handleBack = () => {
    if (disabled || submitting || submitted || currentStepIndex === 0) return;
    setCurrentStepIndex((prev) => prev - 1);
  };

  const handleSkip = async () => {
    if (disabled || submitting || submitted) return;
    if (!isLastStep) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      await handleNext();
    }
  };

  if (submitted) {
    return (
      <div className="aq-submitted" role="status" aria-live="polite">
        <div className="aq-submitted-badge">
          <span className="aq-check-icon" aria-hidden="true">✓</span>
          <strong>Assessment details recorded</strong>
        </div>
        <p className="aq-submitted-summary">{submittedSummary}</p>
      </div>
    );
  }

  if (!currentQ) return null;

  const currentVal = answers[currentQ.id];
  const isOtherSelected =
    currentQ.type === "single_choice"
      ? currentVal === "Other"
      : Array.isArray(currentVal) && currentVal.includes("Other");

  return (
    <section
      className="assessment-question-card"
      aria-label={`${assessment.title} - Question ${currentStepIndex + 1} of ${totalSteps}`}
      id={`aq-${formId}`}
    >
      {/* Header with Category, Step Badge & Animated Progress Bar */}
      <header className="aq-header">
        <div className="aq-header-top">
          <span className="aq-category-badge" aria-hidden="true">
            ✦ {currentQ.category || assessment.title}
          </span>
          <span className="aq-step-indicator">
            Question <strong>{currentStepIndex + 1}</strong> of {totalSteps}
          </span>
        </div>

        {/* Visual Progress Bar */}
        <div
          className="aq-progress-track"
          role="progressbar"
          aria-valuenow={currentStepIndex + 1}
          aria-valuemin={1}
          aria-valuemax={totalSteps}
          aria-label={`Assessment progress: Question ${currentStepIndex + 1} of ${totalSteps}`}
        >
          <div
            className="aq-progress-bar"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </header>

      {/* Active Question Body */}
      <div className="aq-body" key={currentQ.id}>
        <div className="aq-question-heading">
          <h3 className="aq-question-title">{currentQ.question || currentQ.label}</h3>
          {currentQ.explanation && (
            <p className="aq-question-explanation">{currentQ.explanation}</p>
          )}
        </div>

        {/* Single-Select Cards */}
        {currentQ.type === "single_choice" && currentQ.options && (
          <div
            className="aq-cards-grid"
            role="radiogroup"
            aria-label={currentQ.question || currentQ.label}
          >
            {currentQ.options.map((option) => {
              const isSelected = currentVal === option;
              return (
                <button
                  key={option}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  className={`aq-card ${isSelected ? "is-selected" : ""}`}
                  onClick={() => handleSingleSelect(currentQ.id, option)}
                  disabled={disabled || submitting}
                >
                  <span className="aq-card-indicator" aria-hidden="true">
                    {isSelected && <span className="aq-card-dot" />}
                  </span>
                  <span className="aq-card-text">{option}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Multi-Select Cards */}
        {currentQ.type === "multi_choice" && currentQ.options && (
          <div
            className="aq-cards-grid"
            role="group"
            aria-label={currentQ.question || currentQ.label}
          >
            {currentQ.options.map((option) => {
              const selectedList = Array.isArray(currentVal) ? (currentVal as string[]) : [];
              const isSelected = selectedList.includes(option);
              return (
                <button
                  key={option}
                  type="button"
                  aria-pressed={isSelected}
                  className={`aq-card ${isSelected ? "is-selected" : ""}`}
                  onClick={() => handleMultiSelect(currentQ.id, option)}
                  disabled={disabled || submitting}
                >
                  <span className="aq-card-checkbox" aria-hidden="true">
                    {isSelected ? "✓" : ""}
                  </span>
                  <span className="aq-card-text">{option}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Inline "Other" Specification Field */}
        {isOtherSelected && (
          <div className="aq-other-field" role="region" aria-label="Specify other details">
            <label htmlFor={`${formId}-${currentQ.id}-other`} className="aq-other-label">
              Please specify details (optional):
            </label>
            <input
              type="text"
              id={`${formId}-${currentQ.id}-other`}
              value={otherText[currentQ.id] || ""}
              onChange={(e) =>
                setOtherText((prev) => ({
                  ...prev,
                  [currentQ.id]: e.target.value,
                }))
              }
              placeholder="e.g. sharp discomfort around the ribcage..."
              maxLength={150}
              disabled={disabled || submitting}
              className="aq-other-input"
            />
          </div>
        )}

        {/* Severity Slider */}
        {currentQ.type === "slider" && (
          <div className="aq-slider-container">
            <div className="aq-slider-status">
              <span className="aq-slider-score">
                {typeof currentVal === "number" ? currentVal : 5}
                <span className="aq-slider-max"> / {currentQ.max ?? 10}</span>
              </span>
              <span className="aq-slider-descriptor">
                {getSeverityDescriptor(
                  typeof currentVal === "number" ? (currentVal as number) : 5
                )}
              </span>
            </div>

            <input
              type="range"
              id={`${formId}-${currentQ.id}-slider`}
              min={currentQ.min ?? 1}
              max={currentQ.max ?? 10}
              step={1}
              value={typeof currentVal === "number" ? (currentVal as number) : 5}
              onChange={(e) => handleSliderChange(currentQ.id, Number(e.target.value))}
              disabled={disabled || submitting}
              className="aq-range-slider"
              aria-label={currentQ.question || currentQ.label}
              aria-valuemin={currentQ.min ?? 1}
              aria-valuemax={currentQ.max ?? 10}
              aria-valuenow={typeof currentVal === "number" ? (currentVal as number) : 5}
            />

            <div className="aq-slider-ticks" aria-hidden="true">
              <span>1 (Mild)</span>
              <span>5 (Moderate)</span>
              <span>10 (Severe)</span>
            </div>
          </div>
        )}

        {/* Free-text Additional Notes (Collapsible) */}
        <div className="aq-notes-area">
          {!showNotes ? (
            <button
              type="button"
              className="aq-toggle-notes-btn"
              onClick={() => setShowNotes(true)}
              disabled={disabled || submitting}
            >
              ✎ Describe in my own words (optional)
            </button>
          ) : (
            <div className="aq-notes-box">
              <label htmlFor={`${formId}-additional-notes`} className="aq-notes-label">
                Additional context or notes (optional):
              </label>
              <textarea
                id={`${formId}-additional-notes`}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Worsens after eating, started suddenly after exercise..."
                rows={2}
                maxLength={300}
                disabled={disabled || submitting}
                className="aq-notes-input"
              />
            </div>
          )}
        </div>
      </div>

      {/* Assessment Navigation Bar */}
      <footer className="aq-footer">
        <div className="aq-nav-left">
          {currentStepIndex > 0 ? (
            <button
              type="button"
              onClick={handleBack}
              disabled={disabled || submitting}
              className="aq-btn-back"
              aria-label="Go back to previous question"
            >
              ← Back
            </button>
          ) : onFocusChat ? (
            <button
              type="button"
              onClick={onFocusChat}
              disabled={disabled || submitting}
              className="aq-btn-text-mode"
            >
              Type in chat instead
            </button>
          ) : null}
        </div>

        <div className="aq-nav-right">
          <button
            type="button"
            onClick={handleSkip}
            disabled={disabled || submitting}
            className="aq-btn-skip"
          >
            Skip
          </button>

          <button
            type="button"
            onClick={handleNext}
            disabled={disabled || submitting || !isCurrentQuestionAnswered()}
            className="aq-btn-continue"
          >
            {submitting
              ? "Analyzing..."
              : isLastStep
              ? "Complete Assessment →"
              : "Continue →"}
          </button>
        </div>
      </footer>
    </section>
  );
});

export default AssessmentQuestionCard;

