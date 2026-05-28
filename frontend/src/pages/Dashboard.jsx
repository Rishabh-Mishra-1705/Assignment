import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats } from '../services/api';
import SummaryCard from '../components/SummaryCard';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => fetchDashboardStats().then(r => r.data),
    refetchInterval: 30_000,
  });

  if (isLoading) return <p style={{ color: '#64748b' }}>Loading dashboard…</p>;
  if (error) return <p style={{ color: '#dc2626' }}>Error loading stats: {error.message}</p>;

  const d = data;

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24, color: '#1e293b' }}>
        📊 ESG Data Overview
      </h1>

      {/* ── Emissions Summary ───────────────────────────────────────────── */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={sectionHead}>Emissions Summary (Approved Records Only)</h2>
        <div style={cardRow}>
          <SummaryCard label="Total CO₂e" value={d.total_tco2e} unit="tCO₂e" color="#16a34a" icon="🌍" />
          <SummaryCard label="Scope 1 — Direct" value={d.scope1_tco2e} unit="tCO₂e" color="#dc2626" icon="🔥" />
          <SummaryCard label="Scope 2 — Electricity" value={d.scope2_tco2e} unit="tCO₂e" color="#d97706" icon="⚡" />
          <SummaryCard label="Scope 3 — Travel" value={d.scope3_tco2e} unit="tCO₂e" color="#7c3aed" icon="✈️" />
        </div>
      </section>

      {/* ── Record Status ────────────────────────────────────────────────── */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={sectionHead}>Record Status</h2>
        <div style={cardRow}>
          <SummaryCard label="Total Records" value={d.total_records} color="#1e293b" icon="📋" />
          <SummaryCard label="Pending Review" value={d.pending} color="#d97706" icon="⏳" />
          <SummaryCard label="Approved" value={d.approved} color="#16a34a" icon="✅" />
          <SummaryCard label="Suspicious" value={d.suspicious} color="#dc2626" icon="⚠️" />
          <SummaryCard label="Locked for Audit" value={d.locked} color="#475569" icon="🔒" />
        </div>
      </section>

      {/* ── Recent Uploads ───────────────────────────────────────────────── */}
      <section>
        <h2 style={sectionHead}>Recent Uploads</h2>
        <table style={tableStyle}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Filename', 'Status', 'Success Rows', 'Failed Rows', 'Uploaded At'].map(h => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(d.recent_uploads || []).map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={tdStyle}>{u.original_filename}</td>
                <td style={tdStyle}><StatusBadge status={u.processing_status} /></td>
                <td style={tdStyle}>{u.success_rows}</td>
                <td style={tdStyle}>{u.failed_rows}</td>
                <td style={tdStyle}>{new Date(u.uploaded_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

const sectionHead = { fontSize: 16, fontWeight: 700, color: '#475569', marginBottom: 16, textTransform: 'uppercase', letterSpacing: 1 };
const cardRow = { display: 'flex', gap: 16, flexWrap: 'wrap' };
const tableStyle = { width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' };
const thStyle = { padding: '12px 16px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 };
const tdStyle = { padding: '12px 16px', fontSize: 14, color: '#334155' };