import React from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import AppDrawer from "../components/AppDrawer";
import AppFormInput from "../components/AppFormInput";
import AppSelect from "../components/AppSelect";
import { AppButton } from "../components/AppButton";

interface FormValues {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  gender: string;
  dob: string;
  department: string;
  designation: string;
  employeeId: string;
  role: string;
  status: string;
}

export const UserCreate: React.FC = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>();

  const onSubmit = async (data: FormValues) => {
    console.log("Create user payload", data);
    // TODO: call API to create user
    navigate("/users");
  };

  return (
    <AppDrawer isOpen={true} title="Create New User" onClose={() => navigate("/users")}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <AppFormInput label="First Name" name="firstName" registerField={register} error={errors.firstName && "First name required"} />
          <AppFormInput label="Last Name" name="lastName" registerField={register} error={errors.lastName && "Last name required"} />
        </div>
        <AppFormInput label="Email" type="email" name="email" registerField={register} error={errors.email && "Valid email required"} />
        <AppFormInput label="Phone" type="tel" name="phone" registerField={register} />
        <AppSelect
          label="Gender"
          name="gender"
          register={register}
          options={[
            { value: "male", label: "Male" },
            { value: "female", label: "Female" },
            { value: "other", label: "Other" },
          ]}
          error={errors.gender && "Gender required"}
        />
        <AppFormInput label="Date of Birth" type="date" name="dob" registerField={register} error={errors.dob && "DOB required"} />
        <AppFormInput label="Department" name="department" registerField={register} error={errors.department && "Department required"} />
        <AppFormInput label="Designation" name="designation" registerField={register} error={errors.designation && "Designation required"} />
        <AppFormInput label="Employee ID" name="employeeId" registerField={register} error={errors.employeeId && "Employee ID required"} />
        <AppSelect
          label="Role"
          name="role"
          register={register}
          options={[
            { value: "admin", label: "Admin" },
            { value: "manager", label: "Manager" },
            { value: "employee", label: "Employee" },
          ]}
          error={errors.role && "Role required"}
        />
        <AppSelect
          label="Status"
          name="status"
          register={register}
          options={[
            { value: "active", label: "Active" },
            { value: "inactive", label: "Inactive" },
            { value: "suspended", label: "Suspended" },
          ]}
          error={errors.status && "Status required"}
        />
        <div className="flex justify-end space-x-2 mt-4">
          <AppButton variant="secondary" type="button" onClick={() => navigate("/users")}>Cancel</AppButton>
          <AppButton variant="primary" type="submit" disabled={isSubmitting}>Create</AppButton>
        </div>
      </form>
    </AppDrawer>
  );
};

export default UserCreate;


