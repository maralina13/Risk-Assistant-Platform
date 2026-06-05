from __future__ import annotations

from typing import Any


Risk = dict[str, Any]
State = dict[str, Any]


def contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def priority_score(priority: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(priority, 1)


def score_to_number(priority: str) -> int:
    return {"high": 9, "medium": 4, "low": 2}.get(priority, 2)


def requirement_analyst(state: State) -> State:
    text = state["normalized_text"]
    requirements = []
    constraints = []
    unclear_points = []

    if contains_any(text, ["команда", "людей", "человек"]):
        requirements.append("учесть ограниченные ресурсы команды")
    if contains_any(text, ["mvp", "первая версия"]):
        requirements.append("собрать первую версию продукта без лишних функций")

    if contains_any(text, ["полгода", "6 месяцев", "месяц", "недель", "срок"]):
        constraints.append("есть ограничение по срокам")
    if contains_any(text, ["двух человек", "2 человек", "маленькая команда"]):
        constraints.append("маленькая команда")
    if contains_any(text, ["бюджет", "денег", "бесплат", "нет средств"]):
        constraints.append("ограниченный бюджет")
    if contains_any(text, ["турц", "страны", "международ", "расширять"]):
        constraints.append("планируется запуск или расширение по разным регионам")

    if not requirements:
        requirements.append("уточнить основные функции продукта")
    if not constraints:
        constraints.append("ограничения явно не описаны")

    unclear_points.extend(
        [
            "кто первый пользователь продукта",
            "какая функция считается главной для MVP",
            "как будет проверяться качество данных",
        ]
    )

    state["requirements"] = {
        "goal": f"оценить реалистичность проекта: {state['project_title']}",
        "functional_requirements": requirements,
        "constraints": constraints,
        "unclear_points": unclear_points,
    }
    state["trace"].append({"agent": "Requirement Analyst Agent", "action": "requirements_extracted"})
    return state


def risk_analyst(state: State) -> State:
    text = state["normalized_text"]
    risks: list[Risk] = []

    def add(category: str, risk: str, priority: str, mitigation: str) -> None:
        risks.append(
            {
                "id": f"{category[:4]}-{len(risks) + 1:03d}",
                "category": category,
                "risk": risk,
                "probability": "high" if priority == "high" else "medium",
                "impact": "high" if priority in {"high", "medium"} else "low",
                "priority": priority,
                "score": score_to_number(priority),
                "mitigation": mitigation,
            }
        )

    if contains_any(text, ["двух человек", "2 человек", "маленькая команда"]):
        add(
            "organizational",
            "маленькая команда может не успеть закрыть разработку, тестирование, дизайн и проверку идеи",
            "high",
            "разделить роли и оставить в MVP только одну основную пользовательскую задачу",
        )
    if contains_any(text, ["полгода", "6 месяцев", "месяц", "недель", "срок"]):
        add(
            "schedule",
            "срок может уйти на второстепенные функции вместо проверки главной ценности продукта",
            "medium",
            "разбить работу на этапы: прототип, база данных, тестирование, доработка",
        )
    if contains_any(text, ["пользовател", "рынок", "релевант", "нужен", "тратить"]):
        add(
            "market",
            "спрос пока не подтверждён реальными пользователями",
            "high",
            "провести 10-15 интервью и проверить, готовы ли люди пользоваться продуктом регулярно",
        )
    if contains_any(text, ["аллерг", "без глютена", "без лактозы", "кафе", "ресторан", "карта"]):
        add(
            "data_quality",
            "ошибки в данных о заведениях и аллергенах могут привести к опасным рекомендациям",
            "high",
            "проверять источники данных, дату обновления и добавить ручную модерацию записей",
        )
    if contains_any(text, ["турц", "страны", "международ", "расширять", "город"]):
        add(
            "product",
            "слишком широкий географический запуск может размыть MVP и усложнить поддержку данных",
            "medium",
            "начать с одного города или региона и расширяться только после проверки повторяемого сценария",
        )
    if contains_any(text, ["бюджет", "денег", "бесплат", "нет средств"]):
        add(
            "financial",
            "платные API, хостинг и сбор данных могут выйти за рамки бюджета",
            "medium",
            "выбрать бесплатные лимиты сервисов и ограничить число запросов в MVP",
        )

    if not risks:
        add(
            "technical",
            "техническая сложность проекта пока не описана достаточно подробно",
            "medium",
            "описать стек, основные функции и критерии готовности MVP",
        )
        add(
            "market",
            "непонятно, кто именно будет первым пользователем продукта",
            "medium",
            "выбрать одну целевую группу и проверить проблему на интервью",
        )

    state["risks"] = sorted(risks, key=lambda item: item["score"], reverse=True)
    state["trace"].append({"agent": "Risk Analyst Agent", "action": "risks_identified"})
    return state


def mitigation_planner(state: State) -> State:
    plan = []
    for risk in state["risks"]:
        plan.append(
            {
                "risk_id": risk["id"],
                "owner": owner_for_category(risk["category"]),
                "prevention": risk["mitigation"],
                "backup_plan": backup_for_category(risk["category"]),
                "success_metric": metric_for_category(risk["category"]),
            }
        )
    state["mitigation_plan"] = plan
    state["trace"].append({"agent": "Mitigation Planner Agent", "action": "mitigation_plan_created"})
    return state


def owner_for_category(category: str) -> str:
    return {
        "technical": "разработчик",
        "schedule": "тимлид или ответственный за план",
        "organizational": "вся команда",
        "financial": "ответственный за ресурсы",
        "data_quality": "ответственный за данные",
        "market": "ответственный за проверку пользователей",
        "product": "product owner",
    }.get(category, "команда")


def backup_for_category(category: str) -> str:
    return {
        "technical": "заменить сложную функцию ручной или упрощённой версией",
        "schedule": "убрать необязательные функции из первой версии",
        "organizational": "перераспределить задачи и сократить scope",
        "financial": "оставить только бесплатные инструменты и отложить платные интеграции",
        "data_quality": "показывать только проверенные места и явно помечать непроверенные данные",
        "market": "изменить целевую аудиторию или сценарий использования",
        "product": "ограничить запуск одним городом или одной категорией заведений",
    }.get(category, "сократить объём MVP")


def metric_for_category(category: str) -> str:
    return {
        "technical": "основной сценарий работает без ручного вмешательства",
        "schedule": "MVP готов к проверке до конца срока",
        "organizational": "каждая задача имеет ответственного",
        "financial": "MVP работает без превышения бюджета",
        "data_quality": "для каждой записи указан источник и дата проверки",
        "market": "есть подтверждение интереса от первых пользователей",
        "product": "первый запуск ограничен понятной территорией и сценарием",
    }.get(category, "есть понятный критерий готовности")


def critic_validator(state: State) -> State:
    problems = []
    high_risks = [risk for risk in state["risks"] if risk["priority"] == "high"]

    if not state["requirements"]["functional_requirements"]:
        problems.append("Requirement Analyst не выделил требования")
    if not state["risks"]:
        problems.append("Risk Analyst не нашёл риски")
    if len(state["mitigation_plan"]) != len(state["risks"]):
        problems.append("не для всех рисков есть план снижения")
    if len(high_risks) >= 2 and state["revision_count"] == 0:
        problems.append("для идеи с несколькими сильными рисками нужен более осторожный итог")

    if problems:
        state["validation"] = {
            "status": "needs_revision",
            "reason": "; ".join(problems),
            "route_to": "Mitigation Planner Agent",
        }
        state["trace"].append({"agent": "Critic / Validator Agent", "action": "route_to_mitigation_planner"})
    else:
        state["validation"] = {
            "status": "approved",
            "reason": "требования, риски, матрица и план снижения согласованы между собой",
            "route_to": "Report Writer Agent",
        }
        state["trace"].append({"agent": "Critic / Validator Agent", "action": "route_to_report_writer"})
    return state


def revise_after_critic(state: State) -> State:
    state["revision_count"] += 1
    state["recommendations"].insert(0, "не начинать полную версию продукта до проверки самых сильных рисков")
    for item in state["mitigation_plan"]:
        item["backup_plan"] = f"{item['backup_plan']}; при нехватке времени перенести рискованную часть после MVP"
    state["trace"].append({"agent": "Mitigation Planner Agent", "action": "plan_revised_after_critic"})
    return state


def choose_decision(state: State) -> None:
    high_count = sum(1 for risk in state["risks"] if risk["priority"] == "high")
    if high_count >= 3:
        decision = "продолжать только через маленький MVP после проверки спроса"
        reason = "найдено несколько сильных рисков: данные, рынок, команда или масштаб запуска"
    elif high_count >= 1:
        decision = "идею можно продолжать, но сначала нужно сузить объём"
        reason = "есть важные риски, которые лучше проверить до полноценной разработки"
    else:
        decision = "идею можно прорабатывать дальше"
        reason = "критичных рисков по описанию немного, но нужны уточнения по MVP"

    state["decision"] = {"recommendation": decision, "reason": reason}
    state["recommendations"] = [
        "выбрать одну главную функцию для MVP",
        "проверить идею на небольшой группе реальных пользователей",
        "отдельно проверить самый высокий риск из матрицы",
        "после проверки решить, расширять проект или менять идею",
    ]


def report_writer(state: State) -> str:
    risk_rows = "\n".join(
        "| {id} | {category} | {risk} | {probability} | {impact} | {score} | {priority} |".format(**risk)
        for risk in state["risks"]
    )
    mitigation_rows = "\n".join(
        "- **{risk_id}**: ответственный: {owner}; профилактика: {prevention}; запасной план: {backup_plan}; метрика: {success_metric}".format(
            **item
        )
        for item in state["mitigation_plan"]
    )
    requirements = "\n".join(f"- {item}" for item in state["requirements"]["functional_requirements"])
    constraints = "\n".join(f"- {item}" for item in state["requirements"]["constraints"])
    unclear = "\n".join(f"- {item}" for item in state["requirements"]["unclear_points"])
    recommendations = "\n".join(f"- {item};" for item in state["recommendations"])
    trace_rows = "\n".join(
        f"| {index} | {item['agent']} | {item['action']} |" for index, item in enumerate(state["trace"], start=1)
    )
    high_risks = [risk for risk in state["risks"] if risk["priority"] == "high"]
    strongest = "; ".join(risk["risk"] for risk in high_risks[:3]) or "сильных рисков не найдено"

    return f"""# Отчёт Multi-Agent Project Risk Assistant

## 1. Описание проекта

**Название:** {state["project_title"]}

{state["project_description"]}

## 2. Итоговое решение по проекту

**Решение:** {state["decision"]["recommendation"]}.

**Почему:** {state["decision"]["reason"]}.

**Самые важные риски:** {strongest}.

## 3. Что понял Requirement Analyst

**Цель:** {state["requirements"]["goal"]}.

**Требования:**
{requirements}

**Ограничения:**
{constraints}

**Неясные места:**
{unclear}

## 4. Матрица рисков

| ID | Категория | Риск | Вероятность | Влияние | Score | Приоритет |
| --- | --- | --- | --- | --- | ---: | --- |
{risk_rows}

## 5. Как матрица рисков влияет на итог

Матрица влияет на итог напрямую: сильные риски получают больший score. Если сильных рисков несколько, система не рекомендует сразу делать полную версию продукта. В таком случае правильнее сузить MVP, проверить самую рискованную часть и только потом расширять проект.

## 6. Что предлагает Mitigation Planner

{mitigation_rows}

## 7. Проверка Critic / Validator Agent

**Статус:** {state["validation"]["status"]}

**Причина:** {state["validation"]["reason"]}

**Количество доработок:** {state["revision_count"]}

## 8. Финальный вывод по идее

Проект не нужно бросать только из-за рисков. Но начинать с широкой версии опасно: сначала нужно доказать, что пользователям действительно нужен такой продукт, и что команда сможет поддерживать качество данных. Поэтому лучший следующий шаг — маленький MVP с понятной территорией, одной главной функцией и ручной проверкой данных.

## 9. Что проверить дальше

{recommendations}

## 10. Как работали агенты

Пользователь -> API Gateway -> Project Intake Service -> Risk Analysis Service -> внутренний multi-agent workflow -> Report Service -> Финальный отчёт

| Step | Agent | Action |
| ---: | --- | --- |
{trace_rows}

## 11. Ограничения анализа

- Это предварительный анализ по описанию пользователя, а не полноценное исследование рынка.
- Внутри Risk Analysis Service используется воспроизводимый rule-based multi-agent workflow без внешней LLM.
- Категории рисков выбираются системой по содержанию текста, поэтому итог зависит от того, насколько подробно пользователь описал проект.
"""


def run_multi_agent_analysis(project_title: str, project_description: str) -> State:
    state: State = {
        "project_title": project_title,
        "project_description": project_description,
        "normalized_text": f"{project_title} {project_description}".lower(),
        "requirements": {},
        "risks": [],
        "mitigation_plan": [],
        "validation": {},
        "decision": {},
        "recommendations": [],
        "revision_count": 0,
        "trace": [],
    }

    state = requirement_analyst(state)
    state = risk_analyst(state)
    choose_decision(state)
    state = mitigation_planner(state)
    state = critic_validator(state)

    while state["validation"]["status"] == "needs_revision" and state["revision_count"] < 2:
        state = revise_after_critic(state)
        state = critic_validator(state)

    state["report"] = report_writer(state)
    return state
