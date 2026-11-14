"""Select only the facilitator policy and one stakeholder's hidden profile."""

STAKEHOLDERS = {
    "helena": ("CEO Helena Duarte", "Helena"),
    "roberto": ("Diretor industrial Roberto Nogueira", "Roberto"),
    "marcos": ("Manutenção Marcos Vieira", "Marcos"),
    "ana": ("Comercial Ana Paiva", "Ana"),
    "lucas": ("PCP Lucas Mendes", "Lucas"),
    "beatriz": ("Financeiro Beatriz Campos", "Beatriz"),
}


def _between(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        raise ValueError("facilitator guide is missing a required section")
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def build_decision_context(guide_text: str, stakeholder_id: str) -> dict[str, str]:
    if stakeholder_id not in STAKEHOLDERS:
        raise ValueError("stakeholder_id is not in the stakeholder catalog")
    title, first_name = STAKEHOLDERS[stakeholder_id]
    policy_section = _between(guide_text, "## Política de liberação de informação", "## Entrevistas")
    generic_policy = policy_section.split("### Seis perfis", 1)[0].strip()
    if "### Critérios de concessão" in policy_section:
        generic_policy += "\n\n" + policy_section.split("### Critérios de concessão", 1)[1].strip()
    policy_lines = [
        line for line in policy_section.splitlines()
        if line.startswith("|") and title.casefold() in line.casefold()
    ]
    if not policy_lines:
        raise ValueError("facilitator guide is missing this stakeholder's policy row")

    profile_section = _between(guide_text, "## Entrevistas", "## Eventos")
    profile_lines = [
        line for line in profile_section.splitlines()
        if line.startswith(f"- **{first_name}:**")
    ]
    if len(profile_lines) != 1:
        raise ValueError("facilitator guide is missing this stakeholder's profile")

    return {
        "stakeholder_id": stakeholder_id,
        "stakeholder_title": title,
        "policy": generic_policy,
        "stakeholder_policy": policy_lines[0],
        "stakeholder_profile": profile_lines[0],
    }
