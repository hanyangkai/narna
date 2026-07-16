import { Route, Routes } from "react-router-dom";
import Footer from "./components/Footer";
import Nav from "./components/Nav";
import Benchmark from "./pages/Benchmark";
import Billing from "./pages/Billing";
import Compatibility from "./pages/Compatibility";
import Console from "./pages/Console";
import Docs from "./pages/Docs";
import Enterprise from "./pages/Enterprise";
import Landing from "./pages/Landing";
import PassportPage from "./pages/PassportPage";
import Pricing from "./pages/Pricing";
import Registry from "./pages/Registry";
import RunDetail from "./pages/RunDetail";
import Sdk from "./pages/Sdk";
import Specification from "./pages/Specification";

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/docs/:slug" element={<Docs />} />
          <Route path="/specification" element={<Specification />} />
          <Route path="/sdk" element={<Sdk />} />
          <Route path="/compatibility" element={<Compatibility />} />
          <Route path="/benchmark" element={<Benchmark />} />
          <Route path="/registry" element={<Registry />} />
          <Route path="/passport/:agentId" element={<PassportPage />} />
          <Route path="/enterprise" element={<Enterprise />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/console" element={<Console />} />
          <Route path="/console/runs/:runId" element={<RunDetail />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
