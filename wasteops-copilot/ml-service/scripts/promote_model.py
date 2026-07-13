import argparse
from app.core.config import get_settings
from app.registry.model_registry import ModelRegistry
from app.registry.promotion_service import PromotionService


def main():
    parser = argparse.ArgumentParser(description="Explicit human-authorized model promotion")
    parser.add_argument("--model", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--stage", choices=["Staging", "Production", "Archived"], required=True)
    parser.add_argument("--approved-by", required=True)
    args = parser.parse_args()
    PromotionService(ModelRegistry(get_settings().model_artifact_directory)).promote(args.model, args.version, args.stage, approved_by=args.approved_by)


if __name__ == "__main__":
    main()
