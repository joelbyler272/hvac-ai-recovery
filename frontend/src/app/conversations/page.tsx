"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import {
  getConversations,
  getConversation,
  takeoverConversation,
  returnToAI,
  sendMessage,
  type Conversation,
  type Message,
} from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeMessages } from "@/hooks/use-realtime";
import {
  Send,
  Bot,
  User,
  ArrowLeftRight,
  AlertTriangle,
  MessageSquare,
  Mic,
  Phone,
  FileText,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { SkeletonList } from "@/components/ui/skeleton";

export default function ConversationsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messageText, setMessageText] = useState("");
  const [showTranscript, setShowTranscript] = useState(false);

  useRealtimeMessages(selectedId || undefined);

  const { data: listData, isLoading, isError } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => getConversations(token!),
    enabled: !!token,
    refetchInterval: 15000,
  });

  const { data: detailData } = useQuery({
    queryKey: ["conversation", selectedId],
    queryFn: () => getConversation(token!, selectedId!),
    enabled: !!token && !!selectedId,
    refetchInterval: 10000,
  });

  const takeoverMutation = useMutation({
    mutationFn: (id: string) => takeoverConversation(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["conversation", selectedId] });
    },
  });

  const returnMutation = useMutation({
    mutationFn: (id: string) => returnToAI(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["conversation", selectedId] });
    },
  });

  const sendMutation = useMutation({
    mutationFn: (body: string) => sendMessage(token!, selectedId!, body),
    onSuccess: () => {
      setMessageText("");
      queryClient.invalidateQueries({ queryKey: ["conversation", selectedId] });
    },
  });

  const convo = detailData?.conversation;
  const messages = detailData?.messages || [];
  const isVoiceConvo = convo?.channel === "voice";

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-0px)]">
        {/* Conversation List */}
        <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
          <div className="p-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-navy">Conversations</h2>
          </div>
          {isError ? (
            <div className="p-6 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm">Failed to load.</p>
            </div>
          ) : isLoading ? (
            <SkeletonList rows={4} />
          ) : listData?.conversations?.length ? (
            <ul className="divide-y divide-gray-50">
              {listData.conversations.map((c: Conversation) => (
                <li key={c.id}>
                  <button
                    onClick={() => {
                      setSelectedId(c.id);
                      setShowTranscript(false);
                    }}
                    className={`w-full text-left px-4 py-3 hover:bg-warm-white transition-colors ${
                      selectedId === c.id ? "bg-ember/5 border-l-2 border-ember" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {c.channel === "voice" ? (
                          <Phone className="h-3.5 w-3.5 text-teal" />
                        ) : (
                          <MessageSquare className="h-3.5 w-3.5 text-slate-muted" />
                        )}
                        <p className="text-sm font-medium text-navy truncate">
                          {c.lead_name || formatPhone(c.lead_phone || "Unknown")}
                        </p>
                      </div>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          c.status === "human_active"
                            ? "bg-purple-50 text-purple-700"
                            : c.status === "active"
                            ? "bg-teal/10 text-teal"
                            : "bg-gray-100 text-slate-light"
                        }`}
                      >
                        {c.status === "human_active" ? "Human" : c.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-muted mt-0.5 truncate">
                      {c.channel === "voice" ? "Voice AI call" : c.last_message || "No messages yet"}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-12 px-4">
              <MessageSquare className="h-8 w-8 text-slate-muted mx-auto mb-3" />
              <p className="text-sm font-medium text-navy">No active conversations</p>
              <p className="text-xs text-slate-muted mt-1">
                Conversations start when missed calls are recovered.
              </p>
            </div>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-warm-white">
          {selectedId && convo ? (
            <>
              {/* Chat Header */}
              <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-navy">
                      {convo.lead_name || "Unknown"}
                    </p>
                    {isVoiceConvo && (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-teal/10 text-teal">
                        <Mic className="h-3 w-3" />
                        Voice AI
                      </span>
                    )}
                  </div>
                  <p className="text-xs">
                    {convo.status === "human_active" ? (
                      <span className="text-purple-600">You are responding</span>
                    ) : (
                      <span className="text-teal">AI is responding</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={() =>
                    convo.status === "human_active"
                      ? returnMutation.mutate(selectedId)
                      : takeoverMutation.mutate(selectedId)
                  }
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-200 hover:bg-warm-white transition-colors text-navy"
                >
                  <ArrowLeftRight className="h-4 w-4" />
                  {convo.status === "human_active" ? "Return to AI" : "Take Over"}
                </button>
              </div>

              {/* Voice AI Panel: Recording + Transcript */}
              {isVoiceConvo && (convo.recording_url || convo.voice_transcript) && (
                <div className="bg-white border-b border-gray-200 px-4 py-3 space-y-2">
                  {/* Audio Player */}
                  {convo.recording_url && (
                    <div className="flex items-center gap-3">
                      <Mic className="h-4 w-4 text-teal flex-shrink-0" />
                      <audio
                        controls
                        className="flex-1 h-8"
                        src={convo.recording_url}
                      >
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  )}

                  {/* Transcript Toggle */}
                  {convo.voice_transcript && (
                    <div>
                      <button
                        onClick={() => setShowTranscript(!showTranscript)}
                        className="flex items-center gap-1.5 text-xs font-medium text-slate-light hover:text-navy transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        {showTranscript ? "Hide" : "Show"} Voice Transcript
                        {showTranscript ? (
                          <ChevronUp className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5" />
                        )}
                      </button>
                      {showTranscript && (
                        <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm text-navy max-h-60 overflow-y-auto space-y-1.5">
                          {convo.voice_transcript.split("\n").map((line: string, i: number) => {
                            const isAssistant = line.toLowerCase().startsWith("assistant:");
                            const isUser = line.toLowerCase().startsWith("user:");
                            return (
                              <p
                                key={i}
                                className={`${
                                  isAssistant
                                    ? "text-teal"
                                    : isUser
                                    ? "text-navy"
                                    : "text-slate-muted"
                                }`}
                              >
                                {line}
                              </p>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && isVoiceConvo ? (
                  <div className="text-center py-8 text-slate-muted">
                    <Phone className="h-8 w-8 mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Voice AI conversation — see transcript above</p>
                  </div>
                ) : (
                  messages.map((msg: Message) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.direction === "outbound" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[70%] rounded-lg px-4 py-2.5 ${
                          msg.direction === "outbound"
                            ? msg.sender_type === "human"
                              ? "bg-purple-100 text-purple-900"
                              : "bg-ember/10 text-navy"
                            : "bg-white text-navy border border-gray-200"
                        }`}
                      >
                        <div className="flex items-center gap-1 mb-0.5">
                          {msg.sender_type === "ai" ? (
                            <Bot className="h-3 w-3" />
                          ) : msg.sender_type === "human" ? (
                            <User className="h-3 w-3" />
                          ) : null}
                          <span className="text-xs opacity-60">{msg.sender_type}</span>
                        </div>
                        <p className="text-sm">{msg.body}</p>
                        <p className="text-xs mt-1 opacity-50">
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Message Input (only when human active) */}
              {convo.status === "human_active" && (
                <div className="bg-white border-t border-gray-200 p-3">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (messageText.trim()) sendMutation.mutate(messageText);
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="text"
                      value={messageText}
                      onChange={(e) => setMessageText(e.target.value)}
                      placeholder="Type a message..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
                    />
                    <button
                      type="submit"
                      disabled={!messageText.trim() || sendMutation.isPending}
                      className="px-4 py-2 bg-ember text-white rounded-lg text-sm font-medium hover:bg-ember-dark disabled:opacity-50 transition-colors active:scale-[0.98]"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-muted">
              Select a conversation to view
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
