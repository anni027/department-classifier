import { DepartmentCard } from "@/components/DepartmentCard";
import { listDepartments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DepartmentsPage() {
  const departments = await listDepartments();

  return (
    <div className="flex flex-col gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white sm:text-4xl">All Departments</h1>
        <p className="mt-2 text-white/60">15 ways to be part of Taqneeq.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {departments.map((department) => (
          <DepartmentCard key={department.id} department={department} />
        ))}
      </div>
    </div>
  );
}
