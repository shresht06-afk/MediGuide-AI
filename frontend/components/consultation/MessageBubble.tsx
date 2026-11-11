import { memo } from "react";
import type { AssessmentForm } from "@/lib/api";
import QuickAssessment from "./QuickAssessment";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  topic?: string;
  safety?: string;
  assessment?: AssessmentForm | null;
};

type MessageBubbleProps = {
  message: ChatMessage;
  onSendAssessment?: (formattedText: string) => Promise<boolean>;
  disabled?: boolean;
  onFocusChat?: () => void;
};

const MessageBubble = memo(function MessageBubble({
  message,
  onSendAssessment,
  disabled = false,
  onFocusChat,
}: MessageBubbleProps) {
  const emergency = message.safety === "emergency";
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
      <div className="bubble" style={{ whiteSpace: "pre-line" }}>
        {message.content.split(/\n\n+/).map((paragraph, index) => (
          <p key={index}>{paragraph.replace(/^##\s*/, "")}</p>
        ))}
      </div>
      {message.role === "assistant" && message.assessment && onSendAssessment && (
        <QuickAssessment
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
