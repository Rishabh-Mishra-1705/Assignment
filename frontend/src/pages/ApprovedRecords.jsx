import { useQuery } from '@tanstack/react-query';
import { fetchRecords } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function ApprovedRecords() {
  const { data, isLoading } = useQuery({
    queryKey: ['records', 'approved'],
    queryFn: () => fetchRecords({ status: 'APPROVED' }).then(r => r.data.results || r.data),
  });

  const records = data || [];

  const totalCO2e = records
    .reduce((sum, r) => sum + (r.estimated_emission_kgco2e || 0), 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#1e293b' }}>✅ Approved Records</h1>
        <div style={{ background: '#d1fae5', padding: '8px 20px', borderRadius: 8 }}>
          <span style={{ fontSize: 13, color: '#065f46' }}>
            Total CO₂e: <strong>{(totalCO2e / 1000).toFixed(2)} tCO₂e</strong>
          </span>
        </div>
      </div>

      {isLoading ? <p style={{ color: '#64748b' }}>Loading…</p> : (
        <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                {['Activity', 'Scope', 'Qty', 'Unit', 'CO₂e (kg)', 'Date', 'Location', 'Status', 'Locked'].map(h => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={tdStyle}>{r.activity_type_display}</td>
                  <td style={tdStyle}><span style={{ fontSize: 11, color: '#64748b' }}>{r.scope}</span></td>
                  <td style={tdStyle}>{r.normalized_quantity?.toFixed(2)}</td>
                  <td style={tdStyle}>{r.normalized_unit}</td>
                  <td style={tdStyle}>{r.estimated_emission_kgco2e?.toFixed(2) ?? '—'}</td>
                  <td style={tdStyle}>{r.activity_date}</td>
                  <td style={tdStyle}>{r.location || '—'}</td>
                  <td style={tdStyle}><StatusBadge status={r.status} /></td>
                  <td style={tdStyle}>{r.locked_for_audit ? '🔒' : '—'}</td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr><td colSpan={9} style={{ ...tdStyle, textAlign: 'center', padding: 32, color: '#94a3b8' }}>No approved records yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const thStyle = { padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 };
const tdStyle = { padding: '10px 14px', fontSize: 13, color: '#334155' };