import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import WalletConnect from "./components/WalletConnect";
import Profile from "./components/Profile";
import Unauthenticated from "./components/Unauthenticated";

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Routes>
          <Route path="/wallet/connect" element={<WalletConnect />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/auth/login" element={<Unauthenticated />} />
          <Route
            path="/"
            element={
              <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-br from-[#667eea] to-[#764ba2] text-white">
                <h1 className="text-5xl font-bold mb-4 text-center drop-shadow-lg">
                  PoolMind
                </h1>
                <p className="text-xl mb-4 max-w-2xl text-center leading-relaxed">
                  Welcome to PoolMind - Your Stacks Mining Pool Platform
                </p>
                <div className="mt-8 space-x-4">
                  <a
                    href="/profile"
                    className="bg-white text-[#667eea] px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors duration-200 no-underline"
                  >
                    View Profile
                  </a>
                  <a
                    href="/wallet/connect?redirect=/"
                    className="bg-transparent border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-[#667eea] transition-colors duration-200 no-underline"
                  >
                    Connect Wallet
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
