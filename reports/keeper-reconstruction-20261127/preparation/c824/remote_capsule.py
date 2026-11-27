"""Fixed c824 coordinator. Reconstructs only two new private RootDirectories."""
from pathlib import Path
import argparse,base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time,zlib

LAB=Path('/opt/popl-keeper-reconstruction-20261127-c824')
OLD=Path('/opt/popl-keeper-sidecar-recovery-20261126-c821')
UNIT_BASE='popl-keeper-reconstruction-20261127-c824'
MODES=('negative','complete')
OLD_BASE='popl-keeper-sidecar-recovery-20261126-c821'
OLD_UNITS=(OLD_BASE+'.service',*(OLD_BASE+'-'+job+'.service'for job in('checks','source','target')))
SOURCE_PIN='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
CONFIG_PIN='1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
POLICY_PIN='7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED='911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
SOURCE_FILES={'keeper/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'keeper/alerts.py': {'bytes': 23149, 'sha256': '053ac2a70f38801b77afde8ba107c78e322a11630cb04620e1aa35a3f811fe13'}, 'keeper/cast_process.py': {'bytes': 5694, 'sha256': '5856fec6fb15e1abb66750394c2fb7a24314686e964eca0e9363b5007aa5ba3a'}, 'keeper/compound_policy.py': {'bytes': 17260, 'sha256': '129d330417c37747e16456fd18c892550cf870bdad31847e328b42a5c7270e29'}, 'keeper/health.py': {'bytes': 24415, 'sha256': 'dd25d2151295d09dcdebc4b0331b82c8d2b384a5501b49d0bfeb483d396b5c04'}, 'keeper/monitor.py': {'bytes': 194496, 'sha256': '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'}, 'keeper/operation_review.py': {'bytes': 43774, 'sha256': '75f6fc17399ae28791f81d97d5afea2f98a3061662cbb6e9f072b562d6f72f48'}, 'keeper/ops.py': {'bytes': 14444, 'sha256': 'da396ec9c65295fe540f9dc812a0612d8ed27f1ab677fd388b479e2f2372ad89'}, 'keeper/principal.py': {'bytes': 9171, 'sha256': 'b602340db5c7a52ad281c6b60885e2f74cc2708b731595fac5eeb9e026da6874'}, 'keeper/rebalance_confirmation.py': {'bytes': 11926, 'sha256': '6cc29d78aaf4c3804379e9b15d0ff177ff537da1158e66a3111ae2c85d6d317d'}, 'keeper/recovery_bundle.py': {'bytes': 36532, 'sha256': '022cd3b9a3692f9b5576fded8fb15d4aca2797f4ad3bd449561a4d57173de550'}, 'keeper/royalties.py': {'bytes': 17321, 'sha256': '02e04783068eed60db827673c9c27d3a37175edd7dccfa5ddefb8b54c055904c'}, 'keeper/scheduling.py': {'bytes': 17800, 'sha256': 'd79be28db6bac2978f7c8efdfb641e037ce6d2024faa4e60e02f6f7c62049f4a'}, 'keeper/sidecar_recovery.py': {'bytes': 22768, 'sha256': 'eda3b43e316adab4fb8a2161a7d5e5f750ba4e1e0c9b3432037d6acf39396546'}, 'keeper/watchdog.py': {'bytes': 5707, 'sha256': '59b4bb7783453a8f271fd5ab265fd5d2857d55096479be34f10ffe56c8408372'}, 'scripts/keeper-alerts.py': {'bytes': 2629, 'sha256': '4f3b6b3efa9401c4039b9dcdc1fa9bf0c4136c2342f02c7286c895bc0ef027c5'}, 'scripts/keeper-recovery.py': {'bytes': 3423, 'sha256': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}, 'scripts/keeper-schedule.py': {'bytes': 2140, 'sha256': '5c07ec965eba5c5a2d94895ba050f17d49b9689923cf67a05f20f2d0bf29c0b4'}, 'scripts/keeper-sidecar-recovery.py': {'bytes': 2924, 'sha256': '408858a48eb2eb464d9745e7767603c1142f03aa96ba7b280ae7081f8deeca58'}, 'tests_python/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'tests_python/test_keeper_alerts.py': {'bytes': 32525, 'sha256': 'f960f5a50dd1469b3d1f9c1bfb1002e68e1c83982586bc59eec390db83915b6d'}, 'tests_python/test_keeper_scheduling.py': {'bytes': 15979, 'sha256': '15a4f2bf088fc1853437838c3925f2eb5be9295305880dbaa052ef390bedae72'}, 'tests_python/test_keeper_sidecar_recovery.py': {'bytes': 18390, 'sha256': '6811351e1e41563e7a7fe23c494b43938a3afeb81576b64c7b9d6d05239486ef'}, 'zzz_ops/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'zzz_ops/abi.py': {'bytes': 4797, 'sha256': 'c4c755f1a9bf8db70b1ecb81e2b4e6765581961289f6f550502983e375293d91'}, 'zzz_ops/errors.py': {'bytes': 992, 'sha256': '1dcc2855b45af8f806835f70f7f75200aa5b93ef84ddcf862e1e0f067aba5305'}, 'zzz_ops/ethereum_fees.py': {'bytes': 2464, 'sha256': '8c832b5e28beb7d7d5c8d90d6df102bb084a680cf251ded850a2f00fe0cb2ffe'}, 'zzz_ops/execution_price.py': {'bytes': 2280, 'sha256': '1d0ff892d43ec450438e7d2a1c2f783e6d9f9aec66f1fe98e3c35f5b09de47e2'}, 'zzz_ops/lp_execution.py': {'bytes': 6860, 'sha256': '90c985622387a4de8d52dd075856a4cf25e8c2e5bc62f4a3490978fc8cf746b0'}, 'zzz_ops/physical_portfolio.py': {'bytes': 2125, 'sha256': 'f119b665860cb4aaa9fbebe81aa1f2564906dff8466d1febf96ea4eef46e719b'}, 'zzz_ops/position.py': {'bytes': 2437, 'sha256': '54075cb2329e6e1defb4942683378d6a3995a74a6ea5e1f239a8fcf611e30d4d'}, 'zzz_ops/price_policy.py': {'bytes': 7148, 'sha256': '2f5e41da367c04fd811ac14a09bf0662abf8fe46f7a7619a17efa58295ce2958'}, 'zzz_ops/production_v2.py': {'bytes': 102622, 'sha256': '109531b48b9c8a85166c9585351dc40b4b534ec5eea14c5b81d895c1b2209889'}, 'zzz_ops/production_v4.py': {'bytes': 65998, 'sha256': 'ffa0e95b06ca1c166e7e56debcba8829764a204a3f7b7e377fa2310499073d5c'}, 'zzz_ops/protocol_policy.py': {'bytes': 5907, 'sha256': '4d73e7a3f6d6b98c91f083e2c557a48259ac9bcc0dbe2fb7752f74c4335bb5c3'}, 'zzz_ops/range_policy.py': {'bytes': 5859, 'sha256': '4d4d8c1772b45417d98e2aa336e100f59674c7bbbe7f4a35efa8d07f87d90171'}, 'zzz_ops/rebalance_confirmation.py': {'bytes': 17194, 'sha256': '77a41f2520be5d5c6768505e7bfe75f68db79d37f611062750ecd02f58185331'}, 'zzz_ops/rpc.py': {'bytes': 9709, 'sha256': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f'}, 'zzz_ops/state.py': {'bytes': 4644, 'sha256': '78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf'}, 'zzz_ops/tick_math.py': {'bytes': 4949, 'sha256': '5224a360f3fecbc9c1d42094863e74771cee8036a60d8b81647d9e6d45e0c70a'}, 'zzz_ops/work_budget.py': {'bytes': 3633, 'sha256': 'd60de944ee02fc8be02cdbdde0210c84fff02dea8bb63b386cc73688061a535b'}}
PACKAGE_FILES={'manifest.json':{'bytes':None,'sha256':OUTER},
    'selection.json':{'bytes':2354,'sha256':'dfdabc2c7d8e2510efeaab4861fb034af2536269705ee0000f805ccaadce9bb2'},
    'alert-state.json':{'bytes':812,'sha256':'f256fd8ca53e4d45ac11b5c75333f6b4172b8f9579460a1fd7bab48536b3dc98'},
    'selected/manifest.json':{'bytes':3867,'sha256':NESTED},
    'selected/journal.json':{'bytes':2752,'sha256':'dbb5f86672bd14f017d9c99f3b8ff6b8e6a8cf041d2aa9c2eada60b7598a9112'}}
WORKER='IiIiRml4ZWQgYzgyNCBpc29sYXRlZCByZWNvbnN0cnVjdGlvbiB3aXRuZXNzLiBObyBwcm9kdWN0aW9uIGFwcGxpY2F0aW9uIGltcG9ydC4iIiIKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBhcmdwYXJzZSxoYXNobGliLGpzb24sb3MscmUsc2VsZWN0b3JzLHNpZ25hbCxzdGF0LHN1YnByb2Nlc3Msc3lzLHRpbWUsdHJhY2ViYWNrCgpCQVNFPVBhdGgoJy9yZWNvbnN0cnVjdGlvbicpO1JVTlRJTUU9QkFTRS8ncnVudGltZScKT0xEPVBhdGgoJy9vcHQvcG9wbC1rZWVwZXItc2lkZWNhci1yZWNvdmVyeS0yMDI2MTEyNi1jODIxJykKU09VUkNFPU9MRC8nc291cmNlJztDT05GSUc9T0xELydydW50aW1lL2tlZXBlci1jb25maWcuanNvbic7UE9MSUNZPU9MRC8ncnVudGltZS9wb2xpY3kuanNvbicKT1VURVI9J2E5ZGVhNDc1YTIyMDE0YzdlYjVmY2Y5NjU4OTZlYjY5MWEyYmE1YzhkZTM1MmUwYzIzZDZmZDE2MTFkYmIwNWInCk5FU1RFRD0nOTExZDk4ZWY4NmIxY2QyMjkzNzhhZTE1YWM2ODVlOGNlNjcyODVjMDAzNWM4Y2Y2NzBkZmNhM2NjY2M1ZDBkMScKU09VUkNFX1BJTj0nYzI4N2FhMGM0YjhlNDExM2Y3ZmZhMTQ1OWYzOWE3MDRiZDE3YjUxNjVmMjMwODRlM2E4ZjI2OTk1Y2RiMGUwOCcKQ09ORklHX1BJTj0nMWMzZDUxMzQzYjk5MGEyYWJjNGE4N2NmOWRkNzA0OTIzN2YyM2EzNGEzOTcwOGY5NDVkOThmMjI4ZTNmNWNiOCcKUE9MSUNZX1BJTj0nN2U4NWZmOGI2NzA5ODAzY2I5ZjRlNjIxMTUwZDA1YjA4MjYyNTk5ZTk0YTJkY2NkOWEyM2UwMWJiNDE0NTJiYScKRU5EPXRpbWUubW9ub3RvbmljKCkrMTY1CnNoYT1sYW1iZGEgcmF3Omhhc2hsaWIuc2hhMjU2KHJhdykuaGV4ZGlnZXN0KCkKZW5jPWxhbWJkYSB2YWx1ZTooanNvbi5kdW1wcyh2YWx1ZSxzb3J0X2tleXM9VHJ1ZSxzZXBhcmF0b3JzPSgnLCcsJzonKSxhbGxvd19uYW49RmFsc2UpKydcbicpLmVuY29kZSgpCgoKZGVmIG5lZWQodmFsdWUsY29kZT0ncmVjb25zdHJ1Y3Rpb25fYXNzZXJ0aW9uJyk6CiAgICBpZiBub3QgdmFsdWU6cmFpc2UgVmFsdWVFcnJvcihjb2RlKQoKCmRlZiByZWFkKHBhdGgsbWF4aW11bT0xMDQ4NTc2KToKICAgIGJlZm9yZT1wYXRoLmxzdGF0KCk7bmVlZChzdGF0LlNfSVNSRUcoYmVmb3JlLnN0X21vZGUpYW5kIGJlZm9yZS5zdF9ubGluaz09MSBhbmQgYmVmb3JlLnN0X3NpemU8PW1heGltdW0sJ2ZpbGVfYm91bmQnKQogICAgZmQ9b3Mub3BlbihwYXRoLG9zLk9fUkRPTkxZfG9zLk9fTk9GT0xMT1d8b3MuT19OT05CTE9DS3xvcy5PX0NMT0VYRUMpCiAgICB0cnk6CiAgICAgICAgcmF3PWJ5dGVhcnJheSgpCiAgICAgICAgd2hpbGUgVHJ1ZToKICAgICAgICAgICAgcGFydD1vcy5yZWFkKGZkLG1pbigxNjM4NCxtYXhpbXVtKzEtbGVuKHJhdykpKQogICAgICAgICAgICBpZiBub3QgcGFydDpicmVhawogICAgICAgICAgICByYXcuZXh0ZW5kKHBhcnQpO25lZWQobGVuKHJhdyk8PW1heGltdW0sJ2ZpbGVfYm91bmQnKQogICAgICAgIGtleT1sYW1iZGEgc3Q6KHN0LnN0X2RldixzdC5zdF9pbm8sc3Quc3RfbW9kZSxzdC5zdF91aWQsc3Quc3Rfbmxpbmssc3Quc3Rfc2l6ZSxzdC5zdF9tdGltZV9ucykKICAgICAgICBuZWVkKGtleShiZWZvcmUpPT1rZXkob3MuZnN0YXQoZmQpKT09a2V5KHBhdGgubHN0YXQoKSlhbmQgbGVuKHJhdyk9PWJlZm9yZS5zdF9zaXplLCdmaWxlX2NoYW5nZWQnKQogICAgICAgIHJldHVybiBieXRlcyhyYXcpCiAgICBmaW5hbGx5Om9zLmNsb3NlKGZkKQoKCmRlZiB2YWx1ZShwYXRoLG1heGltdW09MTA0ODU3Nik6cmV0dXJuIGpzb24ubG9hZHMocmVhZChwYXRoLG1heGltdW0pKQoKCmRlZiBwdWJsaXNoKGRhdGEpOgogICAgcmF3PWVuYyhkYXRhKTtuZWVkKGxlbihyYXcpPD0zMjc2OCwncmVzdWx0X2JvdW5kJykKICAgIGZkPW9zLm9wZW4oUlVOVElNRS8nUkVTVUxULmpzb24nLG9zLk9fV1JPTkxZfG9zLk9fQ1JFQVR8b3MuT19FWENMfG9zLk9fTk9GT0xMT1csMG82MDApCiAgICB3aXRoIG9zLmZkb3BlbihmZCwnd2InKWFzIHN0cmVhbTpzdHJlYW0ud3JpdGUocmF3KTtzdHJlYW0uZmx1c2goKTtvcy5mc3luYyhzdHJlYW0uZmlsZW5vKCkpCgoKZGVmIHJ1bnRpbWVfdHJlZShmb2xkZXIpOgogICAgYWxsb3dlZF9saW5rcz17J3NpdGVjdXN0b21pemUucHknOicvZXRjL3B5dGhvbjMuMTIvc2l0ZWN1c3RvbWl6ZS5weScsCiAgICAgICAgJ19zeXNjb25maWdkYXRhX19saW51eF94ODZfNjQtbGludXgtZ251LnB5JzonX3N5c2NvbmZpZ2RhdGFfX3g4Nl82NC1saW51eC1nbnUucHknLAogICAgICAgICdjb25maWctMy4xMi14ODZfNjQtbGludXgtZ251L2xpYnB5dGhvbjMuMTIuc28nOicuLi8uLi94ODZfNjQtbGludXgtZ251L2xpYnB5dGhvbjMuMTIuc28uMSd9CiAgICByb3dzPVtdO3RvdGFsPTA7dmlzaXRlZD0wO2xpbmtzPXNldCgpO3N0YWNrPVsoZm9sZGVyLDApXTtlbmQ9dGltZS5tb25vdG9uaWMoKSsyMAogICAgd2hpbGUgc3RhY2s6CiAgICAgICAgZGlyZWN0b3J5LGRlcHRoPXN0YWNrLnBvcCgpO25lZWQoZGVwdGg8PTE2IGFuZCB0aW1lLm1vbm90b25pYygpPGVuZCwncnVudGltZV9pbnZlbnRvcnlfZGVhZGxpbmUnKQogICAgICAgIHdpdGggb3Muc2NhbmRpcihkaXJlY3RvcnkpYXMgZW50cmllczoKICAgICAgICAgICAgZm9yIGVudHJ5IGluIGVudHJpZXM6CiAgICAgICAgICAgICAgICB2aXNpdGVkKz0xO25lZWQodmlzaXRlZDw9ODE5MiBhbmQgdGltZS5tb25vdG9uaWMoKTxlbmQsJ3J1bnRpbWVfaW52ZW50b3J5X2JvdW5kJykKICAgICAgICAgICAgICAgIGlmIGVudHJ5Lm5hbWUgaW4oJ3NpdGUtcGFja2FnZXMnLCdkaXN0LXBhY2thZ2VzJyk6Y29udGludWUKICAgICAgICAgICAgICAgIGl0ZW09ZW50cnkuc3RhdChmb2xsb3dfc3ltbGlua3M9RmFsc2UpO3BhdGg9UGF0aChlbnRyeS5wYXRoKQogICAgICAgICAgICAgICAgaWYgc3RhdC5TX0lTRElSKGl0ZW0uc3RfbW9kZSk6c3RhY2suYXBwZW5kKChwYXRoLGRlcHRoKzEpKTtjb250aW51ZQogICAgICAgICAgICAgICAgaWYgcGF0aC5zdWZmaXggbm90IGluKCcucHknLCcuc28nLCcucHljJyk6Y29udGludWUKICAgICAgICAgICAgICAgIHJlbGF0aXZlPXN0cihwYXRoLnJlbGF0aXZlX3RvKGZvbGRlcikpCiAgICAgICAgICAgICAgICBpZiBzdGF0LlNfSVNMTksoaXRlbS5zdF9tb2RlKToKICAgICAgICAgICAgICAgICAgICBuZWVkKHJlbGF0aXZlIGluIGFsbG93ZWRfbGlua3MgYW5kIGl0ZW0uc3RfdWlkPT0wIGFuZCBpdGVtLnN0X25saW5rPT0xLCdydW50aW1lX2xpbmtfbWV0YWRhdGEnKQogICAgICAgICAgICAgICAgICAgIGtleT1sYW1iZGEgc3Q6KHN0LnN0X2RldixzdC5zdF9pbm8sc3Quc3RfdWlkLHN0LnN0X21vZGUsc3Quc3Rfbmxpbmssc3Quc3Rfc2l6ZSxzdC5zdF9tdGltZV9ucyxzdC5zdF9jdGltZV9ucykKICAgICAgICAgICAgICAgICAgICB0YXJnZXQ9b3MucmVhZGxpbmsocGF0aCk7bmVlZCh0YXJnZXQ9PWFsbG93ZWRfbGlua3NbcmVsYXRpdmVdYW5kIGtleShpdGVtKT09a2V5KHBhdGgubHN0YXQoKSksJ3J1bnRpbWVfbGlua190YXJnZXQnKQogICAgICAgICAgICAgICAgICAgIG5lZWQob3MucmVhZGxpbmsocGF0aCk9PXRhcmdldCBhbmQga2V5KGl0ZW0pPT1rZXkocGF0aC5sc3RhdCgpKSwncnVudGltZV9saW5rX2NoYW5nZWQnKQogICAgICAgICAgICAgICAgICAgIHJvd3MuYXBwZW5kKFsnc3ltbGluaycscmVsYXRpdmUsdGFyZ2V0LGl0ZW0uc3RfdWlkLHN0YXQuU19JTU9ERShpdGVtLnN0X21vZGUpLGl0ZW0uc3RfbmxpbmtdKTtsaW5rcy5hZGQocmVsYXRpdmUpO2NvbnRpbnVlCiAgICAgICAgICAgICAgICBuZWVkKHN0YXQuU19JU1JFRyhpdGVtLnN0X21vZGUpYW5kIG5vdCBpdGVtLnN0X21vZGUmMG8wMjIsJ3J1bnRpbWVfZmlsZV9tZXRhZGF0YScpCiAgICAgICAgICAgICAgICByYXc9cmVhZChwYXRoLDE2Nzc3MjE2KTt0b3RhbCs9bGVuKHJhdyk7bmVlZCh0b3RhbDw9MTM0MjE3NzI4IGFuZCBsZW4ocm93cyk8NDA5NiwncnVudGltZV9pbnZlbnRvcnlfYm91bmQnKQogICAgICAgICAgICAgICAgcm93cy5hcHBlbmQoWydmaWxlJyxyZWxhdGl2ZSxsZW4ocmF3KSxzaGEocmF3KV0pCiAgICByb3dzLnNvcnQoKQogICAgbmVlZChyb3dzIGFuZCBsaW5rcz09c2V0KGFsbG93ZWRfbGlua3MpLCdydW50aW1lX3JlcXVpcmVkX2xpbmtzJykKICAgIHJldHVybnsnZmlsZXMnOmxlbihyb3dzKS1sZW4obGlua3MpLCdzeW1saW5rcyc6bGVuKGxpbmtzKSwnZW50cmllcyc6bGVuKHJvd3MpLCdieXRlcyc6dG90YWwsJ3NoYTI1Nic6c2hhKGVuYyhyb3dzKSl9CgoKZGVmIHByZWZsaWdodChtb2RlKToKICAgIG5lZWQob3MuZ2V0dWlkKCk9PW9zLmdldGdpZCgpPT02NTUzNCBhbmQgc2V0KG9zLmdldGdyb3VwcygpKTw9ezY1NTM0fSwnd3JvbmdfdWlkJykKICAgIGlkZW50aXR5PXZhbHVlKEJBU0UvJ0lERU5USVRZLmpzb24nKTtydW50aW1lPXZhbHVlKEJBU0UvJ1JVTlRJTUVfUkVWSUVXLmpzb24nKQogICAgc291cmNlX3Jhdz1yZWFkKEJBU0UvJ1NPVVJDRV9NQU5JRkVTVC5qc29uJyk7bmVlZChzaGEoc291cmNlX3Jhdyk9PVNPVVJDRV9QSU4sJ3NvdXJjZV9tYW5pZmVzdF9waW4nKQogICAgbWFuaWZlc3Q9anNvbi5sb2Fkcyhzb3VyY2VfcmF3KTtuZWVkKGxlbihtYW5pZmVzdFsnc291cmNlX2ZpbGVzJ10pPT00MSwncmVsZWFzZV9pbnZlbnRvcnknKQogICAgZm9yIG5hbWUscm93IGluIG1hbmlmZXN0Wydzb3VyY2VfZmlsZXMnXS5pdGVtcygpOgogICAgICAgIHJhdz1yZWFkKFNPVVJDRS9uYW1lKTtuZWVkKGxlbihyYXcpPT1yb3dbJ2J5dGVzJ11hbmQgc2hhKHJhdyk9PXJvd1snc2hhMjU2J10sJ3JlbGVhc2VfcGluJykKICAgIG5lZWQoc2hhKHJlYWQoUE9MSUNZKSk9PVBPTElDWV9QSU4sJ3BvbGljeV9waW4nKQogICAgaWYgbW9kZT09J25lZ2F0aXZlJzpuZWVkKG5vdCBvcy5wYXRoLmxleGlzdHMoQ09ORklHKSwnbmVnYXRpdmVfZGVwZW5kZW5jeV9wcmVzZW50JykKICAgIGVsc2U6bmVlZChzaGEocmVhZChDT05GSUcpKT09Q09ORklHX1BJTiwnY29uZmlndXJhdGlvbl9waW4nKQogICAgcGFja2FnZT1CQVNFLydwYWNrYWdlJztmaWxlcz1pZGVudGl0eVsnaW5wdXRfZmlsZXMnXQogICAgZm9yIG5hbWUscm93IGluIGZpbGVzLml0ZW1zKCk6CiAgICAgICAgaWYgbm90IG5hbWUuc3RhcnRzd2l0aCgncGFja2FnZS8nKTpjb250aW51ZQogICAgICAgIHJhdz1yZWFkKEJBU0UvbmFtZSk7bmVlZChsZW4ocmF3KT09cm93WydieXRlcyddYW5kIHNoYShyYXcpPT1yb3dbJ3NoYTI1NiddLCdwYWNrYWdlX3BpbicpCiAgICBmb3IgbG9naWNhbCxleHBlY3RlZCBpbiBydW50aW1lWydmaWxlcyddLml0ZW1zKCk6CiAgICAgICAgcmF3PXJlYWQoUGF0aChsb2dpY2FsKSwxNjc3NzIxNik7bmVlZChsZW4ocmF3KT09ZXhwZWN0ZWRbJ2J5dGVzJ11hbmQgc2hhKHJhdyk9PWV4cGVjdGVkWydzaGEyNTYnXSwnZXh0ZXJuYWxfcnVudGltZV9waW4nKQogICAgbmVlZChydW50aW1lX3RyZWUoUGF0aChydW50aW1lWydzdGRsaWInXSkpPT1ydW50aW1lWydzdGRsaWJfdHJlZSddLCdzdGRsaWJfdHJlZV9waW4nKQogICAgbmVlZChzeXMuZmxhZ3MuaXNvbGF0ZWQ9PTEgYW5kIHN5cy5mbGFncy5ub19zaXRlPT0xIGFuZCBzeXMuZG9udF93cml0ZV9ieXRlY29kZSwncHl0aG9uX2lzb2xhdGlvbicpCiAgICB3aXRoIFBhdGgoJy9wcm9jL3NlbGYvbW91bnRpbmZvJykub3BlbigncmInKWFzIHN0cmVhbTptb3VudD1zdHJlYW0ucmVhZCg2NTUzNykKICAgIG5lZWQobGVuKG1vdW50KTw9NjU1MzYsJ21vdW50aW5mb19ib3VuZCcpCiAgICBsaW5lcz1tb3VudC5kZWNvZGUoJ3V0ZjgnLCdzdHJpY3QnKS5zcGxpdGxpbmVzKCkKICAgIG5lZWQobm90IGFueShzdHIoT0xEKWluIGxpbmUgb3IgJy9vcHQvcG9wbC1rZWVwZXItb2ZmaG9zdC0yMDI2MTEyNi1jODIzJ2luIGxpbmUgZm9yIGxpbmUgaW4gbGluZXMpLCdvbGRfaG9zdF9sYWJfbW91bnQnKQogICAgbmVlZChub3QgUGF0aCgnL29wdC9wb3BsLWtlZXBlci1vZmZob3N0LTIwMjYxMTI2LWM4MjMnKS5leGlzdHMoKSwnb2xkX290aGVyX2xhYl92aXNpYmxlJykKICAgIG9sZD1pZGVudGl0eVsnb2xkX3NvdXJjZV9tYW5pZmVzdF9pbm9kZV9wYWlyJ107ZnJlc2g9KEJBU0UvJ1NPVVJDRV9NQU5JRkVTVC5qc29uJykuc3RhdCgpCiAgICBuZWVkKFtmcmVzaC5zdF9kZXYsZnJlc2guc3RfaW5vXSE9b2xkLCdvbGRfcGh5c2ljYWxfaW5vZGVfdmlzaWJsZScpCiAgICAjIEV2ZXJ5IG9yaWdpbmFsIG9wZXJhdGluZyBzdGF0ZSBpcyBhYnNlbnQsIGluZGVwZW5kZW50bHkgb2YgYSByZXN0b3JlZCBwYWNrYWdlLgogICAgYWJzZW50PVtPTEQvJ3J1bnRpbWUvd29ya2luZy9ydW50aW1lL2pvdXJuYWwuanNvbicsT0xELydydW50aW1lL3NjaGVkdWxlL3NlbGVjdGVkLmpzb24nLAogICAgICAgIE9MRC8ncnVudGltZS9hbGVydHMvc3RhdGUuanNvbicsT0xELydydW50aW1lL3NpZGVjYXItYnVuZGxlJ10KICAgIG5lZWQoYWxsKG5vdCBvcy5wYXRoLmxleGlzdHMocGF0aClmb3IgcGF0aCBpbiBhYnNlbnQpLCdvcGVyYXRpbmdfc3RhdGVfcHJlc2VudCcpCiAgICByZXR1cm57J3Jvb3RfZGlyZWN0b3J5X2lzX25ldyc6VHJ1ZSwnaG9zdF9vcHRfbW91bnRlZCc6RmFsc2UsJ29yaWdpbmFsX29wZXJhdGluZ19zdGF0ZV9hYnNlbnQnOlRydWUsCiAgICAgICAgJ3NvdXJjZV9maWxlc192ZXJpZmllZCc6NDEsJ29yaWdpbmFsX3NvdXJjZTEzXzE5X3VuY2hhbmdlZCc6VHJ1ZSwKICAgICAgICAnbW91bnRpbmZvX3NoYTI1Nic6c2hhKG1vdW50KSwnbW91bnRfY291bnQnOmxlbihsaW5lcyksJ2V4dGVybmFsX3J1bnRpbWVfc2hhMjU2JzpzaGEoZW5jKHJ1bnRpbWUpKSwKICAgICAgICAnZXh0ZXJuYWxfcnVudGltZV9tb3VudHMnOnJ1bnRpbWVbJ21vdW50cyddLCdzdGRsaWJfdHJlZSc6cnVudGltZVsnc3RkbGliX3RyZWUnXSwKICAgICAgICAnb2xkX3NvdXJjZV9tYW5pZmVzdF9pbm9kZV9wYWlyJzpvbGQsJ25ld19zb3VyY2VfbWFuaWZlc3RfaW5vZGVfcGFpcic6W2ZyZXNoLnN0X2RldixmcmVzaC5zdF9pbm9dLAogICAgICAgICdPU19ydW50aW1lX2lzX2V4dGVybmFsJzpUcnVlLCdPU19kaXNhc3Rlcl9yZWNvdmVyeV9wcm92ZWQnOkZhbHNlLCdhY3R1YWxfc2Vjb25kX2hvc3QnOkZhbHNlfQoKCmRlZiBydW4oc2NyaXB0LGFyZ3MsZXhwZWN0ZWRfcmVmdXNhbD1GYWxzZSk6CiAgICBuZWVkKHNjcmlwdCBpbigna2VlcGVyLXJlY292ZXJ5LnB5Jywna2VlcGVyLXNpZGVjYXItcmVjb3ZlcnkucHknKSwnY29tbWFuZF9zY29wZScpCiAgICBhcmd2PVsnL3Vzci9iaW4vcHl0aG9uMycsJy1JJywnLVMnLCctQicsc3RyKFNPVVJDRS8nc2NyaXB0cycvc2NyaXB0KSwqYXJnc10KICAgIG5lZWQoYXJndlsxOjRdPT1bJy1JJywnLVMnLCctQiddLCduYXRpdmVfcHl0aG9uX2ZsYWdzJykKICAgIHN0YXJ0ZWQ9dGltZS5tb25vdG9uaWMoKTtkZWFkbGluZT1taW4oRU5ELHN0YXJ0ZWQrNzUpO2NoaWxkPW93bmVkPU5vbmU7cGFydHM9W2J5dGVhcnJheSgpLGJ5dGVhcnJheSgpXTtzaXplPTAKICAgIHRyeToKICAgICAgICBjaGlsZD1zdWJwcm9jZXNzLlBvcGVuKGFyZ3Ysc3RkaW49c3VicHJvY2Vzcy5ERVZOVUxMLHN0ZG91dD1zdWJwcm9jZXNzLlBJUEUsc3RkZXJyPXN1YnByb2Nlc3MuUElQRSwKICAgICAgICAgICAgc3RhcnRfbmV3X3Nlc3Npb249VHJ1ZSxjbG9zZV9mZHM9VHJ1ZSk7b3duZWQ9Y2hpbGQKICAgICAgICB3aXRoIHNlbGVjdG9ycy5EZWZhdWx0U2VsZWN0b3IoKWFzIHNlbGVjdG9yOgogICAgICAgICAgICBmb3IgaW5kZXgscGlwZSBpbiBlbnVtZXJhdGUoKGNoaWxkLnN0ZG91dCxjaGlsZC5zdGRlcnIpKToKICAgICAgICAgICAgICAgIG9zLnNldF9ibG9ja2luZyhwaXBlLmZpbGVubygpLEZhbHNlKTtzZWxlY3Rvci5yZWdpc3RlcihwaXBlLHNlbGVjdG9ycy5FVkVOVF9SRUFELGluZGV4KQogICAgICAgICAgICB3aGlsZSBzZWxlY3Rvci5nZXRfbWFwKCk6CiAgICAgICAgICAgICAgICBuZWVkKHRpbWUubW9ub3RvbmljKCk8ZGVhZGxpbmUsJ2NvbW1hbmRfZGVhZGxpbmUnKQogICAgICAgICAgICAgICAgZm9yIGtleSxfIGluIHNlbGVjdG9yLnNlbGVjdChtaW4oLjEsbWF4KC4wMDEsZGVhZGxpbmUtdGltZS5tb25vdG9uaWMoKSkpKToKICAgICAgICAgICAgICAgICAgICByYXc9b3MucmVhZChrZXkuZmQsbWluKDE2Mzg0LDY1NTM3LXNpemUpKQogICAgICAgICAgICAgICAgICAgIGlmIG5vdCByYXc6c2VsZWN0b3IudW5yZWdpc3RlcihrZXkuZmlsZW9iaik7Y29udGludWUKICAgICAgICAgICAgICAgICAgICBzaXplKz1sZW4ocmF3KTtuZWVkKHNpemU8PTY1NTM2LCdjb21tYW5kX2NhcHR1cmVfYm91bmQnKTtwYXJ0c1trZXkuZGF0YV0uZXh0ZW5kKHJhdykKICAgICAgICBjb2RlPWNoaWxkLndhaXQodGltZW91dD1tYXgoLjAwMSxkZWFkbGluZS10aW1lLm1vbm90b25pYygpKSk7b3duZWQ9Tm9uZQogICAgICAgIG91dCxlcnI9bWFwKGJ5dGVzLHBhcnRzKQogICAgICAgIGlmIGV4cGVjdGVkX3JlZnVzYWw6CiAgICAgICAgICAgIG5lZWQoY29kZT09MSBhbmQgb3V0PT1iJydhbmQgZXJyPT1iJ0tlZXBlciByZWNvdmVyeSByZWZ1c2VkIChpbnZhbGlkX2lucHV0KS4gUHJlc2VydmUgdGhlIG9yaWdpbmFsIGpvdXJuYWwgYW5kIHNlcGFyYXRlbHkgc2VjdXJlZCBjb25maWd1cmF0aW9uLiBBbiBpbmNvbXBsZXRlIG91dHB1dCBtYXkgcmVtYWluOyB1c2UgYSBuZXcgcGF0aC4gTm90aGluZyB3YXMgc2lnbmVkLCBpbnN0YWxsZWQgb3Igc3RhcnRlZC5cbicsJ25lZ2F0aXZlX25hdGl2ZV9yZWZ1c2FsJykKICAgICAgICAgICAgcGFyc2VkPXsnZml4ZWRfbmF0aXZlX3JlZnVzYWwnOidpbnZhbGlkX2lucHV0JywncmVzdG9yYXRpb25fb3V0cHV0c19hYnNlbnQnOlRydWV9CiAgICAgICAgZWxzZToKICAgICAgICAgICAgbmVlZChjb2RlPT0wIGFuZCBub3QgZXJyLCduYXRpdmVfY2xpX3JlZnVzZWQnKQogICAgICAgICAgICBpZiBzY3JpcHQ9PSdrZWVwZXItc2lkZWNhci1yZWNvdmVyeS5weSc6CiAgICAgICAgICAgICAgICBwYXJzZWQ9anNvbi5sb2FkcyhvdXQpO25lZWQocGFyc2VkWydvayddaXMgVHJ1ZSBhbmQgcGFyc2VkWyd1bnNpZ25lZCddaXMgVHJ1ZSBhbmQgcGFyc2VkWydyZWFkaW5lc3NfYXBwcm92ZWQnXWlzIEZhbHNlLCdzaWRlY2FyX2NsaV9yZXN1bHQnKQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgbWF0Y2g9cmUuc2VhcmNoKHInXig/Ok1hbmlmZXN0fFJlc3RvcmUgcGxhbikgU0hBLTI1NjogKFswLTlhLWZdezY0fSkkJyxvdXQuZGVjb2RlKCd1dGY4Jywnc3RyaWN0JykscmUuTSkKICAgICAgICAgICAgICAgIG5lZWQobWF0Y2ggaXMgbm90IE5vbmUsJ25hdGl2ZV9jbGlfcmVzdWx0Jyk7cGFyc2VkPXsnbWFuaWZlc3Rfb3JfcGxhbl9zaGEyNTYnOm1hdGNoWzFdfQogICAgICAgIHJldHVybnsnc2NyaXB0JzpzY3JpcHQsJ2FjdGlvbic6YXJnc1swXSwncmV0dXJuY29kZSc6Y29kZSwnZXhwZWN0ZWRfcmVmdXNhbCc6ZXhwZWN0ZWRfcmVmdXNhbCwKICAgICAgICAgICAgJ3B5dGhvbl9mbGFncyc6YXJndlsxOjRdLAogICAgICAgICAgICAnZWxhcHNlZF9zZWNvbmRzJzp0aW1lLm1vbm90b25pYygpLXN0YXJ0ZWQsJ3N0ZG91dF9zaGEyNTYnOnNoYShvdXQpLCdzdGRvdXRfYnl0ZXMnOmxlbihvdXQpLAogICAgICAgICAgICAnc3RkZXJyX3NoYTI1Nic6c2hhKGVyciksJ3N0ZGVycl9ieXRlcyc6bGVuKGVyciksJ3BhcnNlZCc6cGFyc2VkfQogICAgZmluYWxseToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGlmIG93bmVkIGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgaWYgb3duZWQucG9sbCgpaXMgTm9uZToKICAgICAgICAgICAgICAgICAgICB0cnk6b3Mua2lsbHBnKG93bmVkLnBpZCxzaWduYWwuU0lHS0lMTCkKICAgICAgICAgICAgICAgICAgICBleGNlcHQgUHJvY2Vzc0xvb2t1cEVycm9yOnBhc3MKICAgICAgICAgICAgICAgIG93bmVkLndhaXQodGltZW91dD0yKQogICAgICAgIGZpbmFsbHk6CiAgICAgICAgICAgIGlmIGNoaWxkIGlzIG5vdCBOb25lOmNoaWxkLnN0ZG91dC5jbG9zZSgpO2NoaWxkLnN0ZGVyci5jbG9zZSgpCgoKZGVmIG1haW4oKToKICAgIHA9YXJncGFyc2UuQXJndW1lbnRQYXJzZXIoKTtwLmFkZF9hcmd1bWVudCgnbW9kZScsY2hvaWNlcz0oJ25lZ2F0aXZlJywnY29tcGxldGUnKSk7bW9kZT1wLnBhcnNlX2FyZ3MoKS5tb2RlCiAgICByZXN1bHQ9eydzY2hlbWEnOjEsJ21vZGUnOm1vZGUsJ3N1Y2Nlc3MnOkZhbHNlLCd1bnNpZ25lZCc6VHJ1ZSwncmVhZGluZXNzX2FwcHJvdmVkJzpGYWxzZSwKICAgICAgICAncHJvZHVjdGlvbl9hcHByb3ZlZCc6RmFsc2UsJ2Nhbm9uaWNhbF9zdGF0ZV92ZXJpZmllZCc6RmFsc2UsJ29wZXJhdGlvbmFsX2ZyZXNobmVzc19hcHByb3ZlZCc6RmFsc2UsCiAgICAgICAgJ3B1YmxpY190cmFuc2FjdGlvbnMnOjAsJ1JQQ19jYWxscyc6MCwndGVzdF9ib2RpZXNfcnVuJzowLCdzb3VyY2Vfc2VydmljZXNfc3RhcnRlZCc6RmFsc2UsCiAgICAgICAgJ29sZF9wb2xpY3lfY2hhbmdlZCc6RmFsc2UsJ25ld19yZXZpZXdfbWF4X2FnZV9zZWNvbmRzJzo4NjQwMCwnb3BlcmF0aW5nX3BvbGljeV9tYXhfYmFja3VwX2FnZV9zZWNvbmRzJzo5MDAsCiAgICAgICAgJ3Jlc3RvcmVzX2FyZV9yZXZpZXdfb25seSc6VHJ1ZSwnYXNvZl9jbG9ja19vdmVycmlkZSc6RmFsc2V9CiAgICBjYWxscz1bXTtiZWdhbj10aW1lLm1vbm90b25pYygpCiAgICB0cnk6CiAgICAgICAgcmVzdWx0Wydpc29sYXRpb24nXT1wcmVmbGlnaHQobW9kZSkKICAgICAgICBwYWNrYWdlPUJBU0UvJ3BhY2thZ2UnO291dGVyPXZhbHVlKHBhY2thZ2UvJ21hbmlmZXN0Lmpzb24nKTtuZXN0ZWQ9dmFsdWUocGFja2FnZS8nc2VsZWN0ZWQvbWFuaWZlc3QuanNvbicpCiAgICAgICAgbmVlZChzaGEocmVhZChwYWNrYWdlLydtYW5pZmVzdC5qc29uJykpPT1PVVRFUiBhbmQgc2hhKHJlYWQocGFja2FnZS8nc2VsZWN0ZWQvbWFuaWZlc3QuanNvbicpKT09TkVTVEVELCdwYWNrYWdlX21hbmlmZXN0X3BpbicpCiAgICAgICAgY3VycmVudD1pbnQodGltZS50aW1lKCkpO2FnZXM9eydvdXRlcic6Y3VycmVudC1vdXRlclsnY3JlYXRlZF9hdCddLCduZXN0ZWQnOmN1cnJlbnQtbmVzdGVkWydjcmVhdGVkX2F0J119CiAgICAgICAgbmVlZChhbGwoMDw9YWdlPD04NjQwMCBmb3IgYWdlIGluIGFnZXMudmFsdWVzKCkpLCdyZXZpZXdfY2FwdHVyZV9hZ2UnKQogICAgICAgIHJlc3VsdC51cGRhdGUoYWN0dWFsX3dhbGxjbG9ja19lcG9jaD1jdXJyZW50LGNhcHR1cmVfYWdlc19zZWNvbmRzPWFnZXMsCiAgICAgICAgICAgIG9yaWdpbmFsX2NhcHR1cmVfdGltZXM9eydvdXRlcic6b3V0ZXJbJ2NyZWF0ZWRfYXQnXSwnbmVzdGVkJzpuZXN0ZWRbJ2NyZWF0ZWRfYXQnXX0sCiAgICAgICAgICAgIG91dHNpZGVfb3JpZ2luYWxfb3BlcmF0aW5nX2FnZT1hbGwoYWdlPjkwMCBmb3IgYWdlIGluIGFnZXMudmFsdWVzKCkpKQogICAgICAgIG5hdGl2ZT1bJy0tY29uZmlnJyxzdHIoQ09ORklHKSwnLS1idW5kbGUnLHN0cihwYWNrYWdlLydzZWxlY3RlZCcpLCctLW1hbmlmZXN0LXNoYTI1NicsTkVTVEVELAogICAgICAgICAgICAnLS1tYXgtYWdlLXNlY29uZHMnLCc4NjQwMCcsJy0tbWluaW11bS1jcmVhdGVkLWF0JyxzdHIobmVzdGVkWydjcmVhdGVkX2F0J10pXQogICAgICAgIGlmIG1vZGU9PSduZWdhdGl2ZSc6CiAgICAgICAgICAgIG5lZWQobm90KFJVTlRJTUUvJ2tlZXBlci1yZXZpZXcnKS5leGlzdHMoKWFuZCBub3QoUlVOVElNRS8nc2lkZWNhci1yZXZpZXcnKS5leGlzdHMoKSwnbmVnYXRpdmVfb3V0cHV0X3ByZWV4aXN0cycpCiAgICAgICAgICAgIGNhbGxzLmFwcGVuZChydW4oJ2tlZXBlci1yZWNvdmVyeS5weScsWyd2ZXJpZnknLCpuYXRpdmVdLGV4cGVjdGVkX3JlZnVzYWw9VHJ1ZSkpCiAgICAgICAgICAgIG5lZWQobm90KFJVTlRJTUUvJ2tlZXBlci1yZXZpZXcnKS5leGlzdHMoKWFuZCBub3QoUlVOVElNRS8nc2lkZWNhci1yZXZpZXcnKS5leGlzdHMoKSwnbmVnYXRpdmVfb3V0cHV0X2NyZWF0ZWQnKQogICAgICAgICAgICByZXN1bHQudXBkYXRlKHN1Y2Nlc3M9VHJ1ZSxtaXNzaW5nX3JlcXVpcmVkX2RlcGVuZGVuY3k9J29yaWdpbmFsX2NvbmZpZ3VyYXRpb24nLG5hdGl2ZV9yZWZ1c2FsX2JlZm9yZV9yZXN0b3JlPVRydWUsY2FsbHM9Y2FsbHMpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgY29uZmlnPXZhbHVlKENPTkZJRyk7cG9saWN5PXZhbHVlKFBPTElDWSkKICAgICAgICAgICAgbmVlZChwb2xpY3lbJ21heF9iYWNrdXBfYWdlX3NlY29uZHMnXT09OTAwIGFuZCBwb2xpY3lbJ21heF9ieXRlcyddPT0xNjc3NzIxNiBhbmQgcG9saWN5WydtYXhfc2Vjb25kcyddPT02MCwnb3JpZ2luYWxfcG9saWN5JykKICAgICAgICAgICAgbmVlZChhbGwobm90IG9zLnBhdGgubGV4aXN0cyhQYXRoKGNvbmZpZ1trZXldKSlmb3Iga2V5IGluKCdrZXlzdG9yZScsJ3Bhc3N3b3JkX2ZpbGUnKSksJ3NpZ25lcl9tYXRlcmlhbF9wcmVzZW50JykKICAgICAgICAgICAgc2lkZT1bJy0tcG9saWN5JyxzdHIoUE9MSUNZKSwnLS1wb2xpY3ktc2hhMjU2JyxQT0xJQ1lfUElOLCctLWJ1bmRsZScsc3RyKHBhY2thZ2UpLAogICAgICAgICAgICAgICAgJy0tbWFuaWZlc3Qtc2hhMjU2JyxPVVRFUiwnLS1tYXgtYWdlLXNlY29uZHMnLCc4NjQwMCcsJy0tbWluaW11bS1jcmVhdGVkLWF0JyxzdHIob3V0ZXJbJ2NyZWF0ZWRfYXQnXSldCiAgICAgICAgICAgIHRhc2tzPVsoJ2tlZXBlci1yZWNvdmVyeS5weScsWyd2ZXJpZnknLCpuYXRpdmVdKSwKICAgICAgICAgICAgICAgICgna2VlcGVyLXJlY292ZXJ5LnB5JyxbJ3Jlc3RvcmUnLCpuYXRpdmUsJy0tb3V0cHV0JyxzdHIoUlVOVElNRS8na2VlcGVyLXJldmlldycpXSksCiAgICAgICAgICAgICAgICAoJ2tlZXBlci1zaWRlY2FyLXJlY292ZXJ5LnB5JyxbJ3ZlcmlmeScsKnNpZGVdKSwKICAgICAgICAgICAgICAgICgna2VlcGVyLXNpZGVjYXItcmVjb3ZlcnkucHknLFsncmVzdG9yZScsKnNpZGUsJy0tb3V0cHV0JyxzdHIoUlVOVElNRS8nc2lkZWNhci1yZXZpZXcnKV0pXQogICAgICAgICAgICBmb3Igc2NyaXB0LGFyZ3MgaW4gdGFza3M6Y2FsbHMuYXBwZW5kKHJ1bihzY3JpcHQsYXJncykpCiAgICAgICAgICAgIGtlZXBlcj1SVU5USU1FLydrZWVwZXItcmV2aWV3JztzaWRlY2FyPVJVTlRJTUUvJ3NpZGVjYXItcmV2aWV3JztnZW5lcmF0aW9uPXZhbHVlKHBhY2thZ2UvJ3NlbGVjdGlvbi5qc29uJylbJ2dlbmVyYXRpb24nXQogICAgICAgICAgICBwYWlycz17J2tlZXBlci1zdGF0ZS5qc29uJzoocGFja2FnZS8nc2VsZWN0ZWQvam91cm5hbC5qc29uJyxrZWVwZXIvJ2tlZXBlci1zdGF0ZS5qc29uJyksCiAgICAgICAgICAgICAgICAnc2NoZWR1bGVyL3NlbGVjdGVkLmpzb24nOihwYWNrYWdlLydzZWxlY3Rpb24uanNvbicsc2lkZWNhci8nc2NoZWR1bGVyL3NlbGVjdGVkLmpzb24nKSwKICAgICAgICAgICAgICAgICdhbGVydHMvc3RhdGUuanNvbic6KHBhY2thZ2UvJ2FsZXJ0LXN0YXRlLmpzb24nLHNpZGVjYXIvJ2FsZXJ0cy9zdGF0ZS5qc29uJyksCiAgICAgICAgICAgICAgICAnc2VsZWN0ZWQvbWFuaWZlc3QuanNvbic6KHBhY2thZ2UvJ3NlbGVjdGVkL21hbmlmZXN0Lmpzb24nLHNpZGVjYXIvJ2JhY2t1cHMnL2dlbmVyYXRpb24vJ21hbmlmZXN0Lmpzb24nKSwKICAgICAgICAgICAgICAgICdzZWxlY3RlZC9qb3VybmFsLmpzb24nOihwYWNrYWdlLydzZWxlY3RlZC9qb3VybmFsLmpzb24nLHNpZGVjYXIvJ2JhY2t1cHMnL2dlbmVyYXRpb24vJ2pvdXJuYWwuanNvbicpfQogICAgICAgICAgICBjb21wYXJlZD17fQogICAgICAgICAgICBmb3IgbmFtZSwoc291cmNlLHRhcmdldClpbiBwYWlycy5pdGVtcygpOgogICAgICAgICAgICAgICAgcmF3PXJlYWQoc291cmNlKTtuZWVkKHJhdz09cmVhZCh0YXJnZXQpLCdyZXN0b3JlZF9yYXdfYnl0ZXNfZGlmZmVyJyk7Y29tcGFyZWRbbmFtZV09eydieXRlcyc6bGVuKHJhdyksJ3NoYTI1Nic6c2hhKHJhdyl9CiAgICAgICAgICAgIG5hdGl2ZV9wbGFuPXZhbHVlKGtlZXBlci8nUkVTVE9SRV9QTEFOLmpzb24nKTtzaWRlX3BsYW49dmFsdWUoc2lkZWNhci8nUkVTVE9SRV9QTEFOLmpzb24nKQogICAgICAgICAgICBuYXRpdmVfcGluPXNoYShyZWFkKGtlZXBlci8nUkVTVE9SRV9QTEFOLmpzb24nKSk7c2lkZV9waW49c2hhKHJlYWQoc2lkZWNhci8nUkVTVE9SRV9QTEFOLmpzb24nKSkKICAgICAgICAgICAgbmVlZChjYWxsc1swXVsncGFyc2VkJ11bJ21hbmlmZXN0X29yX3BsYW5fc2hhMjU2J109PU5FU1RFRCBhbmQgY2FsbHNbMV1bJ3BhcnNlZCddWydtYW5pZmVzdF9vcl9wbGFuX3NoYTI1NiddPT1uYXRpdmVfcGluCiAgICAgICAgICAgICAgICBhbmQgY2FsbHNbMl1bJ3BhcnNlZCddWydtYW5pZmVzdF9zaGEyNTYnXT09T1VURVIgYW5kIGNhbGxzWzNdWydwYXJzZWQnXVsnbWFuaWZlc3Rfc2hhMjU2J109PU9VVEVSCiAgICAgICAgICAgICAgICBhbmQgY2FsbHNbM11bJ3BhcnNlZCddWydyZXN0b3JlX3BsYW5fc2hhMjU2J109PXNpZGVfcGluLCdDTElfb3V0cHV0X2JpbmRpbmcnKQogICAgICAgICAgICBuZWVkKG5hdGl2ZV9wbGFuWyd1bnNpZ25lZCddaXMgVHJ1ZSBhbmQgYWxsKG5hdGl2ZV9wbGFuW2tleV1pcyBGYWxzZSBmb3Iga2V5IGluCiAgICAgICAgICAgICAgICAoJ2xpdmVfcmVhZHknLCdjYW5vbmljYWxfc3RhdGVfdmVyaWZpZWQnLCdvbGRfa2VlcGVyX2ZlbmNlZCcsJ3NpZ25lcl9tYXRlcmlhbF9pbmNsdWRlZCcsJ2NvbmZpZ3VyYXRpb25faW5zdGFsbGVkJywnc2VydmljZV9yZXN0YXJ0ZWQnKSksJ25hdGl2ZV9hZG9wdGlvbl9mbGFnJykKICAgICAgICAgICAgbmVlZChzaWRlX3BsYW5bJ3Vuc2lnbmVkJ11pcyBUcnVlIGFuZCBhbGwoc2lkZV9wbGFuW2tleV1pcyBGYWxzZSBmb3Iga2V5IGluCiAgICAgICAgICAgICAgICAoJ3JlYWRpbmVzc19hcHByb3ZlZCcsJ29sZF9zaWRlY2Fyc19mZW5jZWQnLCdjYW5vbmljYWxfc3RhdGVfdmVyaWZpZWQnLCdzaWduZXJfbWF0ZXJpYWxfaW5jbHVkZWQnLAogICAgICAgICAgICAgICAgJ3BvbGljeV9vcl9jb25maWd1cmF0aW9uX2luc3RhbGxlZCcsJ3NlcnZpY2VzX3Jlc3RhcnRlZCcsJ3J1bnRpbWVfcGF0aHNfbWFwcGVkJywnbG9ja19vd25lcnNoaXBfcmVzdG9yZWQnLCdzZWxlY3RlZF9nZW5lcmF0aW9uX2ZyZXNobmVzc19hcHByb3ZlZCcpKSwnc2lkZWNhcl9hZG9wdGlvbl9mbGFnJykKICAgICAgICAgICAgbG9ja3M9W10KICAgICAgICAgICAgZm9yIHBhdGggaW4oc2lkZWNhci8nc2NoZWR1bGVyL3NjaGVkdWxlLmxvY2snLHNpZGVjYXIvJ2FsZXJ0cy9hbGVydC5sb2NrJyk6CiAgICAgICAgICAgICAgICBpdGVtPXBhdGgubHN0YXQoKTtuZWVkKHN0YXQuU19JU1JFRyhpdGVtLnN0X21vZGUpYW5kIGl0ZW0uc3RfdWlkPT02NTUzNCBhbmQgc3RhdC5TX0lNT0RFKGl0ZW0uc3RfbW9kZSk9PTBvNjAwCiAgICAgICAgICAgICAgICAgICAgYW5kIGl0ZW0uc3Rfbmxpbms9PTEgYW5kIGl0ZW0uc3Rfc2l6ZT09MCBhbmQgcmVhZChwYXRoKT09YicnLCduZXdfbG9ja19tZXRhZGF0YScpCiAgICAgICAgICAgICAgICBsb2Nrcy5hcHBlbmQoeydkZXZpY2UnOml0ZW0uc3RfZGV2LCdpbm9kZSc6aXRlbS5zdF9pbm8sJ3VpZCc6aXRlbS5zdF91aWQsJ21vZGUnOnN0YXQuU19JTU9ERShpdGVtLnN0X21vZGUpLAogICAgICAgICAgICAgICAgICAgICdsaW5rcyc6aXRlbS5zdF9ubGluaywnYnl0ZXMnOml0ZW0uc3Rfc2l6ZX0pCiAgICAgICAgICAgIG5lZWQobGVuKHsocm93WydkZXZpY2UnXSxyb3dbJ2lub2RlJ10pZm9yIHJvdyBpbiBsb2Nrc30pPT0yLCduZXdfbG9ja19hbGlhcycpCiAgICAgICAgICAgIGlkZW50aXR5PXZhbHVlKEJBU0UvJ0lERU5USVRZLmpzb24nKTtuZWVkKHsocm93WydkZXZpY2UnXSxyb3dbJ2lub2RlJ10pZm9yIHJvdyBpbiBsb2Nrc30uaXNkaXNqb2ludCgKICAgICAgICAgICAgICAgIHt0dXBsZShwYWlyKWZvciBwYWlyIGluIGlkZW50aXR5WydvbGRfbG9ja19pbm9kZV9wYWlycyddfSksJ29sZF9sb2NrX3JldXNlZCcpCiAgICAgICAgICAgIG9ic2VydmVyPXZhbHVlKHNpZGVjYXIvJ2FsZXJ0cy9zdGF0ZS5qc29uJyk7c3RhdGU9dmFsdWUoa2VlcGVyLydrZWVwZXItc3RhdGUuanNvbicpCiAgICAgICAgICAgIG5lZWQob2JzZXJ2ZXI9PXZhbHVlKHBhY2thZ2UvJ2FsZXJ0LXN0YXRlLmpzb24nKWFuZCBzdGF0ZT09dmFsdWUocGFja2FnZS8nc2VsZWN0ZWQvam91cm5hbC5qc29uJyksJ2FjY291bnRpbmdfc3RhdGVfY2hhbmdlZCcpCiAgICAgICAgICAgIG5lZWQoc2hhKHJlYWQoUE9MSUNZKSk9PVBPTElDWV9QSU4gYW5kIHNoYShyZWFkKENPTkZJRykpPT1DT05GSUdfUElOLCdyZWZlcmVuY2VzX2NoYW5nZWQnKQogICAgICAgICAgICByZXN1bHQudXBkYXRlKHN1Y2Nlc3M9VHJ1ZSxjYWxscz1jYWxscyxyZXN0b3JlZF9maWxlcz1jb21wYXJlZCxuYXRpdmVfcmVzdG9yZV9wbGFuX3NoYTI1Nj1uYXRpdmVfcGluLAogICAgICAgICAgICAgICAgc2lkZWNhcl9yZXN0b3JlX3BsYW5fc2hhMjU2PXNpZGVfcGluLGFsbF9hZG9wdGlvbl9mbGFnc19mYWxzZT1UcnVlLG5ld19lbXB0eV9sb2Nrcz1sb2NrcywKICAgICAgICAgICAgICAgIG5ld19sb2Nrc19kaXNqb2ludF9mcm9tX29yaWdpbmFscz1UcnVlLHNpZ25lcl9tYXRlcmlhbF9hYnNlbnQ9VHJ1ZSxwZW5kaW5nX3N1bW1hcnk9c2lkZV9wbGFuWydvYnNlcnZlcl9zdW1tYXJ5J11bJ3BlbmRpbmcnXSwKICAgICAgICAgICAgICAgIG91dGJveF9pZHM9W2VudHJ5WydldmVudF9pZCddZm9yIGVudHJ5IGluIG9ic2VydmVyWydvdXRib3gnXV0sc2VxdWVuY2U9b2JzZXJ2ZXJbJ3NlcXVlbmNlJ10sCiAgICAgICAgICAgICAgICByYXdfcmVjb3Jkc19yZXdyaXR0ZW49RmFsc2Usb3JpZ2luYWxfdGltZXN0YW1wc19wcmVzZXJ2ZWQ9VHJ1ZSkKICAgIGV4Y2VwdCBCYXNlRXhjZXB0aW9uIGFzIGV4YzoKICAgICAgICByZXN1bHQudXBkYXRlKGVycm9yX3R5cGU9dHlwZShleGMpLl9fbmFtZV9fLGVycm9yX3NoYTI1Nj1zaGEoc3RyKGV4YykuZW5jb2RlKCkpLGNhbGxzPWNhbGxzLAogICAgICAgICAgICBmcmFtZXM9W3snZmlsZSc6UGF0aChmcmFtZS5maWxlbmFtZSkubmFtZSwnbGluZSc6ZnJhbWUubGluZW5vLCdmdW5jdGlvbic6ZnJhbWUubmFtZX0KICAgICAgICAgICAgICAgIGZvciBmcmFtZSBpbiB0cmFjZWJhY2suZXh0cmFjdF90YihleGMuX190cmFjZWJhY2tfXylbLTg6XV0pCiAgICByZXN1bHRbJ2VsYXBzZWRfc2Vjb25kcyddPXRpbWUubW9ub3RvbmljKCktYmVnYW47cHVibGlzaChyZXN1bHQpCiAgICBwcmludChqc29uLmR1bXBzKHsnc3VjY2Vzcyc6cmVzdWx0WydzdWNjZXNzJ10sJ21vZGUnOm1vZGUsJ25hdGl2ZV9DTElfY2FsbHMnOmxlbihjYWxscyl9KSkKICAgIHJldHVybiAwIGlmIHJlc3VsdFsnc3VjY2VzcyddZWxzZSAxCgoKaWYgX19uYW1lX189PSdfX21haW5fXyc6cmFpc2UgU3lzdGVtRXhpdChtYWluKCkpCg=='
WORKER_SHA='47aa5a19542ef37622aff1ff81c33dbe855bb92b7db48b72073bf8fbc2fb1b6e'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def need(value,code='fixed_c824_refused'):
    if not value:raise ValueError(code)


def run(argv,timeout=15):
    child=owned=None;parts=[bytearray(),bytearray()];size=0;end=time.monotonic()+timeout
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'},start_new_session=True,close_fds=True);owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end,'control_deadline')
                for key,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536,'control_capture_bound');parts[key.data].extend(raw)
        code=child.wait(timeout=max(.001,end-time.monotonic()));owned=None
        return code,bytes(parts[0]),bytes(parts[1])
    finally:
        try:
            if owned is not None:
                if owned.poll()is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()


def read(path,maximum=1048576,owner=0):
    before=path.lstat();need(stat.S_ISREG(before.st_mode)and before.st_uid==owner and before.st_nlink==1
        and not before.st_mode&0o022 and before.st_size<=maximum,'file_metadata')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        raw=bytearray()
        while True:
            part=os.read(fd,min(65536,maximum+1-len(raw)))
            if not part:break
            raw.extend(part);need(len(raw)<=maximum,'file_bound')
        key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns)
        need(key(before)==key(os.fstat(fd))==key(path.lstat())and len(raw)==before.st_size,'file_changed')
        return bytes(raw)
    finally:os.close(fd)


def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result,'duplicate_key');result[key]=value
    return result


def invalid(_):raise ValueError('invalid_number')


def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_float=invalid,parse_constant=invalid)


def properties(unit):
    need(unit in(*OLD_UNITS,*(UNIT_BASE+'-'+mode+'.service'for mode in MODES)))
    fields='Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,User,Group,PrivateNetwork,Restart,KillMode,RootDirectory,BindReadOnlyPaths,ReadWritePaths,RestrictAddressFamilies,InvocationID'
    code,out,_=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+fields])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found');return value


def empty(unit,p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group=='/system.slice/'+unit)
    try:raw=(Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096);return not raw.strip()


def original_snapshot():
    fence={}
    for unit in OLD_UNITS:
        props=properties(unit);need(empty(unit,props)and props.get('ActiveState')in('inactive','failed',None))
        need(props.get('LoadState')=='not-found'or props.get('Restart')=='no');fence[unit]=props
    manifest=read(OLD/'SOURCE_MANIFEST.json');need(sha(manifest)==SOURCE_PIN,'original_source_manifest')
    pins={}
    for name,row in SOURCE_FILES.items():
        raw=read(OLD/'source'/name);need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'original_source_pin');pins[name]=row
    refs={}
    for name,digest,owner in(('keeper-config.json',CONFIG_PIN,65534),('policy.json',POLICY_PIN,0)):
        raw=read(OLD/'runtime'/name,65536,owner);need(sha(raw)==digest,'original_reference_pin')
        refs[name]={'bytes':len(raw),'sha256':digest}
    retained={}
    for name in('working/runtime/journal.json','schedule/selected.json','alerts/state.json',
            *('sidecar-bundle/'+name for name in PACKAGE_FILES)):
        path=OLD/'runtime'/name;raw=read(path,65536,65534);item=path.lstat()
        retained[name]={'bytes':len(raw),'sha256':sha(raw),'metadata':[item.st_dev,item.st_ino,item.st_uid,
            item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns]}
        if name.startswith('sidecar-bundle/'):
            expected=PACKAGE_FILES[name[len('sidecar-bundle/'):]]
            need(sha(raw)==expected['sha256']and(expected['bytes']is None or len(raw)==expected['bytes']),'original_package_pin')
    metadata=[]
    for path in(OLD/'runtime/schedule/schedule.lock',OLD/'runtime/alerts/alert.lock'):
        item=path.lstat();need(stat.S_ISREG(item.st_mode)and item.st_uid==65534 and item.st_nlink==1
            and stat.S_IMODE(item.st_mode)==0o600,'old_lock_metadata')
        metadata.append([item.st_dev,item.st_ino,item.st_uid,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns])
    st=(OLD/'SOURCE_MANIFEST.json').lstat()
    return{'fenced_units':fence,'source_manifest_sha256':SOURCE_PIN,'source_files':pins,'references':refs,'retained_original_files':retained,
        'old_lock_metadata':metadata,'old_source_manifest_inode_pair':[st.st_dev,st.st_ino]}


def unchanged(before,after):
    return all(before[key]==after[key]for key in('source_manifest_sha256','source_files','references','retained_original_files','old_lock_metadata','old_source_manifest_inode_pair'))


def runtime_tree(folder):
    allowed_links={'sitecustomize.py':'/etc/python3.12/sitecustomize.py',
        '_sysconfigdata__linux_x86_64-linux-gnu.py':'_sysconfigdata__x86_64-linux-gnu.py',
        'config-3.12-x86_64-linux-gnu/libpython3.12.so':'../../x86_64-linux-gnu/libpython3.12.so.1'}
    rows=[];total=0;visited=0;links=set();stack=[(folder,0)];end=time.monotonic()+20
    while stack:
        directory,depth=stack.pop();need(depth<=16 and time.monotonic()<end,'runtime_inventory_deadline')
        with os.scandir(directory)as entries:
            for entry in entries:
                visited+=1;need(visited<=8192 and time.monotonic()<end,'runtime_inventory_bound')
                if entry.name in('site-packages','dist-packages'):continue
                item=entry.stat(follow_symlinks=False);path=Path(entry.path)
                if stat.S_ISDIR(item.st_mode):stack.append((path,depth+1));continue
                if path.suffix not in('.py','.so','.pyc'):continue
                relative=str(path.relative_to(folder))
                if stat.S_ISLNK(item.st_mode):
                    need(relative in allowed_links and item.st_uid==0 and item.st_nlink==1,'runtime_link_metadata')
                    key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
                    target=os.readlink(path);need(target==allowed_links[relative]and key(item)==key(path.lstat()),'runtime_link_target')
                    need(os.readlink(path)==target and key(item)==key(path.lstat()),'runtime_link_changed')
                    rows.append(['symlink',relative,target,item.st_uid,stat.S_IMODE(item.st_mode),item.st_nlink]);links.add(relative);continue
                need(stat.S_ISREG(item.st_mode)and not item.st_mode&0o022,'runtime_file_metadata')
                raw=read(path,16777216);total+=len(raw);need(total<=134217728 and len(rows)<4096,'runtime_inventory_bound')
                rows.append(['file',relative,len(raw),sha(raw)])
    rows.sort()
    need(rows and links==set(allowed_links),'runtime_required_links')
    return{'files':len(rows)-len(links),'symlinks':len(links),'entries':len(rows),'bytes':total,'sha256':sha(enc(rows))}


def runtime_review():
    # Only OS stdlib imports. This explicitly supplies and records the external runtime.
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode,'controller_python_isolation')
    import copy,datetime,decimal,fcntl,functools,http.client,math,secrets,shutil,socket,ssl,tempfile,typing,urllib.error,urllib.request,bz2,lzma
    stdlib=Path(os.__file__).resolve().parent;need(re.fullmatch('/usr/lib/python3\\.[0-9]+',str(stdlib))is not None,'OS_stdlib_path')
    executable=Path(sys.executable).resolve();need(re.fullmatch('/usr/bin/python3\\.[0-9]+',str(executable))is not None,'OS_interpreter_path')
    mapped=set()
    with Path('/proc/self/maps').open('rb')as stream:maps_raw=stream.read(65537)
    need(len(maps_raw)<=65536,'OS_maps_bound')
    for line in maps_raw.decode('utf8','strict').splitlines():
        part=line.split(None,5)
        if len(part)==6 and part[5].startswith('/'):
            candidate=Path(part[5]).resolve()
            if '.so'in candidate.name and not candidate.is_relative_to(stdlib):
                need(str(candidate).startswith('/usr/lib/x86_64-linux-gnu/'),'OS_library_scope');mapped.add(candidate)
    need(0<len(mapped)<=32,'OS_library_count')
    mounts=[{'source':str(executable),'target':'/usr/bin/python3'},
        {'source':str(stdlib),'target':str(stdlib)}]
    mounts.extend({'source':str(path),'target':str(path)}for path in sorted(mapped))
    loader=Path('/lib64/ld-linux-x86-64.so.2').resolve();need(loader in mapped,'OS_loader_not_mapped')
    mounts.append({'source':str(loader),'target':'/lib64/ld-linux-x86-64.so.2'})
    files={}
    for row in mounts:
        if row['target']==str(stdlib):continue
        raw=read(Path(row['source']),16777216);files[row['target']]={'bytes':len(raw),'sha256':sha(raw)}
    return{'schema':1,'kind':'popl-c824-external-OS-runtime','version':sys.version,'stdlib':str(stdlib),
        'stdlib_tree':runtime_tree(stdlib),'stdlib_inventory_scope':'regular .py/.so/.pyc bytes including caches plus exactly3 reviewed link metadata; pruned site-packages/dist-packages; link targets never followed',
        'mounts':mounts,'files':files,'site_packages_enabled':False,'OS_runtime_is_external':True,
        'OS_disaster_recovery_proved':False,'actual_second_host':False}


def export(a):
    need(os.getuid()==0);before=original_snapshot();files={}
    for name,owner in(('keeper-config.json',65534),('policy.json',0)):
        raw=read(OLD/'runtime'/name,65536,owner);files['references/'+name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    runtime=runtime_review();after=original_snapshot();need(unchanged(before,after))
    response={'schema':1,'kind':'popl-keeper-reconstruction-reference-export','files':files,'runtime_review':runtime,
        'runtime_review_sha256':sha(enc(runtime)),'original_snapshot_sha256':sha(enc(before)),
        'source_manifest_sha256':SOURCE_PIN,'source_files_count':41,'original_unchanged':True,
        'source_bodies_exported':False,'working_journal_exported':False,'signer_material_exported':False,
        'unsigned':True,'readiness_approved':False}
    need(len(enc(response))<=65536,'reference_export_bound');return response


def write(path,raw,mode=0o444,owner=0):
    need(len(raw)<=2097152,'write_bound');path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchown(stream.fileno(),owner,owner);os.fchmod(stream.fileno(),mode)


def expected_files():
    result={'source/'+name:row for name,row in SOURCE_FILES.items()}
    result.update({'SOURCE_MANIFEST.json':{'bytes':None,'sha256':SOURCE_PIN},
        'references/keeper-config.json':{'bytes':5254,'sha256':CONFIG_PIN},'references/policy.json':{'bytes':None,'sha256':POLICY_PIN}})
    result.update({'package/'+name:row for name,row in PACKAGE_FILES.items()});need(len(result)==49);return result


def packet_files(packet):
    need(type(packet)is dict and set(packet)=={'schema','kind','files','desktop_proof_base64'}
        and type(packet['schema'])is int and packet['schema']==1 and packet['kind']=='popl-keeper-reconstruction-import','import_schema')
    expected=expected_files();need(type(packet['files'])is dict and set(packet['files'])==set(expected),'input_inventory')
    files={};total=0
    for name,row in packet['files'].items():
        need(type(row)is dict and set(row)=={'bytes','sha256','raw_base64'},'member_schema')
        raw=base64.b64decode(row['raw_base64'],validate=True);pin=expected[name]
        need(type(row['bytes'])is int and row['bytes']==len(raw)and 0<len(raw)<=1048576
            and sha(raw)==row['sha256']==pin['sha256']and(pin['bytes']is None or len(raw)==pin['bytes']),'member_pin')
        files[name]=raw;total+=len(raw);need(total<=1048576,'raw_kit_bound')
    return files


def owned():
    need(os.getuid()==0);item=LAB.lstat();need(stat.S_ISDIR(item.st_mode)and item.st_uid==0 and not item.st_mode&0o022)
    identity=decode(read(LAB/'LAB_ID.json',32768));need(identity['controller_sha256']==ACTIVE_CONTROLLER_SHA and identity['worker_sha256']==WORKER_SHA)
    need(sha(read(LAB/'worker.py',65536))==WORKER_SHA);return identity


def install(a):
    need(os.getuid()==0 and not os.path.lexists(LAB),'new_lab_only')
    need(all(properties(UNIT_BASE+'-'+mode+'.service').get('LoadState')=='not-found'for mode in MODES),'unit_exists')
    for digest in(a.desktop_proof_sha256,a.runtime_review_sha256):need(type(digest)is str and re.fullmatch('[0-9a-f]{64}',digest)is not None,'review_pin')
    compressed=sys.stdin.buffer.read(2097153);need(0<len(compressed)<=2097152,'compressed_wire_bound')
    inflater=zlib.decompressobj();raw=inflater.decompress(compressed,2097153)
    need(0<len(raw)<=2097152 and inflater.eof and not inflater.unconsumed_tail and not inflater.unused_data,'expanded_wire_bound')
    packet=decode(raw);files=packet_files(packet);proof_raw=base64.b64decode(packet['desktop_proof_base64'],validate=True)
    need(0<len(proof_raw)<=16384 and sha(proof_raw)==a.desktop_proof_sha256,'desktop_proof_pin');proof=decode(proof_raw)
    need(proof['schema']==1 and proof['kind']=='popl-unsigned-recovery-kit-review'and proof['ok']is True
        and proof['unsigned']is True and proof['readiness_approved']is False and proof['production_approved']is False,'desktop_proof_flags')
    need(proof['source_manifest_sha256']==SOURCE_PIN and proof['configuration_sha256']==CONFIG_PIN and proof['policy_sha256']==POLICY_PIN
        and proof['outer_manifest_sha256']==OUTER and proof['nested_manifest_sha256']==NESTED,'desktop_proof_trust')
    input_files={name:{'bytes':len(data),'sha256':sha(data)}for name,data in files.items()};need(proof['files']==input_files,'desktop_input_binding')
    before=original_snapshot();runtime=runtime_review();need(sha(enc(runtime))==a.runtime_review_sha256,'OS_runtime_review_changed')
    worker=base64.b64decode(WORKER,validate=True);need(sha(worker)==WORKER_SHA)
    LAB.mkdir(mode=0o700);write(LAB/'worker.py',worker)
    for mode in MODES:
        root=LAB/(mode+'-root');root.mkdir(mode=0o755);base=root/'reconstruction';base.mkdir(mode=0o755)
        write(base/'worker.py',worker);write(base/'SOURCE_MANIFEST.json',files['SOURCE_MANIFEST.json'])
        write(base/'RUNTIME_REVIEW.json',enc(runtime))
        identity={'schema':1,'input_files':input_files,'old_source_manifest_inode_pair':before['old_source_manifest_inode_pair'],
            'old_lock_inode_pairs':[row[:2]for row in before['old_lock_metadata']]}
        write(base/'IDENTITY.json',enc(identity))
        for name,data in files.items():
            if name.startswith('source/'):path=root/str(OLD).lstrip('/')/name
            elif name=='references/policy.json':path=root/str(OLD/'runtime/policy.json').lstrip('/')
            elif name=='references/keeper-config.json':
                if mode=='negative':continue
                path=root/str(OLD/'runtime/keeper-config.json').lstrip('/')
            elif name.startswith('package/'):path=base/name
            else:continue
            write(path,data)
        # Only layout prerequisites, never an original live state/lock/signer.
        configuration=decode(files['references/keeper-config.json']);policy=decode(files['references/policy.json'])
        need(policy['configuration']==str(OLD/'runtime/keeper-config.json')and policy['working_directory']==str(OLD/'runtime/working'),'original_logical_paths')
        for logical in[policy['working_directory'],*map(lambda key:str(Path(policy[key]).parent),('scheduler_directory','backup_directory','alert_directory'))]:
            need(Path(logical).is_relative_to(OLD),'layout_scope');(root/logical.lstrip('/')).mkdir(parents=True,exist_ok=True,mode=0o755)
        working=root/policy['working_directory'].lstrip('/');os.chown(working,65534,65534);os.chmod(working,0o700)
        for key in('keystore','password_file'):
            need(Path(configuration[key]).is_relative_to(OLD/'runtime/working'),'fixture_signer_path')
            need(not os.path.lexists(root/configuration[key].lstrip('/')),'signer_material_present')
        runtime_dir=base/'runtime';runtime_dir.mkdir(mode=0o700);os.chown(runtime_dir,65534,65534)
        for name in('stdout.log','stderr.log'):write(runtime_dir/name,b'',0o600,65534)
        for mount in runtime['mounts']:
            target=root/mount['target'].lstrip('/');target.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
            if Path(mount['source']).is_dir():target.mkdir(mode=0o755)
            else:write(target,b'',0o444)
    after=original_snapshot();need(unchanged(before,after),'original_changed')
    write(LAB/'INSTALL.json',enc({'schema':1,'original_before':before,'original_after_snapshot_sha256':sha(enc(after)),'original_unchanged':True,
        'input_files':input_files,'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256,
        'runtime_mounts':runtime['mounts'],'compressed_wire_bytes':len(compressed),'expanded_wire_bytes':len(raw),
        'outer_private_directory_uid':LAB.lstat().st_uid,'outer_private_directory_mode':stat.S_IMODE(LAB.lstat().st_mode),
        'source_fallback':False,'configuration_or_policy_rewritten':False,'original_host_opt_bound':False}),0o600)
    write(LAB/'LAB_ID.json',enc({'schema':1,'controller_sha256':ACTIVE_CONTROLLER_SHA,'worker_sha256':WORKER_SHA,
        'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256}),0o600)
    return{'phase':'installed','input_file_count':49,'compressed_wire_bytes':len(compressed),'expanded_wire_bytes':len(raw),
        'desktop_proof_sha256':a.desktop_proof_sha256,'runtime_review_sha256':a.runtime_review_sha256,
        'original_unchanged':True,'root_directories_created':2,'original_host_opt_bound':False}


def start(a):
    identity=owned();mode=a.mode;unit=UNIT_BASE+'-'+mode+'.service';root=LAB/(mode+'-root')
    need(mode in MODES and not(LAB/('START-'+mode+'.json')).exists()and properties(unit).get('LoadState')=='not-found','no_restart_or_rerun')
    if mode=='complete':
        negative=decode(read(LAB/'negative-root/reconstruction/runtime/RESULT.json',32768,65534))
        need(negative['success']is True and negative['native_refusal_before_restore']is True,'negative_required_first')
        prior=properties(UNIT_BASE+'-negative.service');need(empty(UNIT_BASE+'-negative.service',prior),'negative_not_settled')
    before=original_snapshot();runtime=runtime_review();need(sha(enc(runtime))==identity['runtime_review_sha256'],'runtime_changed')
    binds=' '.join(row['source']+':'+row['target']for row in runtime['mounts'])
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','RootDirectory':str(root),'MountAPIVFS':'yes',
        'PrivateNetwork':'yes','PrivateTmp':'yes','PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes',
        'ProtectProc':'invisible','ProcSubset':'pid',
        'NoNewPrivileges':'yes','ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes',
        'RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
        'RestrictAddressFamilies':'AF_UNIX','ReadWritePaths':'+/reconstruction/runtime','UMask':'0077','Restart':'no',
        'RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2','KillMode':'control-group','SendSIGKILL':'yes',
        'FinalKillSignal':'SIGKILL','MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32','LimitCORE':'0',
        'LimitFSIZE':'65536','StartLimitIntervalSec':'0','BindReadOnlyPaths':binds,
        'StandardOutput':'append:'+str(root/'reconstruction/runtime/stdout.log'),
        'StandardError':'append:'+str(root/'reconstruction/runtime/stderr.log'),'WorkingDirectory':'/reconstruction'}
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit]
    argv+=['--property='+key+'='+item for key,item in policy.items()]
    argv+=['--setenv='+key+'='+item for key,item in{'PATH':'/usr/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items()]
    code,_,_=run([*argv,'--','/usr/bin/python3','-I','-S','-B','/reconstruction/worker.py',mode]);need(code==0,'unit_start_refused')
    write(LAB/('START-'+mode+'.json'),enc({'schema':1,'original_before':before,'policy':policy,'only_new_unit_started':unit}),0o600)
    return{'phase':'started','mode':mode,'unit':unit,'properties':properties(unit)}


def status(a):
    owned();result={}
    for mode in MODES:
        unit=UNIT_BASE+'-'+mode+'.service';props=properties(unit);folder=LAB/(mode+'-root')/'reconstruction/runtime'
        sizes={name:(folder/name).stat().st_size for name in('stdout.log','stderr.log')};need(sum(sizes.values())<=65536,'unit_output_bound')
        result[mode]={'properties':props,'group_empty':empty(unit,props),'result_present':(folder/'RESULT.json').exists(),'output_bytes':sizes}
    return{'phase':'status','units':result}


def stop(a):
    owned();states={}
    for mode in MODES:
        unit=UNIT_BASE+'-'+mode+'.service';before=properties(unit)
        if before.get('LoadState')!='not-found':code,_,_=run(['/usr/bin/systemctl','stop',unit]);need(code==0)
        after=properties(unit);need(empty(unit,after),'group_not_empty');states[mode]={'before_stop':before,'after_stop':after,'group_empty':True}
    original=original_snapshot();installed=decode(read(LAB/'INSTALL.json',32768));need(unchanged(installed['original_before'],original),'original_changed')
    if not(LAB/'FINAL.json').exists():write(LAB/'FINAL.json',enc({'schema':1,'units':states,'new_groups_empty':True,
        'original_after':original,'original_unchanged':True,'old_four_groups_fenced':True}),0o600)
    return{'phase':'stopped','new_groups_empty':True,'original_unchanged':True,'old_four_groups_fenced':True}


def fetch(a):
    owned();need(a.artifact in('RESULT-negative.json','RESULT-complete.json','INSTALL.json','FINAL.json'))
    if a.artifact.startswith('RESULT-'):path=LAB/(a.artifact[7:-5]+'-root')/'reconstruction/runtime/RESULT.json';owner=65534
    else:path=LAB/a.artifact;owner=0
    raw=read(path,32768,owner);return{'name':a.artifact,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii')}


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    p.add_argument('--controller-sha256',required=True);p.add_argument('--desktop-proof-sha256');p.add_argument('--runtime-review-sha256')
    p.add_argument('--mode',choices=MODES);p.add_argument('--artifact');a=p.parse_args()
    need(re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None);globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    print(json.dumps(globals()[a.action](a),sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        code=str(exc)if type(exc)is ValueError and re.fullmatch('[a-z_]{1,64}',str(exc))is not None else None
        print(json.dumps({'refused':True,'error_type':type(exc).__name__,'refusal_code':code,'scope':'fixed_c824_only'}));raise SystemExit(1)from None
