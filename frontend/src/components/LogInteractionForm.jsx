import React from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  updateField,
  submitInteraction,
  resetForm,
  fetchFollowupSuggestions,
} from "../store/interactionSlice";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference"];

// IMPORTANT: `value` must exactly match what the backend/agent sends ("Positive" /
// "Neutral" / "Negative") — only `label` carries the emoji for display. Never put
// emoji inside `value`, or the radio's checked={form.sentiment === value} comparison
// will silently fail to match and the button won't auto-select.
const SENTIMENT_OPTIONS = [
  { value: "Positive", label: "🙂 Positive" },
  { value: "Neutral", label: "😐 Neutral" },
  { value: "Negative", label: "☹️ Negative" },
];

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const { form, status, savedInteraction, suggestions, isDraftPending } = useSelector((s) => s.interaction);

  const handleChange = (field) => (e) => {
    dispatch(updateField({ field, value: e.target.value }));
  };

  const handleRadio = (value) => {
    dispatch(updateField({ field: "sentiment", value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.hcp_name.trim()) return;
    const action = await dispatch(submitInteraction(form));
    if (submitInteraction.fulfilled.match(action)) {
      dispatch(fetchFollowupSuggestions(action.payload.id));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Interaction Details</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">HCP Name</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Search or select HCP..."
            value={form.hcp_name}
            onChange={handleChange("hcp_name")}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Interaction Type</label>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={form.interaction_type}
            onChange={handleChange("interaction_type")}
          >
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-slate-500 mb-1">Attendees</label>
        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Enter names or search..."
          value={form.attendees}
          onChange={handleChange("attendees")}
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-slate-500 mb-1">Topics Discussed</label>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          rows={3}
          placeholder="Enter key discussion points..."
          value={form.topics_discussed}
          onChange={handleChange("topics_discussed")}
        />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Materials Shared</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Search/Add"
            value={form.materials_shared}
            onChange={handleChange("materials_shared")}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Samples Distributed</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Add Sample"
            value={form.samples_distributed}
            onChange={handleChange("samples_distributed")}
          />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-slate-500 mb-2">Observed/Inferred HCP Sentiment</label>
        <div className="flex gap-4">
          {SENTIMENT_OPTIONS.map((opt) => (
            <label key={opt.value} className="flex items-center gap-1.5 text-sm text-slate-700">
              <input
                type="radio"
                name="sentiment"
                checked={form.sentiment === opt.value}
                onChange={() => handleRadio(opt.value)}
                className="accent-brand-500"
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-slate-500 mb-1">Outcomes</label>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          rows={2}
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={handleChange("outcomes")}
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-slate-500 mb-1">Follow-up Actions</label>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          rows={2}
          placeholder="Enter next steps or tasks..."
          value={form.follow_up_actions}
          onChange={handleChange("follow_up_actions")}
        />
      </div>

      {suggestions.length > 0 && (
        <div className="mb-4 bg-brand-50 border border-brand-100 rounded-lg p-3">
          <p className="text-xs font-medium text-brand-700 mb-1">AI Suggested Follow-ups:</p>
          <ul className="text-sm text-brand-600 list-disc list-inside space-y-0.5">
            {suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {isDraftPending && !savedInteraction && (
        <div className="mb-4 flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-700 text-sm rounded-lg px-3 py-2">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
          Draft staged by AI Assistant — not yet saved. Approve in chat or click "Log Interaction" to save.
        </div>
      )}

      {savedInteraction && (
        <div className="mb-4 flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-3 py-2">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
          ✓ Interaction saved successfully (id: {savedInteraction.id?.slice(0, 8)}…)
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={status === "loading"}
          className="bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
        >
          {status === "loading" ? "Saving..." : "Log Interaction"}
        </button>
        <button
          type="button"
          onClick={() => dispatch(resetForm())}
          className="text-sm font-medium px-4 py-2 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          Clear
        </button>
      </div>
    </form>
  );
}