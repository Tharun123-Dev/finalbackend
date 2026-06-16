import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppStoreState {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  currentUser: string | null;
  userRole: string | null;
  setCurrentUser: (user: string, role?: string) => void;
  logout: () => void;
}

export const useAppStore = create<AppStoreState>()(
  persist(
    (set) => ({
      searchQuery: '',
      setSearchQuery: (query) => set({ searchQuery: query }),
      theme: 'dark',
      toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
      currentUser: null,
      userRole: null,
      setCurrentUser: (user, role = 'STAFF') => set({ currentUser: user, userRole: role }),
      logout: () => set({ currentUser: null, userRole: null }),
    }),
    {
      name: 'vendoros-storage',
    }
  )
);
export default useAppStore;

