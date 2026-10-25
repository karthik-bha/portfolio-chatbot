import asyncio
import json
from pathlib import Path

from app.schemas import Message
from app.services.llm import stream_reply

QUESTIONS = Path(__file__).parent / "questions.json"


async def ask(question: str) -> str:
    parts = []
    async for chunk in stream_reply([Message(role="user", content=question)]):
        parts.append(chunk)
    return "".join(parts)


async def main():
    cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        answer = await ask(case["question"])
        low = answer.lower()
        missing = [s for s in case["must_include"] if s.lower() not in low]
        leaked = [s for s in case["must_not_include"] if s.lower() in low]
        ok = not missing and not leaked
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']}")
        if not ok:
            print(f"   missing: {missing}  forbidden found: {leaked}")
            print(f"   answer: {answer[:300]!r}")
        await asyncio.sleep(1)  # be gentle with rate limits
    print(f"\n{passed}/{len(cases)} passed")


asyncio.run(main())