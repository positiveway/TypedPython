from common.parsing import *


def parse_func_definition(line):
    strip_line = line.strip()
    if re.match(r'def .+\((.*)\).*:', strip_line):
        params_line = strip_line[strip_line.find('(') + 1:strip_line.rfind(')')]
        if len(params_line) > 0:
            bracket_count = 0
            prev_cut_pos = 0
            params = []
            for ind, char in enumerate(params_line):
                if char in ['[', '(']:
                    bracket_count += 1
                elif char in [']', ')']:
                    bracket_count -= 1
                elif char == ',' and bracket_count == 0:
                    params.append(params_line[prev_cut_pos:ind])
                    prev_cut_pos = ind + 1

            params.append(params_line[prev_cut_pos:])
            return params

    return []
