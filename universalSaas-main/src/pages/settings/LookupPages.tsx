import React from 'react';
import GenericLookupSettingsList from './GenericLookupSettingsList';
import GenericLookupSettingsForm from './GenericLookupSettingsForm';

// --- Employee Types ---
export function EmployeeTypeList() {
  return <GenericLookupSettingsList title="Employee Types" description="Manage employee types (e.g., Regular, Contractor)" endpoint="/employee-types" createRoute="/settings/employee-types/create" editRoutePrefix="/settings/employee-types/edit" entityLabel="Employee Type" />;
}
export function EmployeeTypeForm() {
  return <GenericLookupSettingsForm titleCreate="Create Employee Type" titleEdit="Edit Employee Type" description="Define an employment arrangement type." endpoint="/employee-types" backRoute="/settings/employee-types" entityLabel="Employee Type" />;
}

// --- Designations ---
export function DesignationList() {
  return <GenericLookupSettingsList title="Designations" description="Manage job titles and designations" endpoint="/designations" createRoute="/settings/designations/create" editRoutePrefix="/settings/designations/edit" entityLabel="Designation" />;
}
export function DesignationForm() {
  return <GenericLookupSettingsForm titleCreate="Create Designation" titleEdit="Edit Designation" description="Define a job title." endpoint="/designations" backRoute="/settings/designations" entityLabel="Designation" />;
}

// --- Work Modes ---
export function WorkModeList() {
  return <GenericLookupSettingsList title="Work Modes" description="Manage work arrangements (e.g., Office, Remote, Hybrid)" endpoint="/work-modes" createRoute="/settings/work-modes/create" editRoutePrefix="/settings/work-modes/edit" entityLabel="Work Mode" />;
}
export function WorkModeForm() {
  return <GenericLookupSettingsForm titleCreate="Create Work Mode" titleEdit="Edit Work Mode" description="Define a work location mode." endpoint="/work-modes" backRoute="/settings/work-modes" entityLabel="Work Mode" />;
}
