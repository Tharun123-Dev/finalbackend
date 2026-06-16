// src/modules/leads/pages/LeadsDashboard.jsx
import React from 'react';
import { Card } from '@/components/ui/card';

export default function LeadsDashboard() {
  return (
    <div className="p-4 grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      <Card className="p-4">Total Leads</Card>
      <Card className="p-4">Qualified Leads</Card>
      <Card className="p-4">Converted Leads</Card>
      {/* Add more KPI cards and charts as needed */}
    </div>
  );
}