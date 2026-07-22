from pixel_bot.repository_consolidation import classify, parse_porcelain


def test_parse_porcelain_handles_modified_and_untracked():
    assert parse_porcelain([" M src/a.py", "?? file.txt"]) == [(" M", "src/a.py"), ("??", "file.txt")]


def test_backup_is_safe_cleanup():
    item = classify("??", "src/pixel_bot/example.py.pixelbot.bak")
    assert item.category == "backup_residuo"
    assert item.confidence == "alta"


def test_source_file_is_project_component():
    item = classify(" M", "src/pixel_bot/interface/control_center.py")
    assert item.category == "componente_progetto"


def test_image_requires_review():
    item = classify("??", "ChatGPT Image.png")
    assert item.category == "asset_da_verificare"
