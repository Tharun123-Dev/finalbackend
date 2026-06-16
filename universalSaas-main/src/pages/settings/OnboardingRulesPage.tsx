import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Mail, FileCheck } from 'lucide-react';
import EntityListPage from '@/components/shared/EntityListPage';

export default function OnboardingRulesPage() {
  return (
    <EntityListPage
      title="Onboarding Rules & Workflows"
      description="Configure event triggers, automated email dispatches, database connection configs, and contract provisions upon new profile onboarding."
    >
      <div className="max-w-3xl mx-auto py-8">
        <div className="bg-card border border-border rounded-xl p-8 text-center space-y-6 shadow-sm">
          <div className="inline-flex p-3.5 bg-primary/10 border border-primary/20 rounded-xl text-primary animate-pulse">
            <Sparkles className="w-6 h-6" />
          </div>

          <div className="space-y-2 max-w-md mx-auto">
            <h3 className="text-sm font-bold text-foreground">Onboarding Configuration Engine</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              We have successfully provisioned the underlying REST endpoints (`/onboarding-configs`) in the backend. 
              The React drag-and-drop workflow builder is currently scheduled for deployment in the next release cycle.
            </p>
          </div>

          {/* Graphical preview of upcoming modules */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left max-w-xl mx-auto pt-4">
            <div className="p-4 bg-muted/40 border border-border rounded-lg space-y-2.5">
              <Mail className="w-5 h-5 text-primary" />
              <h4 className="text-xs font-bold text-foreground">Welcome Emails</h4>
              <p className="text-[10px] text-muted-foreground leading-normal">
                Dispatches automated invitations with security credentials instantly.
              </p>
            </div>

            <div className="p-4 bg-muted/40 border border-border rounded-lg space-y-2.5">
              <FileCheck className="w-5 h-5 text-primary" />
              <h4 className="text-xs font-bold text-foreground">Contract Generation</h4>
              <p className="text-[10px] text-muted-foreground leading-normal">
                Creates offer letters and NDAs using matching templates automatically.
              </p>
            </div>

            <div className="p-4 bg-muted/40 border border-border rounded-lg space-y-2.5">
              <ShieldCheck className="w-5 h-5 text-success" />
              <h4 className="text-xs font-bold text-foreground">Access Controls</h4>
              <p className="text-[10px] text-muted-foreground leading-normal">
                Maps default security permissions based on assigned role profiles.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 justify-center rounded-md border border-input bg-background hover:bg-accent h-9 px-4 text-xs font-semibold text-muted-foreground cursor-not-allowed opacity-50"
              disabled
            >
              Configure Rule Engine <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </EntityListPage>
  );
}
