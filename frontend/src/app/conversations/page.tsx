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
import { Send, Bot, User, ArrowLeftRight, AlertTriangle } from "lucide-react";

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
            <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          </div>
          {isError ? (
            <div className="p-6 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm">Failed to load.</p>
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto" />
            </div>
          ) : listData?.conversations?.length ? (
            <ul className="divide-y divide-gray-50">
              {listData.conversations.map((c: Conversation) => (
                <li key={c.id}>
                  <button
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                      selectedId === c.id ? "bg-brand-50 border-l-2 border-brand-600" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {c.lead_name || formatPhone(c.lead_phone || "Unknown")}
                      </p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          c.status === "human_active"
                            ? "bg-purple-50 text-purple-700"
                            : c.status === "active"
                            ? "bg-green-50 text-green-700"
                            : "bg-gray-50 text-gray-600"
                        }`}
                      >
                        {c.status === "human_active" ? "Human" : c.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {c.last_message || "No messages yet"}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-center py-8 text-sm">
              No active conversations.
            </p>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-gray-50">
          {selectedId && convo ? (
            <>
              {/* Chat Header */}
              <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">
                    {convo.lead_name || "Unknown"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {convo.status === "human_active" ? (
                      <span className="text-purple-600">You are responding</span>
                    ) : (
                      <span className="text-green-600">AI is responding</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={() =>
                    convo.status === "human_active"
                      ? returnMutation.mutate(selectedId)
                      : takeoverMutation.mutate(selectedId)
                  }
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
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
                            : "bg-brand-100 text-brand-900"
                          : "bg-white text-gray-900 border border-gray-200"
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
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                    <button
                      type="submit"
                      disabled={!messageText.trim() || sendMutation.isPending}
                      className="px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              Select a conversation to view
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
