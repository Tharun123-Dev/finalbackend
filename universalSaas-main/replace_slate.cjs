const fs = require('fs');
const file = 'src/pages/integrations/IntegrationsPage.tsx';
let content = fs.readFileSync(file, 'utf8');

// Replace standard text colors
content = content.replace(/text-slate-900/g, 'text-foreground');
content = content.replace(/text-slate-800/g, 'text-foreground\/90');
content = content.replace(/text-slate-700/g, 'text-foreground\/80');
content = content.replace(/text-slate-600/g, 'text-muted-foreground');
content = content.replace(/text-slate-500/g, 'text-muted-foreground');
content = content.replace(/text-slate-400/g, 'text-muted-foreground\/70');
content = content.replace(/text-slate-300/g, 'text-muted');

// Replace backgrounds
content = content.replace(/bg-slate-900/g, 'bg-foreground text-background');
content = content.replace(/bg-slate-800/g, 'bg-foreground\/90 text-background');
content = content.replace(/bg-slate-100/g, 'bg-muted');
content = content.replace(/bg-slate-50/g, 'bg-muted\/50');

// Replace borders
content = content.replace(/border-slate-900/g, 'border-border');
content = content.replace(/border-slate-800/g, 'border-border');
content = content.replace(/border-slate-300/g, 'border-border');
content = content.replace(/border-slate-200/g, 'border-border');

// Replace dynamic color assignments
content = content.replace(/color: 'slate'/g, "color: 'zinc'");
content = content.replace(/'from-slate-400 to-slate-600'/g, "'from-zinc-400 to-zinc-600'");
content = content.replace(/'from-slate-700 to-slate-900'/g, "'from-zinc-700 to-zinc-900'");

fs.writeFileSync(file, content);
console.log('Replaced slate classes successfully.');
