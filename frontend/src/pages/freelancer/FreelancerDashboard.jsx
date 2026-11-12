
import {
  Send,
  BriefcaseBusiness,
  CheckCircle2,
  Wallet,
  Clock3,
  FileCheck2,
  Search,
  ClipboardList,
  Receipt,
  TrendingUp,
} from "lucide-react";

import useDashboard from "../../hooks/useDashboard";
import StatCard from "../../components/dashboard/StatCard";
import {
  DashboardLoading,
  DashboardError,
  EmptyState,
} from "../../components/dashboard/DashboardStates";

const quickActions = [
  {
    label: "Find Projects",
    description: "Discover projects that match your skills.",
    to: "/freelancer/projects",
    icon: Search,
  },
  {
    label: "View Applications",
    description: "Track the status of your applications.",
    to: "/freelancer/applications",
    icon: Send,
  },
  {
    label: "Submit Work",
    description: "Submit completed milestone work.",
    to: "/freelancer/projects",
    icon: FileCheck2,
  },
  {
    label: "Track Milestones",
    description: "Review project milestones and due dates.",
    to: "/freelancer/projects",
    icon: ClipboardList,
  },
  {
    label: "View Earnings",
    description: "Review your verified payment history.",
    to: "/freelancer/account",
    icon: Receipt,
  },
];

function formatMoney(value, currency = "USD") {
  if (Array.isArray(value)) return value.length ? value.map((item) => `${item.currency} ${Number(item.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`).join(" · ") : "—";
  const amount = Number(value || 0);
  try { return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(Number.isFinite(amount) ? amount : 0); }
  catch { return `${currency} ${amount.toFixed(2)}`; }
}

export default function FreelancerDashboard() {
  const { data, loading, error, refresh } = useDashboard("freelancer");

  if (loading) return <DashboardLoading />;
  if (error) return <DashboardError message={error} onRetry={refresh} />;

  const stats = data?.stats || {};

  const cards = [
    {
      title: "Total Applications",
      value: stats.total_applications,
      icon: Send,
      to: "/freelancer/projects",
    },
    {
      title: "Active Projects",
      value: stats.active_projects,
      icon: BriefcaseBusiness,
      to: "/freelancer/projects?status=active",
    },
    {
      title: "Completed Projects",
      value: stats.completed_projects,
      icon: CheckCircle2,
      to: "/freelancer/projects?status=completed",
    },
    {
      title: "Pending Submissions",
      value: stats.pending_submissions,
      icon: FileCheck2,
      to: "/freelancer/projects",
    },
    {
      title: "Earnings Received",
      value: formatMoney(stats.earnings_received),
      icon: TrendingUp,
      description: "Verified captured payments",
      to: "/freelancer/account",
    },
    {
      title: "Payments Awaiting Approval",
      value: stats.payments_awaiting_approval,
      icon: Clock3,
      to: "/freelancer/projects",
    },
    {
      title: "Pending Milestone Payments",
      value: stats.pending_milestone_payments,
      icon: Wallet,
      to: "/freelancer/account",
    },
  ];

  return (
    <main className="min-h-screen bg-[#f8f7ff] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">

        <section className="rounded-3xl bg-gradient-to-r
          from-violet-700 via-purple-700 to-indigo-700 p-7 text-white
          shadow-lg sm:p-9">
          <p className="text-sm font-medium text-violet-100">
            Freelancer Workspace
          </p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Your Work Dashboard
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-violet-100 sm:text-base">
            Manage applications, track milestones, submit work,
            and monitor your verified earnings.
          </p>
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Your Overview
              </h2>
              <p className="text-sm text-slate-500">
                Live figures from your freelancer account.
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
            lg:grid-cols-3">
            {cards.map((card) => (
              <StatCard key={card.title} {...card} />
            ))}
          </div>
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
          <h2 className="text-lg font-bold text-slate-900">Your project milestones</h2>
          <div className="mt-4 space-y-3">
            {(data?.milestones || []).map((milestone) => (
              <div key={milestone.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-4">
                <div><p className="font-semibold text-slate-800">{milestone.title}</p><p className="text-xs capitalize text-violet-700">{milestone.status} · {milestone.currency} {milestone.amount}</p>{milestone.review_deadline && <p className="text-xs text-slate-500">Review deadline: {new Date(milestone.review_deadline).toLocaleString()}</p>}</div>
                <a href={`/freelancer/projects/${milestone.project_id}/workspace`} className="rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700">Open workspace</a>
              </div>
            ))}
            {!(data?.milestones || []).length && <EmptyState title="No milestones yet" message="Milestones from assigned projects will appear here." />}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Recent Transactions
            </h2>
            {data?.recent_transactions?.length ? (
              <div className="mt-4 space-y-3">
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
                title="No earnings records yet"
                message="Verified payment transactions will appear here."
              />
            )}
          </div>

          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Upcoming Deadlines
            </h2>
            {data?.upcoming_deadlines?.length ? (
              <div className="mt-4 space-y-3">
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
                message="Your milestone deadlines will appear here."
              />
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-100
            bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">
              Recent Client Activity
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
                title="No recent client activity"
                message="Updates from your active projects will appear here."
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
