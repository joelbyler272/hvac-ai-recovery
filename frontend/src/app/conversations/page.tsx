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
import { Send, Bot, User, ArrowLeftRight, AlertTriangle, MessageSquare } from "lucide-react";
import { SkeletonList } from "@/components/ui/skeleton";

export default function ConversationsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messageText, setMessageText] = useState("");

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
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-warm-white transition-colors ${
                      selectedId === c.id ? "bg-ember/5 border-l-2 border-ember" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-navy truncate">
                        {c.lead_name || formatPhone(c.lead_phone || "Unknown")}
                      </p>
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
                      {c.last_message || "No messages yet"}
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
                  <p className="font-medium text-navy">
                    {convo.lead_name || "Unknown"}
                  </p>
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

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((msg: Message) => (
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
                ))}
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
