# FAQ

## Why is fault coverage low even when tests pass?

Pattern execution pass/fail is different from broad structural fault detectability. Check fault lists and undetected categories.

## Do I need EDA tools for CI?

No, dry-run mode supports artifact generation for most analysis flows.

## How do I enable multi-core verification?

Pass `--multi-core-config config/multi_core_config.example.txt`.

## How do I enable ML optimization?

Pass `--ml-pattern-optimize --ml-target-coverage 95`.

