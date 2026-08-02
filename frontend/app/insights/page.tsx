"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { AccuracyLine, CategoryBar, SourceSplit, VolumeArea } from "@/components/charts";
import { api } from "@/lib/api";

export default function InsightsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["insights"], queryFn: api.insights });
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: learning } = useQuery({ queryKey: ["learning"], queryFn: api.learningStatus });

  if (isLoading || !data) {
    return (
      <div className="grid h-screen place-items-center">
        <Loader2 className="animate-spin text-muted" />
      </div>
    );
  }

  const latestAcc = data.accuracy_trend.at(-1)?.accuracy ?? null;
  const topSender = data.top_senders[0];

  return (
    <div className="h-screen overflow-auto thin-scroll">
      <header className="border-b border-hairline bg-surface px-6 py-4">
        <h1 className="text-lg font-semibold">Insights</h1>
        <p className="text-sm text-muted">A quick read on your inbox and how well the sorting is holding up.</p>
      </header>

      <div className="mx-auto max-w-5xl p-6">
        {/* Stat tiles */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Stat label="Total messages" value={data.total_emails.toLocaleString()} />
          <Stat label="Unread" value={data.unread.toLocaleString()} />
          <Stat label="Needs reply" value={data.needs_reply.toLocaleString()} accent />
          <Stat
            label="Model accuracy"
            value={latestAcc != null ? `${Math.round(latestAcc * 100)}%` : "-"}
          />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card title="Messages by category" subtitle="Where your mail lands">
            <CategoryBar data={data.by_category} />
          </Card>

          <Card title="Volume over time" subtitle="Emails received per day">
            <VolumeArea data={data.volume_by_day} />
          </Card>

          {health && !health.demo_mode ? (
            <Card title="Learning from you" subtitle="Your corrections are teaching the model">
              <div className="grid grid-cols-2 gap-4 py-2">
                <div>
                  <div className="text-2xl font-semibold">{learning?.corrections ?? 0}</div>
                  <div className="text-xs text-muted">corrections applied</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold">{learning?.classifier_examples ?? 0}</div>
                  <div className="text-xs text-muted">examples the model knows</div>
                </div>
              </div>
              <p className="mt-2 text-xs text-muted">
                An accuracy curve needs known-correct labels, which only the demo data has, so it
                isn&apos;t shown for a real inbox. Each correction still teaches the model right away
                and similar new mail follows it. Switch to demo mode to see the measured curve.
              </p>
            </Card>
          ) : (
            <Card title="Learning curve" subtitle="Accuracy on the labelled set as corrections arrive">
              {data.accuracy_trend.length > 1 ? (
                <AccuracyLine data={data.accuracy_trend} />
              ) : (
                <p className="py-10 text-center text-sm text-muted">
                  Correct a few emails in the inbox to grow this curve.
                </p>
              )}
            </Card>
          )}

          <Card title="How labels were assigned" subtitle="Rules vs. ML vs. your corrections">
            <div className="py-4">
              <SourceSplit data={data.rule_vs_ml} />
            </div>
            {topSender && (
              <p className="mt-4 text-xs text-muted">
                Top sender: <span className="text-ink-2">{topSender.sender_name || topSender.sender}</span>{" "}
                ({topSender.count})
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-xl border border-hairline bg-surface p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${accent ? "text-accent" : "text-ink"}`}>
        {value}
      </div>
    </div>
  );
}

function Card({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-hairline bg-surface p-4">
      <div className="mb-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}
