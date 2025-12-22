from __future__ import annotations

from app.training.train_model import train_model, TrainConfig


def main() -> None:
    # Short training run for CI / dev: reduce boosting rounds so training finishes faster
    cfg = TrainConfig()
    cfg.num_boost_round = 100
    cfg.early_stopping_rounds = 10
    cfg.val_days = 14
    model_path = train_model(cfg)
    print(f"Trained (short) model saved to: {model_path}")


if __name__ == "__main__":
    main()
