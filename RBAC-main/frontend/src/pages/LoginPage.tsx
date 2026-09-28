import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md p-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">KB RAG Assistant</h1>
            <p className="text-gray-500 mt-2">Enterprise Knowledge Base</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                placeholder="alice@enron.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                placeholder="password"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-2">Demo accounts (password: <code>password</code>):</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button onClick={() => { setEmail('alice@enron.com'); setPassword('password'); }}
                className="text-left p-2 rounded hover:bg-white transition">
                <span className="font-medium">Alice</span> — exec_admin
              </button>
              <button onClick={() => { setEmail('david@enron.com'); setPassword('password'); }}
                className="text-left p-2 rounded hover:bg-white transition">
                <span className="font-medium">David</span> — legal_admin
              </button>
              <button onClick={() => { setEmail('priya@enron.com'); setPassword('password'); }}
                className="text-left p-2 rounded hover:bg-white transition">
                <span className="font-medium">Priya</span> — finance_viewer
              </button>
              <button onClick={() => { setEmail('karen@enron.com'); setPassword('password'); }}
                className="text-left p-2 rounded hover:bg-white transition">
                <span className="font-medium">Karen</span> — general_viewer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
