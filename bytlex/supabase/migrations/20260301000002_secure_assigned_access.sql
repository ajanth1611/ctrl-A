-- Replace broad/recursive policies with assignment-based access.
-- Every application row is accessed with the signed-in user's anon-key session.

CREATE OR REPLACE FUNCTION public.campusiq_role()
RETURNS TEXT
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT role
    FROM public.profiles
    WHERE id = auth.uid()
    LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION public.campusiq_is_assigned_staff(target_student_id TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles AS profile
        JOIN public.students AS student
          ON lower(student.mentor_email) = lower(profile.email)
        WHERE profile.id = auth.uid()
          AND profile.role = 'staff'
          AND student.student_id = target_student_id
    );
$$;

CREATE OR REPLACE FUNCTION public.campusiq_owns_student(target_student_id TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles
        WHERE id = auth.uid()
          AND role = 'student'
          AND student_id = target_student_id
    );
$$;

REVOKE ALL ON FUNCTION public.campusiq_role() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.campusiq_is_assigned_staff(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.campusiq_owns_student(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.campusiq_role() TO authenticated;
GRANT EXECUTE ON FUNCTION public.campusiq_is_assigned_staff(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.campusiq_owns_student(TEXT) TO authenticated;

DROP POLICY IF EXISTS admin_all_students ON public.students;
DROP POLICY IF EXISTS staff_assigned_students ON public.students;
DROP POLICY IF EXISTS student_own_record ON public.students;

DROP POLICY IF EXISTS profiles_read_own_or_admin ON public.profiles;
DROP POLICY IF EXISTS profiles_admin_manage ON public.profiles;
CREATE POLICY profiles_read_own_or_admin ON public.profiles
    FOR SELECT TO authenticated
    USING (id = auth.uid() OR public.campusiq_role() = 'admin');
CREATE POLICY profiles_admin_manage ON public.profiles
    FOR ALL TO authenticated
    USING (public.campusiq_role() = 'admin')
    WITH CHECK (public.campusiq_role() = 'admin');

CREATE POLICY admin_all_students ON public.students
    FOR ALL TO authenticated
    USING (public.campusiq_role() = 'admin')
    WITH CHECK (public.campusiq_role() = 'admin');
CREATE POLICY staff_read_assigned_students ON public.students
    FOR SELECT TO authenticated
    USING (public.campusiq_is_assigned_staff(student_id));
CREATE POLICY student_read_own_record ON public.students
    FOR SELECT TO authenticated
    USING (public.campusiq_owns_student(student_id));

ALTER TABLE public.data_import_jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS admin_all_data_import_jobs ON public.data_import_jobs;
CREATE POLICY admin_all_data_import_jobs ON public.data_import_jobs
    FOR ALL TO authenticated
    USING (public.campusiq_role() = 'admin')
    WITH CHECK (public.campusiq_role() = 'admin');

DROP POLICY IF EXISTS admin_all_interventions ON public.interventions;
DROP POLICY IF EXISTS staff_assigned_interventions ON public.interventions;
DROP POLICY IF EXISTS student_read_own_interventions ON public.interventions;
CREATE POLICY admin_all_interventions ON public.interventions
    FOR ALL TO authenticated
    USING (public.campusiq_role() = 'admin')
    WITH CHECK (public.campusiq_role() = 'admin');
CREATE POLICY staff_read_assigned_interventions ON public.interventions
    FOR SELECT TO authenticated
    USING (public.campusiq_is_assigned_staff(student_id));
CREATE POLICY staff_create_assigned_interventions ON public.interventions
    FOR INSERT TO authenticated
    WITH CHECK (
        public.campusiq_is_assigned_staff(student_id)
        AND lower(owner_email) = lower(auth.jwt() ->> 'email')
    );
CREATE POLICY staff_update_assigned_interventions ON public.interventions
    FOR UPDATE TO authenticated
    USING (public.campusiq_is_assigned_staff(student_id))
    WITH CHECK (public.campusiq_is_assigned_staff(student_id));
CREATE POLICY student_read_own_interventions ON public.interventions
    FOR SELECT TO authenticated
    USING (public.campusiq_owns_student(student_id));

DROP POLICY IF EXISTS admin_all_action_plan_tasks ON public.action_plan_tasks;
DROP POLICY IF EXISTS student_read_own_action_plan_tasks ON public.action_plan_tasks;
DROP POLICY IF EXISTS student_update_own_action_plan_tasks ON public.action_plan_tasks;
CREATE POLICY admin_all_action_plan_tasks ON public.action_plan_tasks
    FOR ALL TO authenticated
    USING (public.campusiq_role() = 'admin')
    WITH CHECK (public.campusiq_role() = 'admin');
CREATE POLICY student_read_own_action_plan_tasks ON public.action_plan_tasks
    FOR SELECT TO authenticated
    USING (public.campusiq_owns_student(student_id));
CREATE POLICY staff_read_assigned_action_plan_tasks ON public.action_plan_tasks
    FOR SELECT TO authenticated
    USING (public.campusiq_is_assigned_staff(student_id));
CREATE POLICY student_update_own_action_plan_tasks ON public.action_plan_tasks
    FOR UPDATE TO authenticated
    USING (public.campusiq_owns_student(student_id))
    WITH CHECK (public.campusiq_owns_student(student_id));
CREATE POLICY student_create_own_action_plan_tasks ON public.action_plan_tasks
    FOR INSERT TO authenticated
    WITH CHECK (public.campusiq_owns_student(student_id));
