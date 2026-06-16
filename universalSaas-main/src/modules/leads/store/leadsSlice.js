import { createSlice } from '@reduxjs/toolkit';
import { leadsApi } from '@/modules/leads/services/leadsApi';

const leadsSlice = createSlice({
  name: 'leads',
  initialState: {},
  reducers: {},
  extraReducers: (builder) => {
    builder.addMatcher(
      leadsApi.endpoints.getLeads.matchFulfilled,
      (state, { payload }) => {
        // optional: store normalized leads if needed
      }
    );
  },
});

export default leadsSlice.reducer;