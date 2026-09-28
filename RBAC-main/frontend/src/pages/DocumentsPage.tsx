import { useState, useEffect, useRef } from 'react';
import { documents } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { DocumentOut } from '../types';

const SENSITIVITY = ['public', 'internal', 'confidential', 'restricted'];

export default function DocumentsPage() {
  const { user } = useAuth();
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [sensitivity, setSensitivity] = useState('internal');
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await documents.list();
      setDocs(res.documents);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMsg(null);
    try {
      const res = await documents.upload(file, sensitivity);
      setMsg({ type: 'success', text: `Uploaded ${res.filename} — ${res.chunks_created} chunks created${res.pii_detected ? ' (PII detected)' : ''}` });
      load();
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    try {
      await documents.remove(docId);
      setMsg({ type: 'success', text: `Deleted ${filename}` });
      load();
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    }
  };

  const sensColors: Record<string, string> = {
    public: 'bg-green-100 text-green-700',
    internal: 'bg-blue-100 text-blue-700',
    confidential: 'bg-orange-100 text-orange-700',
    restricted: 'bg-red-100 text-red-700',
  };

  const canUploadRestricted = user?.role === 'exec_admin' || user?.role === 'legal_admin';

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Documents</h2>
          <p className="text-sm text-gray-500 mt-1">Upload and manage knowledge base documents</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={sensitivity}
            onChange={(e) => setSensitivity(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {SENSITIVITY.map((s) => (
              <option key={s} value={s} disabled={s === 'confidential' && !canUploadRestricted}>
                {s}
              </option>
            ))}
          </select>
          <label className={`px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-blue-700 transition ${uploading ? 'opacity-50' : ''}`}>
            {uploading ? 'Uploading...' : 'Upload Document'}
            <input ref={fileRef} type="file" accept=".txt,.pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button onClick={() => setMsg(null)} className="ml-2 font-bold">&times;</button>
        </div>
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading documents...</p>
      ) : docs.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-lg font-medium">No documents yet</p>
          <p className="text-sm mt-1">Upload a .txt or .pdf file to get started</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Filename</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Sensitivity</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Chunks</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Uploaded</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {docs.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-medium">{d.filename}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${sensColors[d.sensitivity_level] || 'bg-gray-100'}`}>
                      {d.sensitivity_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{d.chunk_count}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{new Date(d.upload_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(d.id, d.filename)}
                      className="text-red-500 hover:text-red-700 text-xs font-medium transition"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
