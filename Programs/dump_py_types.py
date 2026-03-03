"""Extract Table 3/A2 type classifications from the Python generation script."""
import sys, json, os
os.chdir(r'F:\onedrive\__documents\papers\FLOPsExport')

source = open('Programs/add_calibration_v30.py', encoding='utf-8').read()

# Insert dump after table3 computation
marker = 'demand_data["table3"] = table3_data'
idx = source.index(marker) + len(marker)

dump_code = """
    import json as _json
    _t3 = {}
    for d in table3_data:
        _t3[d['iso']] = {
            'country': d['country'],
            'type_raw': d.get('type_raw', ''),
            'type_cr': d.get('type_cr', ''),
            'type_bilat': d.get('type_bilat', ''),
        }
    with open('Output/_py_table3_types.json', 'w') as _f:
        _json.dump(_t3, _f, indent=2)
"""

patched = source[:idx] + dump_code + source[idx:]

# Execute (full run including doc generation)
exec(compile(patched, 'patched.py', 'exec'))
