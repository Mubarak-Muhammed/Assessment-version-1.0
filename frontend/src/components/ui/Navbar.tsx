import { NavLink } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../../store';
import { toggleSidebar } from '../../store/uiSlice';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊', exact: true },
  { path: '/log', label: 'Log Interaction', icon: '✏️' },
  { path: '/interactions', label: 'All Interactions', icon: '📋' },
];

const toolItems = [
  { label: 'Log Interaction Tool', icon: '🔬' },
  { label: 'Edit Interaction Tool', icon: '✏️' },
  { label: 'Follow-Up Plan Tool', icon: '📅' },
  { label: 'Doctor Insights Tool', icon: '👨‍⚕️' },
  { label: 'Meeting Summary Tool', icon: '📝' },
];

export default function Navbar() {
  const dispatch = useDispatch<AppDispatch>();
  const { sidebarOpen } = useSelector((state: RootState) => state.ui);
  const user = { name: 'Alex Carter', role: 'Field Representative' };

  return (
    <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
      <div className="sidebar-logo">
        <button className="sidebar-toggle" onClick={() => dispatch(toggleSidebar())} title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}>
          {sidebarOpen ? '←' : '→'}
        </button>
        <div className="logo-icon">💊</div>
        <h2>PharmaCRM</h2>
        <p>AI-First Life Sciences CRM</p>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.exact}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span>{item.icon}</span>
            {sidebarOpen && <span>{item.label}</span>}
          </NavLink>
        ))}

        {sidebarOpen && <div className="nav-section-label" style={{ marginTop: '20px' }}>AI Tools</div>}
        {toolItems.map((tool, i) => (
          <div key={i} className="nav-item" style={{ cursor: 'default', opacity: 0.6, fontSize: '12px' }}>
            <span>{tool.icon}</span>
            {sidebarOpen && <span>{tool.label}</span>}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-avatar">
          <div className="avatar-circle">
            {user.name?.charAt(0) ?? 'A'}
          </div>
          {sidebarOpen && <div className="avatar-info">
            <h4>{user.name ?? 'Field Rep'}</h4>
            <p>{user.role ?? 'Representative'}</p>
          </div>}
        </div>
      </div>
    </aside>
  );
}
