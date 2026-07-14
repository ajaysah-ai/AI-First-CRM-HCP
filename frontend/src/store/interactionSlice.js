import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../api/client.js";

const initialFormState = {
    hcp_name: "",
    interaction_type: "Meeting",
    attendees: "",
    topics_discussed: "",
    materials_shared: "",
    samples_distributed: "",
    sentiment: "Neutral",
    outcomes: "",
    follow_up_actions: "",
};

export const submitInteraction = createAsyncThunk(
    "interaction/submit",
    async(formData, { rejectWithValue }) => {
        try {
            const res = await api.post("/api/interactions", {...formData, source: "form" });
            return res.data;
        } catch (err) {
            return rejectWithValue(
                (err &&
                    err.response &&
                    err.response.data &&
                    err.response.data.detail) ||
                "Failed to save interaction"
            );
        }
    }
);

export const fetchFollowupSuggestions = createAsyncThunk(
    "interaction/suggestFollowups",
    async(interactionId, { rejectWithValue }) => {
        try {
            const res = await api.get(`/api/interactions/${interactionId}/suggest-followups`);
            return res.data.suggestions || [];
        } catch (err) {
            return rejectWithValue(
                (err &&
                    err.response &&
                    err.response.data &&
                    err.response.data.detail) ||
                "Failed to fetch suggestions"
            );
        }
    }
);

export const fetchInteractionHistory = createAsyncThunk(
    "interaction/fetchHistory",
    async(hcpName, { rejectWithValue }) => {
        try {
            const res = await api.get("/api/interactions", { params: { hcp_name: hcpName, limit: 10 } });
            return res.data;
        } catch (err) {
            return rejectWithValue(
                (err &&
                    err.response &&
                    err.response.data &&
                    err.response.data.detail) ||
                "Failed to fetch history"
            );
        }
    }
);

const interactionSlice = createSlice({
    name: "interaction",
    initialState: {
        form: initialFormState,
        savedInteraction: null,
        isDraftPending: false, // true = agent staged a draft awaiting user approval to save
        suggestions: [],
        history: [],
        status: "idle", // idle | loading | succeeded | failed
        error: null,
    },
    reducers: {
        updateField: (state, action) => {
            const { field, value } = action.payload;
            state.form[field] = value;
        },
        resetForm: (state) => {
            state.form = initialFormState;
            state.savedInteraction = null;
            state.isDraftPending = false;
            state.suggestions = [];
        },
        applyAIFields: (state, action) => {
            // Merge fields extracted by the chat agent into the structured form
            state.form = {...state.form, ...action.payload };
        },
        hydrateFromAgent: (state, action) => {
            // Called after every chat turn that produced interaction data (staged OR saved),
            // so the structured form always mirrors what the agent is working with.
            const { interaction: i, saved } = action.payload;
            state.form = {
                hcp_name: i.hcp_name || "",
                interaction_type: i.interaction_type || "Meeting",
                attendees: i.attendees || "",
                topics_discussed: i.topics_discussed || "",
                materials_shared: i.materials_shared || "",
                samples_distributed: i.samples_distributed || "",
                sentiment: i.sentiment || "Neutral",
                outcomes: i.outcomes || "",
                follow_up_actions: i.follow_up_actions || "",
            };
            if (saved) {
                state.savedInteraction = i;
                state.isDraftPending = false;
            } else {
                state.savedInteraction = null;
                state.isDraftPending = true;
            }
        },
        setSuggestionsFromAgent: (state, action) => {
            state.suggestions = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(submitInteraction.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(submitInteraction.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.savedInteraction = action.payload;
                state.isDraftPending = false;
            })
            .addCase(submitInteraction.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.payload;
            })
            .addCase(fetchFollowupSuggestions.fulfilled, (state, action) => {
                state.suggestions = action.payload;
            })
            .addCase(fetchInteractionHistory.fulfilled, (state, action) => {
                state.history = action.payload;
            });
    },
});

export const { updateField, resetForm, applyAIFields, hydrateFromAgent, setSuggestionsFromAgent } =
interactionSlice.actions;
export default interactionSlice.reducer;