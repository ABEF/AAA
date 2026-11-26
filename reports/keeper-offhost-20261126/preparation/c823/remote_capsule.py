"""Fixed c823 exact off-host transport and unsigned restore; no live adoption."""
from pathlib import Path
import argparse,base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time
LAB=Path('/opt/popl-keeper-offhost-20261126-c823')
UNIT='popl-keeper-offhost-20261126-c823.service'
OLD=Path('/opt/popl-keeper-sidecar-recovery-20261126-c821')
OLD_UNIT='popl-keeper-sidecar-recovery-20261126-c821'
OLD_UNITS=(OLD_UNIT+'.service',*(OLD_UNIT+'-'+job+'.service'for job in('checks','source','target')))
POLICY_PIN='7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
CONFIG_PIN='1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
OLD_SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
TRUST_REPORT_PIN='9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371'
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED='911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
FILES={'manifest.json':(None,OUTER),
 'selection.json':(2354,'dfdabc2c7d8e2510efeaab4861fb034af2536269705ee0000f805ccaadce9bb2'),
 'alert-state.json':(812,'f256fd8ca53e4d45ac11b5c75333f6b4172b8f9579460a1fd7bab48536b3dc98'),
 'selected/manifest.json':(3867,NESTED),
 'selected/journal.json':(2752,'dbb5f86672bd14f017d9c99f3b8ff6b8e6a8cf041d2aa9c2eada60b7598a9112')}
WORKER='IiIiTkVXIHVuc2lnbmVkIG9mZi1ob3N0LXBhY2thZ2UgcmVzdG9yZSB3aXRuZXNzOyBvcmlnaW5hbCBwcm90ZWN0ZWQgbGF5b3V0IG9ubHkuIiIiCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAppbXBvcnQgaGFzaGxpYixqc29uLG9zLHJlLHNlbGVjdG9ycyxzaWduYWwsc3RhdCxzdWJwcm9jZXNzLHRpbWUsdHJhY2ViYWNrCgpMQUI9UGF0aCgnL29wdC9wb3BsLWtlZXBlci1vZmZob3N0LTIwMjYxMTI2LWM4MjMnKTtSVU5USU1FPUxBQi8ncnVudGltZScKT1JJR0lOQUw9UGF0aCgnL29wdC9wb3BsLWtlZXBlci1zaWRlY2FyLXJlY292ZXJ5LTIwMjYxMTI2LWM4MjEnKQpTT1VSQ0U9T1JJR0lOQUwvJ3NvdXJjZSc7UE9MSUNZPU9SSUdJTkFMLydydW50aW1lL3BvbGljeS5qc29uJztDT05GSUc9T1JJR0lOQUwvJ3J1bnRpbWUva2VlcGVyLWNvbmZpZy5qc29uJwpPVVRFUj0nYTlkZWE0NzVhMjIwMTRjN2ViNWZjZjk2NTg5NmViNjkxYTJiYTVjOGRlMzUyZTBjMjNkNmZkMTYxMWRiYjA1YicKTkVTVEVEPSc5MTFkOThlZjg2YjFjZDIyOTM3OGFlMTVhYzY4NWU4Y2U2NzI4NWMwMDM1YzhjZjY3MGRmY2EzY2NjYzVkMGQxJwpQT0xJQ1lfUElOPSc3ZTg1ZmY4YjY3MDk4MDNjYjlmNGU2MjExNTBkMDViMDgyNjI1OTllOTRhMmRjY2Q5YTIzZTAxYmI0MTQ1MmJhJwpDT05GSUdfUElOPScxYzNkNTEzNDNiOTkwYTJhYmM0YTg3Y2Y5ZGQ3MDQ5MjM3ZjIzYTM0YTM5NzA4Zjk0NWQ5OGYyMjhlM2Y1Y2I4JwpFTkQ9dGltZS5tb25vdG9uaWMoKSsxNjUKc2hhPWxhbWJkYSByYXc6aGFzaGxpYi5zaGEyNTYocmF3KS5oZXhkaWdlc3QoKQplbmM9bGFtYmRhIHZhbHVlOihqc29uLmR1bXBzKHZhbHVlLHNvcnRfa2V5cz1UcnVlLHNlcGFyYXRvcnM9KCcsJywnOicpLGFsbG93X25hbj1GYWxzZSkrJ1xuJykuZW5jb2RlKCkKCgpkZWYgbmVlZCh2YWx1ZSxjb2RlPSdvZmZob3N0X2Fzc2VydGlvbicpOgogICAgaWYgbm90IHZhbHVlOnJhaXNlIFZhbHVlRXJyb3IoY29kZSkKCgpkZWYgcmVhZChwYXRoKToKICAgIGJlZm9yZT1wYXRoLmxzdGF0KCk7bmVlZChzdGF0LlNfSVNSRUcoYmVmb3JlLnN0X21vZGUpYW5kIGJlZm9yZS5zdF9ubGluaz09MSBhbmQgYmVmb3JlLnN0X3NpemU8PTY1NTM2LCdmaWxlX2JvdW5kJykKICAgIGZkPW9zLm9wZW4ocGF0aCxvcy5PX1JET05MWXxvcy5PX05PRk9MTE9XfG9zLk9fTk9OQkxPQ0t8b3MuT19DTE9FWEVDKQogICAgdHJ5OgogICAgICAgIHBhcnRzPVtdO3NpemU9MAogICAgICAgIHdoaWxlIFRydWU6CiAgICAgICAgICAgIHBhcnQ9b3MucmVhZChmZCxtaW4oMTYzODQsNjU1Mzctc2l6ZSkpCiAgICAgICAgICAgIGlmIG5vdCBwYXJ0OmJyZWFrCiAgICAgICAgICAgIHNpemUrPWxlbihwYXJ0KTtuZWVkKHNpemU8PTY1NTM2LCdmaWxlX2JvdW5kJyk7cGFydHMuYXBwZW5kKHBhcnQpCiAgICAgICAgcmF3PWInJy5qb2luKHBhcnRzKTthZnRlcj1vcy5mc3RhdChmZCk7bmFtZWQ9cGF0aC5sc3RhdCgpCiAgICAgICAga2V5PWxhbWJkYSBpdGVtOihpdGVtLnN0X2RldixpdGVtLnN0X2lubyxpdGVtLnN0X3NpemUsaXRlbS5zdF9tdGltZV9ucykKICAgICAgICBuZWVkKGxlbihyYXcpPD02NTUzNiBhbmQgbGVuKHJhdyk9PWJlZm9yZS5zdF9zaXplIGFuZCBrZXkoYmVmb3JlKT09a2V5KGFmdGVyKT09a2V5KG5hbWVkKSwnZmlsZV9jaGFuZ2VkJykKICAgICAgICByZXR1cm4gcmF3CiAgICBmaW5hbGx5Om9zLmNsb3NlKGZkKQoKCmRlZiB2YWx1ZShwYXRoKTpyZXR1cm4ganNvbi5sb2FkcyhyZWFkKHBhdGgpKQoKCmRlZiBvcmlnaW5hbF9sb2NrcygpOgogICAgcmVzdWx0PVtdCiAgICBmb3IgcGF0aCBpbihPUklHSU5BTC8ncnVudGltZS9zY2hlZHVsZS9zY2hlZHVsZS5sb2NrJyxPUklHSU5BTC8ncnVudGltZS9hbGVydHMvYWxlcnQubG9jaycpOgogICAgICAgIGl0ZW09cGF0aC5sc3RhdCgpO25lZWQoc3RhdC5TX0lTUkVHKGl0ZW0uc3RfbW9kZSlhbmQgaXRlbS5zdF9ubGluaz09MQogICAgICAgICAgICBhbmQgaXRlbS5zdF91aWQ9PTY1NTM0IGFuZCBzdGF0LlNfSU1PREUoaXRlbS5zdF9tb2RlKT09MG82MDAsJ29yaWdpbmFsX2xvY2tfbWV0YWRhdGEnKQogICAgICAgIHJlc3VsdC5hcHBlbmQoW2l0ZW0uc3RfZGV2LGl0ZW0uc3RfaW5vLGl0ZW0uc3RfbW9kZSxpdGVtLnN0X3VpZCxpdGVtLnN0X25saW5rLGl0ZW0uc3Rfc2l6ZSxpdGVtLnN0X210aW1lX25zXSkKICAgIG5lZWQobGVuKHt0dXBsZShyb3dbOjJdKWZvciByb3cgaW4gcmVzdWx0fSk9PTIsJ29yaWdpbmFsX2xvY2tfYWxpYXMnKTtyZXR1cm4gcmVzdWx0CgoKZGVmIHB1Ymxpc2gobmFtZSxkYXRhKToKICAgIG5lZWQobmFtZSBpbignUFJPR1JFU1MuanNvbicsJ1JFU1VMVC5qc29uJykpO3Jhdz1lbmMoZGF0YSk7bmVlZChsZW4ocmF3KTw9MzI3NjgsJ3Jlc3VsdF9ib3VuZCcpCiAgICBwYXRoPVJVTlRJTUUvbmFtZTt0ZW1wPXBhdGgud2l0aF9zdWZmaXgoJy5wYXJ0aWFsJykKICAgIGZkPW9zLm9wZW4odGVtcCxvcy5PX1dST05MWXxvcy5PX0NSRUFUfG9zLk9fRVhDTHxvcy5PX05PRk9MTE9XLDBvNjAwKQogICAgd2l0aCBvcy5mZG9wZW4oZmQsJ3diJylhcyBzdHJlYW06c3RyZWFtLndyaXRlKHJhdyk7c3RyZWFtLmZsdXNoKCk7b3MuZnN5bmMoc3RyZWFtLmZpbGVubygpKQogICAgb3MucmVwbGFjZSh0ZW1wLHBhdGgpCgoKZGVmIHJ1bihzY3JpcHQsYXJncyk6CiAgICBuZWVkKHNjcmlwdCBpbigna2VlcGVyLXJlY292ZXJ5LnB5Jywna2VlcGVyLXNpZGVjYXItcmVjb3ZlcnkucHknKSwnY29tbWFuZF9zY29wZScpCiAgICBhcmd2PVsnL3Vzci9iaW4vcHl0aG9uMycsJy1CJyxzdHIoU09VUkNFLydzY3JpcHRzJy9zY3JpcHQpLCphcmdzXQogICAgc3RhcnRlZD10aW1lLm1vbm90b25pYygpO2RlYWRsaW5lPW1pbihFTkQsc3RhcnRlZCs3NSk7Y2hpbGQ9b3duZWQ9Tm9uZTtwYXJ0cz1bYnl0ZWFycmF5KCksYnl0ZWFycmF5KCldO3NpemU9MAogICAgdHJ5OgogICAgICAgIGNoaWxkPXN1YnByb2Nlc3MuUG9wZW4oYXJndixzdGRpbj1zdWJwcm9jZXNzLkRFVk5VTEwsc3Rkb3V0PXN1YnByb2Nlc3MuUElQRSxzdGRlcnI9c3VicHJvY2Vzcy5QSVBFLAogICAgICAgICAgICBzdGFydF9uZXdfc2Vzc2lvbj1UcnVlLGNsb3NlX2Zkcz1UcnVlKTtvd25lZD1jaGlsZAogICAgICAgIHdpdGggc2VsZWN0b3JzLkRlZmF1bHRTZWxlY3RvcigpYXMgc2VsZWN0b3I6CiAgICAgICAgICAgIGZvciBpbmRleCxwaXBlIGluIGVudW1lcmF0ZSgoY2hpbGQuc3Rkb3V0LGNoaWxkLnN0ZGVycikpOgogICAgICAgICAgICAgICAgb3Muc2V0X2Jsb2NraW5nKHBpcGUuZmlsZW5vKCksRmFsc2UpO3NlbGVjdG9yLnJlZ2lzdGVyKHBpcGUsc2VsZWN0b3JzLkVWRU5UX1JFQUQsaW5kZXgpCiAgICAgICAgICAgIHdoaWxlIHNlbGVjdG9yLmdldF9tYXAoKToKICAgICAgICAgICAgICAgIG5lZWQodGltZS5tb25vdG9uaWMoKTxkZWFkbGluZSwnY29tbWFuZF9kZWFkbGluZScpCiAgICAgICAgICAgICAgICBmb3Iga2V5LF8gaW4gc2VsZWN0b3Iuc2VsZWN0KG1pbiguMSxtYXgoLjAwMSxkZWFkbGluZS10aW1lLm1vbm90b25pYygpKSkpOgogICAgICAgICAgICAgICAgICAgIHJhdz1vcy5yZWFkKGtleS5mZCxtaW4oMTYzODQsNjU1Mzctc2l6ZSkpCiAgICAgICAgICAgICAgICAgICAgaWYgbm90IHJhdzpzZWxlY3Rvci51bnJlZ2lzdGVyKGtleS5maWxlb2JqKTtjb250aW51ZQogICAgICAgICAgICAgICAgICAgIHNpemUrPWxlbihyYXcpO25lZWQoc2l6ZTw9NjU1MzYsJ2NvbW1hbmRfY2FwdHVyZV9ib3VuZCcpO3BhcnRzW2tleS5kYXRhXS5leHRlbmQocmF3KQogICAgICAgIGNvZGU9Y2hpbGQud2FpdCh0aW1lb3V0PW1heCguMDAxLGRlYWRsaW5lLXRpbWUubW9ub3RvbmljKCkpKTtvd25lZD1Ob25lCiAgICAgICAgb3V0LGVycj1tYXAoYnl0ZXMscGFydHMpO25lZWQoY29kZT09MCBhbmQgbm90IGVyciwnb3JpZ2luYWxfY2xpX3JlZnVzZWQnKQogICAgICAgIGlmIHNjcmlwdD09J2tlZXBlci1zaWRlY2FyLXJlY292ZXJ5LnB5JzoKICAgICAgICAgICAgcGFyc2VkPWpzb24ubG9hZHMob3V0KTtuZWVkKHBhcnNlZFsnb2snXWlzIFRydWUgYW5kIHBhcnNlZFsndW5zaWduZWQnXWlzIFRydWUgYW5kIHBhcnNlZFsncmVhZGluZXNzX2FwcHJvdmVkJ11pcyBGYWxzZSwnc2lkZWNhcl9jbGlfcmVzdWx0JykKICAgICAgICBlbHNlOgogICAgICAgICAgICBtYXRjaD1yZS5zZWFyY2gocideKD86TWFuaWZlc3R8UmVzdG9yZSBwbGFuKSBTSEEtMjU2OiAoWzAtOWEtZl17NjR9KSQnLG91dC5kZWNvZGUoJ3V0ZjgnLCdzdHJpY3QnKSxyZS5NKQogICAgICAgICAgICBuZWVkKG1hdGNoIGlzIG5vdCBOb25lLCduYXRpdmVfY2xpX3Jlc3VsdCcpO3BhcnNlZD17J21hbmlmZXN0X29yX3BsYW5fc2hhMjU2JzptYXRjaFsxXX0KICAgICAgICByZXR1cm57J3NjcmlwdCc6c2NyaXB0LCdhY3Rpb24nOmFyZ3NbMF0sJ2FyZ3YnOmFyZ3YsJ3JldHVybmNvZGUnOmNvZGUsCiAgICAgICAgICAgICdlbGFwc2VkX3NlY29uZHMnOnRpbWUubW9ub3RvbmljKCktc3RhcnRlZCwnc3Rkb3V0X3NoYTI1Nic6c2hhKG91dCksJ3N0ZG91dF9ieXRlcyc6bGVuKG91dCksJ3BhcnNlZCc6cGFyc2VkfQogICAgZmluYWxseToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGlmIG93bmVkIGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgaWYgb3duZWQucG9sbCgpaXMgTm9uZToKICAgICAgICAgICAgICAgICAgICB0cnk6b3Mua2lsbHBnKG93bmVkLnBpZCxzaWduYWwuU0lHS0lMTCkKICAgICAgICAgICAgICAgICAgICBleGNlcHQgUHJvY2Vzc0xvb2t1cEVycm9yOnBhc3MKICAgICAgICAgICAgICAgIG93bmVkLndhaXQodGltZW91dD0yKQogICAgICAgIGZpbmFsbHk6CiAgICAgICAgICAgIGlmIGNoaWxkIGlzIG5vdCBOb25lOmNoaWxkLnN0ZG91dC5jbG9zZSgpO2NoaWxkLnN0ZGVyci5jbG9zZSgpCgoKZGVmIG1haW4oKToKICAgIG5lZWQob3MuZ2V0dWlkKCk9PW9zLmdldGdpZCgpPT02NTUzNCBhbmQgc2V0KG9zLmdldGdyb3VwcygpKTw9ezY1NTM0fSwnd3JvbmdfdWlkJykKICAgIHJlc3VsdD17J3NjaGVtYSc6MSwnc3VjY2Vzcyc6RmFsc2UsJ3Vuc2lnbmVkJzpUcnVlLCdyZWFkaW5lc3NfYXBwcm92ZWQnOkZhbHNlLAogICAgICAgICdwcm9kdWN0aW9uX2FwcHJvdmVkJzpGYWxzZSwncHVibGljX3RyYW5zYWN0aW9ucyc6MCwnUlBDX2NhbGxzJzowLCd0ZXN0X2JvZGllc19ydW4nOjAsCiAgICAgICAgJ3NvdXJjZV9zZXJ2aWNlc19zdGFydGVkJzpGYWxzZSwnb2xkX3BvbGljeV9jaGFuZ2VkJzpGYWxzZSwnbmV3X3Jldmlld19tYXhfYWdlX3NlY29uZHMnOjg2NDAwLAogICAgICAgICdvcGVyYXRpbmdfcG9saWN5X21heF9iYWNrdXBfYWdlX3NlY29uZHMnOjkwMCwncmVzdG9yZXNfYXJlX3Jldmlld19vbmx5JzpUcnVlfQogICAgY2FsbHM9W107YmVnYW49dGltZS5tb25vdG9uaWMoKQogICAgdHJ5OgogICAgICAgIG5lZWQoc2hhKHJlYWQoUE9MSUNZKSk9PVBPTElDWV9QSU4gYW5kIHNoYShyZWFkKENPTkZJRykpPT1DT05GSUdfUElOLCdzZXBhcmF0ZV9yZWZlcmVuY2VfcGluJykKICAgICAgICBwb2xpY3k9dmFsdWUoUE9MSUNZKTtjb25maWc9dmFsdWUoQ09ORklHKQogICAgICAgIG5lZWQocG9saWN5WydtYXhfYmFja3VwX2FnZV9zZWNvbmRzJ109PTkwMCBhbmQgcG9saWN5WydtYXhfYnl0ZXMnXT09MTY3NzcyMTYgYW5kIHBvbGljeVsnbWF4X3NlY29uZHMnXT09NjAsJ29yaWdpbmFsX3BvbGljeScpCiAgICAgICAgbWFza19pZHM9W10KICAgICAgICBmb3Iga2V5IGluKCdrZXlzdG9yZScsJ3Bhc3N3b3JkX2ZpbGUnKToKICAgICAgICAgICAgcGF0aD1QYXRoKGNvbmZpZ1trZXldKTtpdGVtPXBhdGgubHN0YXQoKQogICAgICAgICAgICBuZWVkKHN0YXQuU19JU1JFRyhpdGVtLnN0X21vZGUpYW5kIGl0ZW0uc3RfdWlkPT0wIGFuZCBzdGF0LlNfSU1PREUoaXRlbS5zdF9tb2RlKT09MAogICAgICAgICAgICAgICAgYW5kIGl0ZW0uc3Rfc2l6ZT09MCBhbmQgaXRlbS5zdF9ubGluaz09MSwnbWFza19tZXRhZGF0YScpCiAgICAgICAgICAgIHRyeTpmZD1vcy5vcGVuKHBhdGgsb3MuT19SRE9OTFl8b3MuT19OT0ZPTExPVykKICAgICAgICAgICAgZXhjZXB0IFBlcm1pc3Npb25FcnJvcjpwYXNzCiAgICAgICAgICAgIGVsc2U6b3MuY2xvc2UoZmQpO3JhaXNlIFZhbHVlRXJyb3IoJ21hc2tfcmVhZGFibGUnKQogICAgICAgICAgICBtYXNrX2lkcy5hcHBlbmQoW2l0ZW0uc3RfZGV2LGl0ZW0uc3RfaW5vXSkKICAgICAgICBuZWVkKGxlbih7dHVwbGUocm93KWZvciByb3cgaW4gbWFza19pZHN9KT09MiwnbWFza19hbGlhcycpCiAgICAgICAgcGFja2FnZT1SVU5USU1FLydpbXBvcnRlZCc7b3V0ZXI9dmFsdWUocGFja2FnZS8nbWFuaWZlc3QuanNvbicpO25lc3RlZD12YWx1ZShwYWNrYWdlLydzZWxlY3RlZC9tYW5pZmVzdC5qc29uJykKICAgICAgICBuZWVkKHNoYShyZWFkKHBhY2thZ2UvJ21hbmlmZXN0Lmpzb24nKSk9PU9VVEVSIGFuZCBzaGEocmVhZChwYWNrYWdlLydzZWxlY3RlZC9tYW5pZmVzdC5qc29uJykpPT1ORVNURUQsJ3RyYW5zcG9ydF9waW5zJykKICAgICAgICBjdXJyZW50PWludCh0aW1lLnRpbWUoKSk7YWdlcz17J291dGVyJzpjdXJyZW50LW91dGVyWydjcmVhdGVkX2F0J10sJ25lc3RlZCc6Y3VycmVudC1uZXN0ZWRbJ2NyZWF0ZWRfYXQnXX0KICAgICAgICBuZWVkKGFsbCgwPD1hZ2U8PTg2NDAwIGZvciBhZ2UgaW4gYWdlcy52YWx1ZXMoKSksJ3Jldmlld19jYXB0dXJlX2FnZScpCiAgICAgICAgcmVzdWx0LnVwZGF0ZShjYXB0dXJlX2FnZXNfc2Vjb25kcz1hZ2VzLG9yaWdpbmFsX2NhcHR1cmVfdGltZXM9eydvdXRlcic6b3V0ZXJbJ2NyZWF0ZWRfYXQnXSwnbmVzdGVkJzpuZXN0ZWRbJ2NyZWF0ZWRfYXQnXX0sCiAgICAgICAgICAgIG9wZXJhdGlvbmFsX2ZyZXNobmVzc19hcHByb3ZlZD1GYWxzZSxvdXRzaWRlX29yaWdpbmFsX29wZXJhdGluZ19hZ2U9YWxsKGFnZT45MDAgZm9yIGFnZSBpbiBhZ2VzLnZhbHVlcygpKSwKICAgICAgICAgICAgYXNvZl9jbG9ja19vdmVycmlkZT1GYWxzZSxzaWduZXJfbWFza3NfZGlzdGluY3RfdW5yZWFkYWJsZT1tYXNrX2lkcykKICAgICAgICBvbGRfbG9ja3M9b3JpZ2luYWxfbG9ja3MoKQogICAgICAgIG5hdGl2ZT1bJy0tY29uZmlnJyxzdHIoQ09ORklHKSwnLS1idW5kbGUnLHN0cihwYWNrYWdlLydzZWxlY3RlZCcpLCctLW1hbmlmZXN0LXNoYTI1NicsTkVTVEVELAogICAgICAgICAgICAnLS1tYXgtYWdlLXNlY29uZHMnLCc4NjQwMCcsJy0tbWluaW11bS1jcmVhdGVkLWF0JyxzdHIobmVzdGVkWydjcmVhdGVkX2F0J10pXQogICAgICAgIHNpZGU9WyctLXBvbGljeScsc3RyKFBPTElDWSksJy0tcG9saWN5LXNoYTI1NicsUE9MSUNZX1BJTiwnLS1idW5kbGUnLHN0cihwYWNrYWdlKSwKICAgICAgICAgICAgJy0tbWFuaWZlc3Qtc2hhMjU2JyxPVVRFUiwnLS1tYXgtYWdlLXNlY29uZHMnLCc4NjQwMCcsJy0tbWluaW11bS1jcmVhdGVkLWF0JyxzdHIob3V0ZXJbJ2NyZWF0ZWRfYXQnXSldCiAgICAgICAgdGFza3M9Wygna2VlcGVyLXJlY292ZXJ5LnB5JyxbJ3ZlcmlmeScsKm5hdGl2ZV0pLAogICAgICAgICAgICAoJ2tlZXBlci1yZWNvdmVyeS5weScsWydyZXN0b3JlJywqbmF0aXZlLCctLW91dHB1dCcsc3RyKFJVTlRJTUUvJ2tlZXBlci1yZXZpZXcnKV0pLAogICAgICAgICAgICAoJ2tlZXBlci1zaWRlY2FyLXJlY292ZXJ5LnB5JyxbJ3ZlcmlmeScsKnNpZGVdKSwKICAgICAgICAgICAgKCdrZWVwZXItc2lkZWNhci1yZWNvdmVyeS5weScsWydyZXN0b3JlJywqc2lkZSwnLS1vdXRwdXQnLHN0cihSVU5USU1FLydzaWRlY2FyLXJldmlldycpXSldCiAgICAgICAgZm9yIHNjcmlwdCxhcmdzIGluIHRhc2tzOgogICAgICAgICAgICBwdWJsaXNoKCdQUk9HUkVTUy5qc29uJyx7J3NjaGVtYSc6MSwnY29tcGxldGVkJzpjYWxscywnbmV4dCc6c2NyaXB0Kyc6JythcmdzWzBdfSkKICAgICAgICAgICAgY2FsbHMuYXBwZW5kKHJ1bihzY3JpcHQsYXJncykpCiAgICAgICAga2VlcGVyPVJVTlRJTUUvJ2tlZXBlci1yZXZpZXcnO3NpZGVjYXI9UlVOVElNRS8nc2lkZWNhci1yZXZpZXcnCiAgICAgICAgc2VsZWN0ZWQ9dmFsdWUocGFja2FnZS8nc2VsZWN0aW9uLmpzb24nKTtnZW5lcmF0aW9uPXNlbGVjdGVkWydnZW5lcmF0aW9uJ10KICAgICAgICBjb21wYXJpc29ucz17CiAgICAgICAgICAgICdrZWVwZXItc3RhdGUuanNvbic6KHBhY2thZ2UvJ3NlbGVjdGVkL2pvdXJuYWwuanNvbicsa2VlcGVyLydrZWVwZXItc3RhdGUuanNvbicpLAogICAgICAgICAgICAnc2NoZWR1bGVyL3NlbGVjdGVkLmpzb24nOihwYWNrYWdlLydzZWxlY3Rpb24uanNvbicsc2lkZWNhci8nc2NoZWR1bGVyL3NlbGVjdGVkLmpzb24nKSwKICAgICAgICAgICAgJ2FsZXJ0cy9zdGF0ZS5qc29uJzoocGFja2FnZS8nYWxlcnQtc3RhdGUuanNvbicsc2lkZWNhci8nYWxlcnRzL3N0YXRlLmpzb24nKSwKICAgICAgICAgICAgJ3NlbGVjdGVkL21hbmlmZXN0Lmpzb24nOihwYWNrYWdlLydzZWxlY3RlZC9tYW5pZmVzdC5qc29uJyxzaWRlY2FyLydiYWNrdXBzJy9nZW5lcmF0aW9uLydtYW5pZmVzdC5qc29uJyksCiAgICAgICAgICAgICdzZWxlY3RlZC9qb3VybmFsLmpzb24nOihwYWNrYWdlLydzZWxlY3RlZC9qb3VybmFsLmpzb24nLHNpZGVjYXIvJ2JhY2t1cHMnL2dlbmVyYXRpb24vJ2pvdXJuYWwuanNvbicpfQogICAgICAgIGNvbXBhcmVkPXt9CiAgICAgICAgZm9yIG5hbWUsKHNvdXJjZSx0YXJnZXQpaW4gY29tcGFyaXNvbnMuaXRlbXMoKToKICAgICAgICAgICAgcmF3PXJlYWQoc291cmNlKTtuZWVkKHJhdz09cmVhZCh0YXJnZXQpLCdyZXN0b3JlZF9yYXdfYnl0ZXNfZGlmZmVyJyk7Y29tcGFyZWRbbmFtZV09eydieXRlcyc6bGVuKHJhdyksJ3NoYTI1Nic6c2hhKHJhdyl9CiAgICAgICAgbmF0aXZlX3BsYW49dmFsdWUoa2VlcGVyLydSRVNUT1JFX1BMQU4uanNvbicpO3NpZGVfcGxhbj12YWx1ZShzaWRlY2FyLydSRVNUT1JFX1BMQU4uanNvbicpCiAgICAgICAgbmF0aXZlX3BsYW5fcGluPXNoYShyZWFkKGtlZXBlci8nUkVTVE9SRV9QTEFOLmpzb24nKSk7c2lkZV9wbGFuX3Bpbj1zaGEocmVhZChzaWRlY2FyLydSRVNUT1JFX1BMQU4uanNvbicpKQogICAgICAgIG5lZWQoY2FsbHNbMF1bJ3BhcnNlZCddWydtYW5pZmVzdF9vcl9wbGFuX3NoYTI1NiddPT1ORVNURUQKICAgICAgICAgICAgYW5kIGNhbGxzWzFdWydwYXJzZWQnXVsnbWFuaWZlc3Rfb3JfcGxhbl9zaGEyNTYnXT09bmF0aXZlX3BsYW5fcGluCiAgICAgICAgICAgIGFuZCBjYWxsc1syXVsncGFyc2VkJ11bJ21hbmlmZXN0X3NoYTI1NiddPT1PVVRFUgogICAgICAgICAgICBhbmQgY2FsbHNbM11bJ3BhcnNlZCddWydtYW5pZmVzdF9zaGEyNTYnXT09T1VURVIKICAgICAgICAgICAgYW5kIGNhbGxzWzNdWydwYXJzZWQnXVsncmVzdG9yZV9wbGFuX3NoYTI1NiddPT1zaWRlX3BsYW5fcGluLCdDTElfb3V0cHV0X2JpbmRpbmcnKQogICAgICAgIG5lZWQobmF0aXZlX3BsYW5bJ3Vuc2lnbmVkJ11pcyBUcnVlIGFuZCBhbGwobmF0aXZlX3BsYW5ba2V5XWlzIEZhbHNlIGZvciBrZXkgaW4KICAgICAgICAgICAgKCdsaXZlX3JlYWR5JywnY2Fub25pY2FsX3N0YXRlX3ZlcmlmaWVkJywnb2xkX2tlZXBlcl9mZW5jZWQnLCdzaWduZXJfbWF0ZXJpYWxfaW5jbHVkZWQnLCdjb25maWd1cmF0aW9uX2luc3RhbGxlZCcsJ3NlcnZpY2VfcmVzdGFydGVkJykpLCduYXRpdmVfYWRvcHRpb25fZmxhZycpCiAgICAgICAgbmVlZChzaWRlX3BsYW5bJ3Vuc2lnbmVkJ11pcyBUcnVlIGFuZCBhbGwoc2lkZV9wbGFuW2tleV1pcyBGYWxzZSBmb3Iga2V5IGluCiAgICAgICAgICAgICgncmVhZGluZXNzX2FwcHJvdmVkJywnb2xkX3NpZGVjYXJzX2ZlbmNlZCcsJ2Nhbm9uaWNhbF9zdGF0ZV92ZXJpZmllZCcsJ3NpZ25lcl9tYXRlcmlhbF9pbmNsdWRlZCcsCiAgICAgICAgICAgICAncG9saWN5X29yX2NvbmZpZ3VyYXRpb25faW5zdGFsbGVkJywnc2VydmljZXNfcmVzdGFydGVkJywncnVudGltZV9wYXRoc19tYXBwZWQnLCdsb2NrX293bmVyc2hpcF9yZXN0b3JlZCcsJ3NlbGVjdGVkX2dlbmVyYXRpb25fZnJlc2huZXNzX2FwcHJvdmVkJykpLCdzaWRlY2FyX2Fkb3B0aW9uX2ZsYWcnKQogICAgICAgIGxvY2tzPVtdCiAgICAgICAgZm9yIHBhdGggaW4oc2lkZWNhci8nc2NoZWR1bGVyL3NjaGVkdWxlLmxvY2snLHNpZGVjYXIvJ2FsZXJ0cy9hbGVydC5sb2NrJyk6CiAgICAgICAgICAgIGl0ZW09cGF0aC5sc3RhdCgpO25lZWQoc3RhdC5TX0lTUkVHKGl0ZW0uc3RfbW9kZSlhbmQgaXRlbS5zdF91aWQ9PTY1NTM0CiAgICAgICAgICAgICAgICBhbmQgc3RhdC5TX0lNT0RFKGl0ZW0uc3RfbW9kZSk9PTBvNjAwIGFuZCBpdGVtLnN0X25saW5rPT0xIGFuZCBpdGVtLnN0X3NpemU9PTAsJ25ld19sb2NrX21ldGFkYXRhJykKICAgICAgICAgICAgbmVlZChyZWFkKHBhdGgpPT1iJycsJ25ld19sb2NrX25vdF9lbXB0eScpCiAgICAgICAgICAgIGxvY2tzLmFwcGVuZChbaXRlbS5zdF9kZXYsaXRlbS5zdF9pbm9dKQogICAgICAgIG5lZWQobGVuKHt0dXBsZShyb3cpZm9yIHJvdyBpbiBsb2Nrc30pPT0yLCduZXdfbG9ja19hbGlhcycpCiAgICAgICAgbmVlZChvcmlnaW5hbF9sb2NrcygpPT1vbGRfbG9ja3MgYW5kIHt0dXBsZShyb3cpZm9yIHJvdyBpbiBsb2Nrc30uaXNkaXNqb2ludCgKICAgICAgICAgICAge3R1cGxlKHJvd1s6Ml0pZm9yIHJvdyBpbiBvbGRfbG9ja3N9KSwnb3JpZ2luYWxfbG9ja19yZXVzZWRfb3JfY2hhbmdlZCcpCiAgICAgICAgb2JzZXJ2ZXI9dmFsdWUoc2lkZWNhci8nYWxlcnRzL3N0YXRlLmpzb24nKTtzdGF0ZT12YWx1ZShrZWVwZXIvJ2tlZXBlci1zdGF0ZS5qc29uJykKICAgICAgICBuZWVkKG9ic2VydmVyPT12YWx1ZShwYWNrYWdlLydhbGVydC1zdGF0ZS5qc29uJylhbmQgc3RhdGU9PXZhbHVlKHBhY2thZ2UvJ3NlbGVjdGVkL2pvdXJuYWwuanNvbicpLCdhY2NvdW50aW5nX3N0YXRlX2NoYW5nZWQnKQogICAgICAgIG5lZWQoc2hhKHJlYWQoUE9MSUNZKSk9PVBPTElDWV9QSU4gYW5kIHNoYShyZWFkKENPTkZJRykpPT1DT05GSUdfUElOLCdzZXBhcmF0ZV9yZWZlcmVuY2VfY2hhbmdlZCcpCiAgICAgICAgcmVzdWx0LnVwZGF0ZShzdWNjZXNzPVRydWUsY2FsbHM9Y2FsbHMscmVzdG9yZWRfZmlsZXM9Y29tcGFyZWQsCiAgICAgICAgICAgIG5hdGl2ZV9yZXN0b3JlX3BsYW5fc2hhMjU2PW5hdGl2ZV9wbGFuX3BpbixzaWRlY2FyX3Jlc3RvcmVfcGxhbl9zaGEyNTY9c2lkZV9wbGFuX3BpbiwKICAgICAgICAgICAgYWxsX2Fkb3B0aW9uX2ZsYWdzX2ZhbHNlPVRydWUsbmV3X2VtcHR5X2xvY2tfaW5vZGVfcGFpcnM9bG9ja3MsCiAgICAgICAgICAgIG9yaWdpbmFsX2xvY2tfbWV0YWRhdGFfdW5jaGFuZ2VkPW9sZF9sb2NrcyxuZXdfbG9ja3NfZGlzam9pbnRfZnJvbV9vcmlnaW5hbHM9VHJ1ZSwKICAgICAgICAgICAgcGVuZGluZ19zdW1tYXJ5PXNpZGVfcGxhblsnb2JzZXJ2ZXJfc3VtbWFyeSddWydwZW5kaW5nJ10sb3V0Ym94X2lkcz1bZVsnZXZlbnRfaWQnXWZvciBlIGluIG9ic2VydmVyWydvdXRib3gnXV0sCiAgICAgICAgICAgIHNlcXVlbmNlPW9ic2VydmVyWydzZXF1ZW5jZSddLHJhd19yZWNvcmRzX3Jld3JpdHRlbj1GYWxzZSxvcmlnaW5hbF90aW1lc3RhbXBzX3ByZXNlcnZlZD1UcnVlKQogICAgZXhjZXB0IEJhc2VFeGNlcHRpb24gYXMgZXhjOgogICAgICAgIHJlc3VsdC51cGRhdGUoZXJyb3JfdHlwZT10eXBlKGV4YykuX19uYW1lX18sZXJyb3Jfc2hhMjU2PXNoYShzdHIoZXhjKS5lbmNvZGUoKSksY2FsbHM9Y2FsbHMsCiAgICAgICAgICAgIGZyYW1lcz1beydmaWxlJzpQYXRoKGZyYW1lLmZpbGVuYW1lKS5uYW1lLCdsaW5lJzpmcmFtZS5saW5lbm8sJ2Z1bmN0aW9uJzpmcmFtZS5uYW1lfQogICAgICAgICAgICAgICAgZm9yIGZyYW1lIGluIHRyYWNlYmFjay5leHRyYWN0X3RiKGV4Yy5fX3RyYWNlYmFja19fKVstODpdXSkKICAgIHJlc3VsdFsnZWxhcHNlZF9zZWNvbmRzJ109dGltZS5tb25vdG9uaWMoKS1iZWdhbjtwdWJsaXNoKCdSRVNVTFQuanNvbicscmVzdWx0KQogICAgcHJpbnQoanNvbi5kdW1wcyh7J3N1Y2Nlc3MnOnJlc3VsdFsnc3VjY2VzcyddLCdjb21wbGV0ZWRfb3JpZ2luYWxfQ0xJX2NhbGxzJzpsZW4oY2FsbHMpfSkpCiAgICByZXR1cm4gMCBpZiByZXN1bHRbJ3N1Y2Nlc3MnXWVsc2UgMQoKCmlmIF9fbmFtZV9fPT0nX19tYWluX18nOnJhaXNlIFN5c3RlbUV4aXQobWFpbigpKQo='
WORKER_SHA='5ec39493c3f79e22ca8b42eb67833b35556fab68612172434ed9d5e01b93fa9e'
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def need(value):
    if not value:
        raise ValueError('Fixed isolated scheduling control refused')

def run(argv, timeout=15):
    mask = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
    child = owned = None
    output = [bytearray(), bytearray()]
    size = 0
    end = time.monotonic()+timeout
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'},
            start_new_session=True, close_fds=True)
        owned = child
        with selectors.DefaultSelector() as selector:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while selector.get_map():
                need(time.monotonic() < end)
                for key, _ in selector.select(min(.1, max(.001, end-time.monotonic()))):
                    raw = os.read(key.fd, min(16384, 65537-size))
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(raw)
                    need(size <= 65536)
                    output[key.data].extend(raw)
        while True:
            need(time.monotonic() < end)
            previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                try:
                    code = child.wait(timeout=min(.05, max(.001, end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    continue
                owned = None
                return code, bytes(output[0]), bytes(output[1])
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous)
    finally:
        try:
            if owned is not None:
                previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
                try:
                    if owned.returncode is None:
                        try:
                            os.killpg(owned.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    owned.wait(timeout=2)
                    owned = None
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        finally:
            if child is not None:
                child.stdout.close()
                child.stderr.close()

def read(path, maximum, owner=0):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_uid == owner and
        before.st_nlink == 1 and not before.st_mode & 0o022 and 0 <= before.st_size <= maximum)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        data = bytearray()
        while True:
            part = os.read(fd, min(65536, maximum+1-len(data)))
            if not part:
                break
            data.extend(part)
            need(len(data) <= maximum)
        final = os.fstat(fd)
        named = path.lstat()
        key = lambda st: (st.st_dev, st.st_ino, st.st_uid, st.st_mode, st.st_nlink, st.st_size, st.st_mtime_ns)
        need(key(before) == key(opened) == key(final) == key(named) and len(data) == before.st_size)
        return bytes(data)
    finally:
        os.close(fd)

def write_root(name, value):
    need(name in ('LAB_ID.json', 'INSTALL.json', 'START.json', 'FINAL.json'))
    raw = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(raw) <= 32768)
    fd = os.open(LAB/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result);result[key]=value
    return result


def invalid_number(_):raise ValueError('Unsupported transport number')


def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_float=invalid_number,parse_constant=invalid_number)


def properties(unit=UNIT):
    need(unit in (UNIT,*OLD_UNITS))
    fields='Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,Type,User,Group,PrivateNetwork,Restart,KillMode,TimeoutStartUSec,TimeoutStopUSec,BindReadOnlyPaths,ReadWritePaths,RestrictAddressFamilies,ExecMainStartTimestampMonotonic,InvocationID'
    code,out,_=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+fields])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found');return value


def empty(unit,p):
    need(unit in (UNIT,*OLD_UNITS))
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+unit)
    try:raw=(Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096);return not raw.strip()


def fenced_original():
    result={}
    for unit in OLD_UNITS:
        p=properties(unit);need(empty(unit,p)and p.get('ActiveState')in('inactive','failed',None))
        need(p.get('LoadState')=='not-found'or p.get('Restart')=='no');result[unit]=p
    return result


def package_inventory():
    folder=OLD/'runtime/sidecar-bundle'
    for path,expected in((folder,{'manifest.json','selection.json','alert-state.json','selected'}),
            (folder/'selected',{'manifest.json','journal.json'})):
        before=path.lstat();need(stat.S_ISDIR(before.st_mode)and before.st_uid==65534 and not before.st_mode&0o077)
        found=set()
        with os.scandir(path)as entries:
            for entry in entries:
                need(len(found)<len(expected)and entry.name in expected and entry.name not in found)
                item=entry.stat(follow_symlinks=False)
                need(stat.S_ISDIR(item.st_mode)if entry.name=='selected'else stat.S_ISREG(item.st_mode)and item.st_nlink==1)
                need(item.st_uid==65534 and not item.st_mode&0o077);found.add(entry.name)
        after=path.lstat();need(found==expected and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino))


def original_snapshot():
    fence=fenced_original();package_inventory();raw=read(OLD/'SOURCE_MANIFEST.json',65536)
    need(sha(raw)==OLD_SOURCE_PIN);source=decode(raw);pins={}
    for name,row in source['source_files'].items():
        data=read(OLD/'source'/name,1024*1024)
        need(len(data)==row['bytes']and sha(data)==row['sha256']);pins[name]=sha(data)
    refs={}
    for name,digest in(('policy.json',POLICY_PIN),('keeper-config.json',CONFIG_PIN)):
        data=read(OLD/'runtime'/name,65536,owner=0 if name=='policy.json'else 65534)
        need(sha(data)==digest);refs[name]=sha(data)
    for name in('working/runtime/journal.json','schedule/selected.json','alerts/state.json'):
        refs[name]=sha(read(OLD/'runtime'/name,65536,owner=65534))
    package={}
    for name,(size,digest)in FILES.items():
        data=read(OLD/'runtime/sidecar-bundle'/name,65536,owner=65534)
        need(sha(data)==digest and (size is None or len(data)==size));package[name]={'bytes':len(data),'sha256':digest}
    package_inventory()
    return{'fenced_units':fence,'protected_reference_hashes':refs,'source_files_sha256':pins,
        'package_files':package,'source_manifest_sha256':OLD_SOURCE_PIN}


def unchanged(before,after):
    return all(before[key]==after[key]for key in('protected_reference_hashes','source_files_sha256','package_files','source_manifest_sha256'))


def package_data(files):
    need(type(files)is dict and set(files)==set(FILES));result={};total=0
    for name,(size,digest)in FILES.items():
        row=files[name];need(type(row)is dict and set(row)=={'bytes','sha256','raw_base64'})
        raw=base64.b64decode(row['raw_base64'],validate=True)
        need(type(row['bytes'])is int and row['bytes']==len(raw)and 0<len(raw)<=65536
            and sha(raw)==row['sha256']==digest and (size is None or len(raw)==size))
        total+=len(raw);need(total<=65536);result[name]=raw
    return result


def export(a):
    need(os.getuid()==0)
    before=original_snapshot();files={}
    for name in FILES:
        raw=read(OLD/'runtime/sidecar-bundle'/name,65536,owner=65534)
        files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    package_data(files);after=original_snapshot();need(unchanged(before,after))
    result={'schema':1,'kind':'popl-keeper-offhost-export','unsigned':True,'readiness_approved':False,
        'files':files,'original_fenced_before_and_after':True,'original_reference_snapshot_sha256':sha(enc(before)),
        'source_trust_report_sha256':TRUST_REPORT_PIN,'original_files_unchanged':True,
        'policy_configuration_and_signer_material_exported':False}
    need(len(enc(result))<=65536);return result


def owned():
    need(os.getuid()==0)
    item=LAB.lstat();need(stat.S_ISDIR(item.st_mode)and item.st_uid==0 and not item.st_mode&0o022)
    identity=decode(read(LAB/'LAB_ID.json',32768))
    need(identity['controller_sha256']==ACTIVE_CONTROLLER_SHA and identity['worker_sha256']==WORKER_SHA)
    need(sha(read(LAB/'worker.py',65536))==WORKER_SHA)
    need(sha(read(LAB/'desktop-proof.json',8192))==identity['desktop_proof_sha256'])
    return identity


def install(a):
    need(os.getuid()==0 and not os.path.lexists(LAB)and properties().get('LoadState')=='not-found')
    need(type(a.desktop_proof_sha256)is str and re.fullmatch('[0-9a-f]{64}',a.desktop_proof_sha256)is not None)
    raw=sys.stdin.buffer.read(65537);need(0<len(raw)<=65536);packet=decode(raw)
    need(type(packet)is dict and set(packet)=={'schema','kind','files','desktop_proof_base64'}
        and type(packet['schema'])is int and packet['schema']==1 and packet['kind']=='popl-keeper-offhost-import')
    files=package_data(packet['files']);proof_raw=base64.b64decode(packet['desktop_proof_base64'],validate=True)
    need(0<len(proof_raw)<=8192 and sha(proof_raw)==a.desktop_proof_sha256);proof=decode(proof_raw)
    need(type(proof['schema'])is int and proof['schema']==1 and proof['kind']=='popl-keeper-offhost-desktop-proof'and proof['ok']is True
        and proof['unsigned']is True and proof['readiness_approved']is False and proof['production_approved']is False)
    need(proof['outer_manifest_sha256']==OUTER and proof['nested_manifest_sha256']==NESTED
        and proof['policy_sha256']==POLICY_PIN and proof['configuration_sha256']==CONFIG_PIN
        and proof['source_trust_report_sha256']==TRUST_REPORT_PIN)
    need(proof['files']=={name:{'bytes':len(data),'sha256':sha(data)}for name,data in files.items()})
    before=original_snapshot();worker=base64.b64decode(WORKER,validate=True);need(sha(worker)==WORKER_SHA)
    LAB.mkdir(mode=0o755);runtime=LAB/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
    imported=runtime/'imported';imported.mkdir(mode=0o700);os.chown(imported,65534,65534)
    (imported/'selected').mkdir(mode=0o700);os.chown(imported/'selected',65534,65534)
    for name,data in files.items():
        path=imported/name;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno());os.fchown(stream.fileno(),65534,65534)
    for name,data in(('worker.py',worker),('desktop-proof.json',proof_raw)):
        fd=os.open(LAB/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444)
    masks=LAB/'masks';masks.mkdir(mode=0o755)
    for name in('key.empty','password.empty'):
        fd=os.open(masks/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0);os.fchmod(fd,0);os.close(fd)
    os.chmod(masks,0o555)
    for name in('stdout.log','stderr.log'):
        fd=os.open(runtime/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.fchown(fd,65534,65534);os.close(fd)
    after=original_snapshot();need(unchanged(before,after))
    write_root('INSTALL.json',{'schema':1,'original_before':before,'original_after':after,'original_unchanged':True,
        'desktop_proof_sha256':a.desktop_proof_sha256,'input_wire_bytes':len(raw),'input_files':proof['files']})
    write_root('LAB_ID.json',{'schema':1,'controller_sha256':a.controller_sha256,'worker_sha256':WORKER_SHA,
        'desktop_proof_sha256':a.desktop_proof_sha256,'input_files':proof['files']})
    return{'phase':'installed','same_desktop_bytes_imported':True,'input_wire_bytes':len(raw),
        'input_files':proof['files'],'desktop_proof_sha256':a.desktop_proof_sha256,'original_unchanged':True}


def start(a):
    owned();before=original_snapshot();need(not(LAB/'START.json').exists()and properties().get('LoadState')=='not-found')
    masks=[(LAB/'masks'/name).lstat()for name in('key.empty','password.empty')]
    need(all(stat.S_ISREG(item.st_mode)and item.st_uid==0 and item.st_nlink==1 and item.st_size==0
        and stat.S_IMODE(item.st_mode)==0 for item in masks)and len({(item.st_dev,item.st_ino)for item in masks})==2)
    binds=[str(OLD/'source'),str(OLD/'runtime'),str(LAB/'masks/key.empty')+':'+str(OLD/'runtime/working/keystore.secret'),
        str(LAB/'masks/password.empty')+':'+str(OLD/'runtime/working/password.secret')]
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes','PrivateTmp':'yes',
        'PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes','NoNewPrivileges':'yes',
        'ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes',
        'RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
        'RestrictAddressFamilies':'AF_UNIX','ReadWritePaths':str(LAB/'runtime'),'UMask':'0077','Restart':'no',
        'RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2','KillMode':'control-group',
        'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32',
        'LimitCORE':'0','LimitFSIZE':'65536','StartLimitIntervalSec':'0','BindReadOnlyPaths':' '.join(binds),
        'StandardOutput':'append:'+str(LAB/'runtime/stdout.log'),'StandardError':'append:'+str(LAB/'runtime/stderr.log'),
        'WorkingDirectory':str(LAB)}
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+UNIT]
    argv+=['--property='+key+'='+value for key,value in policy.items()]
    argv+=['--setenv='+key+'='+value for key,value in{'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items()]
    code,_,_=run([*argv,'--','/usr/bin/python3','-B',str(LAB/'worker.py')]);need(code==0)
    write_root('START.json',{'schema':1,'original_before':before,'policy':policy,'only_new_unit_started':UNIT})
    return{'phase':'started','unit':UNIT,'properties':properties()}


def status(a):
    owned();p=properties();raw_sizes={name:(LAB/'runtime'/name).stat().st_size for name in('stdout.log','stderr.log')}
    need(sum(raw_sizes.values())<=65536)
    return{'phase':'status','properties':p,'group_empty':empty(UNIT,p),'result_present':(LAB/'runtime/RESULT.json').exists(),
        'actual_execution_started':p.get('ExecMainStartTimestampMonotonic','0').isdigit()and int(p.get('ExecMainStartTimestampMonotonic','0'))>0,
        'output_bytes':raw_sizes}


def stop(a):
    owned();before=properties()
    if before.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',UNIT]);need(code==0)
    after=properties();need(empty(UNIT,after));original=original_snapshot()
    installed=decode(read(LAB/'INSTALL.json',32768));need(unchanged(installed['original_before'],original))
    if not(LAB/'FINAL.json').exists():write_root('FINAL.json',{'schema':1,'before_stop':before,'after_stop':after,
        'new_group_empty':True,'original_after':original,'original_unchanged':True,'old_four_groups_fenced':True})
    return{'phase':'stopped','new_group_empty':True,'old_four_groups_fenced':True,'original_unchanged':True}


def fetch(a):
    owned();need(a.artifact in('RESULT.json','PROGRESS.json','FINAL.json','INSTALL.json'))
    path=LAB/a.artifact if a.artifact in('FINAL.json','INSTALL.json')else LAB/'runtime'/a.artifact
    raw=read(path,32768,owner=0 if a.artifact in('FINAL.json','INSTALL.json')else 65534)
    return{'phase':'saved_artifact','name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    parser.add_argument('--controller-sha256',required=True);parser.add_argument('--desktop-proof-sha256');parser.add_argument('--artifact')
    args=parser.parse_args();need(re.fullmatch('[0-9a-f]{64}',args.controller_sha256)is not None)
    globals()['ACTIVE_CONTROLLER_SHA']=args.controller_sha256
    print(json.dumps(globals()[args.action](args),sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'scope':'fixed_c823_only'}))
        raise SystemExit(1)from None
