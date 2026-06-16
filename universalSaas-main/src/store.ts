// src/store.ts
import { configureStore } from '@reduxjs/toolkit';
import { leadsApi } from '@/modules/leads/services/leadsApi';
import leadsReducer from '@/modules/leads/store/leadsSlice';

export const store = configureStore({
  reducer: {
    [leadsApi.reducerPath]: leadsApi.reducer,
    leads: leadsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(leadsApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

