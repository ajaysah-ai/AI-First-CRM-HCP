import React from "react";
import LogInteractionForm from "./components/LogInteractionForm";
import ChatAssistant from "./components/ChatAssistant";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-xl font-semibold text-slate-800">Log HCP Interaction</h1>
          <p className="text-sm text-slate-500">
            AI-First CRM · HCP Module — log via structured form or conversational chat
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <LogInteractionForm />
          </div>
          <div className="lg:col-span-1">
            <ChatAssistant />
          </div>
        </div>
      </div>
    </div>
  );
}
