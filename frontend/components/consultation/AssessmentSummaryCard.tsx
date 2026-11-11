"use client";

import { memo } from "react";
import type { AssessmentSummary } from "@/lib/api";

type AssessmentSummaryCardProps = {
  summary: AssessmentSummary;
};

const AssessmentSummaryCard = memo(function AssessmentSummaryCard({
  summary,
}: AssessmentSummaryCardProps) {
  return (
    <article
      className="assessment-summary-card"
      aria-label={`Clinical assessment summary for ${summary.category}`}
    >
      <header className="asc-header">
        <div className="asc-badge-row">
          <span className="asc-badge">
            <span className="asc-badge-check" aria-hidden="true">✓</span>
            Assessment Complete
          </span>
          <span className="asc-category">{summary.category}</span>
        </div>
        <h3 className="asc-title">Clinical Assessment Summary</h3>
        <p className="asc-subtitle">
          Structured educational synthesis based on your reported clinical context.
        </p>
      </header>

      {/* Reported Symptoms Breakdown */}
      {summary.reported_symptoms && summary.reported_symptoms.length > 0 && (
        <section className="asc-section" aria-label="Reported symptoms">
          <h4 className="asc-section-heading">Reported Clinical Details</h4>
          <div className="asc-symptoms-grid">
            {summary.reported_symptoms.map((item, idx) => (
              <div key={idx} className="asc-symptom-item">
                <span className="asc-symptom-label">{item.label}</span>
                <span className="asc-symptom-value">{item.value}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Possible Explanations */}
      {summary.possible_explanations && summary.possible_explanations.length > 0 && (
        <section className="asc-section" aria-label="Possible explanations">
          <h4 className="asc-section-heading">Possible Explanations</h4>
          <p className="asc-uncertainty-note">
            Educational considerations to discuss with a doctor — not a clinical diagnosis:
          </p>
          <ul className="asc-list asc-explanations-list">
            {summary.possible_explanations.map((exp, idx) => (
              <li key={idx} className="asc-list-item">
                <span className="asc-bullet" aria-hidden="true">•</span>
                <span>{exp}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Red-Flag Warning Signs */}
      {summary.warning_signs && summary.warning_signs.length > 0 && (
        <section className="asc-section asc-warning-box" aria-label="Urgent warning signs">
          <div className="asc-warning-header">
            <span className="asc-warning-icon" aria-hidden="true">!</span>
            <h4 className="asc-warning-title">Red-Flag Signs Requiring Urgent Care</h4>
          </div>
          <p className="asc-warning-lead">
            Seek emergency medical care immediately if you experience any of the following:
          </p>
          <ul className="asc-list asc-warning-list">
            {summary.warning_signs.map((sign, idx) => (
              <li key={idx} className="asc-list-item asc-warning-item">
                <span className="asc-warning-dot" aria-hidden="true">⚠</span>
                <span>{sign}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Safe Comfort Measures */}
      {summary.safe_measures && summary.safe_measures.length > 0 && (
        <section className="asc-section" aria-label="Safe comfort measures">
          <h4 className="asc-section-heading">Safe Supportive Comfort Measures</h4>
          <ul className="asc-list">
            {summary.safe_measures.map((measure, idx) => (
              <li key={idx} className="asc-list-item">
                <span className="asc-check-dot" aria-hidden="true">✓</span>
                <span>{measure}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Professional Care Referral */}
      <footer className="asc-footer">
        <div className="asc-referral">
          <strong className="asc-referral-title">Physician Evaluation Recommended:</strong>
          <p className="asc-referral-text">
            {summary.professional_care_recommendation}
          </p>
        </div>
        <p className="asc-disclaimer">
          MediGuide AI provides health information for educational purposes only. It is not a replacement
          for professional medical advice, diagnosis, or treatment.
        </p>
      </footer>
    </article>
  );
});

export default AssessmentSummaryCard;

