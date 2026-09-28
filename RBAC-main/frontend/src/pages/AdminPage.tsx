import { useState, useEffect } from 'react';
import { admin } from '../services/api';
import type { AdminStats, AuditLog } from '../types';

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([admin.stats(), admin.auditLogs()])
      .then(([s, l]) => { setStats(s); setLogs(l); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-gray-500">Loading admin dashboard...</div>;
  if (error) return <div className="p-6 text-red-500">Error: {error}</div>;
  if (!stats) return <div className="p-6 text-gray-500">No data available</div>;

  const statCards = [
    { label: 'Total Queries', value: stats.total_queries, color: 'bg-blue-500' },
    { label: 'PII Redacted', value: stats.pii_redacted_count, color: 'bg-orange-500' },
    { label: 'RBAC Blocked', value: stats.rbac_blocked_count, color: 'bg-red-500' },
    { label: 'Documents', value: stats.documents_indexed, color: 'bg-green-500' },
    { label: 'Total Chunks', value: stats.total_chunks, color: 'bg-purple-500' },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Admin Dashboard</h2>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        {statCards.map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={`w-2 h-2 ${s.color} rounded-full mb-2`} />
            <p className="text-2xl font-bold">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Audit Logs</h3>
          <p className="text-xs text-gray-500">Recent RAG queries across all users</p>
        </div>
        {logs.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No audit logs yet</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Time</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">User</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Query</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Role</th>
                <th className="text-center px-4 py-2.5 font-medium text-gray-600">PII</th>
                <th className="text-center px-4 py-2.5 font-medium text-gray-600">Blocked</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-xs font-mono">{log.user_id.slice(0, 8)}...</td>
                  <td className="px-4 py-2.5 max-w-xs truncate">{log.query_text}</td>
                  <td className="px-4 py-2.5">
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full">{log.role_used}</span>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    {log.pii_masked ? <span className="text-orange-500 text-xs font-bold">Yes</span> : <span className="text-gray-300 text-xs">No</span>}
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    {log.rbac_blocked ? <span className="text-red-500 text-xs font-bold">Yes</span> : <span className="text-gray-300 text-xs">No</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
