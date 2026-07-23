/** Conversational RAG interface with evidence, provider status, and chat memory. */
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Database, ExternalLink, MessageCircleQuestion, Plus, Send, Sparkles, User } from "lucide-react";
import { musicApi } from "../api/client";
import { formatDate, formatFullNumber } from "../utils/formatters";

const suggestions = [
  "What are the top 10 trending songs?",
  "Which songs were released in the last hour?",
  "Which artists are gaining attention and why?",
  "Compare the strongest recent music opportunities.",
];

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);

  const conversations = useQuery({
    queryKey: ["assistant-conversations"],
    queryFn: musicApi.listConversations,
  });

  useEffect(() => {
    if (!messages.length) {
      setMessages([{ role: "assistant", answer: "Hi, I am MusicPulse AI assistant.", metric_definition: "I can help you with questions related to trending songs, recent releases, and most popular songs", generated_at: new Date().toISOString(), data: [], sources: [], provider: "MusicPulse AI" }]);
    }
  }, [messages.length]);

  const mutation = useMutation({
    mutationFn: musicApi.askAssistant,
    onSuccess: (response) => {
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, { role: "assistant", ...response }]);
      conversations.refetch();
    },
    onError: (error) => setMessages((current) => [...current, { role: "assistant", answer: `I could not complete that request: ${error.message}`, metric_definition: "The backend request failed.", generated_at: new Date().toISOString(), data: [], sources: [], provider: "error", error: true }]),
  });

  const submit = (event) => {
    event?.preventDefault();
    const value = question.trim();
    if (!value || mutation.isPending) return;
    setMessages((current) => [...current, { role: "user", question: value, generated_at: new Date().toISOString() }]);
    setQuestion("");
    mutation.mutate({ question: value, conversationId });
  };

  const startNew = () => {
    setConversationId(null);
    setMessages([]);
  };

  return (
    <div className="assistant-layout">
      <section className="assistant-panel panel">
        <div className="chat-header">
          <div className="assistant-avatar"><Bot size={24} /></div>
          <div><strong>MusicPulse AI</strong></div>
          <button className="button secondary new-chat-button" type="button" onClick={startNew}><Plus size={16} />New chat</button>
        </div>

        <div className="chat-body">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`message-row ${message.role}`}>
              <div className="message-avatar">{message.role === "assistant" ? <Bot size={18} /> : <User size={18} />}</div>
              <div className={`message-bubble ${message.error ? "message-error" : ""}`}>
                {message.role === "user" ? <p>{message.question}</p> : <>
                  <p className="preserve-lines">{message.answer}</p>
                  {message.data?.length > 0 && <div className="answer-evidence">
                    {message.data.slice(0, 5).map((item, itemIndex) => <div key={item.video_id || item.artist_id || itemIndex} className="evidence-row">
                      <span>{itemIndex + 1}</span><div><strong>{item.title || item.artist}</strong><small>{item.artist && item.title ? item.artist : `${formatFullNumber(item.total_views)} views`}</small></div>
                      {item.url && <a href={item.url} target="_blank" rel="noreferrer"><ExternalLink size={15} /></a>}
                    </div>)}
                  </div>}
                  {message.sources?.length > 0 && <div className="rag-sources"><strong>Retrieved evidence</strong>{message.sources.slice(0, 4).map((source) => <div className="rag-source" key={source.document_id}><span>{Math.round(source.score * 100)}%</span><div><b>{source.title}</b><small>{source.source_type}</small></div>{source.source_url && <a href={source.source_url} target="_blank" rel="noreferrer"><ExternalLink size={14} /></a>}</div>)}</div>}
                  <div className="answer-source"><Database size={14} /><span>{message.metric_definition}</span></div>
                  <div className="provider-row"><span>{message.provider || "system"}</span>{message.fallback_used && <span className="fallback-chip">safe fallback</span>}</div>
                </>}
                <time>{formatDate(message.generated_at)}</time>
              </div>
            </div>
          ))}
          {mutation.isPending && <div className="message-row assistant"><div className="message-avatar"><Bot size={18} /></div><div className="message-bubble typing-bubble"><span /><span /><span /></div></div>}
        </div>

        <form className="chat-input" onSubmit={submit}>
          <div className="input-wrap"><MessageCircleQuestion size={19} /><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Type here.." /></div>
          <button className="button primary send-button" type="submit" disabled={!question.trim() || mutation.isPending}><Send size={18} />Ask</button>
        </form>
      </section>

      <aside className="assistant-sidebar">
        <article className="panel"><div className="side-card-heading"><Sparkles size={19} /><div><strong>Try asking</strong></div></div><div className="suggestion-list">{suggestions.map((item) => <button key={item} type="button" onClick={() => setQuestion(item)}>{item}</button>)}</div></article>
        <article className="panel"><div className="side-card-heading"><MessageCircleQuestion size={19} /><div><strong>Recent Chats</strong></div></div><div className="suggestion-list">{conversations.data?.slice(0, 6).map((chat) => <button key={chat.id} type="button" onClick={async () => { const loaded = await musicApi.getConversation(chat.id); setConversationId(chat.id); setMessages(loaded.messages.map((m) => m.role === "user" ? { role: "user", question: m.content, generated_at: m.created_at } : { role: "assistant", answer: m.content, metric_definition: "Loaded conversation", generated_at: m.created_at, data: [], sources: [], provider: "history" })); }}>{chat.title}</button>)}</div></article>
      </aside>
    </div>
  );
}
