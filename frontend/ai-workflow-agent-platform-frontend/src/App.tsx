import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

import './App.css';
import LiveWorkflowPage from './pages/LiveWorkflowPage';
import RunHistoryPage from './pages/RunHistoryPage';

function App() {
  return (
    <div className="app-shell">
      <header className="app-nav">
        <div className="app-nav__brand">
          <p className="app-nav__eyebrow">AI workflow workspace</p>
          <h1 className="app-nav__title">AI Workflow Agent Platform</h1>
        </div>

        <nav className="app-nav__links" aria-label="Primary">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `app-nav__link${isActive ? ' app-nav__link--active' : ''}`
            }
          >
            Live workflow
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `app-nav__link${isActive ? ' app-nav__link--active' : ''}`
            }
          >
            Run history
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<LiveWorkflowPage />} />
        <Route path="/history" element={<RunHistoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
