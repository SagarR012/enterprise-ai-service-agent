import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { auth } from '../services/api';
import type { DemoUser } from '../types';

export default function UserSwitcher({ onClose }: { onClose: () => void }) {
  const { switchUser } = useAuth();
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    auth.demoUsers().then(setUsers).finally(() => setLoading(false));
  }, []);

  const handleSwitch = async (userId: string) => {
    await switchUser(userId);
    onClose();
  };

  const roleColors: Record<string, string> = {
    exec_admin: 'bg-purple-100 text-purple-700',
    legal_admin: 'bg-red-100 text-red-700',
    finance_viewer: 'bg-green-100 text-green-700',
    general_viewer: 'bg-blue-100 text-blue-700',
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-bold mb-4">Switch Demo User</h2>
        {loading ? (
          <p className="text-gray-500 text-sm">Loading users...</p>
        ) : (
          <div className="space-y-2">
            {users.map((u) => (
              <button
                key={u.id}
                onClick={() => handleSwitch(u.id)}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition text-left"
              >
                <div>
                  <p className="font-medium text-sm">{u.name}</p>
                  <p className="text-xs text-gray-500">{u.email}</p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${roleColors[u.role] || 'bg-gray-100'}`}>
                  {u.role}
                </span>
              </button>
            ))}
          </div>
        )}
        <button onClick={onClose} className="mt-4 w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition">
          Cancel
        </button>
      </div>
    </div>
  );
}
