-- Practice-only candidates (code 999, "treineiros") must never reach the facts.
select * from {{ ref('fct_course_year') }} where course_code = 999
