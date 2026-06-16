import React from 'react';
import { Search as SearchIcon, Filter as FilterIcon, Plus as PlusIcon, X as XIcon } from 'lucide-react';

interface EntityPageProps {
  title: string;
  addButtonLabel?: string;
  onAddClick?: () => void;
  table: React.ReactNode;
  form?: React.ReactNode;
  isDrawerOpen?: boolean;
  closeDrawer?: () => void;
  drawerTitle?: string;
}

export default function EntityPage({
  title,
  addButtonLabel,
  onAddClick,
  table,
  form,
  isDrawerOpen = false,
  closeDrawer,
  drawerTitle = "Create"
}: EntityPageProps) {
  return (
    <div className="flex flex-col gap-4 relative min-h-full">
      {/* Header Area */}
      <div className="flex justify-between items-center flex-wrap gap-3">
        <h1 className="text-xl font-bold tracking-tight text-foreground">{title}</h1>
        
        <div className="flex gap-2 items-center flex-wrap">
          <div className="flex items-center border border-input rounded-lg bg-card px-3 h-10 w-[250px] gap-2">
            <SearchIcon className="h-4 w-4 text-muted-foreground" />
            <input 
              type="text" 
              className="border-0 bg-transparent outline-none w-full text-sm placeholder:text-muted-foreground" 
              placeholder="Search..." 
            />
          </div>
          
          <button className="inline-flex items-center gap-1.5 justify-center rounded-lg border border-input bg-card hover:bg-accent hover:text-accent-foreground h-10 px-4 text-sm font-medium text-muted-foreground active:scale-95 transition-all cursor-pointer">
            <FilterIcon className="h-3.5 w-3.5" />
            Filter
          </button>
          
          {addButtonLabel && onAddClick && (
            <button 
              className="inline-flex items-center gap-1.5 justify-center rounded-lg bg-primary text-primary-foreground hover:opacity-90 h-10 px-4 text-sm font-medium active:scale-95 transition-all cursor-pointer shadow-sm" 
              onClick={onAddClick}
            >
              <PlusIcon className="h-4 w-4" />
              {addButtonLabel}
            </button>
          )}
        </div>
      </div>

      {/* Main Table Content */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden flex-1">
        {table}
      </div>

      {/* Centered Modal instead of Slide-out Drawer */}
      {isDrawerOpen && (
        <>
          <div 
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 transition-all duration-300 animate-in fade-in" 
            onClick={closeDrawer} 
          />
          <div 
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-2rem)] max-w-2xl bg-card border border-border shadow-2xl rounded-2xl z-50 overflow-hidden animate-in zoom-in-95 duration-200"
          >
            <div className="flex justify-between items-center border-b border-border p-5">
              <h2 className="text-lg font-bold text-foreground">{drawerTitle}</h2>
              <button 
                type="button" 
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors cursor-pointer" 
                onClick={closeDrawer}
              >
                <XIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="max-h-[80vh] overflow-y-auto custom-scrollbar">
              {form}
            </div>
          </div>
        </>
      )}
    </div>
  );
}


