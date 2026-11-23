-- Every year from 2003 to 2025 must be in the series (2007 and 2010 were missing in v1).
select y as missing_year
from range(2003, 2026) as t(y)
where y not in (select year from {{ ref('agg_year') }})
