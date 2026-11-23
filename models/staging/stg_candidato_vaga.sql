-- One row per year x modality x category x course, typed.
-- Code 999 ("Curso Treinamento - Candidato por Experiência") are practice-only candidates
-- (treineiros, 2024-2025): they do not apply for any course, so they are removed here.
select
    cast(year as integer)           as year,
    modality,
    category,
    cast(course_code as integer)    as course_code,
    course_name,
    cast(vagas as integer)          as vagas,
    cast(inscritos as integer)      as inscritos,
    source_file
from {{ source('raw', 'candidato_vaga') }}
where cast(course_code as integer) != 999
