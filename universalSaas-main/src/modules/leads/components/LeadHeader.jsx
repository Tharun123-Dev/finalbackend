// src/modules/leads/components/LeadHeader.jsx
import React from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export default function LeadHeader({ lead }) {
  if (!lead) return null;

  return (
    <div className="flex items-center space-x-4 mb-6 p-4 rounded-xl border bg-card shadow-sm">
      <Avatar className="h-12 w-12 bg-primary/10 text-primary font-bold text-lg">
        <AvatarFallback>{lead.name?.charAt(0)?.toUpperCase()}</AvatarFallback>
      </Avatar>
      <div>
        <h2 className="text-xl font-semibold text-foreground">{lead.name}</h2>
        <p className="text-sm text-muted-foreground">{lead.company || 'No Company'}</p>
      </div>
    </div>
  );
}