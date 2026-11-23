-- One row per year: the headline series.
with by_year as (
    select
        year,
        any_value(exam_model)                   as exam_model,
        bool_or(is_atypical_year)               as is_atypical_year,
        count(distinct course_code)             as courses,
        sum(vagas)                              as vagas,
        sum(inscritos)                          as inscritos
    from {{ ref('fct_course_year') }}
    group by year
)

select
    b.*,
    round(b.inscritos / b.vagas, 2)                                 as candidatos_por_vaga,
    o.official_candidates,
    round(b.inscritos / o.official_candidates, 3)                   as share_of_official,
    o.includes_other_institutions                                   as official_includes_other_institutions
from by_year as b
left join {{ ref('official_candidates') }} as o using (year)
order by year
