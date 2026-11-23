-- One row per course code, with the CNPq knowledge area, degree type and campus.
select
    c.course_code,
    c.course_name_latest                as course_name,
    c.grande_area,
    c.subarea,
    c.degree_type,
    c.campus,
    c.first_year,
    c.last_year
from {{ ref('course_classification') }} as c
