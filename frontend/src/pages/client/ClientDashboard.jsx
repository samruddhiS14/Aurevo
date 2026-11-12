import { Link } from "react-router-dom";

import {
  FolderKanban,
  BriefcaseBusiness,
  CheckCircle2,
  Users,
  Wallet,
  CreditCard,
  Clock3,
  FileCheck2,
  Plus,
  Search,
  ClipboardList,
  Receipt,
  CheckCheck,
} from "lucide-react";

import useDashboard from "../../hooks/useDashboard";
import StatCard from "../../components/dashboard/StatCard";
import PaymentChart from "../../components/dashboard/PaymentChart";
import PayMilestoneButton from "../../components/payments/PayMilestoneButton";
import CaptureMilestoneButton from "../../components/payments/CaptureMilestoneButton";
import {
  DashboardLoading,
  DashboardError,
  EmptyState,
} from "../../components/dashboard/DashboardStates";

const quickActions = [
  {
    label: "Create New Project",
    description: "Start a project and define its requirements.",
    to: "/client/projects/create",
    icon: Plus,
  },
  {
    label: "View Project Applications",
    description: "Review proposals from freelancers on your projects.",
    to: "/client/projects",
    icon: Search,
  },
  {
    label: "View Active Projects",
    description: "Manage your ongoing projects.",
    to: "/client/projects",
    icon: FolderKanban,
  },
  {
    label: "Review Submissions",
    description: "Check work submitted by freelancers.",
    to: "/client/projects",
    icon: FileCheck2,
  },
  {
    label: "Manage Payments",
    description: "View your project payment records.",
    to: "/client/account",
    icon: Receipt,
  },
];

function formatMoney(value, currency = "USD") {
  if (Array.isArray(value)) return value.length ? value.map((item) => `${item.currency} ${Number(item.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`).join(" · ") : "—";
  const amount = Number(value || 0);
  try { return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(Number.isFinite(amount) ? amount : 0); }
  catch { return `${currency} ${amount.toFixed(2)}`; }
}

export default function ClientDashboard() {
  const { data, loading, error, refresh } = useDashboard("client");

  if (loading) return <DashboardLoading />;
  if (error) return <DashboardError message={error} onRetry={refresh} />;

  const stats = data?.stats || {};
  const milestones = data?.milestones || [];

  const cards = [
    {
      title: "Total Projects",
      value: stats.total_projects,
      icon: FolderKanban,
      to: "/client/projects",
    },
    {
      title: "Active Projects",
      value: stats.active_projects,
      icon: BriefcaseBusiness,
      to: "/client/projects?status=active",
    },
    {
      title: "Completed Projects",
      value: stats.completed_projects,
      icon: CheckCircle2,
      to: "/client/projects?status=completed",
    },
    {
      title: "Pending Applications",
      value: stats.pending_applications,
      icon: Users,
      to: "/client/projects",
    },
    {
      title: "PayPal Authorized",
      value: formatMoney(stats.total_authorized),
      icon: Wallet,
      description: "Verified authorization records",
      to: "/client/account",
    },
    {
      title: "PayPal Captured",
      value: formatMoney(stats.total_captured),
      icon: CreditCard,
      description: "Verified captured payments",
      to: "/client/account",
    },
    {
      title: "Pending Milestone Payments",
      value: stats.pending_milestone_payments,
      icon: Clock3,
      to: "/client/account",
    },
    {
      title: "Awaiting Submission",
      value: stats.awaiting_submission,
      icon: ClipboardList,
      to: "/client/projects",
    },
    {
      title: "Awaiting Approval",
      value: stats.awaiting_approval,
      icon: FileCheck2,
      to: "/client/projects",
    },
  ];

  return (
    <main className="min-h-screen bg-[#f8f7ff] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">

        <section className="rounded-3xl bg-gradient-to-r
          from-violet-700 via-purple-700 to-indigo-700 p-7 text-white
          shadow-lg sm:p-9">
          <p className="text-sm font-medium text-violet-100">
            Client Workspace
          </p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Your Project Dashboard
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-violet-100 sm:text-base">
            Track your projects, review freelancer submissions,
            and monitor your payments from one place.
          </p>
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Project Overview
              </h2>
              <p className="text-sm text-slate-500">
                Live figures from your account.
              </p>
            </div>
            <button
              onClick={refresh}
              className="rounded-xl border border-violet-200 bg-white
                px-4 py-2 text-sm font-semibold text-violet-700
                hover:bg-violet-50"
            >
              Refresh
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2
            lg:grid-cols-3 xl:grid-cols-3">
            {cards.map((card) => (
              <StatCard key={card.title} {...card} />
            ))}
          </div>
        </section>

        <section>
          <PaymentChart
            authorized={stats.total_authorized}
            captured={stats.total_captured}
          />
        </section>

        <section>
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2
            lg:grid-cols-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <a
                  key={action.label}
                  href={action.to}
                  className="flex items-start gap-4 rounded-2xl border
                    border-violet-100 bg-white p-5 shadow-sm
                    transition hover:-translate-y-1 hover:shadow-md"
                >
                  <div className="rounded-xl bg-violet-50 p-3 text-violet-700">
                    <Icon size={21} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">
                      {action.label}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {action.description}
                    </p>
                  </div>
                </a>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-violet-100 bg-white p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-slate-900">
              Project Milestones & Payments
            </h2>
            <p className="text-sm text-slate-500">
              Review milestone statuses and authorize payments for approved deliverables.
            </p>
          </div>

          {milestones?.length ? (
            <div className="space-y-4">
              {milestones.map((milestone) => (
                <div key={milestone.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/50 p-4">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-800">{milestone.title}</h3>
                    <Link to={`/client/projects/${milestone.project_id}/workspace`} className="text-xs font-semibold text-violet-700">Open project workspace</Link>
                    <p className="text-xs capitalize text-slate-500">
                      Status: <span className="font-medium text-violet-700">{milestone.status}</span>
                    </p>
                  </div>
                  <div className="space-y-2">
                    {milestone.payment_status === "CAPTURED" || milestone.status === "paid" ? <span className="text-sm font-semibold text-emerald-700">Paid and verified</span> : null}
                    {milestone.payment_status === "AUTHORIZED" && milestone.status === "approved" ? <CaptureMilestoneButton milestoneId={milestone.id} onSuccess={refresh} /> : null}
                    {(!milestone.payment_status || ["PENDING", "EXPIRED", "FAILED", "VOIDED"].includes(milestone.payment_status)) && ["not_started", "in_progress", "submitted", "under_review", "approved"].includes(milestone.status) ? <PayMilestoneButton milestoneId={milestone.id} /> : null}
                    {milestone.payment_status === "AUTHORIZED" && milestone.status !== "approved" && <span className="text-xs text-slate-500">Authorization active · capture after approval or eligible 72-hour auto-review</span>}
                    {milestone.payment_status === "RECONCILIATION_REQUIRED" && <span className="text-xs font-semibold text-amber-700">Payment needs reconciliation</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No milestones found"
              message="Project milestones will show up here once created."
            />
          )}
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Recent Transactions
            </h2>
            <p className="mb-4 text-sm text-slate-500">
              Your latest payment records.
            </p>

            {data?.recent_transactions?.length ? (
              <div className="space-y-3">
                {data.recent_transactions.map((transaction) => (
                  <div key={transaction.id}
                    className="flex items-center justify-between gap-3
                      border-b border-slate-100 pb-3 last:border-0">
                    <div>
                      <p className="font-medium text-slate-800">
                        Transaction #{transaction.id}
                      </p>
                      <p className="text-xs text-slate-500">
                        {transaction.created_at
                          ? new Date(transaction.created_at).toLocaleDateString()
                          : "Date unavailable"}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-slate-900">
                        {formatMoney(transaction.amount, transaction.currency)}
                      </p>
                      <p className="text-xs capitalize text-violet-700">
                        {transaction.status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No transactions yet"
                message="Verified payment transactions will appear here."
              />
            )}
          </div>

          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Upcoming Deadlines
            </h2>
            <p className="mb-4 text-sm text-slate-500">
              Milestones that need your attention.
            </p>

            {data?.upcoming_deadlines?.length ? (
              <div className="space-y-3">
                {data.upcoming_deadlines.map((item) => (
                  <div key={item.id}
                    className="rounded-xl bg-violet-50 p-4">
                    <p className="font-semibold text-slate-800">
                      {item.title}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Due: {item.due_date
                        ? new Date(item.due_date).toLocaleString()
                        : "Not specified"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No upcoming deadlines"
                message="Your upcoming milestone deadlines will appear here."
              />
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Recent Project Activity
            </h2>
            {data?.recent_activity?.length ? (
              <div className="mt-4 space-y-3">
                {data.recent_activity.map((activity, index) => (
                  <div key={activity.id ?? index}
                    className="border-b border-slate-100 pb-3">
                    <p className="font-medium text-slate-800">
                      {activity.title}
                    </p>
                    <p className="text-sm text-slate-500">
                      {activity.description}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No recent activity"
                message="Project updates will appear here when activity records exist."
              />
            )}
          </div>

          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Notifications
            </h2>
            {data?.notifications?.length ? (
              <div className="mt-4 space-y-3">
                {data.notifications.map((notification) => (
                  <div key={notification.id}
                    className="rounded-xl bg-slate-50 p-4">
                    <p className="font-semibold text-slate-800">
                      {notification.title}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {notification.message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="You're all caught up"
                message="New notifications will appear here."
              />
            )}
          </div>
        </section>
      </div>
    </main>
  );
}