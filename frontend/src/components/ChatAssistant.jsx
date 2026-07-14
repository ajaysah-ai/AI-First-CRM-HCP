import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Bot, Send, CheckCircle2, PencilLine } from "lucide-react";
import { sendChatMessage } from "../store/chatSlice";
import { hydrateFromAgent, setSuggestionsFromAgent } from "../store/interactionSlice";

export default function ChatAssistant() {
  const dispatch = useDispatch();
  const { messages, status } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || status === "loading") return;
    setInput("");

    const action = await dispatch(sendChatMessage(trimmed));
    if (sendChatMessage.fulfilled.match(action)) {
      const { interaction, suggestions, saved } = action.payload;
      // Whatever the agent just staged/logged/edited, mirror it straight into the
      // structured form on the left so both panels always stay in sync.
      if (interaction) dispatch(hydrateFromAgent({ interaction, saved }));
      if (suggestions?.length) dispatch(setSuggestionsFromAgent(suggestions));
    }
  };

  const handleSend = () => sendMessage(input);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isLastMessage = (i) => i === messages.length - 1;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200">
        <Bot size={18} className="text-brand-500" />
        <div>
          <p className="text-sm font-semibold text-slate-800">AI Assistant</p>
          <p className="text-xs text-slate-400">Log interaction via chat</p>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[320px] max-h-[480px]">
        {messages.map((m, i) => (
          <div key={i} className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`max-w-[90%] text-sm rounded-lg px-3 py-2 ${
                m.role === "user"
                  ? "bg-brand-500 text-white rounded-br-none"
                  : m.saved
                  ? "bg-green-50 border border-green-200 text-green-800 rounded-bl-none"
                  : "bg-slate-100 text-slate-700 rounded-bl-none"
              }`}
            >
              <div className="flex items-start gap-1.5">
                {m.saved && <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-green-600" />}
                <span>{m.content}</span>
              </div>
              {m.toolCalls?.length > 0 && (
                <p className={`mt-1 text-[10px] opacity-70 ${m.saved ? "" : ""}`}>
                  tools used: {m.toolCalls.join(", ")}
                </p>
              )}
            </div>

            {/* Quick approve/keep-editing actions under the latest staged draft */}
            {m.role === "assistant" && m.pendingApproval && isLastMessage(i) && (
              <div className="flex gap-2 mt-1.5">
                <button
                  onClick={() => sendMessage("Yes, log it.")}
                  disabled={status === "loading"}
                  className="flex items-center gap-1 text-xs font-medium bg-green-500 hover:bg-green-600 disabled:opacity-60 text-white px-2.5 py-1 rounded-md transition"
                >
                  <CheckCircle2 size={13} /> Confirm & Log
                </button>
                <button
                  onClick={() => document.getElementById("chat-input")?.focus()}
                  className="flex items-center gap-1 text-xs font-medium border border-slate-300 text-slate-600 hover:bg-slate-50 px-2.5 py-1 rounded-md transition"
                >
                  <PencilLine size={13} /> Keep editing
                </button>
              </div>
            )}
          </div>
        ))}
        {status === "loading" && (
          <div className="flex justify-start">
            <div className="bg-slate-100 text-slate-400 text-sm rounded-lg px-3 py-2 rounded-bl-none">
              thinking…
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 border-t border-slate-200 px-3 py-2">
        <input
          id="chat-input"
          className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          onClick={handleSend}
          disabled={status === "loading"}
          className="bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white p-2 rounded-lg transition"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}