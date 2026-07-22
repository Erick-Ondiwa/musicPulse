/** RAG knowledge-base inspection and manual document management page. */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, FilePlus2, RefreshCw } from "lucide-react";
import { musicApi } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import SectionHeader from "../components/SectionHeader";

export default function KnowledgePage() {
  const client = useQueryClient();
  const [form, setForm] = useState({ title: "", content: "", source_url: "" });
  const query = useQuery({ queryKey: ["knowledge-documents"], queryFn: musicApi.listKnowledge });
  const sync = useMutation({ mutationFn: musicApi.syncKnowledge, onSuccess: () => client.invalidateQueries({ queryKey: ["knowledge-documents"] }) });
  const add = useMutation({ mutationFn: musicApi.addKnowledge, onSuccess: () => { setForm({ title: "", content: "", source_url: "" }); client.invalidateQueries({ queryKey: ["knowledge-documents"] }); } });

  return <div className="content-stack">
    <article className="panel knowledge-form"><SectionHeader title="Add market knowledge" description="Index a report, analyst note, campaign observation, or artist profile for semantic retrieval." />
      <form onSubmit={(event) => { event.preventDefault(); add.mutate({ ...form, source_url: form.source_url || null }); }}>
        <input placeholder="Document title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input placeholder="Optional source URL" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} />
        <textarea placeholder="Knowledge content..." value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} required minLength={10} />
        <button className="button primary" disabled={add.isPending}><FilePlus2 size={17} />{add.isPending ? "Indexing..." : "Add document"}</button>
      </form>
    </article>
    <article className="panel"><SectionHeader title="Indexed knowledge" description="Documents available to the RAG retriever." action={<button className="button secondary" onClick={() => sync.mutate()} disabled={sync.isPending}><RefreshCw size={16} className={sync.isPending ? "spin" : ""} />Sync videos</button>} />
      {query.isLoading && <LoadingState />}{query.error && <ErrorState message={query.error.message} onRetry={query.refetch} />}
      {!query.isLoading && !query.error && !query.data?.length && <EmptyState title="No indexed knowledge" description="Synchronize stored videos or add a manual document." />}
      <div className="knowledge-list">{query.data?.map((doc) => <div className="knowledge-row" key={doc.id}><div className="knowledge-icon"><BookOpen size={18} /></div><div><strong>{doc.title}</strong><span>{doc.source_type} · {doc.embedding_provider}</span></div></div>)}</div>
    </article>
  </div>;
}
