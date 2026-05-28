export default function SummaryCard({ label, value, unit = '', color = '#1e293b', icon = '' }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 12, padding: '20px 24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      borderLeft: `4px solid ${color}`,
      minWidth: 160,
    }}>
      <div style={{ fontSize: 24, marginBottom: 4 }}>{icon}</div>
      <div style={{ fontSize: 28, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
        {unit && <span style={{ fontSize: 14, fontWeight: 600 }}>{unit} </span>}
        {label}
      </div>
    </div>
  );
}