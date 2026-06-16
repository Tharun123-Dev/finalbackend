export function isModuleEnabled(modules: string[] | null, moduleName: string): boolean {
  if (!modules || !Array.isArray(modules) || modules.length === 0) return false;
  if (!moduleName || typeof moduleName !== 'string') return false;
  return modules.map(m => String(m).toUpperCase()).includes(moduleName.toUpperCase());
}


