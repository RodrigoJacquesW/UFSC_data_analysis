-- The sum of applicants per course must be 94%-99% of the official number of candidates
-- (the gap is candidates without a valid 1st option, e.g. practice-only "treineiros").
-- Only up to 2019: from 2020 the official count covers the unified exam (other institutions)
-- or a different process.
select year, inscritos, official_candidates, share_of_official
from {{ ref('agg_year') }}
where year <= 2019
  and (share_of_official is null or share_of_official not between 0.94 and 0.99)
