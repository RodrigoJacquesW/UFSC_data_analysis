-- Fact: applicants and vacancies per course and year (grain: year x modality x course).
select
    i.course_year_key,
    i.year,
    i.modality,
    i.course_code,
    i.inscritos,
    i.vagas,
    round(i.inscritos / nullif(i.vagas, 0), 2)              as candidatos_por_vaga,
    i.ampla_inscritos,
    i.ampla_vagas,
    i.vagas_method,
    {{ exam_model('i.year') }}                               as exam_model,
    i.year = 2021                                            as is_atypical_year
from {{ ref('int_course_year') }} as i
