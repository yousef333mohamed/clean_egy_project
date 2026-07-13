"""Retrieval ranking, filter, and authority metrics."""

from app.evaluation.evaluators import _result


class RetrievalEvaluator:
    name = "retrieval"

    @staticmethod
    def metrics(expected: list[str], retrieved: list[str]) -> dict[str, float]:
        expected_set = set(expected)
        values: dict[str, float] = {}
        for k in (3, 5, 8):
            top = retrieved[:k]
            relevant = sum(item in expected_set for item in top)
            values[f"retrieval_recall_at_{k}"] = relevant / len(expected_set) if expected_set else float(not top)
            values[f"retrieval_precision_at_{k}"] = relevant / len(top) if top else float(not expected_set)
        rank = next((index + 1 for index, item in enumerate(retrieved) if item in expected_set), None)
        values["mean_reciprocal_rank"] = 1 / rank if rank else 0
        return values

    async def evaluate(self, case, actual):
        values = self.metrics(case.expected_documents, actual.retrieved_documents)
        expected_filters = case.expected.get("filters", {})
        filter_ok = all(actual.filters.get(key) == value for key, value in expected_filters.items())
        expected_authority = case.expected.get("authority_labels", {})
        actual_authority = {item.get("document_id"): item.get("authority_level") for item in actual.retrieved_items}
        authority_ok = all(actual_authority.get(key) == value for key, value in expected_authority.items())
        insufficient_ok = actual.insufficient_context == case.expected_insufficient_context
        values.update(
            metadata_filter_accuracy=float(filter_ok), authority_label_accuracy=float(authority_ok), insufficient_context_accuracy=float(insufficient_ok)
        )
        passed = values["retrieval_recall_at_5"] == 1 and filter_ok and authority_ok and insufficient_ok
        return _result(passed, sum(values.values()) / len(values), "Retrieval expectations were not met", metrics=values)
