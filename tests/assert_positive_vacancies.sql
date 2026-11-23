select * from {{ ref('fct_course_year') }} where vagas <= 0 or inscritos < 0
