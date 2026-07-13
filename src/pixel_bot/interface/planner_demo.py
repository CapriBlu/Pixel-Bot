import json

from pixel_bot.core.planner import Planner


def main() -> None:
    planner = Planner()

    goal = input("Obiettivo: ").strip()
    plan = planner.create_plan(goal)

    print()
    print("Piano generato:")
    print(
        json.dumps(
            plan.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()