# Contributing

Thanks for your interest in InsightBridge. This started as a portfolio build with an emphasis on verified, testable claims, and issues and pull requests are welcome.

## Getting started

Fork and clone the repo, then follow the Quick start section in the README to install dependencies (Docker Postgres, the FastAPI backend, and the Next.js web app). Before opening a pull request, run the test suite locally: `cd apps/api && pytest -q && ruff check insightbridge tests`.

## Making changes

Keep changes focused and describe what changed and why in the pull request. Match the existing code style, which is enforced by `ruff` for the Python API. Add or update tests for new behavior rather than removing existing coverage, and if your change affects what actually works end to end, update the "What works today (verified)" table in the README rather than just the feature list.

## Pull requests

Reference any related issue, confirm that GitHub Actions CI passes on your branch, and describe how you tested the change locally, including whether you ran it in demo mode or with a real `OPENAI_API_KEY`.

## Reporting issues

Please include steps to reproduce, expected versus actual behavior, and any relevant logs or error messages. If the issue is about a specific claim in the README, please note which row of the verified/not-verified table it relates to.

## Code of conduct

Be respectful and constructive. This is an actively maintained portfolio project, so response times may vary.
