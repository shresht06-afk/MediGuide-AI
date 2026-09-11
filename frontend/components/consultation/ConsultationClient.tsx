"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { createConversation, getUserFacingError, sendMessage } from "@/lib/api";
import ChatInput from "./ChatInput";
import MessageBubble, { ChatMessage } from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

const prompts = ["What are some healthy breakfast options?", "How can I improve my sleep routine?", "What does a fever usually mean?"];
const welcome: ChatMessage = { id: "welcome", role: "assistant", content: "How can I help you today?\n\nYou can describe a symptom, ask about nutrition, medication, sleep, wellness, or another general health question." };

export default function ConsultationClient() {
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([welcome]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [retryMessage, setRetryMessage] = useState("");
  const newestMessageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createConversation()
      .then((item) => setConversationId(item.id))
      .catch((requestError) => setError(getUserFacingError(requestError)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    newestMessageRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, sending]);

  const send = useCallback(async (content: string) => {
    if (!conversationId || sending) return false;
    setError("");
    setRetryMessage("");
    setSending(true);
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content }]);
    try {
      const response = await sendMessage(conversationId, content);
      setMessages((current) => [...current, { id: response.message_id, role: "assistant", content: response.content, topic: response.topic, safety: response.safety }]);
      return true;
    } catch (requestError) {
      setMessages((current) => current.slice(0, -1));
      setRetryMessage(content);
      setError(getUserFacingError(requestError));
      return false;
    } finally {
      setSending(false);
    }
  }, [conversationId, sending]);

  return <main className="consultation-page"><section className="consultation-shell">
    <header className="consultation-header"><Link className="brand" href="/"><span className="brand-mark">+</span>Mediguide<span className="brand-ai">.ai</span></Link><span className="consultation-status"><i aria-hidden="true"/> Consultation active</span></header>
    <div className="consultation-title"><span>MEDIGUIDE AI</span><h1>How can I help you today?</h1><p>General health information, thoughtfully presented.</p></div>
    <section className="chat-panel" aria-label="MediGuide consultation">
      <div className="chat-messages" aria-live="polite" aria-atomic="false" aria-relevant="additions">
        {messages.map((message) => <MessageBubble key={message.id} message={message}/>)}
        {sending && <TypingIndicator/>}
        <div ref={newestMessageRef} aria-hidden="true"/>
      </div>
      {error && <div className="chat-error" role="alert"><span>{error}</span>{retryMessage && <button type="button" onClick={() => void send(retryMessage)} disabled={sending || !conversationId}>Try again</button>}</div>}
      <ChatInput onSend={send} disabled={loading || sending || !conversationId}/>
    </section>
    <div className="prompt-row" aria-label="Suggested questions">{prompts.map((prompt) => <button key={prompt} onClick={() => void send(prompt)} disabled={loading || sending || !conversationId}>{prompt}</button>)}</div>
    <p className="consultation-disclaimer">MediGuide provides general health information, not a diagnosis. For urgent or severe symptoms, seek professional medical care.</p>
  </section></main>;
}
