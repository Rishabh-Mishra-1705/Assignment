import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchRecords, approveRecord, rejectRecord, lockRecord, bulkApprove } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const FILTERS = [
  { key: 'ALL',          label: 'All Records', params: {} },
  { key: 'PENDING',      label: '⏳ Pending',   params: { status: 'PENDING' } },
  { key: 'SUSPICIOUS',   label: '⚠️ Suspicious', params: { suspicious_flag: 'true' } },
  { key: 'REJECTED',     label: '❌ Rejected',   params: { status: 'REJECTED' } },
];

export default function ReviewQueue() {
  const qc = useQueryClient();
  const [activeFilter, setActiveFilter] = useState('PENDING');
  const [selected, setSelected] = useState([]);
  const [rejectModal, setRejectModal] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  const params = FILTERS.find(f => f.key === activeFilter)?.params || {};
  const { data, isLoading } = useQuery({
    queryKey: ['records', activeFilter],
    queryFn: () => fetchRecords(params).then(r => r.data.results || r.data),
  });
  const records = data || [];

  const invalidate = () => {
    qc.invalidateQueries(['records']);
    qc.invalidateQueries(['dashboard-stats']);
  };

  const approveMut = useMutation({ mutationFn: (id) => approveRecord(id), onSuccess: invalidate });
  const rejectMut = useMutation({ mutationFn: ({ id, reason }) => rejectRecord(id, reason), onSuccess: () => { setRejectModal(null); setRejectReason(''); invalidate(); } });
  const lockMut = useMutation({ mutationFn: (id) => lockRecord(id), onSuccess: invalidate });
  const bulkMut = useMutation({ mutationFn: (ids) => bulkApprove(ids), onSuccess: () => { setSelected([]); invalidate(); } });

  const toggleSelect = (id) =>
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  const selectAll = () =>
    setSelected(records.filter(r => r.status === 'PENDING').map(r => r.id));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#1e293b' }}>🔍 Review Queue</h1>
        {selected.length > 0 && (
          <button onClick={() => bulkMut.mutate(selected)} style={primaryBtn}>
            ✅ Bulk Approve ({selected.length})
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {FILTERS.map(f => (
          <button key={f.key} onClick={() => setActiveFilter(f.key)} style={{
            padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: activeFilter === f.key ? '#1e293b' : '#f1f5f9',
            color: activeFilter === f.key ? '#fff' : '#475569',
            fontWeight: activeFilter === f.key ? 700 : 400, fontSize: 13,
          }}>
            {f.label}
          </button>
        ))}
        {records.length > 0 && activeFilter === 'PENDING' && (
          <button onClick={selectAll} style={{ ...ghostBtn2, marginLeft: 'auto' }}>
            Select All Pending
          </button>
        )}
      </div>

      {isLoading ? <p style={{ color: '#64748b' }}>Loading…</p> : (
        <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={thStyle}></th>
                <th style={thStyle}>Activity</th>
                <th style={thStyle}>Scope</th>
                <th style={thStyle}>Quantity</th>
                <th style={thStyle}>CO₂e (kg)</th>
                <th style={thStyle}>Date</th>
                <th style={thStyle}>Location</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Flags</th>
                <th style={thStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr><td colSpan={10} style={{ ...tdStyle, textAlign: 'center', color: '#94a3b8', padding: 32 }}>No records found</td></tr>
              ) : records.map(r => (
                <tr key={r.id} style={{
                  borderBottom: '1px solid #f1f5f9',
                  background: r.suspicious_flag ? '#fffbeb' : '#fff',
                }}>
                  <td style={tdStyle}>
                    {r.status === 'PENDING' && (
                      <input type="checkbox" checked={selected.includes(r.id)} onChange={() => toggleSelect(r.id)} />
                    )}
                  </td>
                  <td style={tdStyle}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{r.activity_type_display}</span>
                  </td>
                  <td style={tdStyle}>
                    <span style={{ fontSize: 12, color: '#64748b' }}>{r.scope_display?.split('—')[0]}</span>
                  </td>
                  <td style={tdStyle}>{r.normalized_quantity?.toFixed(2)} {r.normalized_unit}</td>
                  <td style={tdStyle}>{r.estimated_emission_kgco2e?.toFixed(2) ?? '—'}</td>
                  <td style={tdStyle}>{r.activity_date}</td>
                  <td style={tdStyle}>{r.location || '—'}</td>
                  <td style={tdStyle}><StatusBadge status={r.status} /></td>
                  <td style={tdStyle}>
                    {r.suspicious_flag && <span title="Suspicious" style={{ color: '#d97706', fontSize: 16 }}>⚠️</span>}
                    {r.locked_for_audit && <span title="Locked" style={{ color: '#475569', fontSize: 16 }}>🔒</span>}
                  </td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {r.status === 'PENDING' && !r.locked_for_audit && (
                        <>
                          <button onClick={() => approveMut.mutate(r.id)} style={greenBtn}>✓</button>
                          <button onClick={() => setRejectModal(r.id)} style={redBtn}>✗</button>
                        </>
                      )}
                      {r.status === 'APPROVED' && !r.locked_for_audit && (
                        <button onClick={() => lockMut.mutate(r.id)} style={grayBtn}>🔒</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModal && (
        <div style={overlay}>
          <div style={modal}>
            <h3 style={{ marginTop: 0 }}>Reject Record</h3>
            <textarea
              placeholder="Reason for rejection (required)..."
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              rows={4}
              style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 14, boxSizing: 'border-box' }}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end' }}>
              <button onClick={() => setRejectModal(null)} style={ghostBtn2}>Cancel</button>
              <button
                onClick={() => rejectReason.trim() && rejectMut.mutate({ id: rejectModal, reason: rejectReason })}
                style={{ ...redBtn, padding: '8px 20px', borderRadius: 8 }}
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const thStyle = { padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5, whiteSpace: 'nowrap' };
const tdStyle = { padding: '10px 14px', fontSize: 13, color: '#334155', verticalAlign: 'middle' };
const primaryBtn = { padding: '10px 20px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 14 };
const greenBtn = { padding: '4px 10px', background: '#d1fae5', color: '#065f46', border: '1px solid #a7f3d0', borderRadius: 6, cursor: 'pointer', fontWeight: 700 };
const redBtn = { padding: '4px 10px', background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 6, cursor: 'pointer', fontWeight: 700 };
const grayBtn = { padding: '4px 10px', background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', borderRadius: 6, cursor: 'pointer' };
const ghostBtn2 = { padding: '8px 16px', background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0', borderRadius: 8, cursor: 'pointer', fontSize: 13 };
const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 };
const modal = { background: '#fff', borderRadius: 12, padding: 24, width: 420, boxShadow: '0 20px 40px rgba(0,0,0,0.2)' };