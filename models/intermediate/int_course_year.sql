-- One row per year x modality x course with comparable totals.
--
-- inscritos: all candidates whose 1st option is the course. Read from the "Total" file
--   when it exists (2003-2012, 2020+); in 2013-2019 from "Classificação Geral", which lists
--   ALL candidates (validated: identical to "Total" in 100% of courses in 2020-2025).
-- vagas: all vacancies offered in the vestibular. In 2013-2019 the "Classificação Geral"
--   file only has the general-list vacancies, so the quota vacancies are added
--   (validated: Total = Geral + sum(quotas) in 100% of courses in 2020-2025).
with s as (
    select * from {{ ref('stg_candidato_vaga') }}
),

pivoted as (
    select
        year,
        modality,
        course_code,
        max(course_name) filter (where category in ('total', 'geral'))    as course_name,
        max(inscritos)   filter (where category = 'total')                as total_inscritos,
        max(vagas)       filter (where category = 'total')                as total_vagas,
        max(inscritos)   filter (where category = 'geral')                as geral_inscritos,
        max(vagas)       filter (where category = 'geral')                as geral_vagas,
        sum(vagas)       filter (where category like 'paa_%')             as quota_vagas,
        max(inscritos)   filter (where category = 'nao_optantes')         as ampla_inscritos,
        max(vagas)       filter (where category = 'nao_optantes')         as ampla_vagas
    from s
    group by all
)

select
    year || '-' || modality || '-' || course_code                       as course_year_key,
    year,
    modality,
    course_code,
    course_name,
    coalesce(total_inscritos, geral_inscritos)                          as inscritos,
    coalesce(total_vagas, geral_vagas + coalesce(quota_vagas, 0))       as vagas,
    case when total_vagas is not null then 'total_file'
         else 'geral_plus_quotas' end                                   as vagas_method,
    ampla_inscritos,
    ampla_vagas
from pivoted
where coalesce(total_inscritos, geral_inscritos) is not null
