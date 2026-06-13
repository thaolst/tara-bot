"""Claude agent with tool-calling - Tara v3.

Them so voi v2:
- get_lucky_dates tool: xem ngay gio tot theo Am Lich (Can Chi, Hoang Dao, xung hop tuoi)
- User profile (birth_date) luu trong session - hoi 1 lan, dung mai
- System prompt mo rong: huong dan Claude ket hop lucky dates + search flights
"""

from __future__ import annotations

import json
import asyncio
import time
from typing import Any, AsyncGenerator
from datetime import date

from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock
from openai import OpenAI

from .config import Config
from .tools.serpapi import search_flights, search_shopping
from .tools.lucky_dates import get_lucky_dates, get_lucky_dates_group

# ── System prompt - FROZEN (Anthropic cache) ──────────────────────────

SYSTEM_PROMPT = """Ban la Tara Bot - agent thong minh chuyen tim ve may bay, san gia do, va xem ngay gio tot.

NGUYEN TAC:
- Tra loi bang tieng Viet tu nhien, than thien.
- Khi user hoi ve may bay, goi tool search_flights.
- Khi user hoi gia san pham, goi tool search_shopping.
- Sau khi tool tra ket qua, chuyen tiep NGUYEN VAN ket qua do cho user, chi them 1-2 cau ngan.
- KHONG reformat lai ket qua tu tool.
- Co the noi chuyen thong thuong - khong can goi tool.

XEM NGAY GIO TOT (get_lucky_dates) - CHI KHI USER CHU DONG HOI:
- CHI goi get_lucky_dates khi user hoi ro rang ve: ngay tot, gio tot, xem ngay, hop tuoi, xuat hanh, nen di ngay nao.
- Neu co NHIEU nguoi cung di (gia dinh, ban be, nhom 2-5 nguoi) -> dung get_lucky_dates_group, truyen list birth_dates.
- KHONG tu dong xem ngay khi user chi hoi ve may bay. Vi du "tim ve di Da Nang cuoi tuan" -> chi goi search_flights, KHONG xem ngay.
- Neu user hoi ket hop ("xem ngay tot roi tim ve di [noi X]"):
  1. Goi get_lucky_dates (hoac _group neu nhieu nguoi) truoc de biet ngay tot
  2. Goi search_flights cho ngay tot nhat
  3. Tong hop: "Ngay [X] tot nhat cho ban, ve ngay do gia [Y]"

USER PROFILE:
- Neu tool get_lucky_dates can birth_date nhung chua co trong lich su hoi thoai, hoi user: 
  "Ban sinh nam nao? (chi can nam cung duoc, hoac ngay sinh day du va gio sinh neu muon chinh xac hon)"
- KHONG bat buoc user nhap du ngay/gio. Chi co nam van xem duoc. User dua bao nhieu thi dung bay nhieu.
- Sau khi biet, ghi nho va su dung cho cac lan sau trong cung cuoc tro chuyen.

MAC DINH CHO CAU HOI MO HO VE THOI GIAN:
- "cuoi tuan" -> thu Sau tuan gan nhat (khong qua khu)
- "tuan sau" -> tuan tiep theo
- "thang toi" -> tu ngay 1 thang sau"""

# ── Tool definitions ──────────────────────────────────────────────────

FLIGHT_TOOL: dict[str, Any] = {
    "name": "search_flights",
    "description": "Tim chuyen bay. Tra ve gia, hang, gio bay.",
    "input_schema": {
        "type": "object",
        "properties": {
            "departure_id":  {"type": "string", "description": "Ma san bay di (IATA). Mac dinh SGN"},
            "arrival_id":    {"type": "string", "description": "Ma san bay den (IATA)"},
            "outbound_date": {"type": "string", "description": "Ngay di (YYYY-MM-DD)"},
            "return_date":   {"type": "string", "description": "Ngay ve (YYYY-MM-DD)"},
            "adults":        {"type": "integer", "description": "So nguoi lon. Mac dinh 1"},
        },
        "required": ["arrival_id"],
    },
}

SHOPPING_TOOL: dict[str, Any] = {
    "name": "search_shopping",
    "description": "Tim san pham, so sanh gia.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Ten san pham can tim"},
        },
        "required": ["query"],
    },
}

LUCKY_DATE_TOOL: dict[str, Any] = {
    "name": "get_lucky_dates",
    "description": (
        "Xem ngay gio tot/xau theo Am Lich cho 1 hoac NHIEU nguoi (ca gia dinh). "
        "Chi goi khi user CHU DONG hoi ve ngay tot, gio tot, xem ngay, hop tuoi, xuat hanh. "
        "KHONG tu dong goi khi user chi tim ve may bay. "
        "Tinh Can Chi ngay, gio Hoang Dao, moi quan he voi tuoi user (Luc Hop, Tam Hop, Luc Xung)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "birth_date": {
                "type": "string",
                "description": "Nam sinh (YYYY) hoac ngay sinh day du (YYYY-MM-DD). "
                               "Cang day du cang chinh xac, nhung chi co nam van chay duoc. "
                               "Lay tu lich su hoi thoai neu co. Neu chua co gi, hoi user.",
            },
            "birth_time": {
                "type": "string",
                "description": "Gio sinh (HH:MM), tuy chon. Chi truyen khi user cung cap.",
            },
            "birth_dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sach ngay sinh cho NHIEU nguoi (vd: ['1995', '1965']). "
                               "Dung khi user hoi cho gia dinh / nhom ban.",
            },
            "from_date": {
                "type": "string",
                "description": "Bat dau xem tu ngay nao (YYYY-MM-DD). Mac dinh hom nay.",
            },
            "days": {
                "type": "integer",
                "description": "So ngay can xem (mac dinh 14, toi da 30).",
            },
        },
    },
}

LUCKY_GROUP_TOOL: dict[str, Any] = {
    "name": "get_lucky_dates_group",
    "description": (
        "Xem ngay xuat hanh hop cho NHIEU nguoi cung di (2-5 nguoi: gia dinh, ban be, nhom). "
        "CHI goi khi user chu dong hoi ngay tot VA cung cap thong tin nhieu nguoi. "
        "Tu dong loai ngay xung voi bat ky ai, tim ngay an toan cho ca nhom."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "birth_dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List nam sinh hoac ngay sinh cua moi nguoi. "
                               "Moi phan tu la YYYY hoac YYYY-MM-DD. Tron lan cung duoc.",
            },
            "from_date": {
                "type": "string",
                "description": "Bat dau xem tu ngay nao (YYYY-MM-DD). Mac dinh hom nay.",
            },
            "days": {
                "type": "integer",
                "description": "So ngay can xem (mac dinh 14, toi da 30).",
            },
        },
        "required": ["birth_dates"],
    },
}

ALL_TOOLS = [FLIGHT_TOOL, SHOPPING_TOOL, LUCKY_DATE_TOOL, LUCKY_GROUP_TOOL]
TOOL_FUNCTIONS: dict[str, Any] = {
    "search_flights":  search_flights,
    "search_shopping": search_shopping,
    "get_lucky_dates": get_lucky_dates,
    "get_lucky_dates_group": get_lucky_dates_group,
}
MAX_TOOL_ITERATIONS = 6  # tang len vi co the goi 2 tool lien tiep (lucky + flights)


# ── Agent ─────────────────────────────────────────────────────────────

class Agent:
    def __init__(self):
        self.mode = getattr(Config, 'llm_mode', 'anthropic') or 'anthropic'
        self.history: list[dict] = []
        # User profile - luu birth_date sau khi user cung cap
        self.user_profile: dict[str, str] = {}

        if self.mode == 'openai':
            self.client = OpenAI(
                api_key=Config.openai_api_key,
                base_url=Config.openai_base_url or None,
            )
            self.model = Config.openai_model or 'gemini-2.5-flash'
        else:
            self.client = Anthropic(api_key=Config.anthropic_api_key)
            self.model = 'claude-sonnet-4-6'

    def _system(self) -> list[dict]:
        """System prompt voi cache_control. Frozen - khong thay doi giua cac request."""
        return [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

    def _with_date(self, user_message: str) -> str:
        """Inject ngay hom nay + user profile vao user message."""
        today = date.today().strftime("%A, %d/%m/%Y")
        profile_str = ""
        if self.user_profile.get("birth_date"):
            profile_str = f"\n[User profile - birth_date: {self.user_profile['birth_date']}]"
        return f"[Hom nay: {today}]{profile_str}\n{user_message}"

    def _extract_profile(self, user_message: str) -> None:
        """Thu trich xuat birth_date tu tin nhan user neu chua co."""
        if self.user_profile.get("birth_date"):
            return
        # Tim 4 chu so lien tiep trong khoang nam hop le
        import re
        years = re.findall(r'\b(19[4-9]\d|200[0-9]|201[0-9]|202[0-4])\b', user_message)
        if years:
            self.user_profile["birth_date"] = years[0]

    def chat(self, user_message: str) -> str:
        """Sync chat - tool-use loop, tra ve text cuoi cung."""
        if self.mode == "openai":
            return self._chat_openai(user_message)

        self._extract_profile(user_message)
        messages = list(self.history)
        injected = self._with_date(user_message)
        messages.append({"role": "user", "content": injected})

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = self._call_claude(messages)
            messages.append({"role": "assistant", "content": response.content})

            u = response.usage
            print(
                f"[iter {iteration + 1}] "
                f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
                f"cache_create={getattr(u, 'cache_creation_input_tokens', 0)} "
                f"input={u.input_tokens} output={u.output_tokens} "
                f"stop={response.stop_reason}"
            )

            if response.stop_reason == "end_turn":
                reply = "\n".join(
                    b.text for b in response.content if isinstance(b, TextBlock)
                )
                self.history.append({"role": "user",      "content": injected})
                self.history.append({"role": "assistant", "content": response.content})
                return reply

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if not isinstance(block, ToolUseBlock):
                        continue
                    result = self._execute_tool(block)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     str(result),
                    })
                messages.append({"role": "user", "content": tool_results})
                continue

            break

        return "Xin loi, em khong the xu ly yeu cau nay. Thu lai voi cau hoi don gian hon nhe!"

    async def stream_chat(self, user_message: str) -> AsyncGenerator[str | dict, None]:
        """Async generator stream cho Telegram fake-streaming."""
        self._extract_profile(user_message)
        messages = list(self.history)
        injected = self._with_date(user_message)
        messages.append({"role": "user", "content": injected})

        for iteration in range(MAX_TOOL_ITERATIONS):
            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=self._system(),
                tools=ALL_TOOLS,
                thinking={"type": "adaptive"},
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    yield chunk

                final = stream.final_message()

            u = final.usage
            print(
                f"[stream iter {iteration + 1}] "
                f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
                f"stop={final.stop_reason}"
            )

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "end_turn":
                self.history.append({"role": "user",      "content": injected})
                self.history.append({"role": "assistant", "content": final.content})
                return

            if final.stop_reason == "tool_use":
                tool_results = []
                for block in final.content:
                    if not isinstance(block, ToolUseBlock):
                        continue
                    yield {"type": "tool_use", "name": block.name}
                    result = self._execute_tool(block)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     str(result),
                    })
                messages.append({"role": "user", "content": tool_results})
                continue

            break

    def _call_claude(self, messages: list) -> Any:
        for attempt in range(3):
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    system=self._system(),
                    tools=ALL_TOOLS,
                    thinking={"type": "adaptive"},
                    messages=messages,
                )
            except Exception as exc:
                if "429" in str(exc) or "rate_limit" in str(exc).lower():
                    time.sleep(30 * (attempt + 1))
                    continue
                raise
        raise Exception("Claude API: rate limit exceeded after 3 retries")

    def _call_openai(self, messages: list[dict[str, Any]]) -> Any:
        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in ALL_TOOLS
        ]
        for attempt in range(3):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self._system_text()}] + messages,
                    tools=tool_defs,
                    temperature=0.2,
                )
            except Exception as exc:
                if "429" in str(exc) or "rate_limit" in str(exc).lower():
                    time.sleep(30 * (attempt + 1))
                    continue
                raise
        raise Exception("OpenAI-compatible API: rate limit exceeded after 3 retries")

    def _parse_openai_response(self, response: Any) -> tuple[str, list[dict[str, Any]]]:
        choice = response.choices[0]
        message = choice.message
        reply_text = message.content or ""
        tool_calls = []
        for tc in getattr(message, "tool_calls", None) or []:
            tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                },
            })
        return reply_text, tool_calls

    def _system_text(self) -> str:
        return SYSTEM_PROMPT

    def _chat_openai(self, user_message: str) -> str:
        self._extract_profile(user_message)
        messages = list(self.history)
        injected = self._with_date(user_message)
        messages.append({"role": "user", "content": injected})

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._call_openai(messages)
            reply_text, tool_calls = self._parse_openai_response(response)

            if not tool_calls:
                self._save_history(user_message, reply_text)
                return reply_text

            assistant_msg = {
                "role": "assistant",
                "content": reply_text or None,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            for tc in tool_calls:
                result = self._execute_tool_name(tc["function"]["name"], tc["function"]["arguments"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        return "Xin loi, em khong the xu ly yeu cau nay. Thu lai voi cau hoi don gian hon nhe!"

    def _save_history(self, user_message: str, reply_text: str) -> None:
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply_text})

    def _execute_tool(self, block: ToolUseBlock) -> str:
        fn = TOOL_FUNCTIONS.get(block.name)
        if not fn:
            return f"Unknown tool: {block.name}"
        try:
            return fn(**block.input)
        except Exception as e:
            return f"Loi khi chay {block.name}: {e}"

    def _execute_tool_name(self, name: str, args: str) -> str:
        fn = TOOL_FUNCTIONS.get(name)
        if not fn:
            return f"Unknown tool: {name}"
        if isinstance(args, str):
            try:
                parsed = json.loads(args) if args else {}
            except Exception:
                parsed = {}
        else:
            parsed = dict(args)
        try:
            return fn(**parsed)
        except Exception as e:
            return f"Loi khi chay {name}: {e}"
