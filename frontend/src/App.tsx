import "./App.css";
import ReactQueryProvider from "./contexts/ReactQueryProvider";
import Home from "./pages/Home";

function App() {
  return (
    <ReactQueryProvider>
      <Home />
    </ReactQueryProvider>
  );
}

export default App;
