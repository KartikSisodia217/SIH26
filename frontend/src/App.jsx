import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";

function App() {
  const [showDashboard, setShowDashboard] = useState(false);

  if (showDashboard) {
    return <Dashboard />;
  }

  return <Landing onLaunch={() => setShowDashboard(true)} />;
}

export default App;