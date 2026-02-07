import { ThemeProvider } from './contexts/ThemeContext';
import VibeCober from './components/VibeCober';

function App() {
  return (
    <ThemeProvider>
      <VibeCober />
    </ThemeProvider>
  );
}

export default App;
