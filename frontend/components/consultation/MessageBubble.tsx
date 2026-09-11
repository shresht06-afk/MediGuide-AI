import { memo } from "react";

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; topic?: string; safety?: string };

const MessageBubble = memo(function MessageBubble({ message }: { message: ChatMessage }) {
  const emergency = message.safety === "emergency";
  return <article className={`chat-message ${message.role} ${emergency ? "emergency" : ""}`} role={emergency ? "alert" : undefined}>
    <div className="message-label">{emergency && <span className="warning-icon" aria-hidden="true">!</span>}{message.role === "assistant" ? "MEDIGUIDE AI" : "YOU"}{message.topic && <span>{message.topic}</span>}</div>
    {emergency && <p className="safety-heading">Urgent professional care may be needed</p>}
    <div className="bubble">{message.content.split(/\n\n+/).map((paragraph, index) => <p key={index}>{paragraph.replace(/^##\s*/, "")}</p>)}</div>
  </article>;
});

export default MessageBubble;
