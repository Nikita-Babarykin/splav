from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from bot.config import Settings


SYSTEM_PROMPT = """Ты редактор и автор, который переписывает тексты в стиле автора по примерам.

Задача:
- сохранить исходный смысл текста;
- сделать текст похожим по тону, ритму и подаче на примеры;
- сохранить язык исходника;
- не выдумывать факты, события, цифры, даты, имена и ссылки;
- не добавлять рекламу, призывы к покупке, даты и ссылки, если этого не было в исходном тексте;
- оставить текст живым, разговорным и образным, но без бессмысленного украшательства;
- если в исходнике есть ссылки, названия, даты или числовые данные, перенеси их аккуратно и без изменений;
- вернуть только готовый переписанный текст без объяснений.

Что важно в стиле:
- разговорная интонация;
- ощущение, что автор рассказывает историю живому человеку;
- конкретные бытовые детали вместо абстракций;
- легкая самоирония, наблюдательность, доброжелательная дерзость;
- короткие и средние абзацы, читаемые в Telegram;
- допускается уместная эмоциональность, но без пафоса ради пафоса.
"""


@dataclass(slots=True)
class RewriteResult:
    text: str


class RewriteError(Exception):
    pass


class StyleRewriter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    def rewrite(self, source_text: str) -> RewriteResult:
        text = source_text.strip()
        if not text:
            raise RewriteError("Пустой текст нельзя переписать.")

        if len(text) > self._settings.max_input_chars:
            raise RewriteError(
                f"Текст слишком длинный. Сейчас лимит {self._settings.max_input_chars} символов."
            )

        style_examples = self._load_style_examples()
        user_prompt = self._build_user_prompt(text, style_examples)

        try:
            response = self._client.responses.create(
                model=self._settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
            )
        except Exception as error:
            raise RewriteError(
                "Не удалось получить ответ от OpenAI. Проверь ключ, модель и доступность API."
            ) from error

        rewritten_text = self._extract_text(response).strip()
        if not rewritten_text:
            raise RewriteError("Модель вернула пустой ответ.")

        return RewriteResult(text=rewritten_text)

    def _load_style_examples(self) -> str:
        try:
            content = self._settings.style_examples_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as error:
            raise RewriteError(
                f"Файл с примерами не найден: {self._settings.style_examples_path}"
            ) from error

        if not content:
            raise RewriteError("Файл с примерами стиля пустой.")

        return content

    @staticmethod
    def _build_user_prompt(source_text: str, style_examples: str) -> str:
        return f"""Ниже идут примеры текстов автора. Используй их как ориентир по стилю, подаче, ритму, юмору и интонации.

ПРИМЕРЫ СТИЛЯ:
{style_examples}

ИСХОДНЫЙ ТЕКСТ:
{source_text}

Перепиши исходный текст в стиле автора из примеров.
Сохрани смысл, факты, ссылки, даты, имена и структуру настолько, насколько это возможно без потери естественности.
Верни только итоговый текст.
"""

    @staticmethod
    def _extract_text(response: object) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        output_items = getattr(response, "output", None) or []
        fragments: list[str] = []

        for item in output_items:
            for content_item in getattr(item, "content", []) or []:
                text_value = getattr(content_item, "text", None)
                if text_value:
                    fragments.append(text_value)

        return "\n".join(fragments)
