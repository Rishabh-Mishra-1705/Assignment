const COLORS = {
  PENDING:       { bg: '#fef3c7', color: '#92400e', label: 'Pending' },
  APPROVED:      { bg: '#d1fae5', color: '#065f46', label: 'Approved' },
  REJECTED:      { bg: '#fee2e2', color: '#991b1b', label: 'Rejected' },
  NEEDS_REVIEW:  { bg: '#e0e7ff', color: '#3730a3', label: 'Needs Review' },
  SUCCESS:       { bg: '#d1fae5', color: '#065f46', label: 'Success' },
  PARTIAL:       { bg: '#fef3c7', color: '#92400e', label: 'Partial' },
  FAILED:        { bg: '#fee2e2', color: '#991b1b', label: 'Failed' },
  PROCESSING:    { bg: '#e0e7ff', color: '#3730a3', label: 'Processing' },
};

export default function StatusBadge({ status }) {
  const s = COLORS[status] || { bg: '#f1f5f9', color: '#475569', label: status };
  return (
    <span style={{
      background: s.bg, color: s.color,
      padding: '2px 10px', borderRadius: 20,
      fontSize: 12, fontWeight: 600,
    }}>
      {s.label}
    </span>
  );
}