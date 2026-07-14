import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../api/client";

const SESSION_ID = "session-" + Math.random().toString(36).slice(2, 10);

export const sendChatMessage = createAsyncThunk(
    "chat/send",
    async(message, { rejectWithValue }) => {
        try {
            const res = await api.post("/api/chat", { session_id: SESSION_ID, message });
            return res.data;
        } catch (err) {
            return rejectWithValue(
                (err &&
                    err.response &&
                    err.response.data &&
                    err.response.data.detail) ||
                "Agent request failed"
            );
        }
    }
);

const chatSlice = createSlice({
    name: "chat",
    initialState: {
        sessionId: SESSION_ID,
        messages: [{
            role: "assistant",
            content: "Log interaction details here (e.g., \"Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure\") or ask for help.",
        }, ],
        status: "idle",
        error: null,
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(sendChatMessage.pending, (state, action) => {
                state.status = "loading";
                state.messages.push({ role: "user", content: action.meta.arg });
            })
            .addCase(sendChatMessage.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.messages.push({
                    role: "assistant",
                    content: action.payload.reply,
                    toolCalls: action.payload.tool_calls,
                    saved: action.payload.saved,
                    pendingApproval: action.payload.pending_approval,
                });
            })
            .addCase(sendChatMessage.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.payload;
                state.messages.push({
                    role: "assistant",
                    content: "⚠️ " + (action.payload || "Something went wrong."),
                });
            });
    },
});

export default chatSlice.reducer;