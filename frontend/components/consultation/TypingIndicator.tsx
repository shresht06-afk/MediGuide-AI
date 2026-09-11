import { memo } from "react";
import Lifeline from "@/components/landing/Lifeline";

const TypingIndicator = memo(function TypingIndicator() {
  return <div className="typing-indicator" role="status" aria-live="polite" aria-label="MediGuide AI is thinking"><div><strong>MEDIGUIDE AI</strong><span aria-hidden="true">Thinking<span className="thinking-dots">•••</span></span></div><Lifeline decorative/></div>;
});

export default TypingIndicator;
