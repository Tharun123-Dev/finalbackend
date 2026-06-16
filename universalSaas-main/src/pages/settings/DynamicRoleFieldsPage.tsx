import React from 'react';
import { Settings2, ArrowRight } from 'lucide-react';
import EntityListPage from '@/components/shared/EntityListPage';

export default function DynamicRoleFieldsPage() {
  return (
    <EntityListPage
      title="Dynamic Role Custom Fields"
      description="Define custom fields, data-type validators, input masks, and conditional visibility policies per role profile."
    >
      <div className="max-w-3xl mx-auto py-8">
        <div className="bg-card border border-border rounded-xl p-8 text-center space-y-6 shadow-sm">
          <div className="inline-flex p-3.5 bg-primary/10 border border-primary/20 rounded-xl text-primary animate-bounce">
            <Settings2 className="w-6 h-6" />
          </div>

          <div className="space-y-2 max-w-md mx-auto">
            <h3 className="text-sm font-bold text-foreground">Dynamic Field Builder</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              We are decoupling dynamic forms from the core User RBAC modules to establish a centralized custom form layout generator.
              The field designer screen will be available here soon.
            </p>
          </div>

          {/* Graphics preview */}
          <div className="border border-border bg-muted/40 rounded-xl p-4 max-w-md mx-auto text-left space-y-3.5">
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
              Active Schema Blueprint (Mockup)
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center bg-card p-2.5 rounded-lg border border-border">
                <span className="text-foreground">Aadhaar Identification Number (Student Role)</span>
                <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded">
                  NUMERIC MASK
                </span>
              </div>
              <div className="flex justify-between items-center bg-card p-2.5 rounded-lg border border-border">
                <span className="text-foreground">PAN Identification Card (Vendor Role)</span>
                <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded">
                  ALPHANUMERIC
                </span>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 justify-center rounded-md border border-input bg-background hover:bg-accent h-9 px-4 text-xs font-semibold text-muted-foreground cursor-not-allowed opacity-50"
              disabled
            >
              Add Custom Schema Field <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </EntityListPage>
  );
}
