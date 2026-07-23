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
    <article className="panel"><SectionHeader title="Indexed knowledge" description="Documents available to the RAG retriever." action={<button className="button secondary" onClick={() => sync.mutate()} disabled={sync.isPending}><RefreshCw size={16} className={sync.isPending ? "spin" : ""} />Sync videos</button>} />
      {query.isLoading && <LoadingState />}{query.error && <ErrorState message={query.error.message} onRetry={query.refetch} />}
      {!query.isLoading && !query.error && !query.data?.length && <EmptyState title="No indexed knowledge" description="Synchronize stored videos or add a manual document." />}
      <div className="knowledge-list">{query.data?.map((doc) => <div className="knowledge-row" key={doc.id}><div className="knowledge-icon"><BookOpen size={18} /></div><div><strong>{doc.title}</strong><span>{doc.source_type}</span></div></div>)}</div>
    </article>
  </div>;
}
