"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type VoiceStatus = "idle" | "listening" | "stopping" | "complete" | "unsupported" | "permission-denied" | "error";
type RecognitionEvent = { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> };
type RecognitionErrorEvent = { error: string };
type Recognition = {
  continuous: boolean; interimResults: boolean; lang: string;
  onstart: (() => void) | null; onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null; onend: (() => void) | null;
  start: () => void; stop: () => void;
};
type RecognitionConstructor = new () => Recognition;

const voiceCopy: Record<Exclude<VoiceStatus, "idle" | "listening" | "stopping">, string> = {
  complete: "Transcription ready. Review or edit it, then send when you're ready.",
  unsupported: "Voice input is not supported in this browser. You can still type your message.",
  "permission-denied": "Microphone access was not allowed. You can still type your message.",
  error: "Voice input could not hear you clearly. Please try again or type your message.",
};

export default function ChatInput({ onSend, disabled }: { onSend: (content: string) => Promise<boolean>; disabled: boolean }) {
  const [value, setValue] = useState("");
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>(() => {
    if (typeof window === "undefined") return "idle";
    const browser = window as typeof window & { SpeechRecognition?: RecognitionConstructor; webkitSpeechRecognition?: RecognitionConstructor };
    return browser.SpeechRecognition || browser.webkitSpeechRecognition ? "idle" : "unsupported";
  });
  const recognitionRef = useRef<Recognition | null>(null);

  useEffect(() => () => recognitionRef.current?.stop(), []);

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    const content = value.trim();
    if (!content || disabled) return;
    const sent = await onSend(content);
    if (sent) setValue("");
  };

  const keyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  };

  const toggleVoice = () => {
    if (voiceStatus === "listening") {
      setVoiceStatus("stopping");
      recognitionRef.current?.stop();
      return;
    }
    if (voiceStatus === "stopping" || recognitionRef.current) return;
    const browser = window as typeof window & { SpeechRecognition?: RecognitionConstructor; webkitSpeechRecognition?: RecognitionConstructor };
    const SpeechRecognition = browser.SpeechRecognition ?? browser.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceStatus("unsupported");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = navigator.language || "en-US";
    recognition.onstart = () => setVoiceStatus("listening");
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).slice(event.resultIndex).filter((result) => result.isFinal).map((result) => result[0].transcript.trim()).filter(Boolean).join(" ");
      if (transcript) {
        setValue((current) => `${current}${current.trim() ? " " : ""}${transcript}`);
        setVoiceStatus("complete");
      }
    };
    recognition.onerror = (event) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") setVoiceStatus("permission-denied");
      else if (event.error !== "aborted") setVoiceStatus("error");
    };
    recognition.onend = () => {
      recognitionRef.current = null;
      setVoiceStatus((status) => status === "permission-denied" || status === "error" || status === "unsupported" || status === "complete" ? status : "idle");
    };
    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      setVoiceStatus("error");
    }
  };

  const voiceMessage = voiceStatus === "listening" ? "Listening — speak now. Your words will appear here for review." : voiceStatus === "stopping" ? "Stopping voice input…" : voiceStatus === "idle" ? "" : voiceCopy[voiceStatus];
  const voiceStatusMessage = voiceStatus === "idle" ? "Microphone ready." : voiceStatus === "listening" ? "Microphone is listening." : voiceStatus === "stopping" ? "Microphone is stopping." : voiceStatus === "unsupported" ? "Voice input is unavailable in this browser." : voiceStatus === "permission-denied" ? "Microphone access was denied." : voiceStatus === "complete" ? "Voice transcription is ready for review." : "Voice input encountered an error.";
  const voiceLabel = voiceStatus === "listening" ? "Stop voice input" : voiceStatus === "stopping" ? "Stopping voice input" : voiceStatus === "unsupported" ? "Voice input unavailable" : voiceStatus === "permission-denied" ? "Voice input unavailable because microphone access was denied" : "Start voice input";
  const voiceTitle = voiceStatus === "listening" ? "Stop voice input" : voiceStatus === "unsupported" ? "Voice input is not supported in this browser" : voiceStatus === "permission-denied" ? "Microphone access was not allowed" : voiceStatus === "error" ? "Try voice input again" : "Use voice input";

  return <form className="chat-input" onSubmit={submit}>
    <textarea value={value} onChange={(event) => setValue(event.target.value)} onKeyDown={keyDown} placeholder="Describe what you're experiencing..." aria-label="Your health question" disabled={disabled} rows={1}/>
    <button type="button" className={`voice-button ${voiceStatus === "listening" ? "is-listening" : ""}`} onClick={toggleVoice} disabled={disabled || voiceStatus === "stopping" || voiceStatus === "unsupported"} aria-label={voiceLabel} aria-describedby="voice-status" aria-pressed={voiceStatus === "listening"} title={voiceTitle}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M6 11a6 6 0 0 0 12 0M12 17v4M9 21h6"/></svg>
      <span className="sr-only">{voiceStatus === "listening" ? "Listening" : "Voice input"}</span>
    </button>
    <button type="submit" className="send-button" disabled={disabled || !value.trim()} aria-label="Send message">{disabled ? <span className="send-loader"/> : "↑"}</button>
    <span id="voice-status" className="sr-only" role="status" aria-live="polite">{voiceStatusMessage}</span>
    {voiceMessage && <p className={`voice-message ${voiceStatus}`} aria-hidden="true">{voiceMessage}</p>}
    <p className="input-help">Press Enter to send · Shift + Enter for a new line</p>
  </form>;
}
