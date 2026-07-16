import types
import pytest

from pixel_bot.automation import mouse_controller as mc


def test_get_mouse_position_calls_pyautogui_position(monkeypatch):
    fake_pos = types.SimpleNamespace(x=123, y=456)

    monkeypatch.setattr(mc.pyautogui, 'position', lambda: fake_pos)

    pos = mc.get_mouse_position()

    assert pos is fake_pos
    assert pos.x == 123 and pos.y == 456


def test_move_mouse_validates_and_calls_moveTo(monkeypatch):
    called = []

    def fake_moveTo(x, y, duration=0.5):
        called.append((x, y, duration))

    monkeypatch.setattr(mc.pyautogui, 'moveTo', fake_moveTo)

    mc.move_mouse(10, 20, duration=0.8)

    assert called == [(10, 20, 0.8)]


def test_click_mouse_validates_and_calls_click(monkeypatch):
    called = []

    def fake_click(x, y):
        called.append((x, y))

    monkeypatch.setattr(mc.pyautogui, 'click', fake_click)

    mc.click_mouse(5, 6)

    assert called == [(5, 6)]


def test_right_double_scroll_and_drag(monkeypatch):
    click_calls = []
    double_calls = []
    scroll_calls = []
    move_calls = []
    drag_calls = []

    def fake_click(*args, **kwargs):
        click_calls.append((args, kwargs))

    def fake_doubleClick(x, y):
        double_calls.append((x, y))

    def fake_scroll(amount, **kwargs):
        scroll_calls.append((amount, kwargs))

    def fake_moveTo(x, y):
        move_calls.append((x, y))

    def fake_dragTo(x, y, duration=0.5):
        drag_calls.append((x, y, duration))

    monkeypatch.setattr(mc.pyautogui, 'click', fake_click)
    monkeypatch.setattr(mc.pyautogui, 'doubleClick', fake_doubleClick)
    monkeypatch.setattr(mc.pyautogui, 'scroll', fake_scroll)
    monkeypatch.setattr(mc.pyautogui, 'moveTo', fake_moveTo)
    monkeypatch.setattr(mc.pyautogui, 'dragTo', fake_dragTo)

    mc.right_click(7, 8)
    assert click_calls and click_calls[-1][1].get('button') == 'right'

    mc.double_click(1, 2)
    assert double_calls == [(1, 2)]

    mc.scroll(5)
    assert scroll_calls and scroll_calls[-1][0] == 5

    # scroll with coordinates
    mc.scroll(-3, x=10, y=20)
    assert scroll_calls[-1] == (-3, {'x': 10, 'y': 20})

    mc.drag_mouse(0, 0, 10, 10, duration=0.4)
    assert move_calls[0] == (0, 0)
    assert drag_calls[0] == (10, 10, 0.4)


def test_invalid_inputs_raise_errors():
    # invalid coordinate types
    with pytest.raises(ValueError):
        mc.move_mouse('a', 0)

    with pytest.raises(ValueError):
        mc.click_mouse(0, 'b')

    with pytest.raises(ValueError):
        mc.right_click(None, 1)

    # invalid duration
    with pytest.raises(ValueError):
        mc.move_mouse(0, 0, duration=1000)

    # scroll amount must be int
    with pytest.raises(ValueError):
        mc.scroll(2.5)

    # scroll with only one coordinate provided
    with pytest.raises(ValueError):
        mc.scroll(1, x=10)
