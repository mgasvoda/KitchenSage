import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout';
import { ChatPage, RecipesPage, GroceryPage, MealPlansPage, DiscoverPage } from './pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="discover" element={<DiscoverPage />} />
          <Route path="recipes" element={<RecipesPage />} />
          <Route path="grocery" element={<GroceryPage />} />
          <Route path="meal-plans" element={<MealPlansPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
