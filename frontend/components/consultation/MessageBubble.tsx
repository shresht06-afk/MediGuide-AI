"use client";

import { memo } from "react";
import type { AssessmentForm, AssessmentQuestion, AssessmentSummary } from "@/lib/api";
import AssessmentQuestionCard from "./AssessmentQuestionCard";
import AssessmentSummaryCard from "./AssessmentSummaryCard";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  topic?: string;
  safety?: string;
  response_type?: "message" | "assessment_question" | "assessment_summary" | "emergency";
  assessment_question?: AssessmentQuestion | null;
  assessment_summary?: AssessmentSummary | null;
  assessment?: AssessmentForm | null;
};

type MessageBubbleProps = {
  message: ChatMessage;
  onSendAssessment?: (formattedText: string) => Promise<boolean>;
  disabled?: boolean;
  onFocusChat?: () => void;
};

function formatDisplayContent(text: string, hasInteractiveCard: boolean): string {
  if (!text) return "";
  if (!hasInteractiveCard) return text;

  // Filter out redundant numbered question blocks when dedicated interactive card is active
  const paragraphs = text.split(/\n\n+/);
  const nonQuestionParagraphs = paragraphs.filter((p) => !/^\s*(\d+[\.\)]|\*|-)\s+[A-Z0-9]/m.test(p));

  if (nonQuestionParagraphs.length > 0) {
    return nonQuestionParagraphs.join("\n\n");
  }

  // Fallback to first sentence / acknowledgment if all paragraphs had list markers
  const firstLine = text.split("\n")[0]?.trim();
  return firstLine || text;
}

const MessageBubble = memo(function MessageBubble({
  message,
  onSendAssessment,
  disabled = false,
  onFocusChat,
}: MessageBubbleProps) {
  const emergency = message.safety === "emergency" || message.response_type === "emergency";
  const hasAssessment = Boolean(message.assessment && onSendAssessment);
  const displayContent = formatDisplayContent(message.content, hasAssessment);

  return (
    <article
      className={`chat-message ${message.role} ${emergency ? "emergency" : ""}`}
      role={emergency ? "alert" : undefined}
    >
      <div className="message-label">
        {emergency && <span className="warning-icon" aria-hidden="true">!</span>}
        {message.role === "assistant" ? "MEDIGUIDE AI" : "YOU"}
        {message.topic && <span>{message.topic}</span>}
      </div>

      {emergency && <p className="safety-heading">Urgent professional care may be needed</p>}

      {displayContent && (
        <div className="bubble" style={{ whiteSpace: "pre-line" }}>
          {displayContent.split(/\n\n+/).map((paragraph, index) => (
            <p key={index}>{paragraph.replace(/^##\s*/, "")}</p>
          ))}
        </div>
      )}

      {/* Structured Clinical Assessment Summary */}
      {message.role === "assistant" && message.assessment_summary && (
        <AssessmentSummaryCard summary={message.assessment_summary} />
      )}

      {/* Interactive One-Question-at-a-Time Assessment Card */}
      {message.role === "assistant" && message.assessment && onSendAssessment && (
        <AssessmentQuestionCard
          assessment={message.assessment}
          onSubmit={onSendAssessment}
          disabled={disabled}
          onFocusChat={onFocusChat}
        />
      )}
    </article>
  );
});

export default MessageBubble;
