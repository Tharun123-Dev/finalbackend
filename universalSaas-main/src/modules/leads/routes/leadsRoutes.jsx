import React from 'react';
import { Route, Routes } from 'react-router-dom';
import LeadsDashboard from '../pages/LeadsDashboard';
import LeadsList from '../pages/LeadsList';
import LeadCreate from '../pages/LeadCreate';
import LeadDetails from '../pages/LeadDetails';
import LeadPipeline from '../pages/LeadPipeline';
import LeadFollowups from '../pages/LeadFollowups';
import LeadReports from '../pages/LeadReports';
import FormBuilder from '../pages/FormBuilder';

export default function LeadsRoutes() {
  return (
    <Routes>
      <Route path="/leads" element={<LeadsDashboard />} />
      <Route path="/leads/list" element={<LeadsList />} />
      <Route path="/leads/create" element={<LeadCreate />} />
      <Route path="/leads/:id" element={<LeadDetails />} />
      <Route path="/leads/pipeline" element={<LeadPipeline />} />
      <Route path="/leads/followups" element={<LeadFollowups />} />
      <Route path="/leads/reports" element={<LeadReports />} />
      <Route path="/settings/leads/form-builder" element={<FormBuilder />} />
    </Routes>
  );
}
