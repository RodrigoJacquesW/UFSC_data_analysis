-- Where the "Total" file exists next to the category files (2020+), total vacancies must equal
-- general-list vacancies plus quota vacancies, and total applicants must equal the general
-- list's applicants. These two identities justify how 2013-2019 is rebuilt.
with s as (select * from {{ ref('stg_candidato_vaga') }}),
p as (
    select
        year, modality, course_code,
        max(vagas)     filter (where category = 'total')        as total_vagas,
        max(inscritos) filter (where category = 'total')        as total_inscritos,
        max(vagas)     filter (where category = 'geral')        as geral_vagas,
        max(inscritos) filter (where category = 'geral')        as geral_inscritos,
        sum(vagas)     filter (where category like 'paa_%')     as quota_vagas
    from s
    where year >= 2020
    group by all
)
select *
from p
where total_vagas is not null and geral_vagas is not null
  and (total_vagas != geral_vagas + coalesce(quota_vagas, 0) or total_inscritos != geral_inscritos)
