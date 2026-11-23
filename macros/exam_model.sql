{# Which selection process a year belongs to. Changes in the process change who applies. #}
{% macro exam_model(year_column) %}
    case
        when {{ year_column }} = 2020 then 'Unificado UFSC/UFFS'
        when {{ year_column }} = 2021 then 'Pandemia: ENEM ou vestibulares anteriores (sem prova)'
        when {{ year_column }} >= 2023 then 'Unificado UFSC/IFSC/IFC'
        else 'Vestibular UFSC'
    end
{% endmacro %}
