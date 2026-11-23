-- Applicants and vacancies per knowledge area, subarea and degree type, per year.
select
    f.year,
    f.is_atypical_year,
    d.grande_area,
    d.subarea,
    d.degree_type,
    count(distinct f.course_code)   as courses,
    sum(f.vagas)                    as vagas,
    sum(f.inscritos)                as inscritos
from {{ ref('fct_course_year') }} as f
join {{ ref('dim_course') }} as d using (course_code)
group by all
