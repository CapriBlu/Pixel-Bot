from pixel_bot.developer.checklist_engine import Checklist, ChecklistStatus


def test_parses_numbered_and_checkbox_items():
    checklist = Checklist.from_text("1. Analizza\n2) Correggi\n- [x] Verifica")
    assert [item.text for item in checklist.items] == ["Analizza", "Correggi", "Verifica"]
    assert checklist.items[-1].status == ChecklistStatus.COMPLETED


def test_completion_requires_all_items_terminal():
    checklist = Checklist.from_text("1. Uno\n2. Due")
    checklist.get(1).complete("ok")
    assert not checklist.is_complete
    checklist.get(2).mark_unavailable("non applicabile")
    assert checklist.is_complete


def test_remaining_excludes_terminal_items():
    checklist = Checklist.from_text("1. Uno\n2. Due")
    checklist.get(1).complete()
    assert [item.id for item in checklist.remaining] == [2]
