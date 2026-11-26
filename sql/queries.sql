-- 1_dup_check_raw
SELECT contact_id, COUNT(*) AS n FROM (SELECT * FROM contacts) GROUP BY contact_id HAVING COUNT(*) > 1;

-- 2_funnel_by_campaign
SELECT e.campaign_id, c.segment, c.personalization,
       COUNT(*) AS sent,
       ROUND(100.0 * SUM(CASE WHEN e.status = 'bounced' THEN 1 ELSE 0 END) / COUNT(*), 1) AS bounce_pct,
       ROUND(100.0 * SUM(e.replied) / SUM(CASE WHEN e.status = 'delivered' THEN 1 ELSE 0 END), 1) AS reply_pct,
       ROUND(100.0 * SUM(e.meeting_booked) / SUM(CASE WHEN e.status = 'delivered' THEN 1 ELSE 0 END), 1) AS meeting_pct
FROM outreach_events e JOIN campaigns c ON c.campaign_id = e.campaign_id
GROUP BY e.campaign_id, c.segment, c.personalization
ORDER BY meeting_pct DESC;

-- 3_bounce_by_email_status
SELECT ct.email_status, COUNT(*) AS sent,
       ROUND(100.0 * SUM(CASE WHEN e.status = 'bounced' THEN 1 ELSE 0 END) / COUNT(*), 1) AS bounce_pct
FROM outreach_events e JOIN contacts ct ON ct.contact_id = e.contact_id
GROUP BY ct.email_status ORDER BY bounce_pct DESC;

-- 4_provider_scorecard_with_rank
WITH p AS (
  SELECT ct.provider, COUNT(*) AS contacts,
         ROUND(100.0 * AVG(CASE WHEN ct.email_status = 'valid' THEN 1.0 ELSE 0 END), 1) AS valid_email_pct,
         ROUND(100.0 * AVG(CASE WHEN ct.title_match = 'Yes' THEN 1.0 ELSE 0 END), 1) AS title_match_pct
  FROM contacts ct GROUP BY ct.provider)
SELECT provider, contacts, valid_email_pct, title_match_pct,
       ROUND(0.5 * valid_email_pct + 0.5 * title_match_pct, 1) AS quality_index,
       RANK() OVER (ORDER BY 0.5 * valid_email_pct + 0.5 * title_match_pct DESC) AS quality_rank
FROM p;

-- 5_monthly_trend
SELECT strftime('%Y-%m', sent_date) AS month, COUNT(*) AS sent,
       ROUND(100.0 * SUM(meeting_booked) / SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END), 2) AS meeting_pct
FROM outreach_events GROUP BY month ORDER BY month;

-- 6_stale_contacts
SELECT COUNT(*) AS stale_contacts FROM contacts WHERE last_verified < '2026-06-01';