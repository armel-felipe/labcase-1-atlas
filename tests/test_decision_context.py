import unittest

from release_service.decision_context import build_decision_context


GUIDE = """# Guide

## Política de liberação de informação
Política comum de concessão: finalidade clara, campos mínimos e salvaguardas.

### Critérios de concessão
- Completa: finalidade proporcional.
- Parcial: limitar período ou colunas.

### Seis perfis e respostas
| Stakeholder | Tendência |
|---|---|
| CEO Helena Duarte | Não escolhe culpado sem cronologia |
| Comercial Ana Paiva | Prefere dados agregados e anonimizados |

## Entrevistas — segredos de personagem
- **Helena:** segredo executivo da Helena.
- **Ana:** segredo reservado da Ana e seus limites.

## Eventos inesperados e evolução
Segredo de outro capítulo que não é necessário para esta decisão.
"""


class DecisionContextTests(unittest.TestCase):
    def test_context_contains_policy_and_only_selected_stakeholder(self):
        context = build_decision_context(GUIDE, "ana")

        self.assertIn("finalidade clara", context["policy"])
        self.assertIn("dados agregados e anonimizados", context["stakeholder_policy"])
        self.assertIn("segredo reservado da Ana", context["stakeholder_profile"])
        self.assertNotIn("segredo executivo da Helena", str(context))
        self.assertNotIn("Segredo de outro capítulo", str(context))

    def test_rejects_unknown_stakeholder_ids(self):
        with self.assertRaises(ValueError):
            build_decision_context(GUIDE, "unknown")


if __name__ == "__main__":
    unittest.main()
