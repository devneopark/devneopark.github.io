import yaml

def parse(file_path: str):
    yml_lines = []
    body_lines = []
    in_yml = False
    yml_parsed = False

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "---":
                if not in_yml and not yml_parsed:
                    in_yml = True
                    continue
                elif in_yml:
                    in_yml = False
                    yml_parsed = True
                    continue

            if in_yml:
                yml_lines.append(line)
            else:
                body_lines.append(line)

    meta = {}
    if yml_lines:
        meta = yaml.safe_load("".join(yml_lines)) or {}

    body_text = "".join(body_lines).strip()
    return meta, body_text